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
