"""The server as a client and a browser reach it, over HTTP."""

import base64
import hashlib
from urllib.parse import parse_qs, urlparse

import pytest
from starlette.testclient import TestClient

from mammoth_mcp_server.app import create_app
from mammoth_mcp_server.config import MCP_RESOURCE_URL, SERVER_URL
from mammoth_mcp_server.consts import OAuthFields, UploadFields
from mammoth_mcp_server.upload_tickets import mint_ticket, read_ticket

from .helpers import (
    GOOD_TOKEN,
    WORKSPACE,
    FakeRedis,
    a_fake_api,
    a_fake_store,
    a_mammoth_that_knows,
    as_caller,
    run,
)

JSON = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
LIST_TOOLS = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
PROJECT = 3
FILES = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/files"


@pytest.fixture
def redis():
    with a_fake_store() as fake, a_mammoth_that_knows():
        yield fake


@pytest.fixture
def server(redis: FakeRedis):
    with TestClient(create_app(), base_url=SERVER_URL) as client:
        yield client


class TestWhoMayCallTheMcpEndpoint:
    def test_a_caller_with_no_token_is_told_where_to_sign_in(self, server: TestClient) -> None:
        refused = server.post("/mcp", json=LIST_TOOLS, headers=JSON)

        assert refused.status_code == 401
        assert "resource_metadata=" in refused.headers["www-authenticate"]

    def test_the_metadata_names_this_server_as_where_to_sign_in(self, server: TestClient) -> None:
        resource = server.get("/.well-known/oauth-protected-resource/mcp").json()
        issuer = server.get("/.well-known/oauth-authorization-server").json()

        assert resource["resource"] == MCP_RESOURCE_URL
        # A client compares the issuer letter for letter with the one it was sent to.
        assert resource["authorization_servers"] == [issuer["issuer"]]
        assert issuer["issuer"].rstrip("/") == SERVER_URL
        assert issuer["registration_endpoint"] == f"{SERVER_URL}/register"

    def test_a_mammoth_api_token_opens_the_endpoint(self, server: TestClient) -> None:
        answer = server.post(
            "/mcp", json=LIST_TOOLS, headers={**JSON, "Authorization": f"Bearer {GOOD_TOKEN}"}
        )

        assert answer.status_code == 200
        names = {tool["name"] for tool in answer.json()["result"]["tools"]}
        assert {"list_workspaces", "add_transformations", "request_upload"} <= names

    def test_a_token_mammoth_does_not_take_is_turned_away(self, server: TestClient) -> None:
        refused = server.post(
            "/mcp", json=LIST_TOOLS, headers={**JSON, "Authorization": "Bearer mm_wrong"}
        )

        assert refused.status_code == 401


class TestTheLoginPage:
    def test_the_page_asks_for_an_api_token_and_nothing_else(self, server: TestClient) -> None:
        page = server.get("/login", params={OAuthFields.STATE: "abc"})

        assert page.status_code == 200
        assert f'name="{OAuthFields.API_TOKEN}"' in page.text
        assert 'value="abc"' in page.text
        assert "secret" not in page.text.lower()

    def test_a_state_cannot_break_out_of_the_page(self, server: TestClient) -> None:
        page = server.get("/login", params={OAuthFields.STATE: '"><script>x</script>'})

        assert "<script>x</script>" not in page.text

    @pytest.mark.parametrize(
        ("pasted", "reason"),
        [("", "Paste your Mammoth API token"), ("not-a-token", "starts with mm_")],
        ids=["nothing", "not-a-token"],
    )
    def test_what_is_not_a_token_is_refused_before_mammoth_is_asked(
        self, server: TestClient, pasted: str, reason: str
    ) -> None:
        page = server.post("/login", data={OAuthFields.STATE: "abc", OAuthFields.API_TOKEN: pasted})

        assert page.status_code == 400
        assert reason in page.text

    def test_a_sign_in_that_expired_redraws_the_page_with_the_reason(
        self, server: TestClient
    ) -> None:
        page = server.post(
            "/login", data={OAuthFields.STATE: "gone", OAuthFields.API_TOKEN: GOOD_TOKEN}
        )

        assert page.status_code == 400
        assert "expired" in page.text


class TestTheUploadPage:
    @staticmethod
    def a_ticket() -> str:
        """A ticket minted as a signed-in caller, as `request_upload` mints one."""
        from mcp.server.auth.middleware.auth_context import get_access_token

        with as_caller(token=GOOD_TOKEN):
            caller = get_access_token()
            assert caller is not None
            return run(mint_ticket(caller, WORKSPACE, PROJECT))

    def test_a_link_with_no_ticket_says_it_is_no_longer_good(self, server: TestClient) -> None:
        page = server.get("/upload", params={UploadFields.TICKET: "made-up"})

        assert page.status_code == 410
        assert "no longer good" in page.text

    def test_a_live_ticket_opens_the_drop_zone(self, server: TestClient) -> None:
        page = server.get("/upload", params={UploadFields.TICKET: self.a_ticket()})

        assert page.status_code == 200
        assert 'type="file"' in page.text

    def test_the_file_goes_to_mammoth_as_the_user_and_the_ticket_is_spent(
        self, server: TestClient
    ) -> None:
        ticket = self.a_ticket()
        with a_fake_api() as api:
            api.answer("POST", FILES, {"id": 31, "status": "processing"})
            sent = server.post(
                "/upload",
                params={UploadFields.TICKET: ticket},
                files={"data": ("sales.csv", b"a,b\n1,2\n", "text/csv")},
            )

        [upload] = api.sent("POST", FILES)
        assert sent.status_code == 200
        assert sent.json() == {UploadFields.STATUS: UploadFields.PROCESSING}
        assert upload.headers["authorization"] == f"Bearer {GOOD_TOKEN}"
        assert b'filename="sales.csv"' in upload.content
        spent = run(read_ticket(ticket))
        assert spent[UploadFields.JOB_ID] == 31
        assert spent[UploadFields.FILE_NAMES] == ["sales.csv"]
        # The link has been used, so nothing may act as the user through it again.
        assert UploadFields.CALLER not in spent
        assert server.get("/upload", params={UploadFields.TICKET: ticket}).status_code == 410

    def test_the_in_chat_uploader_may_read_the_answer(self, server: TestClient) -> None:
        # The uploader runs in the host's sandboxed frame, on another origin. Without
        # this header the browser hides the answer, and the uploader says the file
        # never arrived when it did.
        ticket = self.a_ticket()
        with a_fake_api() as api:
            api.answer("POST", FILES, {"id": 31, "status": "processing"})
            sent = server.post(
                "/upload",
                params={UploadFields.TICKET: ticket},
                files={"data": ("sales.csv", b"a,b\n1,2\n", "text/csv")},
                headers={"Origin": "https://sandbox.example"},
            )

        assert sent.status_code == 200
        assert sent.headers["access-control-allow-origin"] == "*"

    def test_the_in_chat_uploader_may_read_a_refusal_too(self, server: TestClient) -> None:
        refused = server.post(
            "/upload",
            params={UploadFields.TICKET: "made-up"},
            files={"data": ("sales.csv", b"a,b\n1,2\n", "text/csv")},
            headers={"Origin": "https://sandbox.example"},
        )

        assert refused.status_code == 410
        assert refused.headers["access-control-allow-origin"] == "*"

    def test_a_file_sent_on_a_link_that_is_no_longer_good_goes_nowhere(
        self, server: TestClient
    ) -> None:
        with a_fake_api() as api:
            refused = server.post(
                "/upload",
                params={UploadFields.TICKET: "made-up"},
                files={"data": ("sales.csv", b"a,b\n1,2\n", "text/csv")},
            )

        assert refused.status_code == 410
        assert api.requests == []

    def test_an_upload_with_no_file_is_refused_and_the_ticket_kept(
        self, server: TestClient
    ) -> None:
        ticket = self.a_ticket()

        refused = server.post("/upload", params={UploadFields.TICKET: ticket}, data={"x": "y"})

        assert refused.status_code == 400
        assert server.get("/upload", params={UploadFields.TICKET: ticket}).status_code == 200


class TestTheWholeSignInAsAClientDrivesIt:
    """Register, be sent to the login page, paste a token, trade the code, call a tool."""

    REDIRECT = "https://client.example/callback"
    VERIFIER = "a-code-verifier-that-is-long-enough-to-be-accepted-as-one"

    @classmethod
    def challenge(cls) -> str:
        digest = hashlib.sha256(cls.VERIFIER.encode()).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    def test_a_pasted_token_ends_in_a_tool_call_as_that_user(self, server: TestClient) -> None:
        registered = server.post(
            "/register",
            json={
                "redirect_uris": [self.REDIRECT],
                "token_endpoint_auth_method": "none",
                "grant_types": ["authorization_code"],
                "response_types": ["code"],
            },
        ).json()
        client_id = registered["client_id"]

        to_login = server.get(
            "/authorize",
            params={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": self.REDIRECT,
                "code_challenge": self.challenge(),
                "code_challenge_method": "S256",
                "state": "the-clients-own-state",
                "resource": MCP_RESOURCE_URL,
            },
            follow_redirects=False,
        )
        login_url = urlparse(to_login.headers["location"])
        state = parse_qs(login_url.query)[OAuthFields.STATE][0]
        assert login_url.path == "/login"

        back = server.post(
            "/login",
            data={OAuthFields.STATE: state, OAuthFields.API_TOKEN: GOOD_TOKEN},
            follow_redirects=False,
        )
        sent_back = parse_qs(urlparse(back.headers["location"]).query)
        assert back.headers["location"].startswith(self.REDIRECT)
        assert sent_back["state"] == ["the-clients-own-state"]

        issued = server.post(
            "/token",
            data={
                "grant_type": "authorization_code",
                "code": sent_back["code"][0],
                "redirect_uri": self.REDIRECT,
                "client_id": client_id,
                "code_verifier": self.VERIFIER,
                "resource": MCP_RESOURCE_URL,
            },
        ).json()
        ours = issued["access_token"]
        assert not ours.startswith("mm_")

        with a_fake_api() as api:
            api.answer("GET", "/workspaces", {"workspaces": [{"id": WORKSPACE}]})
            called = server.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "list_workspaces", "arguments": {}},
                },
                headers={**JSON, "Authorization": f"Bearer {ours}"},
            )

        [request] = api.sent("GET", "/workspaces")
        assert called.json()["result"]["structuredContent"] == {"workspaces": [{"id": WORKSPACE}]}
        # The tool call reached Mammoth with the user's own token, not ours.
        assert request.headers["authorization"] == f"Bearer {GOOD_TOKEN}"
