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
| `mammoth_mcp_server/oauth.py`, `login.py` | The sign-in: an OAuth server whose login page asks for an API token. |
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
| `MCP_HOST`, `MCP_PORT` | `127.0.0.1`, `8270` | Where the server listens. |

## Sign-in

A user signs in with their own Mammoth API token (`mm_...`), created in Mammoth at Workspace
settings, API Tokens.

- **Claude web, ChatGPT (OAuth):** the client opens this server's login page. The user pastes the
  token. The server checks it with Mammoth and gives the client a token of its own. The user's
  token is kept sealed in Redis for 30 days.
- **A client that sends headers (Claude Code):** send `Authorization: Bearer mm_...`. Nothing is
  stored.

Every tool call reaches Mammoth with the user's own token, so the user's permissions apply. A
token belongs to one workspace; a tool call for another workspace is refused.

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
