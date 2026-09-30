"""A failed job's text lives in ``response.reason``; the waiters must surface it.

Runs against a real loopback HTTP server (no transport doubles).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothJobFailedError

REASON = "no data for pipeline step 1 of dataview 3062 yet; the step is 'added'"
FAILED = {"id": 7, "status": "failure", "response": {"reason": REASON}}


class _FailedJobHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        many = urlparse(self.path).path.rstrip("/").endswith("/jobs")
        body = json.dumps({"jobs": [FAILED]} if many else {"job": FAILED})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def client() -> Iterator[MammothClient]:
    server = HTTPServer(("127.0.0.1", 0), _FailedJobHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    server.shutdown()


def test_wait_for_job_reports_the_response_reason(client: MammothClient) -> None:
    with pytest.raises(MammothJobFailedError) as excinfo:
        client.jobs.wait_for_job(7, timeout=5)
    assert excinfo.value.details["failure_reason"] == REASON


def test_wait_for_jobs_reports_the_response_reason(client: MammothClient) -> None:
    with pytest.raises(MammothJobFailedError) as excinfo:
        client.jobs.wait_for_jobs([7], timeout=5)
    assert excinfo.value.details["failure_reason"] == REASON
