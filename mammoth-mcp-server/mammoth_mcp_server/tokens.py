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
from mcp.server.auth.provider import AccessToken

from . import sdk
from .consts import TOKEN_CLIENT, TokenClaims


class MammothTokenVerifier:
    """The MCP SDK's `TokenVerifier`, answered by Mammoth."""

    async def verify_token(self, token: str) -> AccessToken | None:
        """Say who a bearer token stands for, or None when Mammoth refuses it.

        The answer carries the resource Mammoth issued the token for, as it
        said it. The bearer check then turns away a token whose resource is
        not this server, and a token with none.

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
            scopes=[],
            resource=issued.resource,
            claims={TokenClaims.WORKSPACE_ID: issued.id},
        )


token_verifier = MammothTokenVerifier()
