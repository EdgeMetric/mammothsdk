"""A loopback HTTP server that records every request and answers scripted routes."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest

from mammoth.client import MammothClient


class RecordingServer(HTTPServer):
    """Records requests; ``answers`` maps ``"METHOD /path"`` (or ``"/path"``) to a body or
    to ``(status, body)``. Unscripted routes answer 200 ``{"ok": true}``."""

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.requests: list[dict[str, object]] = []
        self.answers: dict[str, object] = {}


class _Handler(BaseHTTPRequestHandler):
    server: RecordingServer

    def _answer(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        parts = urlsplit(self.path)
        path = parts.path.removeprefix("/api/v2")
        self.server.requests.append(
            {
                "method": self.command,
                "path": path,
                "query": {k: v[0] for k, v in parse_qs(parts.query).items()},
                "body": json.loads(raw) if raw else None,
            }
        )
        scripted = self.server.answers.get(f"{self.command} {path}", self.server.answers.get(path))
        status, body = scripted if isinstance(scripted, tuple) else (200, scripted or {"ok": True})
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if status != 204:
            self.wfile.write(json.dumps(body).encode())

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _answer  # noqa: N815

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def server() -> Iterator[RecordingServer]:
    srv = RecordingServer()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()


@pytest.fixture
def client(server: RecordingServer) -> MammothClient:
    c = MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    c.set_project_id(25654)
    return c
