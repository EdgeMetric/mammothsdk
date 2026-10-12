"""``collections.list()`` tells the server which workspace to list in.

Uses an ``mm_`` API token: that path has no default ``X-WORKSPACE-ID`` session header,
so the per-request header is the only thing that can carry the workspace id.
A real loopback HTTP server answers the workspace lookup and records the list request.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlsplit

import pytest

from mammoth.client import MammothClient

_TOKEN_WORKSPACE_ID = 7


class _Recorder(BaseHTTPRequestHandler):
    seen: list[dict[str, Any]] = []

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        _Recorder.seen.append({"path": path, "headers": dict(self.headers)})
        body: dict[str, Any] = (
            {"id": _TOKEN_WORKSPACE_ID}
            if path.endswith("/workspaces/current")
            else {"collections": []}
        )
        payload = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args: object) -> None:
        return None


@pytest.fixture
def served() -> Iterator[MammothClient]:
    _Recorder.seen = []
    server = HTTPServer(("127.0.0.1", 0), _Recorder)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    client = MammothClient(
        api_token="mm_test_token",
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    yield client
    server.shutdown()


async def test_collections_list_sends_the_client_workspace_header(
    served: MammothClient,
) -> None:
    await served.collections.list()
    list_request = next(r for r in _Recorder.seen if r["path"].endswith("/collections"))
    assert list_request["headers"].get("x-workspace-id") == str(_TOKEN_WORKSPACE_ID)
