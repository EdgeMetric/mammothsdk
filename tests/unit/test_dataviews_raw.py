"""``raw`` on dataview data reads reaches the backend as a GET query param and a POST body field.

A real loopback HTTP server records what the SDK actually sends.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

from mammoth.client import MammothClient


class _Recorder(BaseHTTPRequestHandler):
    seen: list[dict[str, Any]] = []

    def _reply(self, body: dict[str, Any] | None = None) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        posted = json.loads(self.rfile.read(length)) if length else None
        self.seen.append({"query": parse_qs(urlparse(self.path).query), "body": posted})
        payload = json.dumps({"data": []}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_POST = _reply  # noqa: N815 - names fixed by http.server

    def log_message(self, *args: object) -> None:
        return None


@pytest.fixture
def served() -> Iterator[tuple[MammothClient, list[dict[str, Any]]]]:
    _Recorder.seen = []
    server = HTTPServer(("127.0.0.1", 0), _Recorder)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    client = MammothClient(
        api_key="test-key",
        api_secret="test-secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}",
        api_root="",
        allow_insecure_loopback_http=True,
    )
    client.project_id = 100
    yield client, _Recorder.seen
    server.shutdown()


async def test_get_data_sends_raw_only_when_asked(
    served: tuple[MammothClient, list[dict[str, Any]]],
) -> None:
    client, seen = served
    await client.dataviews.get_data(dataset_id=1, dataview_id=2, sequence=0)
    await client.dataviews.get_data(dataset_id=1, dataview_id=2, sequence=0, raw=True)
    assert "raw" not in seen[0]["query"]
    assert seen[1]["query"]["raw"] == ["true"]


async def test_query_data_sends_raw_only_when_asked(
    served: tuple[MammothClient, list[dict[str, Any]]],
) -> None:
    client, seen = served
    await client.dataviews.query_data(dataset_id=1, dataview_id=2, sequence=0)
    await client.dataviews.query_data(dataset_id=1, dataview_id=2, sequence=0, raw=True)
    assert "raw" not in seen[0]["body"]
    assert seen[1]["body"]["raw"] is True
