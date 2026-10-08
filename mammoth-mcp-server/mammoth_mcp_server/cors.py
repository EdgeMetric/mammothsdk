"""CORS for the MCP endpoint, so a browser-based MCP client can reach it.

A browser sends a preflight (`OPTIONS`) before it sends a bearer token, and the
preflight carries no token. The auth check in front of `/mcp` would answer it
with 401, which blocks the client before it can sign in. This answers the
preflight first, and lets the client read the headers sign-in depends on.
"""

from starlette.datastructures import MutableHeaders
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .config import MCP_PATH

# Any origin may call: the request carries a bearer token and no cookie.
ALLOW_ORIGIN = "*"
ALLOW_METHODS = "GET, POST, DELETE, OPTIONS"
ALLOW_HEADERS = (
    "Authorization, Content-Type, Accept, Mcp-Session-Id, Mcp-Protocol-Version, Last-Event-ID"
)
# A client reads WWW-Authenticate to find where to sign in, and Mcp-Session-Id to keep a session.
EXPOSE_HEADERS = "WWW-Authenticate, Mcp-Session-Id"
PREFLIGHT_MAX_AGE_S = "600"


class McpCors:
    """ASGI middleware: CORS on `MCP_PATH` only; every other path is left as it was."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] != MCP_PATH:
            await self.app(scope, receive, send)
            return
        if scope["method"] == "OPTIONS":
            preflight = Response(
                status_code=204,
                headers={
                    "Access-Control-Allow-Origin": ALLOW_ORIGIN,
                    "Access-Control-Allow-Methods": ALLOW_METHODS,
                    "Access-Control-Allow-Headers": ALLOW_HEADERS,
                    "Access-Control-Expose-Headers": EXPOSE_HEADERS,
                    "Access-Control-Max-Age": PREFLIGHT_MAX_AGE_S,
                },
            )
            await preflight(scope, receive, send)
            return

        async def send_with_cors(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Access-Control-Allow-Origin"] = ALLOW_ORIGIN
                headers["Access-Control-Expose-Headers"] = EXPOSE_HEADERS
            await send(message)

        await self.app(scope, receive, send_with_cors)
