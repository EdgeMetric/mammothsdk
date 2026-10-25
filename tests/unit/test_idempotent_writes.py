"""Writes carry an Idempotency-Key and are replayed only against a server that honours it.

Runs against a real loopback HTTP server (no transport doubles).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mammoth import client as client_module
from mammoth.client import (
    IDEMPOTENCY_KEY_HEADER,
    MammothClient,
    honours_idempotency_keys,
    mark_idempotency_keys_honoured,
)
from mammoth.exceptions import MammothAPIError


class _KeyServer(HTTPServer):
    #: Echo the key, as a server with the Idempotency-Key middleware does.
    echo: bool = True
    #: Answer the first N requests with this: an int status, or "drop" to close the socket.
    fail_first: int = 0
    failure: int | str = 502

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.keys: list[str | None] = []


class _Handler(BaseHTTPRequestHandler):
    server: _KeyServer

    def _answer(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        key = self.headers.get(IDEMPOTENCY_KEY_HEADER)
        self.server.keys.append(key)
        failing = len(self.server.keys) <= self.server.fail_first
        if failing and self.server.failure == "drop":
            self.close_connection = True
            self.connection.close()
            return
        status = int(self.server.failure) if failing else 200
        self.send_response(status)
        if key and self.server.echo:
            self.send_header(IDEMPOTENCY_KEY_HEADER, key)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        body = {"error_code": "4GENR038"} if status == 409 else {"ok": not failing}
        self.wfile.write(json.dumps(body).encode())

    do_GET = do_POST = _answer  # noqa: N815

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> Iterator[_KeyServer]:
    monkeypatch.setattr(client_module, "_HONOURS_IDEMPOTENCY", set())
    srv = _KeyServer()
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


async def test_a_write_carries_a_fresh_key_and_a_read_none(server: _KeyServer) -> None:
    client = _client(server.server_port)
    await client._request("POST", "/things", json={"a": 1})
    await client._request("POST", "/things", json={"a": 1})
    await client._request("GET", "/things")
    first, second, read = server.keys
    assert first and second and first != second
    assert read is None


async def test_an_echoed_key_teaches_the_client_the_server_honours_keys(
    server: _KeyServer,
) -> None:
    client = _client(server.server_port)
    assert not honours_idempotency_keys(client.base_url)
    await client._request("POST", "/things", json={})
    assert honours_idempotency_keys(client.base_url)


async def test_a_dropped_write_is_replayed_with_the_same_key(server: _KeyServer) -> None:
    client = _client(server.server_port)
    mark_idempotency_keys_honoured(client.base_url)
    server.fail_first, server.failure = 1, "drop"
    assert await client._request("POST", "/things", json={}) == {"ok": True}
    assert len(server.keys) == 2 and server.keys[0] == server.keys[1]


async def test_a_write_still_running_is_asked_again(server: _KeyServer) -> None:
    client = _client(server.server_port)
    mark_idempotency_keys_honoured(client.base_url)
    server.fail_first, server.failure = 1, 409
    assert await client._request("POST", "/things", json={}) == {"ok": True}
    assert server.keys[0] == server.keys[1]


async def test_a_write_is_not_replayed_by_a_server_not_known_to_honour_keys(
    server: _KeyServer,
) -> None:
    server.echo = False
    server.fail_first, server.failure = 1, 502
    with pytest.raises(MammothAPIError) as excinfo:
        await _client(server.server_port)._request("POST", "/things", json={})
    assert excinfo.value.status_code == 502
    assert len(server.keys) == 1


async def test_a_caller_key_is_kept(server: _KeyServer) -> None:
    client = _client(server.server_port)
    await client._request("POST", "/things", json={}, headers={"idempotency-key": "mine"})
    assert server.keys == ["mine"]


async def test_a_write_still_running_after_the_retries_is_an_unknown_outcome(
    server: _KeyServer,
) -> None:
    client = _client(server.server_port)
    mark_idempotency_keys_honoured(client.base_url)
    server.fail_first, server.failure = 99, 409
    with pytest.raises(MammothAPIError) as excinfo:
        await client._request("POST", "/things", json={})
    assert excinfo.value.status_code == 409
    assert excinfo.value.operation_state == "outcome_unknown"
    assert len(server.keys) == 3 and len(set(server.keys)) == 1
