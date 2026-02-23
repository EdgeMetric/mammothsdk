"""E2E tests for MCP tool calls via the remote server.

Requires a running MCP server, valid Mammoth credentials, and a known view ID.
Set env vars: MCP_SERVER_URL, MAMMOTH_API_KEY, MAMMOTH_API_SECRET, MAMMOTH_WORKSPACE_ID
Optional: MAMMOTH_TEST_VIEW_ID (default: 276668)
"""

from __future__ import annotations

import httpx

from tests.conftest import mcp_tool_call


class TestMCPSession:
    """Test MCP session initialization."""

    def test_session_established(self, mcp_session: dict):
        assert mcp_session["session_id"]
        assert mcp_session["msg_counter"] >= 2


class TestConnectionTools:
    """Test connection and discovery tools."""

    def test_list_projects(
        self, http_client: httpx.Client, server_url: str, oauth_token: str, mcp_session: dict
    ):
        data = mcp_tool_call(http_client, server_url, oauth_token, mcp_session, "list_projects", {})
        assert data["success"] is True
        assert "data" in data
        projects = data["data"]
        assert isinstance(projects, list)
        assert len(projects) > 0
        assert "id" in projects[0]
        assert "name" in projects[0]


class TestViewTools:
    """Test view-related tools (auto-discovery, data fetch)."""

    def test_get_view_auto_discovers_project(
        self,
        http_client: httpx.Client,
        server_url: str,
        oauth_token: str,
        mcp_session: dict,
        test_view_id: int,
    ):
        data = mcp_tool_call(
            http_client, server_url, oauth_token, mcp_session, "get_view", {"view_id": test_view_id}
        )
        assert data["success"] is True, f"get_view failed: {data.get('error')}"
        view = data["data"]
        assert view["id"] == test_view_id
        assert "name" in view
        assert "dataset_id" in view
        assert "columns" in view
        assert len(view["columns"]) > 0

    def test_get_data(
        self,
        http_client: httpx.Client,
        server_url: str,
        oauth_token: str,
        mcp_session: dict,
        test_view_id: int,
    ):
        data = mcp_tool_call(
            http_client,
            server_url,
            oauth_token,
            mcp_session,
            "get_data",
            {"view_id": test_view_id, "limit": 5},
        )
        assert data["success"] is True, f"get_data failed: {data.get('error')}"
        assert "data" in data

    def test_get_view_nonexistent_returns_error(
        self,
        http_client: httpx.Client,
        server_url: str,
        oauth_token: str,
        mcp_session: dict,
    ):
        data = mcp_tool_call(
            http_client, server_url, oauth_token, mcp_session, "get_view", {"view_id": 999999999}
        )
        assert data["success"] is False


class TestDiscoveryTools:
    """Test dataset and view listing tools."""

    def test_list_datasets(
        self,
        http_client: httpx.Client,
        server_url: str,
        oauth_token: str,
        mcp_session: dict,
        test_view_id: int,
    ):
        # First call get_view to set the project via auto-discovery
        mcp_tool_call(
            http_client, server_url, oauth_token, mcp_session, "get_view", {"view_id": test_view_id}
        )
        data = mcp_tool_call(http_client, server_url, oauth_token, mcp_session, "list_datasets", {})
        assert data["success"] is True, f"list_datasets failed: {data.get('error')}"

    def test_get_help(
        self,
        http_client: httpx.Client,
        server_url: str,
        oauth_token: str,
        mcp_session: dict,
    ):
        data = mcp_tool_call(
            http_client,
            server_url,
            oauth_token,
            mcp_session,
            "get_help",
            {"topic": "transformations"},
            expect_json=False,
        )
        # get_help returns plain markdown text, not JSON
        assert isinstance(data, str)
        assert len(data) > 100


class TestPipelineTools:
    """Test pipeline listing tools."""

    def test_list_tasks(
        self,
        http_client: httpx.Client,
        server_url: str,
        oauth_token: str,
        mcp_session: dict,
        test_view_id: int,
    ):
        data = mcp_tool_call(
            http_client,
            server_url,
            oauth_token,
            mcp_session,
            "list_tasks",
            {"view_id": test_view_id},
        )
        assert data["success"] is True, f"list_tasks failed: {data.get('error')}"
