"""E2E tests for the OAuth 2.0 PKCE flow.

Requires a running MCP server and valid Mammoth credentials.
Set env vars: MCP_SERVER_URL, MAMMOTH_API_KEY, MAMMOTH_API_SECRET, MAMMOTH_WORKSPACE_ID
"""

from __future__ import annotations

import base64
import hashlib
import re
import secrets
import urllib.parse

import httpx
import pytest


class TestOAuthMetadata:
    """Test the OAuth discovery endpoint."""

    def test_well_known_returns_endpoints(self, http_client: httpx.Client, server_url: str):
        r = http_client.get(f"{server_url}/.well-known/oauth-authorization-server")
        assert r.status_code == 200
        meta = r.json()
        assert "authorization_endpoint" in meta
        assert "token_endpoint" in meta
        assert "registration_endpoint" in meta


class TestClientRegistration:
    """Test Dynamic Client Registration (RFC 7591)."""

    def test_register_client(self, http_client: httpx.Client, server_url: str):
        r = http_client.get(f"{server_url}/.well-known/oauth-authorization-server")
        meta = r.json()

        r = http_client.post(
            meta["registration_endpoint"],
            json={
                "client_name": "test-registration",
                "redirect_uris": ["http://localhost:9999/callback"],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
            },
        )
        assert r.status_code in (200, 201)
        data = r.json()
        assert "client_id" in data
        assert data["client_id"].startswith("mammoth-")


class TestFullOAuthFlow:
    """Test the complete OAuth PKCE flow end-to-end."""

    def test_authorize_redirects_to_login(self, http_client: httpx.Client, server_url: str):
        # Register a client
        r = http_client.get(f"{server_url}/.well-known/oauth-authorization-server")
        meta = r.json()
        r = http_client.post(
            meta["registration_endpoint"],
            json={
                "client_name": "test-auth",
                "redirect_uris": ["http://localhost:9999/callback"],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
            },
        )
        client_id = r.json()["client_id"]

        # Authorize
        code_verifier = secrets.token_urlsafe(43)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        r = http_client.get(
            f"{server_url}/authorize",
            params={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": "http://localhost:9999/callback",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "state": "test-state",
            },
        )
        location = r.headers.get("location", "")
        assert "/login" in location, f"Expected redirect to /login, got: {location}"

    def test_login_page_renders(self, http_client: httpx.Client, server_url: str):
        # Register + authorize to get a login URL
        r = http_client.get(f"{server_url}/.well-known/oauth-authorization-server")
        meta = r.json()
        r = http_client.post(
            meta["registration_endpoint"],
            json={
                "client_name": "test-login-page",
                "redirect_uris": ["http://localhost:9999/callback"],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
            },
        )
        client_id = r.json()["client_id"]

        code_verifier = secrets.token_urlsafe(43)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        r = http_client.get(
            f"{server_url}/authorize",
            params={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": "http://localhost:9999/callback",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "state": "test-state",
            },
        )
        login_url = r.headers.get("location", "")
        full_url = login_url if login_url.startswith("http") else f"{server_url}{login_url}"

        r = http_client.get(full_url)
        assert r.status_code == 200
        assert 'name="api_key"' in r.text
        assert 'name="api_secret"' in r.text
        assert 'name="workspace_id"' in r.text
        assert 'name="state"' in r.text

    def test_full_flow_returns_token(self, oauth_token: str):
        """The oauth_token fixture runs the entire flow — just verify it returns a string."""
        assert isinstance(oauth_token, str)
        assert len(oauth_token) > 20

    def test_invalid_credentials_rejected(
        self,
        http_client: httpx.Client,
        server_url: str,
    ):
        """Submitting wrong credentials should show an error, not issue a token."""
        r = http_client.get(f"{server_url}/.well-known/oauth-authorization-server")
        meta = r.json()
        r = http_client.post(
            meta["registration_endpoint"],
            json={
                "client_name": "test-bad-creds",
                "redirect_uris": ["http://localhost:9999/callback"],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
            },
        )
        client_id = r.json()["client_id"]

        code_verifier = secrets.token_urlsafe(43)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        state = secrets.token_urlsafe(32)
        r = http_client.get(
            f"{server_url}/authorize",
            params={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": "http://localhost:9999/callback",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "state": state,
            },
        )
        login_url = r.headers.get("location", "")
        full_url = login_url if login_url.startswith("http") else f"{server_url}{login_url}"
        r = http_client.get(full_url)
        m = re.search(r'name="state" value="([^"]+)"', r.text)
        internal_state = m.group(1)

        # Submit bad credentials
        r = http_client.post(
            f"{server_url}/login/callback",
            data={
                "state": internal_state,
                "api_key": "INVALID_KEY",
                "api_secret": "INVALID_SECRET",
                "workspace_id": "999999",
            },
        )
        # Should not redirect with a code — should show error or redirect without code
        location = r.headers.get("location", "")
        if location:
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(location).query)
            assert "code" not in qs, "Should not issue code for invalid credentials"
        else:
            # Error shown on page
            assert r.status_code in (200, 400, 401, 403)
