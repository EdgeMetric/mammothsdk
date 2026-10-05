"""The authorization server that signs a user in with a Mammoth API token.

Claude web and ChatGPT offer a connector one way to sign in: OAuth. So this
server runs a small authorization server of its own: the client registers
itself, we show a login page that asks for the user's Mammoth API token
(`mm_...`), and the client trades the code it gets back for a token of ours.

Every later tool call carries our token alone, and the Mammoth API accepts only
the user's own. So our token has to lead back to theirs: Redis holds it sealed
(`store.seal`), no worker keeps it in memory, and the record expires after
`TOKEN_SECONDS`.

A client that can send a header of its own needs none of this: it sends the
user's API token as the bearer, and `load_access_token` reads that too.
"""

import asyncio
import secrets
import time

from mammoth.client import MammothClient
from mammoth.exceptions import MammothError
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    IdentityAssertionParams,
    RefreshToken,
    TokenError,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import AnyUrl

from . import sdk
from .config import MCP_LOGIN_URL, MCP_RESOURCE_URL
from .consts import (
    API_TOKEN_PREFIX,
    CODE_SECONDS,
    LOGIN_SECONDS,
    ROUTE_TIMEOUT_SECONDS,
    TOKEN_SECONDS,
    OAuthFields,
    TokenClaims,
)
from .store import forget, recall, remember, seal, unseal


class LoginRefused(Exception):
    """The login page could not be completed. The message is shown to the user."""


async def read_token_workspace(api_token: str) -> int:
    """Ask Mammoth which workspace an API token is for, which also proves it is good.

    The SDK makes this request without `await`, so it runs in a thread: on the
    event loop, every caller this worker serves would wait for it. The SDK
    keeps the answer for the life of the process.

    Raises:
        MammothError: If Mammoth refuses the token, or cannot be reached.
    """
    client = MammothClient(
        api_token=api_token,
        base_url=sdk.api_url(),
        api_root=sdk.api_root(),
        allow_insecure_loopback_http=True,
        timeout=ROUTE_TIMEOUT_SECONDS,
    )
    async with client:
        return await asyncio.to_thread(lambda: client.workspace_id)


class TokenOAuthProvider:
    """The OAuth authorization server the MCP SDK drives.

    It implements the SDK's `OAuthAuthorizationServerProvider` protocol. There
    are no refresh tokens: an access token lives for 30 days, and the user signs
    in again afterwards.
    """

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        """Find a client that registered itself earlier."""
        registered = await recall(OAuthFields.CLIENT, client_id)
        return OAuthClientInformationFull(**registered) if registered else None

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        """Give a client its own id and remember what it told us.

        The id a client asks for is ignored: it names itself, so two clients
        could otherwise claim the same id and read each other's codes.
        """
        client_info.client_id = f"mammoth-{secrets.token_hex(16)}"
        client_info.client_id_issued_at = int(time.time())
        await remember(
            OAuthFields.CLIENT,
            client_info.client_id,
            client_info.model_dump(mode="json"),
            TOKEN_SECONDS,
        )

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Send the user to the login page, holding on to what the client asked for."""
        state = secrets.token_urlsafe(32)
        await remember(
            OAuthFields.LOGIN,
            state,
            {
                OAuthFields.CLIENT_ID: client.client_id,
                OAuthFields.REDIRECT_URI: str(params.redirect_uri),
                OAuthFields.EXPLICIT_REDIRECT: params.redirect_uri_provided_explicitly,
                OAuthFields.CODE_CHALLENGE: params.code_challenge,
                OAuthFields.SCOPES: params.scopes or [],
                OAuthFields.RESOURCE: params.resource,
                OAuthFields.CLIENT_STATE: params.state,
            },
            LOGIN_SECONDS,
        )
        return f"{MCP_LOGIN_URL}?{OAuthFields.STATE}={state}"

    async def accept_login(self, state: str, api_token: str) -> str:
        """Check the token and send the user back to the client with a code.

        Args:
            state: What the login page was opened with.
            api_token: The Mammoth API token the user pasted.

        Returns:
            The client's own redirect URI, carrying the code and the client's state.

        Raises:
            LoginRefused: If the sign-in has expired, or Mammoth does not take
                the token.
        """
        asked = await recall(OAuthFields.LOGIN, state)
        if asked is None:
            raise LoginRefused("This sign-in has expired. Start again from your client.")
        try:
            workspace_id = await read_token_workspace(api_token)
        except MammothError as refused:
            raise LoginRefused(
                "Mammoth did not accept that API token. Copy it again from"
                " Workspace settings, API Tokens."
            ) from refused
        await forget(OAuthFields.LOGIN, state)
        code = secrets.token_urlsafe(32)
        await remember(
            OAuthFields.CODE,
            code,
            asked
            | {
                OAuthFields.EXPIRES_AT: time.time() + CODE_SECONDS,
                OAuthFields.CREDENTIALS: seal(
                    {OAuthFields.API_TOKEN: api_token, OAuthFields.WORKSPACE_ID: workspace_id}
                ),
            },
            CODE_SECONDS,
        )
        return construct_redirect_uri(
            asked[OAuthFields.REDIRECT_URI],
            code=code,
            state=asked[OAuthFields.CLIENT_STATE],
        )

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        """Find a code this client was given. The SDK then checks its PKCE challenge."""
        issued = await recall(OAuthFields.CODE, authorization_code)
        if issued is None or issued[OAuthFields.CLIENT_ID] != client.client_id:
            return None
        return AuthorizationCode(
            code=authorization_code,
            scopes=issued[OAuthFields.SCOPES],
            expires_at=issued[OAuthFields.EXPIRES_AT],
            client_id=issued[OAuthFields.CLIENT_ID],
            code_challenge=issued[OAuthFields.CODE_CHALLENGE],
            redirect_uri=AnyUrl(issued[OAuthFields.REDIRECT_URI]),
            redirect_uri_provided_explicitly=issued[OAuthFields.EXPLICIT_REDIRECT],
            resource=issued[OAuthFields.RESOURCE],
        )

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        """Turn a code into the token the client keeps.

        Raises:
            TokenError: If the code has expired or was already spent.
        """
        issued = await recall(OAuthFields.CODE, authorization_code.code)
        if issued is None:
            raise TokenError(
                error="invalid_grant",
                error_description="This code has expired or was already used.",
            )
        await forget(OAuthFields.CODE, authorization_code.code)
        token = secrets.token_urlsafe(48)
        await remember(
            OAuthFields.TOKEN,
            token,
            {
                OAuthFields.CLIENT_ID: issued[OAuthFields.CLIENT_ID],
                OAuthFields.SCOPES: issued[OAuthFields.SCOPES],
                OAuthFields.CREDENTIALS: issued[OAuthFields.CREDENTIALS],
            },
            TOKEN_SECONDS,
        )
        return OAuthToken(access_token=token, expires_in=TOKEN_SECONDS)

    async def load_access_token(self, token: str) -> AccessToken | None:
        """Say who a bearer token stands for, or None when it stands for nobody.

        Two kinds arrive: a token this server issued at its login page, and a
        Mammoth API token a client sends as it is. Ours never starts with the
        API token's prefix, so neither can be mistaken for the other.
        """
        if token.startswith(API_TOKEN_PREFIX):
            return await self.load_api_token(token)
        issued = await recall(OAuthFields.TOKEN, token)
        if issued is None:
            return None
        return AccessToken(
            token=token,
            client_id=issued[OAuthFields.CLIENT_ID],
            scopes=issued[OAuthFields.SCOPES],
            # This server issues tokens for itself alone, so the resource is its
            # own URL — which is what the bearer middleware insists on.
            resource=MCP_RESOURCE_URL,
            claims=unseal(issued[OAuthFields.CREDENTIALS]),
        )

    async def load_api_token(self, api_token: str) -> AccessToken | None:
        """The caller a Mammoth API token stands for, if Mammoth takes the token."""
        try:
            workspace_id = await read_token_workspace(api_token)
        except MammothError:
            return None
        return AccessToken(
            token=api_token,
            client_id=API_TOKEN_PREFIX,
            scopes=[],
            # The token was presented to this server, so it is the resource the
            # bearer middleware insists the caller was admitted for.
            resource=MCP_RESOURCE_URL,
            claims={TokenClaims.API_TOKEN: api_token, TokenClaims.WORKSPACE_ID: workspace_id},
        )

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        """Drop a token, so the client has to sign in again."""
        await forget(OAuthFields.TOKEN, token.token)

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        """No refresh tokens are issued, so none can be loaded."""
        return None

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        """Never available: the client signs in again instead.

        Raises:
            TokenError: Always.
        """
        raise TokenError(
            error="unsupported_grant_type",
            error_description="This server issues no refresh tokens.",
        )

    async def exchange_identity_assertion(
        self, client: OAuthClientInformationFull, params: IdentityAssertionParams
    ) -> OAuthToken:
        """Never available: there is no enterprise identity provider behind this.

        Raises:
            TokenError: Always.
        """
        raise TokenError(
            error="unsupported_grant_type",
            error_description="This server accepts no identity assertions.",
        )


# The endpoints and the MCP endpoint drive the same provider: it keeps nothing of
# its own, so the two see one sign-in whichever worker serves them.
oauth_provider = TokenOAuthProvider()
