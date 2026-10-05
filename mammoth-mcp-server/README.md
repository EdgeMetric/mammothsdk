# mammoth-mcp-server

The Mammoth MCP server. An AI client (Claude, ChatGPT) uses its tools to explore, clean, transform
and export data in Mammoth, as the signed-in user.

The server depends on one Mammoth package: the SDK (`mammoth-io`). Every tool reaches Mammoth
through the API, as the SDK does. The server imports no backend code.

## Layout

| Path | What it holds |
|---|---|
| `mammoth_mcp_server/tools/` | The tools, one module per area (views, pipeline, files, dashboards, ...). |
| `mammoth_mcp_server/sdk.py` | The SDK client a tool call is given, and the API's errors in words a model can use. |
| `mammoth_mcp_server/jobs.py` | The wait for a job that an API route started. |
| `mammoth_mcp_server/task_params.py` | The map from a transformation to the pipeline task the API takes. |
| `mammoth_mcp_server/store.py` | Short-lived records in Redis: sign-ins, tokens, upload tickets. |
| `mammoth_mcp_server/oauth.py`, `login.py` | The sign-in: an OAuth server whose login page offers a Mammoth login or an API token. |
| `mammoth_mcp_server/keycloak.py` | The Mammoth login: this server's sign-in at Keycloak, and token refresh. |
| `mammoth_mcp_server/upload_routes.py` | The page a user drops a local file on. |
| `mammoth_mcp_server/app.py` | The ASGI app and `main()`. |
| `mammoth_mcp_server/config.py` | Every deployment setting, read from the environment. |

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `MCP_SERVER_URL` | `https://mcp.mammoth.io` | This server, as a client reaches it. |
| `MAMMOTH_APP_URL` | `https://app.mammoth.io` | The web app, for the links a tool gives the user. |
| `MAMMOTH_DASHBOARD_URL` | `MAMMOTH_APP_URL` | The host that serves a published dashboard. |
| `MAMMOTH_API_URL` | `MAMMOTH_APP_URL` + `/api/v2` | The API every tool call goes to. |
| `MAMMOTH_API_ROOT` | `/api/v2` | The path the API is served under. Set it empty for an API reached directly. |
| `MCP_REDIS_URL` | `redis://localhost:6379/0` | Where sign-ins, tokens and upload tickets are kept. |
| `MCP_ENCRYPTION_KEY` | none | A Fernet key. Stored credentials are sealed with it. Required. |
| `MCP_STORE_PREFIX` | `mammoth_mcp` | Keeps this deployment's records apart in a shared Redis. |
| `MCP_KEYCLOAK_URL`, `MCP_KEYCLOAK_REALM` | none | Keycloak, and the realm Mammoth users sign in to. |
| `MCP_KEYCLOAK_CLIENT_ID`, `MCP_KEYCLOAK_CLIENT_SECRET` | none | This server's Keycloak client. Unset: API token login only. |
| `MCP_KEYCLOAK_SCOPE` | `openid offline_access` | What the server asks Keycloak for. |
| `MCP_HOST`, `MCP_PORT` | `127.0.0.1`, `8270` | Where the server listens. |

## Sign-in

Claude web and ChatGPT open this server's login page. The user signs in one of two ways:

- **Sign in with Mammoth:** the user's normal Mammoth login, through Keycloak. The server keeps the
  user's Keycloak tokens sealed in Redis and refreshes them before they end. Every workspace the
  user can open is available.
- **API token:** the user pastes their own Mammoth API token (`mm_...`), created in Mammoth at
  Workspace settings, API Tokens. The server checks it with Mammoth and keeps it sealed for 30
  days. A token belongs to one workspace; a tool call for another workspace is refused.

A client that can send headers (Claude Code) can instead send `Authorization: Bearer mm_...`.
Nothing is stored for it.

Every tool call reaches Mammoth with the user's own credentials, so the user's permissions apply.
The client only ever holds a token of this server's.

### Keycloak

One-time setup per environment:

1. In the realm, an admin creates a confidential OpenID Connect client, for example
   `mammoth-mcp`, with the standard flow on and the redirect URI
   `<MCP_SERVER_URL>/login/keycloak/callback`. For long-lived connectors, allow the
   `offline_access` scope.
2. Set `MCP_KEYCLOAK_URL`, `MCP_KEYCLOAK_REALM`, `MCP_KEYCLOAK_CLIENT_ID` and
   `MCP_KEYCLOAK_CLIENT_SECRET` for this server.
3. In mvc-service `const.ini`, section `[keycloak]`, add `MCP_CLIENTS = mammoth-mcp`. apiv2 then
   asks no anti-CSRF cookie of tokens issued to that client: it holds no browser cookie, and its
   token travels in a header no web page can set.

## Run

```bash
pip install mammoth-mcp-server
cp .env.example .env        # then set the values
mammoth-mcp-server          # or: uvicorn mammoth_mcp_server.app:create_app --factory
```

`deploy/` holds an example systemd unit and an example nginx server block.

## Tests

```bash
cd mammoth-mcp-server
python -m pytest tests -q
```

The tests reach no server. The SDK client and the tools are real; only the HTTP transport under
the client is replaced.
