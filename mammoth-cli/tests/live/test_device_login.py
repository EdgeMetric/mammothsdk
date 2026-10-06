"""Live checks: device-code sign-in (RFC 8628) and API key expiry against a real server.

WAITING FOR DEPLOY. These need the W8-B backend (``/oauth/device-authorization``, the
``device_code`` grant, ``API_TOKEN_EXPIRED``) on the target server. They skip until
``MAMMOTH_W8B_DEPLOYED=1`` is set; set it only after the backend is deployed there.

The first three need nothing but the apitests token (the CLI's OAuth client id for the
server is built in). The approval tests also need a signed-in browser session of a user
who belongs to the workspace, because only a session may approve a code:
``MAMMOTH_LIVE_SESSION_FILE`` names a JSON file ``{"cookie": "sstokn=...; xcsrftkn=...",
"csrf": "<xcsrftkn value>"}`` copied from that session. They skip without it.

    MAMMOTH_W8B_DEPLOYED=1 MAMMOTH_SERVER_PREFIX=koyal MAMMOTH_EVAL_TOKEN_FILE=... \\
        pytest tests/live/test_device_login.py -m live -v
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from mammoth_cli.context import oauth
from mammoth_cli.context.endpoint import resolve_base_url
from mammoth_cli.errors.envelope import CliError

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("MAMMOTH_W8B_DEPLOYED") != "1",
        reason="waiting for the W8-B backend deploy (set MAMMOTH_W8B_DEPLOYED=1 after it)",
    ),
]

ENV_SESSION_FILE = "MAMMOTH_LIVE_SESSION_FILE"
KEY_TTL_DAYS = 30


@pytest.fixture(scope="module")
def base_url() -> str:
    return resolve_base_url(os.environ.get("MAMMOTH_SERVER_PREFIX"))


@pytest.fixture(scope="module")
def client_id() -> str:
    return oauth.client_id_for(os.environ.get("MAMMOTH_SERVER_PREFIX"))


@pytest.fixture(scope="module")
def session_headers() -> dict[str, str]:
    path = os.environ.get(ENV_SESSION_FILE)
    if not path or not Path(path).is_file():
        pytest.skip(f"{ENV_SESSION_FILE} does not name a session file")
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"Cookie": document["cookie"], "X-CSRF-TOKEN": document["csrf"]}


def _poll(base_url: str, client_id: str, device_code: str) -> tuple[int, dict[str, object]]:
    response = httpx.post(
        f"{base_url}/oauth/token",
        data={
            "grant_type": oauth.DEVICE_GRANT_TYPE,
            "device_code": device_code,
            "client_id": client_id,
        },
        timeout=30,
    )
    return response.status_code, response.json()


def _approve(base_url: str, headers: dict[str, str], user_code: str) -> httpx.Response:
    return httpx.post(
        f"{base_url}/oauth/device-approve",
        json={"user_code": user_code, "project_id": None},
        headers=headers,
        timeout=30,
    )


def test_a_device_code_starts_and_waits_for_approval(base_url: str, client_id: str) -> None:
    challenge = oauth.start_device_login(base_url, client_id=client_id)
    assert challenge.interval >= 1 and challenge.expires_in > 0
    assert challenge.user_code.count("-") == 1
    status, body = _poll(base_url, client_id, challenge.device_code)
    assert (status, body["error"]) == (400, "authorization_pending")


def test_polling_faster_than_the_interval_is_slow_down(base_url: str, client_id: str) -> None:
    challenge = oauth.start_device_login(base_url, client_id=client_id)
    _poll(base_url, client_id, challenge.device_code)
    status, body = _poll(base_url, client_id, challenge.device_code)
    assert (status, body["error"]) == (400, "slow_down")
    assert oauth.read_poll(status, body, challenge.interval) == challenge.interval + 5


def test_an_unknown_device_code_is_invalid_grant(base_url: str, client_id: str) -> None:
    status, body = _poll(base_url, client_id, "not-a-device-code")
    assert (status, body["error"]) == (400, "invalid_grant")


def test_the_cli_signs_in_with_a_device_code_once_approved(
    base_url: str, client_id: str, session_headers: dict[str, str]
) -> None:
    said: list[str] = []
    result: list[oauth.OAuthSession] = []
    errors: list[BaseException] = []

    def login() -> None:
        try:
            result.append(oauth.device_login(base_url, client_id=client_id, say=said.append))
        except CliError as exc:
            errors.append(exc)

    thread = threading.Thread(target=login)
    thread.start()
    deadline = time.monotonic() + 30
    while not any("-" in line and line.strip().isupper() for line in said):
        assert time.monotonic() < deadline, "the CLI never printed a code"
        time.sleep(0.2)
    code = next(line.strip() for line in said if line.strip().isupper() and "-" in line)
    assert _approve(base_url, session_headers, code).status_code == 204
    thread.join(timeout=60)
    assert not errors, errors
    assert result and result[0].access.startswith("mm_")


def test_a_key_the_cli_creates_expires_in_30_days(
    base_url: str, client_id: str, session_headers: dict[str, str]
) -> None:
    challenge = oauth.start_device_login(base_url, client_id=client_id)
    assert _approve(base_url, session_headers, challenge.user_code).status_code == 204
    time.sleep(challenge.interval + oauth.POLL_MARGIN_SECONDS)
    status, body = _poll(base_url, client_id, challenge.device_code)
    assert status == 200
    grant = oauth.TokenGrant(str(body["access_token"]), str(body["refresh_token"]), 3600)
    created = httpx.post(
        f"{base_url}/workspaces/{body['workspace_id']}/clientapps",
        json={"app_name": "uqa-live-device-key", "description": "w8-b live check"},
        headers={"Authorization": f"Bearer {grant.access}"},
        timeout=30,
    )
    assert created.status_code == 201, created.text
    expires = datetime.fromisoformat(created.json()["expires_at"]).replace(tzinfo=UTC)
    days = (expires - datetime.now(UTC)).total_seconds() / 86400
    assert KEY_TTL_DAYS - 0.1 < days < KEY_TTL_DAYS + 0.1
    key = created.json()
    removed = httpx.delete(
        f"{base_url}/workspaces/{body['workspace_id']}/clientapps/{key['app_key']}",
        headers={"Authorization": f"Bearer {grant.access}"},
        timeout=30,
    )
    assert removed.status_code == 204, removed.text
