"""`token revoke` of the own OAuth grant deletes that grant; errors keep the client key out."""

from __future__ import annotations

import http.server
import threading
from collections.abc import Callable, Iterator
from typing import Any

import pytest

from mammoth_cli.commands import client_app
from mammoth_cli.context import credentials
from mammoth_cli.context.credentials import OAuthSession
from mammoth_cli.testing import make_runner
from tests.realcode.test_end_to_end_cli import _bind_real_service

ServiceFactory = Callable[..., Any]
CLIENT_ID = "oc_cli_secret_key"
SESSION = OAuthSession("mm_" + "a" * 43, "12.secret.mac", 4_000_000_000, CLIENT_ID, 12)


class _Grants(http.server.BaseHTTPRequestHandler):
    seen: list[tuple[str, str, str | None]] = []

    def do_DELETE(self) -> None:
        self.seen.append((self.command, self.path, self.headers.get("Authorization")))
        self.send_response(204)
        self.end_headers()

    def log_message(self, *_args: Any) -> None:
        return


@pytest.fixture
def grants_server() -> Iterator[str]:
    _Grants.seen = []
    server = http.server.HTTPServer(("127.0.0.1", 0), _Grants)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_revoking_the_own_grant_deletes_it_by_grant_id(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, grants_server: str
) -> None:
    credentials.store_credentials("default", storage="file", oauth=SESSION)
    monkeypatch.setattr(client_app, "resolve_base_url", lambda _prefix: grants_server)
    api = _bind_real_service(monkeypatch, real_service, project_id=180)

    result = make_runner().invoke(
        ["token", "revoke", CLIENT_ID, "--yes", "--output", "json", "--no-input"]
    )

    assert result.exit_code == 0, result.output
    assert _Grants.seen == [("DELETE", "/self/oauth-grants/12", f"Bearer {SESSION.access}")]
    assert not [r for r in api.requests if r.method == "DELETE"]


def test_a_failed_client_app_call_does_not_repeat_the_client_key(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    api = _bind_real_service(monkeypatch, real_service, project_id=180)
    api.on("DELETE", r"/clientapps/", status=500, body={"message": "boom"})

    result = make_runner().invoke(
        ["token", "revoke", "KEYSECRET123", "--yes", "--output", "json", "--no-input"]
    )

    assert result.exit_code != 0
    assert "KEYSECRET123" not in result.output.replace('"client_key":', "")
