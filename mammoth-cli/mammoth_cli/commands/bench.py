"""The ``bench`` command: one read command, N at a time, measured.

``mammoth bench COMMAND... --concurrency N --repeat R [--warmup W]`` (the flags after the
command, or as ``--concurrency=N`` anywhere) runs ``mammoth
COMMAND...`` ``N`` at a time, ``R`` rounds, in this one process. All calls share one
keep-alive connection pool (:class:`~mammoth_cli.runtime.embed_pool.EmbedRuntime`) and
one login, so a round measures the server, not process start, credential lookup or TLS.
Each round starts on a barrier: the ``N`` calls are released together, so the server
sees ``N`` requests at once. ``W`` unmeasured warm-up rounds (default 1) open the
connections first.

It reports the 50th and 95th percentile and the maximum of the request duration the SDK
already logs for every HTTP request (``duration_ms`` of the ``mammoth.http`` log), and of
the whole command as the caller sees it, with the status counts and the error codes of
the calls that failed.

Only a ``read`` command can be benched: running a write N x R times is not a measurement.
"""

from __future__ import annotations

import logging
import math
import shlex
import threading
import time
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from mammoth_cli import embed
from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.run import resolve_command_id
from mammoth_cli.context.resolver import ExplicitLogin, resolve_auth
from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.embed_pool import EmbedRuntime
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import resolved_project

CODE_INVALID_BENCH = "invalid_bench"
CODE_BENCH_COMMAND_REFUSED = "bench_command_refused"

#: The flags ``bench`` reads itself, each taking a whole number, and their defaults.
BENCH_FLAGS: dict[str, int] = {"--concurrency": 1, "--repeat": 1, "--warmup": 1}
#: The bounds of each flag: past them a run is a load test, not a benchmark.
_LIMITS: dict[str, tuple[int, int]] = {
    "--concurrency": (1, 64),
    "--repeat": (1, 100),
    "--warmup": (0, 10),
}
#: Seconds a call may wait at the round's barrier for the others.
_BARRIER_TIMEOUT = 60.0
_HTTP_LOGGER = "mammoth.http"

type Call = Callable[[], dict[str, Any]]


@dataclass(frozen=True)
class BenchArgs:
    """What to bench and how: the command, and the flags ``bench`` reads itself.

    Attributes:
        command: The command line after ``mammoth``, without the ``bench`` flags.
        concurrency: The calls released together in each round.
        repeat: The measured rounds.
        warmup: The unmeasured rounds before them.
    """

    command: tuple[str, ...]
    concurrency: int
    repeat: int
    warmup: int


def parse_args(tokens: Sequence[str]) -> BenchArgs:
    """Split ``bench``'s own flags from the command it benches.

    Args:
        tokens: Everything after ``mammoth bench`` that the global options left.

    Returns:
        The command and the flag values.

    Raises:
        CliError: ``invalid_bench`` when a flag has no whole number in its bounds,
            or no command is given.
    """
    values = dict(BENCH_FLAGS)
    command: list[str] = []
    rest = iter(tokens)
    for token in rest:
        name, sep, inline = token.partition("=")
        if name not in BENCH_FLAGS:
            # A command given as one quoted string ("project list") is its words.
            command.extend(shlex.split(token) if not command and " " in token else [token])
            continue
        raw = inline if sep else next(rest, None)
        values[name] = _whole_number(name, raw)
    if not command:
        raise _invalid("Name the command to bench, for example: mammoth bench project list.")
    return BenchArgs(
        command=tuple(command),
        concurrency=values["--concurrency"],
        repeat=values["--repeat"],
        warmup=values["--warmup"],
    )


def _whole_number(flag: str, raw: str | None) -> int:
    low, high = _LIMITS[flag]
    try:
        value = int(raw or "")
    except ValueError:
        raise _invalid(f"{flag} takes a whole number from {low} to {high}, got {raw!r}.") from None
    if not low <= value <= high:
        raise _invalid(f"{flag} takes a whole number from {low} to {high}, got {value}.")
    return value


def _invalid(message: str) -> CliError:
    return CliError(
        code=CODE_INVALID_BENCH,
        message=message,
        exit_status=EXIT_USAGE,
        hint="mammoth bench view list --concurrency 8 --repeat 5",
    )


def percentiles(values: Sequence[float]) -> dict[str, float | None]:
    """The nearest-rank 50th and 95th percentile and the maximum of ``values``.

    Args:
        values: The measurements, in any order.

    Returns:
        ``p50_ms``, ``p95_ms`` and ``max_ms``; each None when there are no values.
    """
    ordered = sorted(values)
    if not ordered:
        return {"p50_ms": None, "p95_ms": None, "max_ms": None}

    def rank(percent: int) -> float:
        return ordered[max(math.ceil(percent / 100 * len(ordered)), 1) - 1]

    return {"p50_ms": rank(50), "p95_ms": rank(95), "max_ms": ordered[-1]}


def run_rounds(call: Call, *, concurrency: int, rounds: int) -> list[dict[str, Any]]:
    """Run ``call`` ``concurrency`` at a time for ``rounds`` rounds.

    Each round starts ``concurrency`` threads that wait on one barrier and call
    together once all of them are ready, then waits for every call to end before
    the next round, so no round overlaps another.

    Args:
        call: Runs the command once and returns its envelope.
        concurrency: The calls released together in each round.
        rounds: How many rounds to run.

    Returns:
        Every call's envelope, round by round.
    """
    envelopes: list[dict[str, Any]] = []
    for _ in range(rounds):
        envelopes.extend(_round(call, concurrency))
    return envelopes


def _round(call: Call, concurrency: int) -> list[dict[str, Any]]:
    """One round: ``concurrency`` calls released together by a barrier, each one's envelope."""
    barrier = threading.Barrier(concurrency)
    results: list[dict[str, Any]] = [{} for _ in range(concurrency)]

    def worker(slot: int) -> None:
        barrier.wait(timeout=_BARRIER_TIMEOUT)
        results[slot] = call()

    threads = [threading.Thread(target=worker, args=(slot,)) for slot in range(concurrency)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


class _Durations(logging.Handler):
    """Keeps the ``duration_ms`` and status of every logged HTTP request."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.requests: list[tuple[float, str]] = []

    def emit(self, record: logging.LogRecord) -> None:
        fields = getattr(record, "mammoth", None)
        if isinstance(fields, dict) and fields.get("event") == "http":
            self.requests.append((float(fields["duration_ms"]), str(fields.get("status"))))


@contextmanager
def _http_durations() -> Iterator[_Durations]:
    """Collect the ``mammoth.http`` request durations while the block runs."""
    logger = logging.getLogger(_HTTP_LOGGER)
    handler = _Durations()
    level = logger.level
    if not logger.isEnabledFor(logging.INFO):
        logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(level)


def summarize(
    envelopes: Sequence[dict[str, Any]], requests: Sequence[tuple[float, str]]
) -> dict[str, Any]:
    """The bench result: call and request counts, errors, and duration percentiles.

    Args:
        envelopes: Every measured call's envelope.
        requests: Every measured HTTP request's ``duration_ms`` and status.

    Returns:
        ``calls``, ``errors``, ``error_codes``, ``http`` (requests, status counts and
        duration percentiles) and ``command_ms`` (the per-call ``elapsed_ms`` percentiles).
    """
    errors = Counter(
        str(envelope["error"].get("code")) for envelope in envelopes if "error" in envelope
    )
    elapsed = [
        float(body["elapsed_ms"])
        for envelope in envelopes
        if isinstance(body := envelope.get("error", envelope.get("meta")), dict)
        and "elapsed_ms" in body
    ]
    return {
        "calls": len(envelopes),
        "errors": sum(errors.values()),
        "error_codes": dict(errors),
        "http": {
            "requests": len(requests),
            "status": dict(Counter(status for _, status in requests)),
            **percentiles([duration for duration, _ in requests]),
        },
        "command_ms": percentiles(elapsed),
    }


def _login(invocation: Invocation) -> ExplicitLogin:
    """The resolved credentials of ``invocation`` as one login every call shares.

    A browser login's access token is read once: a bench is far shorter than its life.
    """
    auth = resolve_auth(invocation)
    token = auth.api_token
    if token is None and auth.token_provider is not None:
        token = auth.token_provider()
    host = urlsplit(auth.base_url).hostname or ""
    return ExplicitLogin(
        api_key=auth.api_key,
        api_secret=auth.api_secret,
        workspace_id=auth.workspace_id,
        server_prefix=host.split(".", 1)[0] or None,
        api_token=token,
        headers=auth.headers,
    )


def _refuse_unless_read(command: Sequence[str]) -> str:
    """The id of the command to bench; refused unless the manifest calls it a read."""
    command_id = resolve_command_id(command)
    record = command_by_id(command_id) if command_id else None
    if record is None or command_id == "bench":
        raise CliError(
            code=CODE_BENCH_COMMAND_REFUSED,
            message=f"'{' '.join(command)}' is not a command bench can run.",
            exit_status=EXIT_USAGE,
            hint="Bench a read command, for example: mammoth bench project list.",
        )
    if record.get("mutation_class") != "read":
        raise CliError(
            code=CODE_BENCH_COMMAND_REFUSED,
            message=(
                f"'{command_id.replace('.', ' ')}' changes data "
                f"({record.get('mutation_class')}); bench runs read commands only."
            ),
            exit_status=EXIT_USAGE,
        )
    return command_id


def bench(invocation: Invocation) -> HandlerResult:
    """Run one read command N at a time for R rounds and report its latency."""
    args = parse_args(invocation.extra_args)
    command_id = _refuse_unless_read(args.command)
    login = _login(invocation)
    project_id = resolved_project(invocation)
    pool = args.concurrency
    with EmbedRuntime(max_connections=pool, max_keepalive_connections=pool) as runtime:

        def call() -> dict[str, Any]:
            return embed.invoke(
                list(args.command),
                login=login,
                project_id=project_id,
                timeout=invocation.timeout,
                runtime=runtime,
            )

        run_rounds(call, concurrency=pool, rounds=args.warmup)
        with _http_durations() as http:
            started = time.perf_counter()
            envelopes = run_rounds(call, concurrency=pool, rounds=args.repeat)
            wall_ms = round((time.perf_counter() - started) * 1000)
    data = {
        "command": command_id.replace(".", " "),
        "argv": list(args.command),
        "concurrency": args.concurrency,
        "repeat": args.repeat,
        "warmup": args.warmup,
        "wall_ms": wall_ms,
        **summarize(envelopes, http.requests),
    }
    return data, {"workspace_id": login.workspace_id}
