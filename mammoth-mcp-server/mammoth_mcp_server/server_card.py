"""The server card: what a client or a crawler learns about this server before it connects.

Served at `/.well-known/mcp/server-card.json` with no token. Every value comes
from where the server already has it: the version from the package (a test
holds it equal to `pyproject.toml` and `server.json`), the endpoint and the
issuer from the deployment's settings.
"""

from mcp.types import LATEST_PROTOCOL_VERSION
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from . import __version__
from .config import DOCS_URL, MCP_OAUTH_URL, MCP_PATH, MCP_RESOURCE_URL
from .consts import MCP_INSTRUCTIONS, MCP_SERVER_NAME

SERVER_CARD_PATH = "/.well-known/mcp/server-card.json"
# The card is public and read by browsers as well as crawlers.
CARD_HEADERS = {"Access-Control-Allow-Origin": "*"}


def server_card() -> dict[str, object]:
    """The card, as this deployment would hand it out."""
    return {
        "version": __version__,
        "protocolVersion": LATEST_PROTOCOL_VERSION,
        "serverInfo": {"name": MCP_SERVER_NAME, "version": __version__},
        "description": MCP_INSTRUCTIONS,
        "documentationUrl": DOCS_URL,
        "transport": {"type": "streamable-http", "endpoint": MCP_PATH},
        "authentication": {
            "required": True,
            "schemes": ["oauth2"],
            "issuer": MCP_OAUTH_URL,
            "resource": MCP_RESOURCE_URL,
        },
    }


async def serve_server_card(request: Request) -> Response:
    """Answer the card to anyone who asks."""
    return JSONResponse(server_card(), headers=CARD_HEADERS)
