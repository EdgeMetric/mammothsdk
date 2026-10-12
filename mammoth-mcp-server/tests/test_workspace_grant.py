"""The one workspace a connection belongs to.

A token is issued for a single workspace: Mammoth refuses it on every other
one. `list_workspaces` asked for the whole account anyway, so a connection
fenced to one workspace was told the names of all the rest — the names of a
customer's other workspaces, read by whoever holds a staff or agency grant.
These tests hold the tool to the grant.
"""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.consts import ListFields
from mammoth_mcp_server.sdk import own_workspace
from mammoth_mcp_server.tools.discovery import list_workspaces

from .helpers import WORKSPACE, a_fake_api, as_caller, run

OTHER = WORKSPACE + 1
WORKSPACES_PATH = "/workspaces"
WORKSPACE_PATH = f"/workspaces/{WORKSPACE}"


def a_workspace(workspace_id: int) -> dict[str, object]:
    return {ListFields.ID: workspace_id, ListFields.NAME: f"workspace {workspace_id}"}


class TestTheCallersOwnWorkspace:
    def test_a_caller_knows_the_workspace_their_token_belongs_to(self) -> None:
        with as_caller():
            assert own_workspace() == WORKSPACE

    def test_a_tool_call_without_a_caller_is_a_bug_not_an_answer(self) -> None:
        with pytest.raises(RuntimeError):
            own_workspace()


class TestListingWorkspaces:
    def test_the_caller_is_shown_the_workspace_their_token_belongs_to(self) -> None:
        with a_fake_api() as api:
            api.answer("GET", WORKSPACE_PATH, a_workspace(WORKSPACE))
            with as_caller():
                found = run(list_workspaces())
        assert found[ListFields.WORKSPACES] == [a_workspace(WORKSPACE)]

    def test_another_workspaces_name_is_never_answered(self) -> None:
        """The defect this guards: the tool listed the whole account, so a
        connection fenced to one workspace read the names of all the others."""
        with a_fake_api() as api:
            api.answer(
                "GET",
                WORKSPACES_PATH,
                {ListFields.WORKSPACES: [a_workspace(WORKSPACE), a_workspace(OTHER)]},
            )
            api.answer("GET", WORKSPACE_PATH, a_workspace(WORKSPACE))
            with as_caller():
                found = run(list_workspaces())
        assert found[ListFields.WORKSPACES] == [a_workspace(WORKSPACE)]
        assert f"workspace {OTHER}" not in str(found)

    def test_it_asks_for_the_grants_workspace_by_id(self) -> None:
        """Asked for by id, not filtered out of a page: the account's other
        workspaces are never sent to this server at all."""
        with a_fake_api() as api:
            api.answer("GET", WORKSPACE_PATH, a_workspace(WORKSPACE))
            with as_caller():
                run(list_workspaces())
        assert api.sent("GET", WORKSPACE_PATH)
        assert not api.sent("GET", WORKSPACES_PATH)

    def test_a_workspace_mammoth_will_not_answer_for_is_reported_not_swallowed(self) -> None:
        with a_fake_api() as api:
            api.answer("GET", WORKSPACE_PATH, {"message": "gone"}, status=404)
            with as_caller(), pytest.raises(ToolError):
                run(list_workspaces())
