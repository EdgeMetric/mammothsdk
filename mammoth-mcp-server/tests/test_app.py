"""The server as a client and a browser reach it, over HTTP."""

import pytest
from starlette.testclient import TestClient

from mammoth_mcp_server.app import create_app
from mammoth_mcp_server.config import MCP_OAUTH_URL, MCP_RESOURCE_URL, SERVER_URL
from mammoth_mcp_server.consts import UploadFields
from mammoth_mcp_server.upload_tickets import mint_ticket, read_ticket

from .helpers import (
    GOOD_TOKEN,
    WORKSPACE,
    FakeRedis,
    a_fake_api,
    a_fake_store,
    as_caller,
    knows_the_token,
    run,
)

JSON = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
LIST_TOOLS = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
AS_THE_USER = {**JSON, "Authorization": f"Bearer {GOOD_TOKEN}"}
PROJECT = 3
FILES = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/files"


@pytest.fixture
def redis():
    with a_fake_store() as fake:
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

    def test_the_metadata_names_mammoth_as_where_to_sign_in(self, server: TestClient) -> None:
        resource = server.get("/.well-known/oauth-protected-resource/mcp").json()

        assert resource["resource"] == MCP_RESOURCE_URL
        # A client compares the issuer letter for letter with the one it is sent to.
        assert resource["authorization_servers"] == [MCP_OAUTH_URL]

    @pytest.mark.parametrize(
        "path",
        ["/.well-known/oauth-authorization-server", "/authorize", "/token", "/register", "/login"],
    )
    def test_the_server_has_no_sign_in_of_its_own(self, server: TestClient, path: str) -> None:
        assert server.get(path).status_code == 404

    def test_a_token_mammoth_issued_for_this_server_opens_the_endpoint(
        self, server: TestClient
    ) -> None:
        with a_fake_api() as api:
            knows_the_token(api)
            answer = server.post("/mcp", json=LIST_TOOLS, headers=AS_THE_USER)

        [asked] = api.sent("GET", "/workspaces/current")
        assert answer.status_code == 200
        assert asked.headers["authorization"] == f"Bearer {GOOD_TOKEN}"
        names = {tool["name"] for tool in answer.json()["result"]["tools"]}
        assert {"list_workspaces", "add_transformations", "request_upload"} <= names

    @pytest.mark.parametrize(
        "resource",
        [None, "https://another.example/mcp", SERVER_URL],
        ids=["issued-for-no-server", "issued-for-another-server", "not-the-mcp-uri"],
    )
    def test_a_live_token_that_is_not_for_this_server_is_turned_away(
        self, server: TestClient, resource: str | None
    ) -> None:
        with a_fake_api() as api:
            knows_the_token(api, resource=resource)
            refused = server.post("/mcp", json=LIST_TOOLS, headers=AS_THE_USER)

        assert refused.status_code == 401

    def test_a_token_mammoth_does_not_take_is_turned_away(self, server: TestClient) -> None:
        with a_fake_api() as api:
            api.answer("GET", "/workspaces/current", {"message": "Invalid token"}, status=401)
            refused = server.post("/mcp", json=LIST_TOOLS, headers=AS_THE_USER)

        assert refused.status_code == 401

    def test_mammoth_is_asked_again_on_every_request(self, server: TestClient) -> None:
        # Nothing is kept, so a token the user revoked stops working at once.
        with a_fake_api() as api:
            knows_the_token(api)
            api.answer("GET", "/workspaces/current", {"message": "Invalid token"}, status=401)
            first = server.post("/mcp", json=LIST_TOOLS, headers=AS_THE_USER)
            second = server.post("/mcp", json=LIST_TOOLS, headers=AS_THE_USER)

        assert (first.status_code, second.status_code) == (200, 401)

    def test_a_tool_call_reaches_mammoth_with_the_callers_own_token(
        self, server: TestClient
    ) -> None:
        with a_fake_api() as api:
            knows_the_token(api)
            api.answer("GET", "/workspaces", {"workspaces": [{"id": WORKSPACE}]})
            called = server.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "list_workspaces", "arguments": {}},
                },
                headers=AS_THE_USER,
            )

        [request] = api.sent("GET", "/workspaces")
        assert called.json()["result"]["structuredContent"] == {"workspaces": [{"id": WORKSPACE}]}
        assert request.headers["authorization"] == f"Bearer {GOOD_TOKEN}"
        assert request.headers["x-workspace-id"] == str(WORKSPACE)


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
