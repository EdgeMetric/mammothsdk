"""Unit tests for ``mammoth bench``: flags, the start barrier, and the reported latency."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import httpx
import pytest
from mammoth import client as sdk_client

from mammoth_cli.commands import bench
from mammoth_cli.context.resolver import ExplicitLogin
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation

_HTTP = logging.getLogger("mammoth.http")


# Each embedded call asks GET /workspaces/current whether the token is pinned to projects.
# The servers below answer "not pinned" and leave that probe out of `requests`, so their
# request counts are the benched requests only.
_NOT_PINNED = httpx.Response(200, json={"id": 4, "name": "ws"})


def _is_pin_probe(request: httpx.Request) -> bool:
    return request.method == "GET" and request.url.path.endswith("/workspaces/current")


def _inv(*args: str) -> Invocation:
    return Invocation(command_id="bench", extra_args=list(args))


def test_flags_are_read_from_anywhere_on_the_line() -> None:
    args = bench.parse_args(["--concurrency=8", "view", "list", "--repeat", "3", "290"])
    assert args == bench.BenchArgs(("view", "list", "290"), concurrency=8, repeat=3, warmup=1)
    assert bench.parse_args(["project", "list", "--no-retry"]).no_retry is True
    assert args.no_retry is False


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


class _Server:
    """Answers the SDK's requests after a pause; the n-th project list gets a 404."""

    def __init__(self, *, pause: float, missing: int) -> None:
        self.pause = pause
        self.missing = missing
        self.requests: list[httpx.Request] = []
        self.probes = 0  # pin probes, kept out of `requests`
        self.lock = threading.Lock()

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if _is_pin_probe(request):
            with self.lock:
                self.probes += 1
            time.sleep(self.pause)  # the probe is a benched request too
            return _NOT_PINNED
        with self.lock:
            self.requests.append(request)
            number = sum(r.url.path.endswith("/projects") for r in self.requests)
        time.sleep(self.pause)
        if request.url.path.endswith("/projects") and number == self.missing:
            return httpx.Response(404, json={"message": "Not found"})
        return httpx.Response(200, json={"projects": [], "limit": 100, "offset": 0, "next": ""})


def test_bench_reports_the_durations_the_sdk_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only the network is faked: the real embed.invoke and SDK log the requests bench reads."""
    server = _Server(pause=0.02, missing=3)  # the warm-up round lists twice
    real = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kw: real(**{**kw, "transport": httpx.MockTransport(server)})
    )
    login = ExplicitLogin(
        api_key=None, api_secret=None, workspace_id=4, api_token="mm_x", server_prefix="box"
    )
    monkeypatch.setattr(bench, "_login", lambda _: login)
    monkeypatch.setattr(bench, "resolved_project", lambda _: 3)

    data, meta = bench.bench(
        _inv("project", "list", "--concurrency", "2", "--repeat", "2", "--warmup", "1")
    )

    http = data["http"]
    assert meta == {"workspace_id": 4}
    assert data["timing"] == "client"
    assert (data["calls"], data["errors"]) == (4, 1)
    # Every measured request is counted, the warm-up round's are not: each of the 4 calls
    # is one pin probe plus one project list.
    assert http["requests"] == 2 * data["calls"] < len(server.requests) + server.probes
    assert http["status"] == {"200": http["requests"] - 1, "404": 1}
    assert http["p50_ms"] >= 20
    assert http["max_ms"] >= http["p95_ms"] >= http["p50_ms"]
    assert data["command_ms"]["p50_ms"] >= http["p50_ms"]
    assert not any(isinstance(h, bench._Durations) for h in _HTTP.handlers)


def test_a_call_that_raises_is_an_error_not_a_clean_call() -> None:
    def call() -> dict[str, Any]:
        raise RuntimeError("boom")

    envelopes = bench.run_rounds(call, concurrency=2, rounds=1)

    assert [e["error"]["code"] for e in envelopes] == ["bench_call_failed"] * 2
    assert envelopes[0]["error"]["message"] == "RuntimeError: boom"
    summary = bench.summarize(envelopes, [])
    assert (summary["calls"], summary["errors"]) == (2, 2)
    assert summary["error_codes"] == {"bench_call_failed": 2}


def test_a_broken_barrier_is_reported_as_each_calls_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(bench, "_BARRIER_TIMEOUT", 0.01)
    started = threading.Event()
    real_start = threading.Thread.start

    def start_one_late(thread: threading.Thread) -> None:
        if started.is_set():
            time.sleep(0.2)
        started.set()
        real_start(thread)

    monkeypatch.setattr(threading.Thread, "start", start_one_late)
    envelopes = bench.run_rounds(lambda: {"data": [], "meta": {}}, concurrency=2, rounds=1)

    assert all(e["error"]["code"] == "bench_call_failed" for e in envelopes)
    assert "BrokenBarrierError" in envelopes[0]["error"]["message"]


@pytest.mark.parametrize("command", [["project", "create", "x"], ["bench"], ["nope"]])
def test_only_read_commands_are_benched(command: list[str]) -> None:
    with pytest.raises(CliError) as excinfo:
        bench.bench(_inv(*command))
    assert excinfo.value.code == "bench_command_refused"


def test_a_command_given_as_one_quoted_string_is_its_words() -> None:
    args = bench.parse_args(["view list 290", "--repeat=2"])
    assert args.command == ("view", "list", "290")
    assert args.repeat == 2


class _Gateway:
    """Answers the first `bad` project lists with a 502 from a CDN, then 200."""

    def __init__(self, bad: int) -> None:
        self.bad = bad
        self.requests: list[httpx.Request] = []
        self.probes = 0  # pin probes, kept out of `requests`
        self.lock = threading.Lock()

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if _is_pin_probe(request):
            with self.lock:
                self.probes += 1
            return _NOT_PINNED
        with self.lock:
            self.requests.append(request)
            number = len(self.requests)
        if number <= self.bad:
            return httpx.Response(502, json={}, headers={"X-Cache": "Error from cloudfront"})
        return httpx.Response(200, json={"projects": [], "limit": 100, "offset": 0, "next": ""})


def _bench_through(
    monkeypatch: pytest.MonkeyPatch, server: _Gateway, *flags: str
) -> dict[str, Any]:
    """Run `bench project list` once-per-round against `server` and return its data."""
    real = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kw: real(**{**kw, "transport": httpx.MockTransport(server)})
    )
    monkeypatch.setattr(sdk_client, "_RETRY_BACKOFF_S", 0.01)
    login = ExplicitLogin(
        api_key=None, api_secret=None, workspace_id=4, api_token="mm_x", server_prefix="box"
    )
    monkeypatch.setattr(bench, "_login", lambda _: login)
    monkeypatch.setattr(bench, "resolved_project", lambda _: 3)
    data, _meta = bench.bench(_inv("project", "list", "--repeat", "2", "--warmup", "0", *flags))
    return data


def test_a_retried_502_is_counted_as_an_attempt_not_hidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _Gateway(bad=1)
    data = _bench_through(monkeypatch, server)
    http = data["http"]
    assert (data["calls"], data["errors"]) == (2, 0)  # the retry made the call succeed
    # Each of the 2 calls sends a pin probe and a project list; the first list is retried once.
    assert len(server.requests) == 3
    assert server.probes == 2
    assert http["attempts"] == len(server.requests) + server.probes == 5
    assert (http["requests"], http["retries"]) == (4, 1)
    assert http["attempt_status"] == {"502": 1, "200": 4}
    assert http["status"] == {"200": 4}
    assert http["retry_wait_ms"] == 10
    assert data["no_retry"] is False


def test_no_retry_sends_each_request_once_and_reports_the_502(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _Gateway(bad=1)
    data = _bench_through(monkeypatch, server, "--no-retry")
    http = data["http"]
    # One project list per call: nothing was sent again. Each call also sent one pin probe.
    assert (len(server.requests), server.probes) == (2, 2)
    assert (http["attempts"], http["requests"], http["retries"]) == (4, 4, 0)
    assert http["retry_wait_ms"] == 0
    assert http["status"] == {"502": 1, "200": 3}
    assert data["errors"] == 1
    assert data["no_retry"] is True


def test_summarize_separates_final_statuses_from_every_attempt() -> None:
    attempts = [
        bench.Attempt(100.0, "502", "retry", 250),
        bench.Attempt(120.0, "502", "retry", 500),
        bench.Attempt(90.0, "200", "ok"),
    ]
    http = bench.summarize([{"meta": {"elapsed_ms": 1000}}], attempts)["http"]
    assert http["attempts"] == 3 and http["requests"] == 1 and http["retries"] == 2
    assert http["attempt_status"] == {"502": 2, "200": 1}
    assert http["status"] == {"200": 1}
    assert http["retry_wait_ms"] == 750
