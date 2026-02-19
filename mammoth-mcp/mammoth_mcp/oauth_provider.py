"""MCP OAuth Authorization Server provider backed by Redis."""

from __future__ import annotations

import logging
import secrets
import time
import urllib.parse
from typing import Any

import httpx
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    RefreshToken,
    TokenError,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from mammoth_mcp.settings import Settings
from mammoth_mcp.token_store import RedisTokenStore

logger = logging.getLogger(__name__)


class MammothOAuthProvider:
    """OAuth 2.0 Authorization Server that authenticates users via Mammoth API credentials."""

    def __init__(self, settings: Settings, token_store: RedisTokenStore):
        self._settings = settings
        self._store = token_store

    # ── Dynamic Client Registration (RFC 7591) ─────────────────

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        data = await self._store.get_client(client_id)
        if data is None:
            return None
        return OAuthClientInformationFull(**data)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        client_id = f"mammoth-{secrets.token_hex(16)}"
        client_info.client_id = client_id
        client_info.client_id_issued_at = int(time.time())
        await self._store.store_client(client_id, client_info.model_dump(mode="json"))
        logger.info("Registered OAuth client %s", client_id)

    # ── Authorization ──────────────────────────────────────────

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        state_data = {
            "client_id": client.client_id,
            "redirect_uri": str(params.redirect_uri),
            "code_challenge": params.code_challenge,
            "scopes": params.scopes or [],
            "redirect_uri_provided_explicitly": params.redirect_uri_provided_explicitly,
            "resource": params.resource,
        }
        state_key = secrets.token_urlsafe(32)
        await self._store.store_state(state_key, state_data)
        login_url = f"{self._settings.server_url}/login?state={state_key}"
        logger.info("Authorization started, redirecting to login (state=%s)", state_key[:8])
        return login_url

    # ── Authorization code exchange ────────────────────────────

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        data = await self._store.get_code(authorization_code)
        if data is None:
            return None
        if data["client_id"] != client.client_id:
            return None
        return AuthorizationCode(
            code=authorization_code,
            scopes=data.get("scopes", []),
            expires_at=data["expires_at"],
            client_id=data["client_id"],
            code_challenge=data["code_challenge"],
            redirect_uri=data["redirect_uri"],
            redirect_uri_provided_explicitly=data.get("redirect_uri_provided_explicitly", True),
            resource=data.get("resource"),
        )

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        logger.info("Token exchange for client %s, code=%s...", client.client_id, authorization_code.code[:8])
        code_data = await self._store.get_code(authorization_code.code)
        if code_data is None:
            logger.error("Auth code not found in Redis (expired or already used)")
            raise TokenError(error="invalid_grant", error_description="Authorization code expired or invalid")

        await self._store.delete_code(authorization_code.code)

        bearer_token = secrets.token_urlsafe(48)
        expires_at = int(time.time()) + self._settings.access_token_ttl
        token_data = {
            "client_id": client.client_id,
            "credentials": code_data["credentials"],
            "scopes": code_data.get("scopes", []),
            "expires_at": expires_at,
            "resource": code_data.get("resource"),
        }
        await self._store.store_token(bearer_token, token_data)
        logger.info("Issued access token for client %s", client.client_id)

        return OAuthToken(
            access_token=bearer_token,
            token_type="Bearer",
            expires_in=self._settings.access_token_ttl,
        )

    # ── Refresh tokens (not supported — long-lived access tokens) ──

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        return None

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        raise TokenError(error="unsupported_grant_type", error_description="Refresh tokens are not supported")

    # ── Token verification & revocation ────────────────────────

    async def load_access_token(self, token: str) -> AccessToken | None:
        logger.debug("load_access_token called, token=%s...", token[:8] if token else "NONE")
        data = await self._store.get_token(token)
        if data is None:
            logger.warning("Access token not found in Redis: %s...", token[:8] if token else "NONE")
            return None
        if data.get("expires_at") and data["expires_at"] < time.time():
            await self._store.delete_token(token)
            return None
        return AccessToken(
            token=token,
            client_id=data["client_id"],
            scopes=data.get("scopes", []),
            expires_at=data.get("expires_at"),
            resource=data.get("resource"),
        )

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        await self._store.delete_token(token.token)
        logger.info("Revoked token for client %s", token.client_id)


# ── Login page & callback (custom routes) ──────────────────

LOGIN_HTML = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mammoth Analytics — Connect</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
           background: #f5f5f5; display: flex; justify-content: center; align-items: center;
           min-height: 100vh; }
    .card { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,.08);
            padding: 2.5rem; width: 100%; max-width: 420px; }
    h1 { font-size: 1.4rem; margin-bottom: .25rem; }
    p.sub { color: #666; font-size: .9rem; margin-bottom: 1.5rem; }
    label { display: block; font-size: .85rem; font-weight: 600; margin-bottom: .3rem; }
    input { width: 100%; padding: .6rem .75rem; border: 1px solid #ddd; border-radius: 6px;
            font-size: .95rem; margin-bottom: 1rem; }
    input:focus { outline: none; border-color: #4a90d9; box-shadow: 0 0 0 2px rgba(74,144,217,.2); }
    button { width: 100%; padding: .7rem; background: #4a90d9; color: #fff; border: none;
             border-radius: 6px; font-size: 1rem; font-weight: 600; cursor: pointer; }
    button:hover { background: #3a7bc8; }
    .error { background: #fef2f2; color: #b91c1c; padding: .75rem; border-radius: 6px;
             font-size: .85rem; margin-bottom: 1rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Mammoth Analytics</h1>
    <p class="sub">Enter your API credentials to connect.</p>
    {error}
    <form method="POST" action="/login/callback">
      <input type="hidden" name="state" value="{state}">
      <label>API Key</label>
      <input type="text" name="api_key" required placeholder="Your Mammoth API key">
      <label>API Secret</label>
      <input type="password" name="api_secret" required placeholder="Your Mammoth API secret">
      <label>Workspace ID</label>
      <input type="number" name="workspace_id" required placeholder="e.g. 2">
      <button type="submit">Connect</button>
    </form>
  </div>
</body>
</html>
"""


def _render_login(state: str, error: str = "") -> str:
    error_html = f'<div class="error">{error}</div>' if error else ""
    return LOGIN_HTML.replace("{state}", state).replace("{error}", error_html)


async def validate_mammoth_credentials(
    api_key: str, api_secret: str, workspace_id: int, base_url: str,
) -> bool:
    """Validate credentials by making a lightweight Mammoth API call."""
    headers = {
        "X-API-KEY": api_key,
        "X-API-SECRET": api_secret,
        "X-WORKSPACE-ID": str(workspace_id),
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{base_url}/workspaces/{workspace_id}/projects", headers=headers)
            return resp.status_code == 200
    except httpx.HTTPError:
        logger.exception("Credential validation failed")
        return False


def register_login_routes(mcp_server: Any, settings: Settings, token_store: RedisTokenStore) -> None:
    """Register /login and /login/callback custom routes on the FastMCP server."""
    from starlette.requests import Request
    from starlette.responses import HTMLResponse, RedirectResponse

    @mcp_server.custom_route("/login", methods=["GET"])
    async def login_page(request: Request) -> HTMLResponse:
        state = request.query_params.get("state", "")
        if not state:
            return HTMLResponse(_render_login("", error="Missing state parameter."), status_code=400)
        return HTMLResponse(_render_login(state))

    @mcp_server.custom_route("/login/callback", methods=["POST"])
    async def login_callback(request: Request) -> RedirectResponse | HTMLResponse:
        form = await request.form()
        state = str(form.get("state", ""))
        api_key = str(form.get("api_key", "")).strip()
        api_secret = str(form.get("api_secret", "")).strip()
        workspace_id_str = str(form.get("workspace_id", "0")).strip()
        base_url = str(form.get("base_url", "")).strip() or settings.mammoth_base_url

        if not state or not api_key or not api_secret or workspace_id_str == "0":
            return HTMLResponse(
                _render_login(state, error="All fields are required."), status_code=400
            )

        workspace_id = int(workspace_id_str)

        # Validate credentials against Mammoth API
        valid = await validate_mammoth_credentials(api_key, api_secret, workspace_id, base_url)
        if not valid:
            return HTMLResponse(
                _render_login(state, error="Invalid credentials — check your API key, secret, and workspace ID."),
                status_code=400,
            )

        # Load authorization state
        state_data = await token_store.get_state(state)
        if not state_data:
            return HTMLResponse(
                _render_login(state, error="Session expired. Please try again."), status_code=400
            )
        await token_store.delete_state(state)

        # Generate authorization code
        auth_code = secrets.token_urlsafe(32)
        code_data = {
            "client_id": state_data["client_id"],
            "code_challenge": state_data["code_challenge"],
            "redirect_uri": state_data["redirect_uri"],
            "redirect_uri_provided_explicitly": state_data.get("redirect_uri_provided_explicitly", True),
            "scopes": state_data.get("scopes", []),
            "resource": state_data.get("resource"),
            "credentials": {
                "api_key": api_key,
                "api_secret": api_secret,
                "workspace_id": workspace_id,
                "base_url": base_url,
            },
            "expires_at": time.time() + settings.auth_code_ttl,
        }
        await token_store.store_code(auth_code, code_data)

        # Redirect back to client with authorization code
        redirect_uri = state_data["redirect_uri"]
        params = urllib.parse.urlencode({"code": auth_code, "state": state})
        sep = "&" if "?" in redirect_uri else "?"
        return RedirectResponse(url=f"{redirect_uri}{sep}{params}", status_code=302)
