"""Connected apps and workspace OAuth clients: the wire each SDK method sends.

Runs against a real loopback HTTP server that records every request.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest

from mammoth.client import MammothClient


class _RecordingServer(HTTPServer):
    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.requests: list[dict[str, object]] = []
        self.status = 200


class _Handler(BaseHTTPRequestHandler):
    server: _RecordingServer

    def _answer(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        parts = urlsplit(self.path)
        content_type = self.headers.get("Content-Type", "")
        self.server.requests.append(
            {
                "method": self.command,
                "path": parts.path.removeprefix("/api/v2"),
                "query": {k: v[0] for k, v in parse_qs(parts.query).items()},
                "body": json.loads(raw) if raw and "json" in content_type else raw,
            }
        )
        self.send_response(self.server.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if self.server.status != 204:
            self.wfile.write(b'{"ok": true}')

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _answer  # noqa: N815

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def server() -> Iterator[_RecordingServer]:
    srv = _RecordingServer()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()


@pytest.fixture
def client(server: _RecordingServer) -> MammothClient:
    c = MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    c.set_project_id(25654)
    return c


async def test_connected_apps_lists_the_signed_in_users_grants(
    server: _RecordingServer, client: MammothClient
) -> None:
    result = await client.user_profile.connected_apps()
    assert (server.requests[0]["method"], server.requests[0]["path"]) == (
        "GET",
        "/self/oauth-grants",
    )
    assert result == {"ok": True}


async def test_revoke_connected_app_deletes_that_grant_on_an_empty_204(
    server: _RecordingServer, client: MammothClient
) -> None:
    server.status = 204
    result = await client.user_profile.revoke_connected_app(7)
    assert (server.requests[0]["method"], server.requests[0]["path"]) == (
        "DELETE",
        "/self/oauth-grants/7",
    )
    assert result == {}


async def test_oauth_clients_list_uses_the_client_workspace_by_default(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.oauth_clients.list()
    await client.oauth_clients.list(workspace_id=9)
    assert [(r["method"], r["path"]) for r in server.requests] == [
        ("GET", "/workspaces/1/oauth-clients"),
        ("GET", "/workspaces/9/oauth-clients"),
    ]


async def test_oauth_clients_create_sends_only_the_fields_given(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.oauth_clients.create(
        "Reporting app", ["https://app.example.com/callback"], description="Nightly export"
    )
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("POST", "/workspaces/1/oauth-clients")
    assert sent["body"] == {
        "name": "Reporting app",
        "redirect_uris": ["https://app.example.com/callback"],
        "token_endpoint_auth_method": "client_secret_basic",
        "description": "Nightly export",
    }


async def test_oauth_clients_delete_names_the_client_in_the_workspace_path(
    server: _RecordingServer, client: MammothClient
) -> None:
    server.status = 204
    await client.oauth_clients.delete(5, workspace_id=9)
    assert (server.requests[0]["method"], server.requests[0]["path"]) == (
        "DELETE",
        "/workspaces/9/oauth-clients/5",
    )


async def test_oauth_clients_revoke_grant_hits_the_grant_sub_path(
    server: _RecordingServer, client: MammothClient
) -> None:
    server.status = 204
    await client.oauth_clients.revoke_grant(5)
    assert (server.requests[0]["method"], server.requests[0]["path"]) == (
        "DELETE",
        "/workspaces/1/oauth-clients/5/grant",
    )
