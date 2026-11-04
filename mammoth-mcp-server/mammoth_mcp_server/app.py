"""The MCP server as a process of its own: the ASGI app, and how to run it."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.types import ASGIApp, Receive, Scope, Send

from .config import HOST, MCP_PATH, PORT
from .cors import McpCors
from .sdk import close_http_client
from .server import mcp_server, register_tools
from .store import cipher
from .telemetry import write_events


class SlashedMcpPath:
    """ASGI middleware: `/mcp/` is the same endpoint as `/mcp`.

    Behind TLS termination the server sees `http`, so the redirect Starlette
    would send points at `http://`. A client that follows it either sends its
    token in the clear or loses it, so `/mcp/` is served, not redirected.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Hand the request on, with `/mcp/` rewritten to `/mcp`.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive channel.
            send: The ASGI send channel.
        """
        if scope["type"] == "http" and scope["path"] == f"{MCP_PATH}/":
            scope = {**scope, "path": MCP_PATH}
        await self.app(scope, receive, send)


def check_settings() -> None:
    """Fail now, with the reason, rather than at the first upload.

    A worker that dies at startup is restarted for ever by the process that
    runs it, so the deployment looks alive and serves nothing. Run this before
    the server starts, and the process stops with the reason instead.

    Raises:
        RuntimeError: If the deployment set no `MCP_ENCRYPTION_KEY`.
        ValueError: If it set one that is not a Fernet key.
    """
    cipher()


def create_app() -> Starlette:
    """Build the app a server runs: every tool, behind the token check.

    Stateless JSON mode: any worker can serve any request, and no response is
    a stream. So the server scales by adding workers, with nothing shared
    between them but the store.

    Raises:
        RuntimeError: If the deployment set no `MCP_ENCRYPTION_KEY`.
        ValueError: If it set one that is not a Fernet key.
    """
    check_settings()
    # Here, not in main(): a deployment runs `uvicorn ...:create_app --factory`.
    write_events()
    register_tools()
    app = mcp_server.streamable_http_app(
        streamable_http_path=MCP_PATH,
        stateless_http=True,
        json_response=True,
        # DNS-rebinding protection is for servers on localhost. Here a browser on
        # another origin cannot send the bearer token: CORS preflight stops it.
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
    app.router.redirect_slashes = False  # Every redirect it sends would point at `http://`.
    app.add_middleware(McpCors)
    app.add_middleware(SlashedMcpPath)  # Added last, so it runs first: `/mcp/` gets CORS too.
    mcp_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(scope: Starlette) -> AsyncIterator[None]:
        # The SDK's connection pool is opened by the first call and shared by all.
        try:
            async with mcp_lifespan(scope):
                yield
        finally:
            await close_http_client()

    app.router.lifespan_context = lifespan
    return app


def main() -> None:
    """Run the server on the host and port the environment names."""
    uvicorn.run(create_app(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()
