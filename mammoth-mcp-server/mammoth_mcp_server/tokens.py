"""Who a bearer token stands for: the one check a caller passes to reach a tool.

This server signs nobody in. Mammoth's own authorization server does, and it
issues a token for one server at a time (RFC 8707): the client names this
server's URI when it asks, and Mammoth keeps that URI with the token. So a
token is good here only when Mammoth says two things of it: that it is live,
and that it was issued for this server. A Mammoth API token made by hand is
live and was issued for no server, so it opens nothing here.

Mammoth is asked on every request, and nothing is kept: a token the user
revoked, or one that ran out, stops working here with the same request.
"""

from mammoth.exceptions import MammothAuthError
from mammoth.models.workspaces import CurrentWorkspace
from mcp.server.auth.provider import AccessToken

from . import sdk
from .consts import TOKEN_CLIENT, TokenClaims
from .read_only import READ_SCOPE


class MammothTokenVerifier:
    """The MCP SDK's `TokenVerifier`, answered by Mammoth."""

    async def verify_token(self, token: str) -> AccessToken | None:
        """Say who a bearer token stands for, or None when Mammoth refuses it.

        The answer carries the resource Mammoth issued the token for, as it
        said it. The bearer check then turns away a token whose resource is
        not this server, and a token with none. It carries the projects the
        user picked when they connected too, so a tool can act in them rather
        than ask, and name them when the model reaches for another. A connection
        the user granted read-only carries the `read` scope, and only the tools
        that read run for it.

        Raises:
            MammothError: If Mammoth cannot be reached. The caller is then told
                the server failed, not to sign in again.
        """
        try:
            async with sdk.client_with(token) as client:
                issued = await client.workspaces.current()
        except MammothAuthError:
            return None
        return AccessToken(
            token=token,
            client_id=TOKEN_CLIENT,
            scopes=[READ_SCOPE] if issued.read_only else [],
            resource=issued.resource,
            claims={
                TokenClaims.WORKSPACE_ID: issued.id,
                TokenClaims.PROJECT_IDS: pinned_projects(issued),
            },
        )


def pinned_projects(issued: CurrentWorkspace) -> list[int] | None:
    """The projects a token is pinned to, or None for every project.

    A Mammoth older than multi-project sign-in names one project alone, as
    `project`; that one project is then the whole list.
    """
    if issued.projects:
        return sorted(issued.projects)
    return [issued.project] if issued.project is not None else None


token_verifier = MammothTokenVerifier()
