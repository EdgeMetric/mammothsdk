"""A connection the user limited to reading.

A user who wants an assistant to look at their data but never change it picks
read-only when they connect. Mammoth puts that on the token as a scope, and
this server turns away every tool that would write — by what the tool itself
says it does, so a new tool is covered the day it is added rather than when
somebody remembers to add it to a list.
"""

import pytest
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.config import MCP_RESOURCE_URL
from mammoth_mcp_server.read_only import READ_SCOPE, ReadOnly, may_run
from mammoth_mcp_server.server import mcp_server, register_tools

from .helpers import run


def as_a_caller_who(*scopes: str):
    """A caller whose token carries exactly these scopes."""
    access = AccessToken(
        token="mm_test",
        client_id="a-client",
        scopes=list(scopes),
        resource=MCP_RESOURCE_URL,
        claims={},
    )
    return auth_context_var.set(AuthenticatedUser(access))


def a_context(tool: str) -> object:
    class Ctx:
        method = "tools/call"
        params = {"name": tool}
        session = None

    return Ctx()


async def answers(_ctx: object) -> str:
    return "done"


class TestWhichToolsAReadOnlyConnectionMayRun:
    def setup_method(self) -> None:
        register_tools()

    def teardown_method(self) -> None:
        auth_context_var.set(None)

    def test_a_read_only_connection_may_read(self) -> None:
        as_a_caller_who(READ_SCOPE)

        assert may_run("get_data") is True

    def test_a_read_only_connection_may_not_write(self) -> None:
        as_a_caller_who(READ_SCOPE)

        assert may_run("delete_views") is False

    def test_a_read_only_connection_may_not_run_a_tool_that_changes_things(self) -> None:
        as_a_caller_who(READ_SCOPE)

        assert may_run("add_transformations") is False

    def test_a_full_connection_may_write(self) -> None:
        """No read scope means the connection was never limited, which is every
        token Mammoth issues today."""
        as_a_caller_who()

        assert may_run("delete_views") is True

    def test_every_tool_is_judged_by_its_own_annotation(self) -> None:
        """The point of reading the annotation: no list to keep in step."""
        as_a_caller_who(READ_SCOPE)

        for tool in run(mcp_server.list_tools()):
            reads = bool(tool.annotations and tool.annotations.read_only_hint)
            assert may_run(tool.name) is reads, tool.name

    def test_a_tool_nobody_has_heard_of_is_refused_rather_than_allowed(self) -> None:
        """An unknown name must not be a way past the limit."""
        as_a_caller_who(READ_SCOPE)

        assert may_run("no_such_tool") is False


class TestTheRefusal:
    def setup_method(self) -> None:
        register_tools()

    def teardown_method(self) -> None:
        auth_context_var.set(None)

    async def test_a_write_is_refused_before_it_reaches_mammoth(self) -> None:
        as_a_caller_who(READ_SCOPE)

        with pytest.raises(ToolError) as refused:
            await ReadOnly()(a_context("delete_views"), answers)

        assert "read-only" in str(refused.value).lower()

    async def test_the_refusal_names_the_tool_that_was_refused(self) -> None:
        as_a_caller_who(READ_SCOPE)

        with pytest.raises(ToolError) as refused:
            await ReadOnly()(a_context("delete_views"), answers)

        assert "delete_views" in str(refused.value)

    async def test_a_read_goes_through_untouched(self) -> None:
        as_a_caller_who(READ_SCOPE)

        assert await ReadOnly()(a_context("get_data"), answers) == "done"

    async def test_a_full_connection_is_not_slowed_down_by_the_check(self) -> None:
        as_a_caller_who()

        assert await ReadOnly()(a_context("delete_views"), answers) == "done"


class TestTheServerEnforcesIt:
    def test_the_running_server_has_the_limit_on_it(self) -> None:
        """A check that is written but never registered stops nothing."""
        assert any(isinstance(one, ReadOnly) for one in mcp_server.middleware)
