"""Signing in with a Mammoth API token, step by step, as a client drives it."""

import base64
import hashlib
import json

import pytest
from mcp.server.auth.provider import AuthorizationParams, TokenError
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import AnyUrl

from mammoth_mcp_server.config import MCP_LOGIN_URL, MCP_RESOURCE_URL
from mammoth_mcp_server.consts import TOKEN_SECONDS, OAuthFields, TokenClaims
from mammoth_mcp_server.oauth import LoginRefused, TokenOAuthProvider
from mammoth_mcp_server.store import redis_key

from .helpers import GOOD_TOKEN, WORKSPACE, FakeRedis, a_fake_store, a_mammoth_that_knows, run

REDIRECT = "https://client.example/callback"
VERIFIER = "a-code-verifier-long-enough-to-be-one"
CHALLENGE = (
    base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).rstrip(b"=").decode()
)


@pytest.fixture
def redis():
    with a_fake_store() as fake, a_mammoth_that_knows():
        yield fake


class TestSigningInWithAnApiToken:
    provider = TokenOAuthProvider()

    def register(self) -> OAuthClientInformationFull:
        client = OAuthClientInformationFull(redirect_uris=[AnyUrl(REDIRECT)], client_id="mine")
        run(self.provider.register_client(client))
        return client

    def open_login(self, client: OAuthClientInformationFull) -> str:
        """Start a sign-in and return the state the login page is opened with."""
        login_url = run(
            self.provider.authorize(
                client,
                AuthorizationParams(
                    state="the-clients-own-state",
                    scopes=[],
                    code_challenge=CHALLENGE,
                    redirect_uri=AnyUrl(REDIRECT),
                    redirect_uri_provided_explicitly=True,
                    resource=MCP_RESOURCE_URL,
                ),
            )
        )
        assert login_url.startswith(f"{MCP_LOGIN_URL}?{OAuthFields.STATE}=")
        return login_url.split("=", 1)[1]

    def sign_in(self, client: OAuthClientInformationFull, token: str = GOOD_TOKEN) -> str:
        """Paste a token on the login page and return the code the client is sent."""
        back_to_client = run(self.provider.accept_login(self.open_login(client), token))
        assert back_to_client.startswith(REDIRECT)
        assert "state=the-clients-own-state" in back_to_client
        return back_to_client.split("code=", 1)[1].split("&", 1)[0]

    def token_of(self, client: OAuthClientInformationFull, code: str) -> str:
        loaded = run(self.provider.load_authorization_code(client, code))
        assert loaded is not None
        return run(self.provider.exchange_authorization_code(client, loaded)).access_token

    def test_a_client_is_given_an_id_of_its_own(self, redis: FakeRedis) -> None:
        # A client names itself, so two could otherwise claim the same id and
        # read each other's codes.
        client = self.register()

        assert client.client_id != "mine"
        assert run(self.provider.get_client(client.client_id)) is not None

    def test_a_good_token_signs_the_user_in_as_themselves(self, redis: FakeRedis) -> None:
        client = self.register()

        ours = self.token_of(client, self.sign_in(client))
        caller = run(self.provider.load_access_token(ours))

        assert caller is not None
        assert caller.claims == {
            TokenClaims.API_TOKEN: GOOD_TOKEN,
            TokenClaims.WORKSPACE_ID: WORKSPACE,
        }
        assert caller.resource == MCP_RESOURCE_URL

    def test_a_token_mammoth_does_not_take_is_refused_on_the_page(self, redis: FakeRedis) -> None:
        client = self.register()

        with pytest.raises(LoginRefused, match="did not accept"):
            run(self.provider.accept_login(self.open_login(client), "mm_wrong"))

    def test_a_refused_sign_in_can_be_tried_again(self, redis: FakeRedis) -> None:
        # The user mistyped; the page they are on must still work.
        client = self.register()
        state = self.open_login(client)
        with pytest.raises(LoginRefused):
            run(self.provider.accept_login(state, "mm_wrong"))

        assert run(self.provider.accept_login(state, GOOD_TOKEN)).startswith(REDIRECT)

    def test_a_sign_in_that_expired_is_refused(self, redis: FakeRedis) -> None:
        with pytest.raises(LoginRefused, match="expired"):
            run(self.provider.accept_login("no-such-state", GOOD_TOKEN))

    def test_a_code_buys_one_token_and_no_more(self, redis: FakeRedis) -> None:
        client = self.register()
        code = self.sign_in(client)
        loaded = run(self.provider.load_authorization_code(client, code))
        run(self.provider.exchange_authorization_code(client, loaded))

        with pytest.raises(TokenError):
            run(self.provider.exchange_authorization_code(client, loaded))

    def test_a_code_is_no_good_to_another_client(self, redis: FakeRedis) -> None:
        code = self.sign_in(self.register())

        assert run(self.provider.load_authorization_code(self.register(), code)) is None

    def test_the_store_never_holds_the_users_token_in_the_clear(self, redis: FakeRedis) -> None:
        client = self.register()
        ours = self.token_of(client, self.sign_in(client))

        stored = redis.values[redis_key(OAuthFields.TOKEN, ours)]

        assert GOOD_TOKEN not in stored
        assert GOOD_TOKEN not in json.dumps(json.loads(stored))
        assert all(GOOD_TOKEN not in value for value in redis.values.values())

    def test_a_token_lasts_thirty_days(self, redis: FakeRedis) -> None:
        client = self.register()
        ours = self.token_of(client, self.sign_in(client))

        assert redis.seconds[redis_key(OAuthFields.TOKEN, ours)] == TOKEN_SECONDS

    def test_a_revoked_token_stands_for_nobody(self, redis: FakeRedis) -> None:
        client = self.register()
        ours = self.token_of(client, self.sign_in(client))
        caller = run(self.provider.load_access_token(ours))

        run(self.provider.revoke_token(caller))

        assert run(self.provider.load_access_token(ours)) is None

    def test_a_token_this_server_never_issued_stands_for_nobody(self, redis: FakeRedis) -> None:
        assert run(self.provider.load_access_token("made-up")) is None


class TestAClientThatSendsTheApiTokenItself:
    provider = TokenOAuthProvider()

    def test_a_good_api_token_is_its_own_sign_in(self, redis: FakeRedis) -> None:
        caller = run(self.provider.load_access_token(GOOD_TOKEN))

        assert caller is not None
        assert caller.claims[TokenClaims.API_TOKEN] == GOOD_TOKEN
        assert caller.claims[TokenClaims.WORKSPACE_ID] == WORKSPACE
        # Nothing is stored for it: the client holds the token itself.
        assert redis.values == {}

    def test_an_api_token_mammoth_does_not_take_stands_for_nobody(self, redis: FakeRedis) -> None:
        assert run(self.provider.load_access_token("mm_wrong")) is None
