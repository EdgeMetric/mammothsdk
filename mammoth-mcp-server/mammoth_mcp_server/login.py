"""The login page of the authorization server: where a user pastes their API token.

The MCP SDK serves the OAuth endpoints themselves from .
The page in between is ours:  sends the browser here, and a token
Mammoth accepts sends it back to the client with a code.
"""

from html import escape

from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

from .config import MCP_LOGIN_URL
from .consts import API_TOKEN_PREFIX, OAuthFields
from .oauth import LoginRefused, oauth_provider

LOGIN_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mammoth Analytics — Connect</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
           sans-serif; background: #f5f5f5; display: flex; justify-content: center;
           align-items: center; min-height: 100vh; }}
    .card {{ background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,.08);
            padding: 2.5rem; width: 100%; max-width: 420px; }}
    h1 {{ font-size: 1.4rem; margin-bottom: .25rem; }}
    p.sub {{ color: #666; font-size: .9rem; margin-bottom: 1.5rem; }}
    label {{ display: block; font-size: .85rem; font-weight: 600; margin-bottom: .3rem; }}
    input {{ width: 100%; padding: .6rem .75rem; border: 1px solid #ddd;
            border-radius: 6px; font-size: .95rem; margin-bottom: 1rem; }}
    button {{ width: 100%; padding: .7rem; background: #4a90d9; color: #fff;
             border: none; border-radius: 6px; font-size: 1rem; font-weight: 600;
             cursor: pointer; }}
    .error {{ background: #fef2f2; color: #b91c1c; padding: .75rem;
             border-radius: 6px; font-size: .85rem; margin-bottom: 1rem; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Mammoth Analytics</h1>
    <p class="sub">Paste your Mammoth API token to connect this client.
      You create one in Mammoth: Workspace settings, API Tokens.</p>
    {error}
    <form method="POST" action="{action}">
      <input type="hidden" name="{state_field}" value="{state}">
      <label for="api-token">API token</label>
      <input id="api-token" type="password" name="{token_field}" required autofocus
             autocomplete="off" placeholder="mm_...">
      <button type="submit">Connect</button>
    </form>
  </div>
</body>
</html>
"""
MISSING_TOKEN = "Paste your Mammoth API token."
NOT_A_TOKEN = f"A Mammoth API token starts with {API_TOKEN_PREFIX}. Copy the whole token."


def render_login(state: str, error: str = "") -> str:
    """Draw the login page, with a reason the last attempt was refused."""
    return LOGIN_PAGE.format(
        error=f'<div class="error">{escape(error)}</div>' if error else "",
        action=MCP_LOGIN_URL,
        state_field=OAuthFields.STATE,
        state=escape(state),
        token_field=OAuthFields.API_TOKEN,
    )


async def login(request: Request) -> Response:
    """Show the login page, or take what the user pasted on it."""
    if request.method == "GET":
        return HTMLResponse(render_login(request.query_params.get(OAuthFields.STATE, "")))
    return await accept_login(request)


async def accept_login(request: Request) -> Response:
    """Take the token and send the user back to the client with a code.

    A refused sign-in redraws the page with the reason rather than failing the
    request: the user is in a browser, and can correct what they pasted.
    """
    form = await request.form()
    state = str(form.get(OAuthFields.STATE, ""))
    try:
        back_to_client = await oauth_provider.accept_login(state, read_token(form))
    except LoginRefused as refused:
        return HTMLResponse(render_login(state, str(refused)), status_code=400)
    return RedirectResponse(back_to_client, status_code=302)


def read_token(form: object) -> str:
    """Read the token the user pasted.

    Raises:
        LoginRefused: If nothing was pasted, or it is not shaped like a token.
    """
    pasted = str(form.get(OAuthFields.API_TOKEN, "")).strip()  # type: ignore[attr-defined]
    if not pasted:
        raise LoginRefused(MISSING_TOKEN)
    if not pasted.startswith(API_TOKEN_PREFIX):
        raise LoginRefused(NOT_A_TOKEN)
    return pasted
