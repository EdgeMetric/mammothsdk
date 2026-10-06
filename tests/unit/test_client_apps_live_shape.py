"""Client-app models match the payloads the live apiv2 returns (QA W7-17).

The payloads below were recorded from koyal's apiv2 ``/workspaces/4/clientapps``
(secret values replaced by placeholders). Runs against a real loopback HTTP
server, no transport doubles.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from mammoth.client import MammothClient

LIST_PAYLOAD: dict[str, Any] = {
    "result": [
        {
            "id": 2,
            "app_name": "automated_key_testapp",
            "app_key": "KEY-PLACEHOLDER-1",
            "type": "legacy",
            "description": "Auto generated key for running tests",
            "workspace_id": 4,
            "user_id": 5,
            "project_id": None,
            "last_usage": None,
            "created_at": None,
        },
        {
            "id": 199,
            "app_name": "agent-evals",
            "app_key": "KEY-PLACEHOLDER-2",
            "type": "token",
            "description": "golden eval runner",
            "workspace_id": 4,
            "user_id": 5,
            "project_id": None,
            "last_usage": "2026-10-06T10:15:00",
            "created_at": None,
        },
    ]
}
LIST_FIELDS_PAYLOAD: dict[str, Any] = {
    "result": [{"description": "golden eval runner", "id": 199, "app_name": "agent-evals"}]
}
POST_PAYLOAD: dict[str, Any] = {
    "app_name": "uqa-rca-w7-17",
    "app_key": "KEY-PLACEHOLDER-3",
    "description": "rca",
    "workspace_id": 4,
    "user_id": 5,
    "token": "mm_TOKEN-PLACEHOLDER",
}


class _Server(HTTPServer):
    def __init__(self, post_payload: dict[str, Any]) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.post_payload = post_payload
        self.post_bodies: list[dict[str, Any]] = []


class _Handler(BaseHTTPRequestHandler):
    server: _Server

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_GET(self) -> None:  # noqa: N802
        fields = "fields=" in self.path
        self._send(200, LIST_FIELDS_PAYLOAD if fields else LIST_PAYLOAD)

    def do_POST(self) -> None:  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
        self.server.post_bodies.append(body)
        if "description" not in body:  # the live BE requires it
            self._send(400, {"detail": "description: Field required"})
            return
        self._send(201, self.server.post_payload)

    def log_message(self, *args: object) -> None:
        return


def _serve(post_payload: dict[str, Any]) -> Iterator[_Server]:
    srv = _Server(post_payload)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()


@pytest.fixture
def server() -> Iterator[_Server]:
    yield from _serve(POST_PAYLOAD)


@pytest.fixture
def drifted_server() -> Iterator[_Server]:
    # A 2xx create whose body drifts from the model: the secret must still surface.
    yield from _serve({**POST_PAYLOAD, "workspace_id": "four", "user_id": None})


def _client(srv: HTTPServer) -> MammothClient:
    return MammothClient(
        "key",
        "secret",
        workspace_id=4,
        base_url=f"http://127.0.0.1:{srv.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )


async def test_list_parses_live_payload(server: _Server) -> None:
    result = await _client(server).client_apps.list()
    assert [a.id for a in result.result] == [2, 199]
    assert result.result[1].type == "token"
    assert result.result[0].app_name == "automated_key_testapp"
    assert result.result[0].workspace_id == 4


async def test_list_parses_field_filtered_payload(server: _Server) -> None:
    result = await _client(server).client_apps.list(fields="id,app_name,description")
    assert result.result[0].app_name == "agent-evals"
    assert result.result[0].app_key is None


async def test_create_returns_token_from_live_payload(server: _Server) -> None:
    created = await _client(server).client_apps.create(app_name="uqa-rca-w7-17", description="rca")
    assert created.token == "mm_TOKEN-PLACEHOLDER"
    assert created.app_key == "KEY-PLACEHOLDER-3"
    assert created.workspace_id == 4


async def test_create_without_description_satisfies_required_field(server: _Server) -> None:
    created = await _client(server).client_apps.create(app_name="uqa-rca-w7-17")
    assert server.post_bodies == [{"app_name": "uqa-rca-w7-17", "description": ""}]
    assert created.token == "mm_TOKEN-PLACEHOLDER"


async def test_create_surfaces_token_even_if_body_drifts_from_model(
    drifted_server: _Server,
) -> None:
    created = await _client(drifted_server).client_apps.create(app_name="x", description="d")
    assert created.token == "mm_TOKEN-PLACEHOLDER"
