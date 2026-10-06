"""Who a bearer token stands for, as Mammoth says it."""

import pytest
from mammoth.exceptions import MammothError

from mammoth_mcp_server.config import MCP_RESOURCE_URL
from mammoth_mcp_server.consts import TokenClaims
from mammoth_mcp_server.tokens import token_verifier

from .helpers import GOOD_TOKEN, WORKSPACE, a_fake_api, knows_the_token, run


class TestWhoATokenStandsFor:
    def test_the_caller_is_who_mammoth_says_the_token_is_for(self) -> None:
        with a_fake_api() as api:
            knows_the_token(api, workspace_id=WORKSPACE)
            caller = run(token_verifier.verify_token(GOOD_TOKEN))

        assert caller is not None
        assert caller.token == GOOD_TOKEN
        assert caller.resource == MCP_RESOURCE_URL
        assert caller.claims == {TokenClaims.WORKSPACE_ID: WORKSPACE}

    def test_mammoth_is_asked_with_the_token_itself(self) -> None:
        with a_fake_api() as api:
            knows_the_token(api)
            run(token_verifier.verify_token(GOOD_TOKEN))

        [asked] = api.requests
        assert (asked.method, asked.url.path) == ("GET", "/workspaces/current")
        assert asked.headers["authorization"] == f"Bearer {GOOD_TOKEN}"

    def test_a_token_issued_for_no_server_is_reported_as_such(self) -> None:
        # A Mammoth API token made by hand is live, and was issued for no
        # server. The bearer check refuses a caller with no resource.
        with a_fake_api() as api:
            knows_the_token(api, resource=None)
            caller = run(token_verifier.verify_token(GOOD_TOKEN))

        assert caller is not None
        assert caller.resource is None

    def test_a_token_mammoth_refuses_stands_for_nobody(self) -> None:
        with a_fake_api() as api:
            api.answer("GET", "/workspaces/current", {"message": "Invalid token"}, status=401)
            caller = run(token_verifier.verify_token("mm_gone"))

        assert caller is None

    def test_a_mammoth_that_fails_is_not_read_as_a_bad_token(self) -> None:
        # None would tell the client to sign the user in again, for nothing.
        with a_fake_api() as api:
            api.answer("GET", "/workspaces/current", {"message": "No"}, status=400)
            with pytest.raises(MammothError):
                run(token_verifier.verify_token(GOOD_TOKEN))
