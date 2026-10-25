"""A job wait checks a running job at least every half second by default.

The default ``job_poll_seconds`` caps the growing gap between checks. At the old
two seconds a caller answering a person waited up to two seconds past the moment
the job finished.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mammoth.client import MammothClient

_RUNNING_CHECKS = 7
_checks: list[float] = []


class _SlowJobHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        _checks.append(time.monotonic())
        status = "processing" if len(_checks) <= _RUNNING_CHECKS else "success"
        body = json.dumps({"job": {"id": 7, "status": status, "response": {}}})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def client() -> Iterator[MammothClient]:
    _checks.clear()
    server = HTTPServer(("127.0.0.1", 0), _SlowJobHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    server.shutdown()


async def test_a_default_client_checks_a_running_job_at_least_every_half_second(
    client: MammothClient,
) -> None:
    await client.jobs.wait_for_job(7, timeout=30)
    assert len(_checks) == _RUNNING_CHECKS + 1
    gaps = [later - earlier for earlier, later in zip(_checks, _checks[1:], strict=False)]
    assert max(gaps) < 0.8, gaps
    assert max(gaps) > 0.4, gaps  # the gap still grows to the cap
