"""The real SDK service aimed at a loopback HTTP server that records every request.

Tests for CLI helpers that read a record and send an edit use this instead of a fake
service: the SDK builds the real requests, the server keeps what it received, and a test
asserts on the body that went over the wire.
"""

from __future__ import annotations

import json
import re
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest
from mammoth.client import MammothClient

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.services.sdk_service import SdkMammothService

PROJECT = 4300
API = "/api/v2/workspaces/4"


class Recorder(HTTPServer):
    """A loopback server: canned JSON answers by (method, path) and a log of requests."""

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.answers: dict[tuple[str, str], Any] = {}
        self.requests: list[tuple[str, str, Any]] = []

    def bodies(self, method: str, pattern: str) -> list[Any]:
        """The bodies received for ``method`` on paths matching the regex ``pattern``."""
        return [
            body
            for verb, path, body in self.requests
            if verb == method and re.search(pattern, path)
        ]


class _Handler(BaseHTTPRequestHandler):
    """Records the request and sends the canned answer, or 404."""

    server: Recorder

    def _answer(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        path = self.path.split("?")[0]
        self.server.requests.append((self.command, path, json.loads(raw) if raw else None))
        known = (self.command, path) in self.server.answers
        body = json.dumps(self.server.answers.get((self.command, path), {})).encode()
        self.send_response(200 if known else 404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_PATCH = do_POST = _answer  # noqa: N815

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def server() -> Iterator[Recorder]:
    srv = Recorder()
    threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
    yield srv
    srv.shutdown()
    srv.server_close()


@pytest.fixture
def service(server: Recorder) -> Iterator[SdkMammothService]:
    instance = SdkMammothService(
        ResolvedAuth(
            api_key="key",
            api_secret="secret",
            workspace_id=4,
            base_url="https://unused.invalid/api/v2",
        )
    )
    instance._client = MammothClient(
        "key",
        "secret",
        workspace_id=4,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    instance._client.set_project_id(PROJECT)
    try:
        yield instance
    finally:
        instance.close()
