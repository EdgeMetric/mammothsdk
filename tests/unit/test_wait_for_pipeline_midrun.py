"""``wait_for_pipeline`` polls through a pipeline GET taken mid-run.

Against a real loopback HTTP server (no transport doubles): the first reads
show a pipeline that is running with no usable state, the last shows it ready.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mammoth.client import MammothClient

_BODIES = [
    {"state": None},
    {},
    {"state": "modifying"},
    {"state": "running"},
    {"state": "READY"},
]


class _MidRunHandler(BaseHTTPRequestHandler):
    reads = 0

    def do_GET(self) -> None:  # noqa: N802
        cls = type(self)
        body = json.dumps(_BODIES[min(cls.reads, len(_BODIES) - 1)])
        cls.reads += 1
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def client() -> Iterator[MammothClient]:
    _MidRunHandler.reads = 0
    server = HTTPServer(("127.0.0.1", 0), _MidRunHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    client = MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    client.set_project_id(2)
    yield client
    server.shutdown()


async def test_wait_polls_through_missing_and_transient_states(client: MammothClient) -> None:
    pipeline = await client.pipeline.wait_for_pipeline(
        7, dataset_id=9, timeout=20, poll_interval=0.05
    )
    assert pipeline["state"] == "READY"
    assert _MidRunHandler.reads == len(_BODIES)
