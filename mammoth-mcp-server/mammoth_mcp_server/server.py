"""The MCP server object every tool registers itself on, and who may call it.

The MCP SDK builds the whole HTTP side from what is given here: the MCP
endpoint, the OAuth endpoints and their metadata, and the check that turns a
caller without a token away with a pointer to where to sign in.
"""

from mcp.server import MCPServer
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions

from .config import (
    KEYCLOAK_CALLBACK_PATH,
    KEYCLOAK_LOGIN_PATH,
    MCP_LOGIN_PATH,
    MCP_OAUTH_URL,
    MCP_RESOURCE_URL,
    MCP_UPLOAD_PATH,
)
from .consts import MCP_INSTRUCTIONS, MCP_SERVER_NAME
from .login import back_from_mammoth, login, login_with_mammoth
from .oauth import oauth_provider
from .upload_app import upload_app
from .upload_routes import upload

mcp_server = MCPServer(
    MCP_SERVER_NAME,
    instructions=MCP_INSTRUCTIONS,
    extensions=[upload_app],
    auth_server_provider=oauth_provider,
    # The two URLs are validated from their text, which keeps a URL with no
    # path as it was written. A client compares an issuer letter for letter.
    auth=AuthSettings.model_validate(
        {
            "issuer_url": MCP_OAUTH_URL,
            "resource_server_url": MCP_RESOURCE_URL,
            # A client names itself and is given an id: Claude web and ChatGPT
            # register themselves, and no one registers them by hand. Revoking
            # is how a client signs the user out again.
            "client_registration_options": ClientRegistrationOptions(enabled=True),
            "revocation_options": RevocationOptions(enabled=True),
            "required_scopes": [],
            # Every token this server admits says it is for this server, so one
            # issued for another resource is turned away.
            "validate_token_resource": True,
        }
    ),
)
# Pages a browser opens with no token of its own: the sign-in pages, which are
# where a token is got, and the upload page, guarded by its single-use ticket.
mcp_server.custom_route(MCP_LOGIN_PATH, methods=["GET", "POST"])(login)
mcp_server.custom_route(KEYCLOAK_LOGIN_PATH, methods=["GET"])(login_with_mammoth)
mcp_server.custom_route(KEYCLOAK_CALLBACK_PATH, methods=["GET"])(back_from_mammoth)
mcp_server.custom_route(MCP_UPLOAD_PATH, methods=["GET", "POST"])(upload)


def register_tools() -> None:
    """Import every tool module, which registers its tools on `mcp_server`.

    Imported here rather than at module scope: a tool module imports
    `mcp_server` from this module, so the server must exist first.
    """
    from . import tools  # noqa: F401
