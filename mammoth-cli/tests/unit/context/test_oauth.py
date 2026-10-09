"""Browser sign-in pieces that run on real local objects: files, sockets, hashes."""

from __future__ import annotations

import base64
import hashlib
import threading
import time
from pathlib import Path

import httpx
import pytest

from mammoth_cli.context import credentials, oauth
from mammoth_cli.context.credentials import OAuthSession
from mammoth_cli.errors.envelope import CliError


def _session(expires_in: int) -> OAuthSession:
    return OAuthSession(
        access="mm_" + "a" * 43,
        refresh="12.secret.mac",
        expires_at=int(time.time()) + expires_in,
        client_id="oc_test",
        grant_id=12,
    )


def test_pkce_challenge_is_s256_of_the_verifier() -> None:
    verifier, challenge = oauth.new_pkce_pair()
    digest = hashlib.sha256(verifier.encode()).digest()
    assert challenge == base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    assert 43 <= len(verifier) <= 128


def test_session_survives_the_file_store_and_replace_keeps_the_backend(
    isolated_cli_config: Path,
) -> None:
    first = _session(3600)
    credentials.store_credentials("default", storage="file", oauth=first)
    loaded = credentials.load_credential("default")
    assert loaded is not None and loaded.kind == "oauth" and loaded.oauth == first
    renewed = OAuthSession("mm_" + "b" * 43, "12.next.mac", first.expires_at + 3600, "oc_test", 12)
    assert credentials.replace_oauth_session("default", renewed) == "file"
    stored = credentials.load_credential("default")
    assert stored is not None and stored.oauth == renewed


def test_a_token_credential_still_loads_as_a_token(isolated_cli_config: Path) -> None:
    credentials.store_credentials("default", storage="file", api_token="mm_" + "t" * 43)
    loaded = credentials.load_credential("default")
    assert loaded is not None and loaded.kind == "token" and loaded.oauth is None


def test_refresh_lock_admits_one_process_at_a_time(isolated_cli_config: Path) -> None:
    counter = isolated_cli_config / "counter"
    counter.write_text("0")

    def bump() -> None:
        with oauth._file_lock("default"):
            value = int(counter.read_text())
            time.sleep(0.01)
            counter.write_text(str(value + 1))

    threads = [threading.Thread(target=bump) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert counter.read_text() == "8"


def test_a_fresh_stored_session_is_returned_without_a_refresh(isolated_cli_config: Path) -> None:
    fresh = _session(3600)
    credentials.store_credentials("default", storage="file", oauth=fresh)
    # The base url is unroutable on purpose: a fresh session must not touch it.
    assert oauth.refresh_session("default", "https://127.0.0.1:9/api/v2") == fresh


def test_refresh_without_a_stored_session_says_login_expired(isolated_cli_config: Path) -> None:
    with pytest.raises(CliError) as caught:
        oauth.refresh_session("default", "https://127.0.0.1:9/api/v2")
    assert caught.value.code == oauth.CODE_LOGIN_EXPIRED


def test_loopback_listener_receives_the_redirect_on_a_random_port() -> None:
    with oauth.loopback_listener() as server:
        uri = oauth.redirect_uri_for(server)
        assert uri.startswith("http://127.0.0.1:") and uri.endswith("/callback")
        reply: list[httpx.Response] = []
        client = threading.Thread(
            target=lambda: reply.append(httpx.get(uri, params={"code": "c1", "state": "s1"}))
        )
        client.start()
        params = oauth.wait_for_callback(server, timeout=10)
        client.join()
    assert params == {"code": "c1", "state": "s1"} and reply[0].status_code == 200


@pytest.mark.parametrize(
    "params",
    [
        {"code": "c", "state": "other"},
        {"code": "c", "state": "s", "iss": "https://evil.example/api/v2"},
        {"error": "access_denied", "state": "s"},
        {"state": "s"},
    ],
)
def test_callback_checks_refuse_a_bad_redirect(params: dict[str, str]) -> None:
    with pytest.raises(CliError) as caught:
        oauth.check_callback(params, state="s", issuer="https://x.mammoth.io/api/v2")
    assert caught.value.code == oauth.CODE_OAUTH_LOGIN_FAILED


def test_callback_checks_accept_the_matching_redirect() -> None:
    params = {"code": "c", "state": "s", "iss": "https://x.mammoth.io/api/v2"}
    assert oauth.check_callback(params, state="s", issuer="https://x.mammoth.io/api/v2") == "c"


# --- device code (RFC 8628) ---------------------------------------------------------

_CHALLENGE = {
    "device_code": "dc_secret",
    "user_code": "BCDF-GHJK",
    "verification_uri": "https://app.mammoth.io/#/oauth/device",
    "verification_uri_complete": "https://app.mammoth.io/#/oauth/device?user_code=BCDF-GHJK",
    "expires_in": 900,
    "interval": 5,
}
_GRANT = {"access_token": "mm_" + "a" * 43, "refresh_token": "12.r.m", "expires_in": 3600}


def test_device_challenge_is_read_from_the_server_answer() -> None:
    challenge = oauth.parse_device_challenge(dict(_CHALLENGE))
    assert (challenge.user_code, challenge.interval, challenge.expires_in) == ("BCDF-GHJK", 5, 900)
    assert challenge.verification_uri_complete.endswith("user_code=BCDF-GHJK")


def test_device_challenge_without_a_complete_uri_is_still_usable() -> None:
    body = {k: v for k, v in _CHALLENGE.items() if k != "verification_uri_complete"}
    assert oauth.parse_device_challenge(body).verification_uri_complete == ""


def test_an_unreadable_device_challenge_is_a_failed_login() -> None:
    with pytest.raises(CliError) as caught:
        oauth.parse_device_challenge({"device_code": "x"})
    assert caught.value.code == oauth.CODE_OAUTH_LOGIN_FAILED


def test_pending_keeps_the_interval() -> None:
    assert oauth.read_poll(400, {"error": "authorization_pending"}, 5) == 5


def test_slow_down_adds_five_seconds() -> None:
    assert oauth.read_poll(400, {"error": "slow_down"}, 5) == 10
    assert oauth.read_poll(400, {"error": "slow_down"}, 10) == 15


def test_an_approved_poll_returns_the_tokens() -> None:
    grant = oauth.read_poll(200, dict(_GRANT), 5)
    assert isinstance(grant, oauth.TokenGrant)
    assert grant.access == _GRANT["access_token"] and grant.expires_in == 3600


def test_a_denied_poll_is_a_failed_login() -> None:
    with pytest.raises(CliError) as caught:
        oauth.read_poll(400, {"error": "access_denied"}, 5)
    assert caught.value.code == oauth.CODE_OAUTH_LOGIN_FAILED
    assert "denied" in caught.value.message


def test_an_expired_code_says_to_run_device_login_again() -> None:
    with pytest.raises(CliError) as caught:
        oauth.read_poll(400, {"error": "expired_token"}, 5)
    assert caught.value.code == oauth.CODE_DEVICE_LOGIN_EXPIRED
    assert caught.value.recovery_commands == ["mammoth auth login --device"]


@pytest.mark.parametrize(
    "status, body",
    [(400, {"error": "invalid_grant"}), (500, {}), (401, {"error": "invalid_client"})],
)
def test_any_other_poll_answer_stops_the_login(status: int, body: dict[str, object]) -> None:
    with pytest.raises(CliError) as caught:
        oauth.read_poll(status, body, 5)
    assert caught.value.code == oauth.CODE_OAUTH_LOGIN_FAILED


def test_device_grant_type_is_the_rfc_8628_urn() -> None:
    assert oauth.DEVICE_GRANT_TYPE == "urn:ietf:params:oauth:grant-type:device_code"


def test_a_grant_carries_the_workspace_and_project_the_server_pinned() -> None:
    grant = oauth._parse_grant({**_GRANT, "workspace_id": 247, "project_id": 16712})
    assert (grant.workspace_id, grant.project_id) == (247, 16712)
    session = oauth.session_from_grant(grant, "oc_test")
    assert (session.workspace_id, session.project_id) == (247, 16712)


@pytest.mark.parametrize("extra", [{}, {"workspace_id": None, "project_id": None}])
def test_a_grant_without_scope_has_none(extra: dict[str, object]) -> None:
    grant = oauth._parse_grant({**_GRANT, **extra})
    assert grant.workspace_id is None and grant.project_id is None


# Real network, no stand-ins. No test covers a server that publishes
# ``mammoth_cli_client_id``: none does yet, and a fake server is not allowed.


@pytest.fixture(autouse=False)
def fresh_metadata_cache() -> None:
    oauth.published_client_id.cache_clear()


def test_koyal_signs_in_with_what_it_publishes_else_the_builtin_client(
    fresh_metadata_cache: None,
) -> None:
    published = oauth.published_client_id("koyal")
    assert oauth.client_id_for("koyal") == (published or oauth.BUILTIN_CLIENT_ID)


def test_a_server_that_answers_no_metadata_uses_the_builtin_client(
    fresh_metadata_cache: None,
) -> None:
    # www.mammoth.io is a real host that has no OAuth metadata (it redirects).
    assert oauth.published_client_id("www") is None
    assert oauth.client_id_for("www") == "mammoth-cli"


def test_an_unreachable_server_uses_the_builtin_client(fresh_metadata_cache: None) -> None:
    assert oauth.published_client_id("no-such-env-for-mammoth-cli-test") is None
    assert oauth.client_id_for("no-such-env-for-mammoth-cli-test") == "mammoth-cli"
