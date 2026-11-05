"""The package uploaded to OpenAI's plugin portal keeps to its limits."""

import json
from pathlib import Path

from mammoth_mcp_server.config import MCP_RESOURCE_URL

PLUGIN = Path(__file__).parents[1] / "openai-plugin"
MAX_SHORT_FIELD = 30
MAX_LONG_DESCRIPTION = 4000
MAX_STARTER_PROMPTS = 3
MAX_STARTER_PROMPT = 128


def interface() -> dict[str, object]:
    manifest = json.loads((PLUGIN / "plugin.json").read_text())
    return manifest["extensions"]["com.openai"]["interface"]


def test_the_listing_fits_the_portals_limits() -> None:
    listing = interface()

    assert len(listing["displayName"]) <= MAX_SHORT_FIELD
    assert len(listing["shortDescription"]) <= MAX_SHORT_FIELD
    assert len(listing["longDescription"]) <= MAX_LONG_DESCRIPTION
    assert len(listing["defaultPrompt"]) <= MAX_STARTER_PROMPTS
    assert all(len(prompt) <= MAX_STARTER_PROMPT for prompt in listing["defaultPrompt"])


def test_the_images_the_listing_names_are_in_the_package() -> None:
    listing = interface()

    assert (PLUGIN / listing["logo"]).is_file()
    assert (PLUGIN / listing["composerIcon"]).is_file()


def test_the_package_points_at_this_server() -> None:
    servers = json.loads((PLUGIN / "mcp.json").read_text())["mcpServers"]

    assert [server["url"] for server in servers.values()] == [MCP_RESOURCE_URL]
