"""``doctor``'s ``server`` check against real sockets: a live local server and a closed port."""

from __future__ import annotations

import json
import socket
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mammoth_cli.commands import doctor as doctor_cmd


def _serve(status: int, body: bytes) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            code, payload = (status, body) if self.path == "/health" else (401, b"{}")
            self.send_response(code)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args: object) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.fixture
def healthy_server() -> Iterator[str]:
    yield from _serve(200, json.dumps({"status": "healthy"}).encode())


@pytest.fixture
def versioned_server() -> Iterator[str]:
    yield from _serve(
        200, json.dumps({"status": "healthy", "version": "9.1", "commit": "ab12"}).encode()
    )


@pytest.fixture
def failing_server() -> Iterator[str]:
    yield from _serve(503, b"{}")


def test_server_check_healthy_reports_status_and_latency(healthy_server: str) -> None:
    check = doctor_cmd._check_server(healthy_server)
    assert check["name"] == "server"
    assert check["ok"] is True
    assert check["status_code"] == 200
    assert isinstance(check["latency_ms"], int)
    assert check["detail"] == f"healthy in {check['latency_ms']} ms"
    assert "version" not in check and "commit" not in check


def test_server_check_picks_up_version_and_commit(versioned_server: str) -> None:
    check = doctor_cmd._check_server(versioned_server)
    assert (check["version"], check["commit"]) == ("9.1", "ab12")


def test_server_check_fails_on_non_2xx(failing_server: str) -> None:
    check = doctor_cmd._check_server(failing_server)
    assert check["ok"] is False
    assert check["status_code"] == 503
    assert "HTTP 503" in check["detail"]


def test_server_check_unreachable_port_is_not_ok() -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    check = doctor_cmd._check_server(f"http://127.0.0.1:{port}")
    assert check["ok"] is False
    assert "unreachable" in check["detail"]
    assert "status_code" not in check


def test_server_check_times_out_on_a_silent_server() -> None:
    with socket.socket() as silent:
        silent.bind(("127.0.0.1", 0))
        silent.listen(1)  # accepts the connection, never answers
        check = doctor_cmd._check_server(f"http://127.0.0.1:{silent.getsockname()[1]}", timeout=0.3)
    assert check["ok"] is False
    assert "within 0.3s" in check["detail"]


def test_server_check_ignores_auth_it_needs_none(healthy_server: str) -> None:
    # The same server answers 401 to every other route; /health still reports healthy.
    assert doctor_cmd._check_server(healthy_server)["ok"] is True
