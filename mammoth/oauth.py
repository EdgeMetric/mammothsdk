"""Plain HTTP calls of the OAuth sign-in flow that sit outside the REST resources.

The token endpoint takes a form body and returns tokens, and the grant revoke
call is authorised by the access token it removes. Neither fits the workspace
scoped client, so they live here, keeping every Mammoth HTTP call in the SDK.
"""

from __future__ import annotations

from typing import Any

import httpx

_TIMEOUT_SECONDS = 30.0
_METADATA_TIMEOUT_SECONDS = 5.0


class OAuthTransportError(Exception):
    """Mammoth could not be reached."""


def _post_form(base_url: str, path: str, form: dict[str, str]) -> tuple[int, Any]:
    try:
        response = httpx.post(
            f"{base_url}{path}",
            data=form,
            timeout=_TIMEOUT_SECONDS,
            follow_redirects=False,
        )
    except httpx.HTTPError as exc:
        raise OAuthTransportError(str(exc)) from exc
    try:
        return response.status_code, response.json()
    except ValueError:
        return response.status_code, None


def token_request(base_url: str, form: dict[str, str]) -> tuple[int, Any]:
    """POST a form to ``/oauth/token``. Return ``(status_code, json_body_or_None)``.

    Raises:
        OAuthTransportError: when the server cannot be reached.
    """
    return _post_form(base_url, "/oauth/token", form)


def device_authorization_request(base_url: str, form: dict[str, str]) -> tuple[int, Any]:
    """POST a form to ``/oauth/device-authorization`` (RFC 8628 §3.1).

    Return ``(status_code, json_body_or_None)``.

    Raises:
        OAuthTransportError: when the server cannot be reached.
    """
    return _post_form(base_url, "/oauth/device-authorization", form)


def metadata_request(base_url: str) -> tuple[int, Any]:
    """GET ``/.well-known/oauth-authorization-server`` (RFC 8414).

    Return ``(status_code, json_body_or_None)``. The short timeout keeps a slow
    or dead server from stalling a sign-in menu.

    Raises:
        OAuthTransportError: when the server cannot be reached.
    """
    try:
        response = httpx.get(
            f"{base_url}/.well-known/oauth-authorization-server",
            timeout=_METADATA_TIMEOUT_SECONDS,
            follow_redirects=False,
        )
    except httpx.HTTPError as exc:
        raise OAuthTransportError(str(exc)) from exc
    try:
        return response.status_code, response.json()
    except ValueError:
        return response.status_code, None


def revoke_grant(base_url: str, grant_id: int, access_token: str) -> int:
    """DELETE ``/self/oauth-grants/{grant_id}``. Return the HTTP status code.

    Raises:
        OAuthTransportError: when the server cannot be reached.
    """
    try:
        response = httpx.delete(
            f"{base_url}/self/oauth-grants/{grant_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=_TIMEOUT_SECONDS,
            follow_redirects=False,
        )
    except httpx.HTTPError as exc:
        raise OAuthTransportError(str(exc)) from exc
    return response.status_code
