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

## Tests

```bash
cd mammoth-mcp-server
python -m pytest tests -q
```

The tests reach no server. The SDK client and the tools are real; only the HTTP transport under
the client is replaced.
