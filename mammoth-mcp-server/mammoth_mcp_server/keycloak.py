"""Signing a user in with their Mammoth login, through Keycloak.

This server is a Keycloak client of its own. The login page sends the user to
Keycloak; Keycloak sends them back with a code; the code buys this server the
user's tokens. From then on every tool call carries the user's Keycloak access
token, refreshed here before it ends, so apiv2 checks the user exactly as it
checks the web app.

The tokens are kept sealed in the store, with the token this server gave the
client (`oauth`), and never leave this server.
"""

import base64
import hashlib
import secrets
import time
import typing
from urllib.parse import urlencode

import httpx

from .config import (
    KEYCLOAK_CLIENT_ID,
    KEYCLOAK_CLIENT_SECRET,
    KEYCLOAK_ISSUER,
    KEYCLOAK_REDIRECT_URL,
    KEYCLOAK_SCOPE,
)
from .consts import (
    LOGIN_SECONDS,
    ROUTE_TIMEOUT_SECONDS,
    TOKEN_SECONDS,
    KeycloakFields,
    TokenClaims,
)
from .store import Record, forget, recall, remember

type Tokens = dict[str, typing.Any]

_transport: httpx.AsyncBaseTransport | None = None


def use_transport(transport: httpx.AsyncBaseTransport | None) -> None:
    """Send Keycloak requests through `transport` instead — a test's own Keycloak, say."""
    global _transport
    _transport = transport


class KeycloakRefused(Exception):
    """Keycloak would not sign the user in, or would not keep them signed in."""


async def start_sign_in(login_state: str) -> str:
    """Remember a sign-in in flight, and return the Keycloak URL that starts it.

    Args:
        login_state: The state the login page was opened with, which leads
            back to the client that asked for the sign-in.
    """
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    await remember(
        KeycloakFields.SIGN_IN,
        state,
        {KeycloakFields.LOGIN_STATE: login_state, KeycloakFields.VERIFIER: verifier},
        LOGIN_SECONDS,
    )
    query = {
        "client_id": KEYCLOAK_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": KEYCLOAK_REDIRECT_URL,
        "scope": KEYCLOAK_SCOPE,
        "state": state,
        "code_challenge": challenge_of(verifier),
        "code_challenge_method": "S256",
    }
    return f"{KEYCLOAK_ISSUER}{KeycloakFields.AUTH_PATH}?{urlencode(query)}"


def challenge_of(verifier: str) -> str:
    """The PKCE challenge (S256) for a code verifier."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


async def finish_sign_in(state: str, code: str) -> tuple[str, Tokens, int]:
    """Trade the code Keycloak sent back for the user's tokens.

    Returns:
        The login page's state, the tokens as a caller's claims hold them, and
        how long the sign-in may be kept.

    Raises:
        KeycloakRefused: If the sign-in expired, or Keycloak refused the code.
    """
    in_flight = await recall(KeycloakFields.SIGN_IN, state)
    if in_flight is None:
        raise KeycloakRefused("This sign-in has expired. Start again from your client.")
    await forget(KeycloakFields.SIGN_IN, state)
    answer = await ask_for_tokens(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": KEYCLOAK_REDIRECT_URL,
            "code_verifier": in_flight[KeycloakFields.VERIFIER],
        }
    )
    return str(in_flight[KeycloakFields.LOGIN_STATE]), read_tokens(answer), session_seconds(answer)


async def refresh(tokens: Tokens) -> Tokens:
    """New tokens for a user whose access token is about to end.

    Raises:
        KeycloakRefused: If the user's Keycloak session has ended.
    """
    answer = await ask_for_tokens(
        {"grant_type": "refresh_token", "refresh_token": tokens[TokenClaims.KEYCLOAK_REFRESH]}
    )
    renewed = read_tokens(answer)
    # Keycloak may keep the refresh token it had and send none back.
    renewed[TokenClaims.KEYCLOAK_REFRESH] = (
        renewed[TokenClaims.KEYCLOAK_REFRESH] or tokens[TokenClaims.KEYCLOAK_REFRESH]
    )
    return renewed


def is_ending(tokens: Tokens, margin: float) -> bool:
    """Whether the access token ends within `margin` seconds."""
    return float(tokens[TokenClaims.KEYCLOAK_EXPIRES_AT]) - margin <= time.time()


def session_seconds(answer: Record) -> int:
    """How long this server keeps the sign-in: as long as Keycloak keeps the session.

    An offline session reports no end of its own (`0`), and lives for as long
    as the realm lets it; this server then keeps it for `TOKEN_SECONDS`.
    """
    left = int(answer.get(KeycloakFields.REFRESH_EXPIRES_IN) or 0)
    return min(left, TOKEN_SECONDS) if left > 0 else TOKEN_SECONDS


async def ask_for_tokens(grant: dict[str, str]) -> Record:
    """Send one grant to Keycloak's token endpoint, as this server's client.

    Raises:
        KeycloakRefused: If Keycloak refuses the grant or cannot be reached.
    """
    form = {**grant, "client_id": KEYCLOAK_CLIENT_ID}
    if KEYCLOAK_CLIENT_SECRET:
        form["client_secret"] = KEYCLOAK_CLIENT_SECRET
    try:
        async with httpx.AsyncClient(transport=_transport, timeout=ROUTE_TIMEOUT_SECONDS) as client:
            answer = await client.post(f"{KEYCLOAK_ISSUER}{KeycloakFields.TOKEN_PATH}", data=form)
    except httpx.HTTPError as unreachable:
        raise KeycloakRefused("Mammoth's sign-in could not be reached. Try again.") from unreachable
    if answer.status_code != 200:
        raise KeycloakRefused("Mammoth's sign-in refused this. Sign in again.")
    return typing.cast(Record, answer.json())


def read_tokens(answer: Record) -> Tokens:
    """The tokens Keycloak answered with, as a caller's claims hold them."""
    return {
        TokenClaims.KEYCLOAK_ACCESS: answer[KeycloakFields.ACCESS_TOKEN],
        TokenClaims.KEYCLOAK_REFRESH: answer.get(KeycloakFields.REFRESH_TOKEN),
        TokenClaims.KEYCLOAK_EXPIRES_AT: time.time() + int(answer[KeycloakFields.EXPIRES_IN]),
    }
