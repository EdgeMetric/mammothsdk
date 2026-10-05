"""The MCP server object every tool registers itself on."""

from mcp.server import MCPServer

from .consts import MCP_INSTRUCTIONS, MCP_SERVER_NAME
from .upload_app import upload_app

mcp_server = MCPServer(MCP_SERVER_NAME, instructions=MCP_INSTRUCTIONS, extensions=[upload_app])


def register_tools() -> None:
    """Import every tool module, which registers its tools on `mcp_server`.

    Imported here rather than at module scope: a tool module imports
    `mcp_server` from this module, so the server must exist first.
    """
    from . import tools  # noqa: F401
