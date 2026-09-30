"""Idempotent reads retry a transient 502/503/504; writes never do.

Runs against a real loopback HTTP server (no transport doubles).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError


class _FlakyServer(HTTPServer):
    fail_first: int = 1
    fail_status: int = 502
    retry_after: str | None = None

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.hits: list[str] = []


class _Handler(BaseHTTPRequestHandler):
    server: _FlakyServer

    def _answer(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        self.server.hits.append(self.command)
        failing = len(self.server.hits) <= self.server.fail_first
        self.send_response(self.server.fail_status if failing else 200)
        if failing and self.server.retry_after is not None:
            self.send_header("Retry-After", self.server.retry_after)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": not failing}).encode())

    do_GET = do_POST = _answer  # noqa: N815

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def server() -> Iterator[_FlakyServer]:
    srv = _FlakyServer()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()


def _client(port: int) -> MammothClient:
    return MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{port}/api/v2",
        allow_insecure_loopback_http=True,
    )


async def test_get_retries_one_502_then_succeeds(server: _FlakyServer) -> None:
    result = await _client(server.server_port)._request("GET", "/things")
    assert result == {"ok": True}
    assert server.hits == ["GET", "GET"]


async def test_get_honours_retry_after(server: _FlakyServer) -> None:
    server.fail_status = 503
    server.retry_after = "0"
    assert await _client(server.server_port)._request("GET", "/things") == {"ok": True}
    assert len(server.hits) == 2


async def test_post_502_is_not_retried(server: _FlakyServer) -> None:
    with pytest.raises(MammothAPIError) as excinfo:
        await _client(server.server_port)._request("POST", "/things", json={"a": 1})
    assert excinfo.value.status_code == 502
    assert server.hits == ["POST"]


async def test_get_fails_after_bounded_attempts(server: _FlakyServer) -> None:
    server.fail_first = 99
    with pytest.raises(MammothAPIError) as excinfo:
        await _client(server.server_port)._request("GET", "/things")
    assert excinfo.value.status_code == 502
    assert server.hits == ["GET", "GET", "GET"]


async def test_get_connect_error_is_bounded_and_mapped() -> None:
    srv = _FlakyServer()
    port = srv.server_port
    srv.server_close()  # nothing listening
    with pytest.raises(MammothAPIError, match="Connection error"):
        await _client(port)._request("GET", "/things")
