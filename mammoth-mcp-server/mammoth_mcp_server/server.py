"""The MCP server object every tool registers itself on, and who may call it.

The MCP SDK builds the whole HTTP side from what is given here: the MCP
endpoint, the metadata that names where to sign in, and the check that turns a
caller without a token away with a pointer to that metadata. This server is a
resource server alone: it has no sign-in of its own.
"""

from mcp.server import MCPServer
from mcp.server.auth.settings import AuthSettings

from .config import MCP_OAUTH_URL, MCP_RESOURCE_URL, MCP_UPLOAD_PATH
from .consts import MCP_INSTRUCTIONS, MCP_SERVER_NAME
from .read_only import ReadOnly
from .telemetry import Telemetry
from .tokens import token_verifier
from .upload_app import upload_app
from .upload_routes import upload

mcp_server = MCPServer(
    MCP_SERVER_NAME,
    instructions=MCP_INSTRUCTIONS,
    extensions=[upload_app],
    # One JSON line per call, so the launch can be measured. It records which
    # tool ran and never what it ran on.
    # The limit runs before the record, so a refused write is recorded as one.
    middleware=[Telemetry(), ReadOnly()],
    token_verifier=token_verifier,
    # The two URLs are validated from their text, which keeps a URL as it was
    # written. A client compares an issuer letter for letter.
    auth=AuthSettings.model_validate(
        {
            "issuer_url": MCP_OAUTH_URL,
            "resource_server_url": MCP_RESOURCE_URL,
            "required_scopes": [],
            # A token is taken only when Mammoth issued it for this server, so
            # one issued for another resource, or for none, is turned away.
            "validate_token_resource": True,
        }
    ),
)
# The page a browser opens with no token of its own, guarded by its single-use
# ticket.
mcp_server.custom_route(MCP_UPLOAD_PATH, methods=["GET", "POST"])(upload)


def register_tools() -> None:
    """Import every tool module, which registers its tools on `mcp_server`.

    Imported here rather than at module scope: a tool module imports
    `mcp_server` from this module, so the server must exist first.
    """
    from . import tools  # noqa: F401
