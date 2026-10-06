"""The MCP server as a process of its own: the ASGI app, and how to run it."""

import uvicorn
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette

from .config import HOST, MCP_PATH, PORT
from .server import mcp_server, register_tools


def create_app() -> Starlette:
    """Build the app a server runs: every tool, behind the token check.

    Stateless JSON mode: any worker can serve any request, and no response is
    a stream. So the server scales by adding workers, with nothing shared
    between them but the store.
    """
    register_tools()
    return mcp_server.streamable_http_app(
        streamable_http_path=MCP_PATH,
        stateless_http=True,
        json_response=True,
        # DNS-rebinding protection is for servers on localhost. Here a browser on
        # another origin cannot send the bearer token: CORS preflight stops it.
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )


def main() -> None:
    """Run the server on the host and port the environment names."""
    uvicorn.run(create_app(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()
