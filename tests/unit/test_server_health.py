"""``server_health``: the public ``/health`` probe, against a real loopback server and socket."""

from __future__ import annotations

import socket

import pytest

from mammoth.client import server_health
from mammoth.exceptions import MammothAPIError

from ._loopback import RecordingServer
from ._loopback import server as server  # noqa: F401


def _base(srv: RecordingServer) -> str:
    return f"http://127.0.0.1:{srv.server_port}/api/v2"


def test_reports_status_and_latency_without_a_token(server: RecordingServer) -> None:
    health = server_health(_base(server))
    assert health["status_code"] == 200
    assert isinstance(health["latency_ms"], int)
    assert "version" not in health
    assert server.requests[0]["path"] == "/health"


def test_returns_a_non_2xx_status_instead_of_raising(server: RecordingServer) -> None:
    server.answers["/health"] = (503, {"status": "down"})
    assert server_health(_base(server))["status_code"] == 503


def test_picks_up_version_and_commit(server: RecordingServer) -> None:
    server.answers["/health"] = {"status": "healthy", "version": "9.1", "commit": "ab12"}
    health = server_health(_base(server))
    assert (health["version"], health["commit"]) == ("9.1", "ab12")


def test_closed_port_raises() -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    with pytest.raises(MammothAPIError, match="unreachable"):
        server_health(f"http://127.0.0.1:{port}/api/v2")


def test_silent_server_times_out() -> None:
    with socket.socket() as silent:
        silent.bind(("127.0.0.1", 0))
        silent.listen(1)
        with pytest.raises(MammothAPIError, match="within 0.3s"):
            server_health(f"http://127.0.0.1:{silent.getsockname()[1]}/api/v2", timeout=0.3)
