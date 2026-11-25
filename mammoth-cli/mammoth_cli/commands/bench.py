"""The ``bench`` command: one read command, N at a time, measured.

``mammoth bench COMMAND... --concurrency N --repeat R [--warmup W]`` (the flags after the
command, or as ``--concurrency=N`` anywhere) runs ``mammoth
COMMAND...`` ``N`` at a time, ``R`` rounds, in this one process. All calls share one
keep-alive connection pool (:class:`~mammoth_cli.runtime.embed_pool.EmbedRuntime`) and
one login, so a round measures the server, not process start, credential lookup or TLS.
Each round starts on a barrier: the ``N`` calls are released together, so the server
sees ``N`` requests at once. ``W`` unmeasured warm-up rounds (default 1) open the
connections first.

Every HTTP attempt is counted, not only the last of a call: ``http.attempts`` is all of
them, ``http.requests`` the ones that ended a call, ``http.retries`` the attempts the SDK
retried (a 429/502/503/504 read), ``http.attempt_status`` the status of every attempt,
``http.status`` the status of the final ones and ``http.retry_wait_ms`` the backoff slept
between attempts. That wait is part of ``command_ms`` and never of the per-attempt
``http`` durations. ``--no-retry`` sends each request once, so a gateway error is measured as
what it is (mammothsdk#431).

It reports the 50th and 95th percentile and the maximum of the request duration the SDK
already logs for every HTTP request (``duration_ms`` of the ``mammoth.http`` log), and of
the whole command as the caller sees it, with the status counts and the error codes of
the calls that failed. Both are measured on this side (``timing: client``): one HTTP
attempt's round trip, timed by the SDK from just before the send. The server sends no
timing of its own (no ``Server-Timing`` header), so server time is not reported.

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
#: The error code of a call that never returned an envelope (it raised, or its round's
#: barrier broke); counted as an error, never as a clean call.
CODE_BENCH_CALL_FAILED = "bench_call_failed"
#: Where the durations are measured: on this side, around each HTTP attempt.
TIMING = "client"

#: The flags ``bench`` reads itself, each taking a whole number, and their defaults.
BENCH_FLAGS: dict[str, int] = {"--concurrency": 1, "--repeat": 1, "--warmup": 1}
#: The bounds of each flag: past them a run is a load test, not a benchmark.
_LIMITS: dict[str, tuple[int, int]] = {
    "--concurrency": (1, 64),
    "--repeat": (1, 100),
    "--warmup": (0, 10),
}
#: The flag that sends each request once (mammothsdk#431).
NO_RETRY_FLAG = "--no-retry"
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
        no_retry: Send every request once, with no SDK retry (mammothsdk#431).
    """

    command: tuple[str, ...]
    concurrency: int
    repeat: int
    warmup: int
    no_retry: bool = False


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
    no_retry = False
    rest = iter(tokens)
    for token in rest:
        if token == NO_RETRY_FLAG:
            no_retry = True
            continue
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
        no_retry=no_retry,
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
        try:
            barrier.wait(timeout=_BARRIER_TIMEOUT)
            results[slot] = call()
        except Exception as failure:  # noqa: BLE001 - reported as this call's error
            results[slot] = {
                "error": {
                    "code": CODE_BENCH_CALL_FAILED,
                    "message": f"{type(failure).__name__}: {failure}",
                }
            }

    threads = [threading.Thread(target=worker, args=(slot,)) for slot in range(concurrency)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


@dataclass(frozen=True)
class Attempt:
    """One HTTP attempt, as the SDK logged it (mammothsdk#431).

    Attributes:
        duration_ms: The attempt's round trip.
        status: The response status as text, or ``None`` when none came.
        outcome: ``retry`` when the SDK sent the request again, else how the call ended.
        retry_wait_ms: The backoff slept after this attempt, in milliseconds.
    """

    duration_ms: float
    status: str
    outcome: str = "ok"
    retry_wait_ms: int = 0

    @property
    def retried(self) -> bool:
        """Whether the SDK sent this request again after this attempt."""
        return self.outcome == "retry"


class _Durations(logging.Handler):
    """Keeps every logged HTTP attempt: its duration, status, outcome and retry wait."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.requests: list[Attempt] = []

    def emit(self, record: logging.LogRecord) -> None:
        fields = getattr(record, "mammoth", None)
        if isinstance(fields, dict) and fields.get("event") == "http":
            self.requests.append(
                Attempt(
                    duration_ms=float(fields["duration_ms"]),
                    status=str(fields.get("status")),
                    outcome=str(fields.get("outcome") or "ok"),
                    retry_wait_ms=int(fields.get("retry_wait_ms") or 0),
                )
            )


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


def summarize(envelopes: Sequence[dict[str, Any]], attempts: Sequence[Attempt]) -> dict[str, Any]:
    """The bench result: call and request counts, errors, and duration percentiles.

    Args:
        envelopes: Every measured call's envelope.
        attempts: Every measured HTTP attempt, retried ones included.

    Returns:
        ``calls``, ``errors``, ``error_codes``, ``http`` (attempts, requests that ended a call,
        retries, the retry wait, the status of every attempt and of the final ones, and the
        per-attempt duration percentiles) and ``command_ms`` (the per-call ``elapsed_ms``
        percentiles).
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
    final = [a for a in attempts if not a.retried]
    return {
        "calls": len(envelopes),
        "errors": sum(errors.values()),
        "error_codes": dict(errors),
        "http": {
            "attempts": len(attempts),
            "requests": len(final),
            "retries": len(attempts) - len(final),
            "retry_wait_ms": sum(a.retry_wait_ms for a in attempts),
            "attempt_status": dict(Counter(a.status for a in attempts)),
            "status": dict(Counter(a.status for a in final)),
            **percentiles([a.duration_ms for a in attempts]),
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
                no_retry=args.no_retry,
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
        "timing": TIMING,
        "no_retry": args.no_retry,
        **summarize(envelopes, http.requests),
    }
    return data, {"workspace_id": login.workspace_id}
