"""What a client or a registry learns about the server before it signs in."""

import json
import re
import tomllib
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mammoth_mcp_server import __version__
from mammoth_mcp_server.app import create_app
from mammoth_mcp_server.config import MCP_RESOURCE_URL, SERVER_URL
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


# The Server Card schema of SEP-2127, ported from `schema.ts` at
# modelcontextprotocol/experimental-ext-server-card commit
# 92999cb3f5d82e648385cb92ce41ed9aa1386eda: required fields, their types and
# the length and pattern limits the schema states.
CARD_SCHEMA_URL = "https://static.modelcontextprotocol.io/schemas/v1/server-card.schema.json"
NAME_PATTERN = re.compile(r"^[a-zA-Z0-9.-]+/[a-zA-Z0-9._-]+$")
REMOTE_URL_PATTERN = re.compile(r"^(https?://[^\s]+|\{[a-zA-Z_][a-zA-Z0-9_]*\}[^\s]*)$")


def schema_problems(card: dict) -> list[str]:
    """What a SEP-2127 validator would reject in this card."""
    problems = []
    if card.get("$schema") != CARD_SCHEMA_URL:
        problems.append("$schema")
    if not isinstance(card.get("name"), str) or not (
        3 <= len(card["name"]) <= 200 and NAME_PATTERN.match(card["name"])
    ):
        problems.append("name")
    if not isinstance(card.get("version"), str) or len(card["version"]) > 255:
        problems.append("version")
    if not isinstance(card.get("description"), str) or not 1 <= len(card["description"]) <= 100:
        problems.append("description")
    if "title" in card and not (isinstance(card["title"], str) and 1 <= len(card["title"]) <= 100):
        problems.append("title")
    for remote in card.get("remotes", []):
        if remote.get("type") not in ("streamable-http", "sse"):
            problems.append("remotes.type")
        if not (isinstance(remote.get("url"), str) and REMOTE_URL_PATTERN.match(remote["url"])):
            problems.append("remotes.url")
    return problems


class TestTheServerCard:
    @pytest.fixture
    def server(self):
        with a_fake_store(), TestClient(create_app(), base_url=SERVER_URL) as client:
            yield client

    @pytest.mark.parametrize("path", ["/.well-known/mcp/server-card.json", "/mcp/server-card"])
    def test_the_card_is_served_without_a_token_and_fits_the_schema(
        self, server: TestClient, path: str
    ) -> None:
        card = server.get(path)

        assert card.status_code == 200
        assert card.headers["content-type"].startswith("application/mcp-server-card+json")
        body = card.json()
        assert schema_problems(body) == []
        assert body["remotes"][0]["url"] == MCP_RESOURCE_URL

    def test_the_card_names_and_describes_the_server_as_server_json_does(
        self, server: TestClient
    ) -> None:
        entry = json.loads((PACKAGE / "server.json").read_text())
        body = server.get("/mcp/server-card").json()

        assert (body["name"], body["description"], body["version"]) == (
            entry["name"],
            entry["description"],
            entry["version"],
        )

    def test_the_two_paths_serve_the_same_card(self, server: TestClient) -> None:
        assert (
            server.get("/mcp/server-card").content
            == server.get("/.well-known/mcp/server-card.json").content
        )

    def test_a_browser_may_read_cache_and_revalidate_the_card(self, server: TestClient) -> None:
        card = server.get("/mcp/server-card")

        assert card.headers["access-control-allow-origin"] == "*"
        assert card.headers["access-control-allow-methods"] == "GET"
        assert card.headers["access-control-allow-headers"] == "Content-Type, If-None-Match"
        assert card.headers["access-control-expose-headers"] == "ETag"
        assert card.headers["cache-control"] == "public, max-age=3600"

        again = server.get("/mcp/server-card", headers={"If-None-Match": card.headers["etag"]})
        assert again.status_code == 304
        assert again.content == b""


class TestWhoMammothSeesCalling:
    def test_a_tool_call_says_it_comes_from_the_mcp_server(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", f"/workspaces/{WORKSPACE}/projects", {"projects": []})
            call_tool("list_projects", workspace_id=WORKSPACE)

        [sent] = api.sent("GET", f"/workspaces/{WORKSPACE}/projects")
        assert sent.headers["user-agent"] == USER_AGENT == f"mammoth-mcp-server/{__version__}"
