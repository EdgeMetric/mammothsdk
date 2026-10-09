"""The server card: what a client or a crawler learns about this server before it connects.

Shaped by the Server Card schema of SEP-2127 (`schema.ts` in
modelcontextprotocol/experimental-ext-server-card). Served with no token at
`/.well-known/mcp/server-card.json` and at `<streamable-http-url>/server-card`,
the location the SEP reserves. Every value comes from where the server already
has it: the name and description from `consts` (a test holds `server.json` to
them), the version from the package, the endpoint from the deployment's settings.
"""

import hashlib
import json

from mcp.types import LATEST_PROTOCOL_VERSION
from starlette.requests import Request
from starlette.responses import Response

from . import __version__
from .config import MCP_OAUTH_URL, MCP_PATH, MCP_RESOURCE_URL
from .consts import MCP_SERVER_NAME, REGISTRY_DESCRIPTION, REGISTRY_NAME

SERVER_CARD_PATH = "/.well-known/mcp/server-card.json"
SERVER_CARD_MCP_PATH = f"{MCP_PATH}/server-card"
SERVER_CARD_SCHEMA = "https://static.modelcontextprotocol.io/schemas/v1/server-card.schema.json"
CARD_MEDIA_TYPE = "application/mcp-server-card+json"
# The card is public and read by browsers as well as crawlers: the headers
# docs/discovery.md of the extension asks for.
CARD_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type, If-None-Match",
    "Access-Control-Expose-Headers": "ETag",
    "Cache-Control": "public, max-age=3600",
}


def server_card() -> dict[str, object]:
    """The card, as this deployment would hand it out."""
    return {
        "$schema": SERVER_CARD_SCHEMA,
        "name": REGISTRY_NAME,
        "version": __version__,
        "description": REGISTRY_DESCRIPTION,
        "title": MCP_SERVER_NAME,
        "websiteUrl": "https://mammoth.io",
        "remotes": [
            {
                "type": "streamable-http",
                "url": MCP_RESOURCE_URL,
                "supportedProtocolVersions": [LATEST_PROTOCOL_VERSION],
            }
        ],
        "_meta": {"io.mammoth/authorization-issuer": MCP_OAUTH_URL},
    }


async def serve_server_card(request: Request) -> Response:
    """Answer the card to anyone who asks, or 304 to one that already holds it."""
    if request.method == "OPTIONS":
        return Response(status_code=204, headers=CARD_HEADERS)
    body = json.dumps(server_card())
    etag = f'"{hashlib.sha256(body.encode()).hexdigest()[:32]}"'
    headers = {**CARD_HEADERS, "ETag": etag}
    if etag in request.headers.get("if-none-match", ""):
        return Response(status_code=304, headers=headers)
    return Response(body, media_type=CARD_MEDIA_TYPE, headers=headers)
