"""Shared fixtures for MCP server e2e tests.

Required environment variables (set in .env.test or shell):
    MCP_SERVER_URL     – e.g. https://mcp.mammoth.io
    MAMMOTH_API_KEY    – Mammoth API key
    MAMMOTH_API_SECRET – Mammoth API secret
    MAMMOTH_WORKSPACE_ID – Mammoth workspace ID

Optional:
    MAMMOTH_TEST_VIEW_ID – a known view ID to test against (default: 276668)
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import secrets
import urllib.parse

import httpx
import pytest

# ---------------------------------------------------------------------------
# Env helpers
# ---------------------------------------------------------------------------

def _env(name: str, default: str | None = None) -> str:
    val = os.environ.get(name, default or "")
    if not val:
        pytest.skip(f"{name} not set")
    return val


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def server_url() -> str:
    return _env("MCP_SERVER_URL").rstrip("/")


@pytest.fixture(scope="session")
def api_key() -> str:
    return _env("MAMMOTH_API_KEY")


@pytest.fixture(scope="session")
def api_secret() -> str:
    return _env("MAMMOTH_API_SECRET")


@pytest.fixture(scope="session")
def workspace_id() -> str:
    return _env("MAMMOTH_WORKSPACE_ID")


@pytest.fixture(scope="session")
def test_view_id() -> int:
    return int(os.environ.get("MAMMOTH_TEST_VIEW_ID", "276668"))


@pytest.fixture(scope="session")
def http_client() -> httpx.Client:
    client = httpx.Client(timeout=60, follow_redirects=False)
    yield client
    client.close()


# ---------------------------------------------------------------------------
# OAuth helpers
# ---------------------------------------------------------------------------

def _parse_sse(text: str) -> list[dict]:
    """Parse SSE response body into JSON-RPC messages."""
    messages = []
    for block in text.split("\n\n"):
        for line in block.strip().split("\n"):
            if line.startswith("data: "):
                try:
                    messages.append(json.loads(line[6:]))
                except json.JSONDecodeError:
                    pass
    return messages


@pytest.fixture(scope="session")
def oauth_token(
    http_client: httpx.Client,
    server_url: str,
    api_key: str,
    api_secret: str,
    workspace_id: str,
) -> str:
    """Run the full OAuth 2.0 PKCE flow and return a bearer token."""
    # 1. Metadata
    r = http_client.get(f"{server_url}/.well-known/oauth-authorization-server")
    assert r.status_code == 200, f"OAuth metadata failed: {r.status_code} {r.text[:200]}"
    meta = r.json()

    # 2. Dynamic client registration
    r = http_client.post(
        meta["registration_endpoint"],
        json={
            "client_name": "pytest-e2e",
            "redirect_uris": ["http://localhost:9999/callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        },
    )
    assert r.status_code in (200, 201), f"Registration failed: {r.status_code} {r.text[:200]}"
    client_id = r.json()["client_id"]

    # 3. PKCE
    code_verifier = secrets.token_urlsafe(43)
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    state = secrets.token_urlsafe(32)

    # 4. Authorize
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
    assert login_url, "No redirect to login page"

    # 5. Get login page (extract internal state)
    full_url = login_url if login_url.startswith("http") else f"{server_url}{login_url}"
    r = http_client.get(full_url)
    m = re.search(r'name="state" value="([^"]+)"', r.text)
    assert m, "Could not extract internal state from login page"
    internal_state = m.group(1)

    # 6. Submit credentials
    r = http_client.post(
        f"{server_url}/login/callback",
        data={
            "state": internal_state,
            "api_key": api_key,
            "api_secret": api_secret,
            "workspace_id": workspace_id,
        },
    )
    redirect_location = r.headers.get("location", "")
    parsed = urllib.parse.urlparse(redirect_location)
    qs = urllib.parse.parse_qs(parsed.query)
    auth_code = qs.get("code", [""])[0]
    assert auth_code, f"No auth code in redirect: {redirect_location}"
    returned_state = qs.get("state", [""])[0]
    assert returned_state == state, "OAuth state mismatch"

    # 7. Token exchange
    r = http_client.post(
        meta["token_endpoint"],
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": "http://localhost:9999/callback",
            "client_id": client_id,
            "code_verifier": code_verifier,
        },
    )
    assert r.status_code == 200, f"Token exchange failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def mcp_session(
    http_client: httpx.Client,
    server_url: str,
    oauth_token: str,
) -> dict:
    """Initialize an MCP session and return {session_id, msg_counter}."""
    headers = {
        "Authorization": f"Bearer {oauth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    # Initialize
    r = http_client.post(
        f"{server_url}/mcp",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 1,
            "params": {
                "capabilities": {},
                "protocolVersion": "2025-03-26",
                "clientInfo": {"name": "pytest-e2e", "version": "0.1"},
            },
        },
    )
    assert r.status_code == 200, f"MCP initialize failed: {r.status_code} {r.text[:200]}"
    session_id = r.headers.get("mcp-session-id", "")
    assert session_id, "No mcp-session-id in response"

    # Send initialized notification
    notif_headers = dict(headers)
    notif_headers["Mcp-Session-Id"] = session_id
    http_client.post(
        f"{server_url}/mcp",
        headers=notif_headers,
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
    )

    return {"session_id": session_id, "msg_counter": 2}


def mcp_tool_call(
    http_client: httpx.Client,
    server_url: str,
    oauth_token: str,
    session: dict,
    tool_name: str,
    arguments: dict,
    expect_json: bool = True,
) -> dict | str:
    """Make an MCP tool call and return the parsed result data."""
    session["msg_counter"] += 1
    msg_id = session["msg_counter"]

    headers = {
        "Authorization": f"Bearer {oauth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Mcp-Session-Id": session["session_id"],
    }

    r = http_client.post(
        f"{server_url}/mcp",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": msg_id,
            "params": {"name": tool_name, "arguments": arguments},
        },
    )
    assert r.status_code == 200, f"MCP tool call failed: {r.status_code} {r.text[:200]}"

    # Parse response (SSE or JSON)
    content_type = r.headers.get("content-type", "")
    if content_type.startswith("text/event-stream"):
        messages = _parse_sse(r.text)
        resp = None
        for m in messages:
            if m.get("id") == msg_id:
                resp = m
                break
        if resp is None and messages:
            resp = messages[-1]
        assert resp is not None, "No matching SSE message found"
    else:
        resp = r.json()

    # Extract tool result
    assert "error" not in resp, f"JSON-RPC error: {resp.get('error')}"
    result = resp.get("result", {})
    content = result.get("content", [])
    assert content, "Empty content in tool response"

    text_item = next((c for c in content if c.get("type") == "text"), None)
    assert text_item, "No text content in tool response"

    if not expect_json:
        return text_item["text"]

    return json.loads(text_item["text"])
