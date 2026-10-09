"""What a client or a registry learns about the server before it signs in."""

import json
import tomllib
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mammoth_mcp_server import __version__
from mammoth_mcp_server.app import create_app
from mammoth_mcp_server.config import MCP_OAUTH_URL, MCP_RESOURCE_URL, SERVER_URL
from mammoth_mcp_server.sdk import USER_AGENT

from .helpers import WORKSPACE, a_fake_api, a_fake_store, as_caller, call_tool

PACKAGE = Path(__file__).parent.parent


class TestTheRegistryEntry:
    def test_server_json_names_the_version_and_url_the_package_serves(self) -> None:
        entry = json.loads((PACKAGE / "server.json").read_text())
        project = tomllib.loads((PACKAGE / "pyproject.toml").read_text())["project"]

        assert entry["version"] == project["version"] == __version__
        assert [remote["url"] for remote in entry["remotes"]] == ["https://mcp.mammoth.io/mcp"]
        assert entry["name"] == "io.mammoth/mcp"
        # The registry refuses a description longer than this.
        assert len(entry["description"]) <= 100


class TestTheServerCard:
    @pytest.fixture
    def server(self):
        with a_fake_store(), TestClient(create_app(), base_url=SERVER_URL) as client:
            yield client

    def test_the_card_is_served_without_a_token(self, server: TestClient) -> None:
        card = server.get("/.well-known/mcp/server-card.json")

        assert card.status_code == 200
        body = card.json()
        assert body["serverInfo"]["version"] == __version__
        assert body["transport"] == {"type": "streamable-http", "endpoint": "/mcp"}
        assert body["authentication"]["issuer"] == MCP_OAUTH_URL
        assert body["authentication"]["resource"] == MCP_RESOURCE_URL
        assert body["documentationUrl"].startswith("https://")


class TestWhoMammothSeesCalling:
    def test_a_tool_call_says_it_comes_from_the_mcp_server(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", f"/workspaces/{WORKSPACE}/projects", {"projects": []})
            call_tool("list_projects", workspace_id=WORKSPACE)

        [sent] = api.sent("GET", f"/workspaces/{WORKSPACE}/projects")
        assert sent.headers["user-agent"] == USER_AGENT == f"mammoth-mcp-server/{__version__}"
