"""Unit tests for ``mammoth bench``: flags, the start barrier, and the reported latency."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import pytest

from mammoth_cli.commands import bench
from mammoth_cli.context.resolver import ExplicitLogin
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation

_HTTP = logging.getLogger("mammoth.http")


def _inv(*args: str) -> Invocation:
    return Invocation(command_id="bench", extra_args=list(args))


def _log_request(duration_ms: int, status: int = 200) -> None:
    """Log one request the way the SDK's client does."""
    _HTTP.info(
        "http GET /x outcome=ok status=%s elapsed_ms=%s",
        status,
        duration_ms,
        extra={"mammoth": {"event": "http", "status": status, "duration_ms": duration_ms}},
    )


def test_flags_are_read_from_anywhere_on_the_line() -> None:
    args = bench.parse_args(["--concurrency=8", "view", "list", "--repeat", "3", "290"])
    assert args == bench.BenchArgs(("view", "list", "290"), concurrency=8, repeat=3, warmup=1)


@pytest.mark.parametrize(
    "tokens",
    [
        ["project", "list", "--concurrency", "0"],
        ["project", "list", "--concurrency", "65"],
        ["project", "list", "--repeat"],
        ["project", "list", "--warmup", "x"],
        ["--repeat", "2"],
    ],
)
def test_bad_flags_or_no_command_are_refused(tokens: list[str]) -> None:
    with pytest.raises(CliError) as excinfo:
        bench.parse_args(tokens)
    assert excinfo.value.code == "invalid_bench"


def test_percentiles_are_nearest_rank() -> None:
    assert bench.percentiles(list(range(100, 0, -1))) == {
        "p50_ms": 50,
        "p95_ms": 95,
        "max_ms": 100,
    }
    assert bench.percentiles([7]) == {"p50_ms": 7, "p95_ms": 7, "max_ms": 7}
    assert bench.percentiles([]) == {"p50_ms": None, "p95_ms": None, "max_ms": None}


def test_a_round_starts_together_even_when_its_threads_start_slowly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Thread starts 50 ms apart; the barrier still releases all calls at once.

    Without the barrier the first call starts about 150 ms before the last, and the
    next round would start before this one's calls end.
    """
    start = threading.Thread.start

    def slow_start(self: threading.Thread) -> None:
        start(self)
        time.sleep(0.05)

    monkeypatch.setattr(threading.Thread, "start", slow_start)
    spans: list[tuple[float, float]] = []
    lock = threading.Lock()

    def call() -> dict[str, Any]:
        began = time.perf_counter()
        time.sleep(0.05)
        with lock:
            spans.append((began, time.perf_counter()))
        return {"data": {}, "meta": {"elapsed_ms": 50}}

    envelopes = bench.run_rounds(call, concurrency=4, rounds=2)

    assert len(envelopes) == 8
    first, second = sorted(spans)[:4], sorted(spans)[4:]
    for round_spans in (first, second):
        starts = [began for began, _ in round_spans]
        assert max(starts) - min(starts) < 0.03
    assert max(end for _, end in first) <= min(began for began, _ in second)


def test_bench_reports_the_logged_request_durations(monkeypatch: pytest.MonkeyPatch) -> None:
    """The percentiles come from the SDK's logged duration_ms, warm-up excluded."""
    calls: list[list[str]] = []
    lock = threading.Lock()

    def invoke(argv: list[str], **options: Any) -> dict[str, Any]:
        with lock:
            calls.append(argv)
            number = len(calls)
        assert options["project_id"] == 3
        assert options["runtime"] is not None
        if number <= 2:  # the warm-up round
            _log_request(10_000)
            return {"data": [], "meta": {"elapsed_ms": 10_000}}
        _log_request(number * 10, status=200 if number < 6 else 503)
        if number == 6:
            return {"error": {"code": "server_error", "elapsed_ms": 70}}
        return {"data": [], "meta": {"elapsed_ms": number * 10 + 5}}

    monkeypatch.setattr(bench.embed, "invoke", invoke)
    monkeypatch.setattr(
        bench, "_login", lambda _: ExplicitLogin(api_key=None, api_secret=None, workspace_id=4)
    )
    monkeypatch.setattr(bench, "resolved_project", lambda _: 3)

    data, meta = bench.bench(_inv("project", "list", "--concurrency", "2", "--repeat", "2"))

    assert calls == [["project", "list"]] * 6
    assert meta == {"workspace_id": 4}
    assert (data["calls"], data["errors"], data["error_codes"]) == (4, 1, {"server_error": 1})
    assert data["http"] == {
        "requests": 4,
        "status": {"200": 3, "503": 1},
        "p50_ms": 40.0,
        "p95_ms": 60.0,
        "max_ms": 60.0,
    }
    assert data["command_ms"] == {"p50_ms": 45.0, "p95_ms": 70.0, "max_ms": 70.0}
    assert not any(isinstance(h, bench._Durations) for h in _HTTP.handlers)


@pytest.mark.parametrize("command", [["project", "create", "x"], ["bench"], ["nope"]])
def test_only_read_commands_are_benched(command: list[str]) -> None:
    with pytest.raises(CliError) as excinfo:
        bench.bench(_inv(*command))
    assert excinfo.value.code == "bench_command_refused"


def test_a_command_given_as_one_quoted_string_is_its_words() -> None:
    args = bench.parse_args(["view list 290", "--repeat=2"])
    assert args.command == ("view", "list", "290")
    assert args.repeat == 2
