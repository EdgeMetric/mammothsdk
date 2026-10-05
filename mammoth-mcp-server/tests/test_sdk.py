"""The SDK client a tool call is given: whose it is, where it points, and what it says on failure."""

import pytest
from mammoth.exceptions import MammothAPIError
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.consts import JOB_POLL_SECONDS, UPLOAD_FIELD
from mammoth_mcp_server.sdk import (
    API_ERROR_PREFIX,
    UNREADABLE_API_ERROR,
    build_client,
    read_sdk_errors,
    request_api,
)

from .helpers import API_URL, TOKEN, WORKSPACE, a_fake_api, as_caller, run


async def a_client(workspace_id: int | None = WORKSPACE, project_id: int | None = None):
    async with build_client(workspace_id, project_id) as client:
        return client


class TestTheClientATooLCallIsGiven:
    def test_the_caller_keeps_their_own_token(self) -> None:
        with as_caller(token="mm_theirs"):
            client = run(a_client())

        assert client.session.headers["authorization"] == "Bearer mm_theirs"

    def test_the_client_acts_in_the_workspace_the_token_is_for(self) -> None:
        # Left to the SDK, the client would ask the API which workspace the
        # token is for, with a request that blocks every other caller.
        with a_fake_api() as api, as_caller():
            client = run(a_client())

        assert client.workspace_id == WORKSPACE
        assert api.requests == []

    def test_a_workspace_the_token_is_not_for_is_refused_by_name(self) -> None:
        with as_caller(workspace_id=7), pytest.raises(ToolError, match="workspace 7, not 8"):
            run(a_client(workspace_id=8))

    def test_a_call_made_before_a_workspace_is_known_gets_a_client(self) -> None:
        with as_caller():
            client = run(a_client(workspace_id=None))

        assert client.workspace_id == WORKSPACE

    def test_the_client_carries_the_project_the_tool_call_is_in(self) -> None:
        with as_caller():
            client = run(a_client(project_id=11))

        assert client.project_id == 11

    def test_a_tool_call_with_no_caller_is_refused(self) -> None:
        # A tool that ran without a caller would act as nobody, which is the
        # one thing this server must never let happen.
        with pytest.raises(RuntimeError, match="no authenticated MCP caller"):
            run(a_client())

    def test_the_client_closes_its_connections_when_the_tool_call_ends(self) -> None:
        with as_caller():
            client = run(a_client())

        assert client.session.is_closed
        assert client.download_session.is_closed

    def test_the_client_asks_a_running_job_as_often_as_a_tool_does(self) -> None:
        with as_caller():
            client = run(a_client())

        assert client.job_poll_seconds == JOB_POLL_SECONDS

    def test_the_client_calls_the_api_this_process_was_told_to(self) -> None:
        with a_fake_api(), as_caller():
            client = run(a_client())

        assert client.base_url == API_URL


class TestWhatAModelIsToldWhenTheApiRefuses:
    def test_the_apis_own_words_become_the_tool_error(self) -> None:
        async def refused() -> None:
            raise MammothAPIError("Dataset name already exists")

        with pytest.raises(ToolError, match="Dataset name already exists") as error:
            run(read_sdk_errors(refused()))

        assert str(error.value).startswith(API_ERROR_PREFIX)

    def test_a_refusal_with_no_words_still_says_something(self) -> None:
        async def refused() -> None:
            raise MammothAPIError("   ")

        with pytest.raises(ToolError, match=UNREADABLE_API_ERROR):
            run(read_sdk_errors(refused()))


class TestARouteTheSdkHasNoMethodFor:
    @staticmethod
    async def ask(method: str, path: str, **sent: object) -> dict:
        async with build_client(WORKSPACE) as client:
            return await request_api(client, method, path, **sent)

    def test_the_call_goes_out_as_the_caller_and_its_payload_comes_back(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", "/workspaces", {"workspaces": [{"id": WORKSPACE}]})
            payload = run(self.ask("GET", "/workspaces", query={"limit": 5}))

        [request] = api.sent("GET", "/workspaces")
        assert payload == {"workspaces": [{"id": WORKSPACE}]}
        assert request.headers["authorization"] == f"Bearer {TOKEN}"
        assert request.url.params["limit"] == "5"

    def test_a_file_goes_under_the_field_the_upload_route_reads(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", "/files", {"id": 4})
            run(self.ask("POST", "/files", upload=[("a.csv", b"x,y\n1,2\n", "text/csv")]))

        [request] = api.sent("POST", "/files")
        assert f'name="{UPLOAD_FIELD}"; filename="a.csv"'.encode() in request.content

    def test_a_refusal_reaches_the_model_in_the_apis_words(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", "/workspaces", {"message": "No such workspace"}, status=404)
            with pytest.raises(ToolError, match="No such workspace"):
                run(self.ask("GET", "/workspaces"))
