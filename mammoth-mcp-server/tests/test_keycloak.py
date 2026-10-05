"""Signing in with a Mammoth login, through Keycloak, as a client and a browser drive it.

Keycloak is faked at its two endpoints: the browser is sent to its sign-in
page, and this server trades a code and refreshes tokens at its token endpoint.
Everything else is the real server.
"""

import base64
import hashlib
import json
import time
from collections.abc import Iterator
from contextlib import ExitStack
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError
from starlette.testclient import TestClient

from mammoth_mcp_server import keycloak, login
from mammoth_mcp_server.app import create_app
from mammoth_mcp_server.config import MCP_RESOURCE_URL, SERVER_URL
from mammoth_mcp_server.consts import OAuthFields, TokenClaims
from mammoth_mcp_server.sdk import build_client
from mammoth_mcp_server.store import recall, redis_key, unseal

from .helpers import WORKSPACE, FakeRedis, a_fake_api, a_fake_store, run

ISSUER = "https://keycloak.example/auth/realms/mammoth"
CLIENT_ID = "mammoth-mcp"
CLIENT_SECRET = "the-client-secret"
REDIRECT = "https://client.example/callback"
VERIFIER = "a-code-verifier-that-is-long-enough-to-be-accepted-as-one"
JSON = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


class FakeKeycloak:
    """Keycloak's token endpoint: one code it will trade, and refresh tokens it honours."""

    def __init__(self) -> None:
        self.codes: dict[str, str] = {}
        self.grants: list[dict[str, str]] = []
        self.refresh_refused = False
        self.lives = 300
        self.session = 3600

    def handle(self, request: httpx.Request) -> httpx.Response:
        form = {k: v[0] for k, v in parse_qs(request.content.decode()).items()}
        self.grants.append(form)
        if (form.get("client_id"), form.get("client_secret")) != (CLIENT_ID, CLIENT_SECRET):
            return httpx.Response(401, json={"error": "unauthorized_client"})
        if form["grant_type"] == "authorization_code":
            challenge = self.codes.pop(form["code"], None)
            digest = hashlib.sha256(form["code_verifier"].encode()).digest()
            if challenge != base64.urlsafe_b64encode(digest).rstrip(b"=").decode():
                return httpx.Response(400, json={"error": "invalid_grant"})
            return self.tokens("first")
        if self.refresh_refused:
            return httpx.Response(400, json={"error": "invalid_grant"})
        return self.tokens("renewed")

    def tokens(self, which: str) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "access_token": f"kc-access-{which}",
                "refresh_token": f"kc-refresh-{which}",
                "expires_in": self.lives,
                "refresh_expires_in": self.session,
            },
        )


@pytest.fixture
def kc() -> Iterator[FakeKeycloak]:
    fake = FakeKeycloak()
    with ExitStack() as stack:
        for module, name, value in (
            (login, "KEYCLOAK_ENABLED", True),
            (keycloak, "KEYCLOAK_ISSUER", ISSUER),
            (keycloak, "KEYCLOAK_CLIENT_ID", CLIENT_ID),
            (keycloak, "KEYCLOAK_CLIENT_SECRET", CLIENT_SECRET),
        ):
            stack.enter_context(patch.object(module, name, value))
        keycloak.use_transport(httpx.MockTransport(fake.handle))
        stack.callback(keycloak.use_transport, None)
        yield fake


@pytest.fixture
def redis() -> Iterator[FakeRedis]:
    with a_fake_store() as fake:
        yield fake


@pytest.fixture
def server(redis: FakeRedis, kc: FakeKeycloak) -> Iterator[TestClient]:
    with TestClient(create_app(), base_url=SERVER_URL) as client:
        yield client


def challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def open_login_page(server: TestClient) -> tuple[str, str]:
    """Register a client and start its sign-in. Returns its id and the login page's state."""
    client_id = server.post(
        "/register",
        json={
            "redirect_uris": [REDIRECT],
            "token_endpoint_auth_method": "none",
            "grant_types": ["authorization_code"],
            "response_types": ["code"],
        },
    ).json()["client_id"]
    to_login = server.get(
        "/authorize",
        params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": REDIRECT,
            "code_challenge": challenge(VERIFIER),
            "code_challenge_method": "S256",
            "state": "the-clients-own-state",
            "resource": MCP_RESOURCE_URL,
        },
        follow_redirects=False,
    )
    return client_id, parse_qs(urlparse(to_login.headers["location"]).query)["state"][0]


def sign_in_at_keycloak(server: TestClient, kc: FakeKeycloak, state: str) -> httpx.Response:
    """Press the button, sign in at Keycloak, and come back. Returns where we are sent."""
    to_keycloak = server.get("/login/keycloak", params={"state": state}, follow_redirects=False)
    sent = urlparse(to_keycloak.headers["location"])
    asked = {k: v[0] for k, v in parse_qs(sent.query).items()}
    assert f"{sent.scheme}://{sent.netloc}{sent.path}" == (f"{ISSUER}/protocol/openid-connect/auth")
    assert asked["client_id"] == CLIENT_ID
    assert asked["redirect_uri"] == f"{SERVER_URL}/login/keycloak/callback"
    assert asked["code_challenge_method"] == "S256"
    kc.codes["kc-code"] = asked["code_challenge"]
    return server.get(
        "/login/keycloak/callback",
        params={"code": "kc-code", "state": asked["state"]},
        follow_redirects=False,
    )


def our_token(server: TestClient, client_id: str, back: httpx.Response) -> str:
    code = parse_qs(urlparse(back.headers["location"]).query)["code"][0]
    return server.post(
        "/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT,
            "client_id": client_id,
            "code_verifier": VERIFIER,
            "resource": MCP_RESOURCE_URL,
        },
    ).json()["access_token"]


def call_tool(server: TestClient, token: str, name: str, **arguments: object) -> dict:
    return server.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        headers={**JSON, "Authorization": f"Bearer {token}"},
    ).json()["result"]


class TestTheLoginPage:
    def test_the_page_offers_the_mammoth_login_when_the_server_has_one(
        self, server: TestClient
    ) -> None:
        page = server.get("/login", params={"state": "abc"})

        assert "Sign in with Mammoth" in page.text
        assert "/login/keycloak?state=abc" in page.text

    def test_the_page_offers_the_api_token_alone_when_it_has_none(self, server: TestClient) -> None:
        with patch.object(login, "KEYCLOAK_ENABLED", False):
            page = server.get("/login", params={"state": "abc"})

        assert "Sign in with Mammoth" not in page.text


class TestSigningInWithAMammothLogin:
    def test_a_mammoth_login_ends_in_tool_calls_as_that_user_in_any_workspace(
        self, server: TestClient, kc: FakeKeycloak
    ) -> None:
        client_id, state = open_login_page(server)

        back = sign_in_at_keycloak(server, kc, state)
        ours = our_token(server, client_id, back)

        assert back.headers["location"].startswith(REDIRECT)
        assert "state=the-clients-own-state" in back.headers["location"]
        with a_fake_api() as api:
            api.answer("GET", "/workspaces", {"workspaces": [{"id": 4}, {"id": 9}]})
            api.answer("GET", "/workspaces/9/projects", {"projects": []})
            assert not call_tool(server, ours, "list_workspaces").get("isError")
            assert not call_tool(server, ours, "list_projects", workspace_id=9).get("isError")

        listed, projects = api.requests
        # Mammoth is called with the user's own Keycloak token, never with ours,
        # and a login is not tied to one workspace.
        assert listed.headers["authorization"] == "Bearer kc-access-first"
        assert projects.headers["authorization"] == "Bearer kc-access-first"
        assert projects.headers["x-workspace-id"] == "9"

    def test_the_server_signs_in_at_keycloak_as_its_own_client_with_pkce(
        self, server: TestClient, kc: FakeKeycloak
    ) -> None:
        _, state = open_login_page(server)

        sign_in_at_keycloak(server, kc, state)

        [grant] = kc.grants
        assert grant["grant_type"] == "authorization_code"
        assert grant["client_secret"] == CLIENT_SECRET
        assert grant["code_verifier"]

    def test_the_users_keycloak_tokens_are_stored_sealed(
        self, server: TestClient, kc: FakeKeycloak, redis: FakeRedis
    ) -> None:
        client_id, state = open_login_page(server)
        our_token(server, client_id, sign_in_at_keycloak(server, kc, state))

        assert all("kc-access" not in value for value in redis.values.values())
        assert all("kc-refresh" not in value for value in redis.values.values())

    def test_the_sign_in_is_kept_as_long_as_keycloak_keeps_the_session(
        self, server: TestClient, kc: FakeKeycloak, redis: FakeRedis
    ) -> None:
        kc.session = 1800
        client_id, state = open_login_page(server)

        ours = our_token(server, client_id, sign_in_at_keycloak(server, kc, state))

        assert redis.seconds[redis_key(OAuthFields.TOKEN, ours)] == 1800

    def test_a_sign_in_keycloak_refused_is_shown_on_the_login_page(
        self, server: TestClient
    ) -> None:
        page = server.get("/login/keycloak/callback", params={"error": "access_denied"})

        assert page.status_code == 400
        assert "not completed" in page.text

    def test_a_code_keycloak_will_not_trade_is_shown_on_the_login_page(
        self, server: TestClient, kc: FakeKeycloak
    ) -> None:
        _, state = open_login_page(server)
        to_keycloak = server.get("/login/keycloak", params={"state": state}, follow_redirects=False)
        kc_state = parse_qs(urlparse(to_keycloak.headers["location"]).query)["state"][0]

        page = server.get("/login/keycloak/callback", params={"code": "forged", "state": kc_state})

        assert page.status_code == 400
        assert "refused" in page.text

    def test_a_keycloak_sign_in_cannot_be_finished_twice(
        self, server: TestClient, kc: FakeKeycloak
    ) -> None:
        # A copied callback link must not sign a second client in.
        _, state = open_login_page(server)
        to_keycloak = server.get("/login/keycloak", params={"state": state}, follow_redirects=False)
        asked = parse_qs(urlparse(to_keycloak.headers["location"]).query)
        kc.codes["kc-code"] = asked["code_challenge"][0]
        kc.codes["kc-code-2"] = asked["code_challenge"][0]
        callback = "/login/keycloak/callback"
        server.get(callback, params={"code": "kc-code", "state": asked["state"][0]})

        again = server.get(callback, params={"code": "kc-code-2", "state": asked["state"][0]})

        assert again.status_code == 400
        assert "expired" in again.text
        # Refused before Keycloak is asked: the second code is never traded.
        assert len(kc.grants) == 1

    def test_a_keycloak_sign_in_that_expired_is_refused(self, server: TestClient) -> None:
        page = server.get("/login/keycloak/callback", params={"code": "c", "state": "gone"})

        assert page.status_code == 400
        assert "expired" in page.text


class TestKeepingTheLoginFresh:
    """A Keycloak access token lives minutes; the connector lives far longer."""

    def signed_in(self, server: TestClient, kc: FakeKeycloak) -> str:
        client_id, state = open_login_page(server)
        return our_token(server, client_id, sign_in_at_keycloak(server, kc, state))

    @staticmethod
    def a_client_bearer(ours: str) -> str:
        """The bearer a tool call's client carries, for the caller our token stands for."""
        from mcp.server.auth.middleware.auth_context import auth_context_var
        from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser

        from mammoth_mcp_server.oauth import oauth_provider

        caller = run(oauth_provider.load_access_token(ours))
        assert caller is not None
        reset = auth_context_var.set(AuthenticatedUser(caller))

        async def bearer() -> str:
            async with build_client(WORKSPACE) as client:
                return str(client.session.headers["authorization"])

        try:
            return run(bearer())
        finally:
            auth_context_var.reset(reset)

    def test_an_access_token_about_to_end_is_refreshed_and_the_new_one_kept(
        self, server: TestClient, kc: FakeKeycloak
    ) -> None:
        kc.lives = 10
        ours = self.signed_in(server, kc)

        first = self.a_client_bearer(ours)
        kc.lives = 300
        second = self.a_client_bearer(ours)

        assert first == "Bearer kc-access-renewed"
        stored = unseal(run(recall(OAuthFields.TOKEN, ours))[OAuthFields.CREDENTIALS])
        assert stored[TokenClaims.KEYCLOAK_ACCESS] == "kc-access-renewed"
        assert stored[TokenClaims.KEYCLOAK_REFRESH] == "kc-refresh-renewed"
        assert second == first

    def test_a_fresh_access_token_is_used_as_it_is(
        self, server: TestClient, kc: FakeKeycloak
    ) -> None:
        ours = self.signed_in(server, kc)

        assert self.a_client_bearer(ours) == "Bearer kc-access-first"
        assert [grant["grant_type"] for grant in kc.grants] == ["authorization_code"]

    def test_a_session_keycloak_ended_asks_the_user_to_sign_in_again(
        self, server: TestClient, kc: FakeKeycloak
    ) -> None:
        kc.lives = 10
        ours = self.signed_in(server, kc)
        kc.refresh_refused = True

        with pytest.raises(ToolError, match="sign-in has ended"):
            self.a_client_bearer(ours)

        assert run(recall(OAuthFields.TOKEN, ours)) is None

    def test_refreshing_keeps_the_refresh_token_when_keycloak_sends_none(
        self, kc: FakeKeycloak
    ) -> None:
        def no_new_refresh(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"access_token": "a2", "expires_in": 300})

        keycloak.use_transport(httpx.MockTransport(no_new_refresh))
        renewed = run(
            keycloak.refresh(
                {
                    TokenClaims.KEYCLOAK_ACCESS: "a1",
                    TokenClaims.KEYCLOAK_REFRESH: "r1",
                    TokenClaims.KEYCLOAK_EXPIRES_AT: time.time(),
                }
            )
        )

        assert renewed[TokenClaims.KEYCLOAK_REFRESH] == "r1"
        assert json.dumps(renewed)
