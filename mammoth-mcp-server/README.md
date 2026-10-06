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
| `mammoth_mcp_server/tokens.py` | The check of a caller's token: Mammoth says whether it is live and which server it is for. |
| `mammoth_mcp_server/store.py` | Short-lived records in Redis: upload tickets. |
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
| `MAMMOTH_OAUTH_URL` | `MAMMOTH_APP_URL` + `/api/v2` | Mammoth's authorization server (its issuer), where a client signs the user in. |
| `MCP_REDIS_URL` | `redis://localhost:6379/0` | Where upload tickets are kept. |
| `MCP_ENCRYPTION_KEY` | none | A Fernet key. The caller's token in an upload ticket is sealed with it. Required. |
| `MCP_STORE_PREFIX` | `mammoth_mcp` | Keeps this deployment's records apart in a shared Redis. |
| `MCP_HOST`, `MCP_PORT` | `127.0.0.1`, `8270` | Where the server listens. |

## Sign-in

This server signs nobody in. Mammoth's own authorization server does: the OAuth server the Mammoth
API serves. This server is an OAuth resource server only.

1. A client calls `/mcp` with no token. The server answers `401` and points to
   `/.well-known/oauth-protected-resource/mcp`.
2. That document names Mammoth's authorization server (`MAMMOTH_OAUTH_URL`). The client reads the
   server's metadata there and sends the user to it.
3. The user signs in to Mammoth, picks a workspace and a project, and approves. The client asks
   for a token for this server's URI, `<MCP_SERVER_URL>/mcp` (the `resource` parameter, RFC 8707).
4. The client calls `/mcp` with that token. On every request the server asks Mammoth what the token
   is for (`GET /workspaces/current`). The server takes the token only when Mammoth says it is live
   and was issued for this server's URI.
5. Each tool call goes to the Mammoth API with the same token, so the user's permissions apply.

A token belongs to one workspace. A tool call for another workspace is refused. A Mammoth API token
made by hand in Workspace settings was issued for no server, so this server refuses it.

The server keeps no sign-in and no token, with one exception: an upload link holds the caller's
token, sealed, in Redis until the user uploads or 30 minutes pass.

### What Mammoth needs

- The MCP server's URI, `<MCP_SERVER_URL>/mcp`, in mvc-service `const.ini`, section `[oauth]`,
  key `MCP_RESOURCES`. Mammoth issues a token for no other resource.
- `GET /workspaces/current` must return the token's `resource` beside the workspace `id`. Without
  it this server refuses every token.

**Before it works in an environment** below lists every step, in the order to check them.

## Run

### As a container, which needs nothing on the host but Docker

The image is built from this repository, so a deployment never waits for a
release of the SDK. Build it from the **repository root**, which is the build
context:

```bash
cp mammoth-mcp-server/deploy/.dockerignore.example .dockerignore
docker build -f mammoth-mcp-server/deploy/Dockerfile -t mammoth-mcp-server .
docker run --env-file mammoth-mcp-server/deploy/.env -p 8270:8270 mammoth-mcp-server
```

With a Redis of its own, as one stack:

```bash
cp mammoth-mcp-server/.env.example mammoth-mcp-server/deploy/.env   # then set the values
docker compose -f mammoth-mcp-server/deploy/compose.yaml up -d --build
```

The server keeps nothing in memory between requests, so it scales by adding
containers. They share only Redis.

### From a virtual environment

```bash
pip install mammoth-mcp-server
cp .env.example .env        # then set the values
mammoth-mcp-server          # or: uvicorn mammoth_mcp_server.app:create_app --factory
```

### What `deploy/` holds

| File | What it is for |
|---|---|
| `Dockerfile` | The image, built from this repository |
| `compose.yaml` | The server and a Redis, as one stack |
| `.dockerignore.example` | Copy to the repository root before building |
| `mammoth-mcp-server-container.service.example` | systemd, running the container |
| `mammoth-mcp-server.service.example` | systemd, running a virtual environment |
| `nginx.example.conf` | Both server blocks a deployment needs |

## Before it works in an environment

Each of these stops the sign-in on its own, so check them in order.

1. **DNS and the front door** point `MCP_SERVER_URL` at the server's port.
   `deploy/nginx.example.conf` holds the server block.
2. **`MCP_ENCRYPTION_KEY` is set.** It is the only secret this server keeps.
   Nothing else is required that has no default; see **Settings**.
3. **Mammoth knows this server:** `MCP_RESOURCES = <MCP_SERVER_URL>/mcp`, in
   mvc-service `const.ini`, section `[oauth]`. Mammoth issues a token for no
   other resource.
4. **The Mammoth host serves its OAuth metadata where a client looks for it.**
   For an issuer with a path, RFC 8414 puts the document at
   `/.well-known/oauth-authorization-server/api/v2`, and apiv2 serves it at its
   own path, so the front door has to join the two. The second server block in
   `deploy/nginx.example.conf` does it. Check it with:

   ```bash
   curl https://<mammoth host>/.well-known/oauth-authorization-server/api/v2
   ```

   It must answer the document, not `404`.
5. **The web app's OAuth consent page is deployed.** Without it the user lands
   on a page that does not exist, and approves nothing.

Then a client connects to `<MCP_SERVER_URL>/mcp`, and the user signs in to
Mammoth and picks a workspace and a project.

## Tests

```bash
cd mammoth-mcp-server
python -m pytest tests -q
```

The tests reach no server. The SDK client and the tools are real; only the HTTP transport under
the client is replaced.
