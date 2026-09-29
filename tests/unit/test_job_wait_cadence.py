"""Job wait cadence against a real loopback HTTP server (no transport doubles)."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mammoth.api.jobs import _poll_delay
from mammoth.client import MammothClient

FINISH_AFTER_S = 0.5


class _JobHandler(BaseHTTPRequestHandler):
    """Reports job 7 as processing until FINISH_AFTER_S after the first poll."""

    first_poll: float | None = None
    poll_times: list[float] = []

    def do_GET(self) -> None:  # noqa: N802
        now = time.monotonic()
        cls = type(self)
        if cls.first_poll is None:
            cls.first_poll = now
        cls.poll_times.append(now)
        done = now - cls.first_poll >= FINISH_AFTER_S
        body = json.dumps({"job": {"id": 7, "status": "success" if done else "processing"}})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def client() -> Iterator[MammothClient]:
    _JobHandler.first_poll = None
    _JobHandler.poll_times = []
    server = HTTPServer(("127.0.0.1", 0), _JobHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    server.shutdown()


def test_poll_delay_grows_and_is_capped() -> None:
    gaps = [_poll_delay(n, 2) for n in range(8)]
    assert gaps[0] < 0.5
    assert gaps == sorted(gaps)
    assert gaps[-1] == 2


def test_fast_job_is_not_held_for_a_fixed_two_second_poll(client: MammothClient) -> None:
    started = time.monotonic()
    job = client.jobs.wait_for_job(7, timeout=10)
    elapsed = time.monotonic() - started

    assert job["status"] == "success"
    assert _JobHandler.poll_times[0] - started < 0.5  # first check is immediate
    assert elapsed < 1.5  # a fixed 2 s poll could not finish before 2 s
