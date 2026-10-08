"""``metadata_request`` GETs the RFC 8414 document and reports what came back.

Runs against a real loopback HTTP server (no transport doubles).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mammoth import oauth

_METADATA_PATH = "/.well-known/oauth-authorization-server"


class _Server(HTTPServer):
    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.paths: list[str] = []


class _Handler(BaseHTTPRequestHandler):
    server: _Server

    def do_GET(self) -> None:  # noqa: N802
        self.server.paths.append(self.path)
        if self.path == _METADATA_PATH:
            self._send(200, json.dumps({"mammoth_cli_client_id": "oc_x"}).encode())
        elif self.path == "/redirect/.well-known/oauth-authorization-server":
            self.send_response(302)
            self.send_header("Location", "/elsewhere")
            self.end_headers()
        elif self.path == "/text/.well-known/oauth-authorization-server":
            self._send(200, b"not json")
        else:
            self._send(404, json.dumps({"error": "nope"}).encode())

    def _send(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def server() -> Iterator[_Server]:
    srv = _Server()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()
    srv.server_close()


def _base(srv: _Server, prefix: str = "") -> str:
    return f"http://127.0.0.1:{srv.server_port}{prefix}"


def test_returns_status_and_json_body(server: _Server) -> None:
    assert oauth.metadata_request(_base(server)) == (200, {"mammoth_cli_client_id": "oc_x"})
    assert server.paths == [_METADATA_PATH]


def test_does_not_follow_a_redirect(server: _Server) -> None:
    status, body = oauth.metadata_request(_base(server, "/redirect"))
    assert (status, body) == (302, None)
    assert server.paths == ["/redirect" + _METADATA_PATH]


def test_non_json_body_is_none(server: _Server) -> None:
    assert oauth.metadata_request(_base(server, "/text")) == (200, None)


def test_error_status_is_reported(server: _Server) -> None:
    assert oauth.metadata_request(_base(server, "/missing")) == (404, {"error": "nope"})


def test_unreachable_server_raises_transport_error() -> None:
    srv = _Server()
    port = srv.server_port
    srv.server_close()
    with pytest.raises(oauth.OAuthTransportError):
        oauth.metadata_request(f"http://127.0.0.1:{port}")
