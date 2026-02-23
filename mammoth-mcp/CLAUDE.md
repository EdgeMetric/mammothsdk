# CLAUDE.md — mammoth-mcp

MCP server for Mammoth Analytics. Exposes SDK functionality as MCP tools for Claude Desktop, Claude Code, and Claude UI.

## Commands

```bash
# Install
cd mammoth-mcp && poetry install

# Run single profile (stdio mode — local dev)
MCP_PROFILE=transformations poetry run mammoth-mcp

# Run single profile (remote mode — server)
MCP_PROFILE=transformations MODE=remote PORT=9000 \
  poetry run uvicorn mammoth_mcp.server:create_app --factory --host 0.0.0.0 --port 9000

# Run all 3 profiles (remote mode — production)
./start.sh              # start
./start.sh status       # check
./start.sh stop         # stop
./start.sh restart      # restart

# Lint & format
black mammoth_mcp/ && ruff check mammoth_mcp/

# Tests
pytest tests/ -q
```

## Architecture

### 3 Server Profiles

Split into 3 profiles to keep tool counts manageable (~50 each instead of 135 combined):

| Profile | Tools | Purpose |
|---------|-------|---------|
| `transformations` | ~57 | Data exploration, transformation, export, draft mode |
| `import` | ~43 | Webhooks, cloud connectors, file management, batches |
| `admin` | ~85 | Organization, dashboards, automations, users, API keys |

Profile is set via `MCP_PROFILE` env var. `start.sh` launches all 3 with separate ports.

### Key Files

| File | Purpose |
|------|---------|
| `server.py` | FastMCP server, lifespan, ASGI app factory, profile-driven tool loading |
| `settings.py` | Pydantic settings from `.env` / environment |
| `instructions.py` | Per-profile LLM instructions (injected into every MCP session) |
| `helpers.py` | `get_manager`, `handle_errors`, `log_tool_call`, `run_sync`, `success_response` |
| `state.py` | `ClientManager` (wraps SDK client), `UserClientRegistry` (remote mode) |
| `oauth_provider.py` | OAuth 2.0 provider + login page (remote mode only) |
| `token_store.py` | Redis token storage with Fernet encryption (remote mode only) |
| `rate_limit.py` | Per-user rate limiting middleware (remote mode only) |
| `config.py` | `MammothConfig` dataclass for stdio credentials |
| `tools/` | One file per tool module (23 files), loaded by profile |

### Tool Loading

`server.py` has a `TOOL_PROFILES` dict mapping profile names to lists of tool module names. At import time, it loads the modules for the active profile via `importlib.import_module()`.

### Modes

- **stdio** — local single-user. Credentials from env vars. Used by Claude Desktop / Claude Code.
- **remote** — deployed multi-user. OAuth 2.0 with Redis token store. Used by Claude UI. Each user authenticates with their own Mammoth API key/secret.

### Deployment (Remote Mode)

3 uvicorn instances behind nginx path-based proxy:
```
mcp.mammoth.io/transformations/ → localhost:9000
mcp.mammoth.io/import/          → localhost:9001
mcp.mammoth.io/admin/           → localhost:9002
```

Each profile gets its own `SERVER_URL` (base + `/profile`) for correct OAuth routing. See `nginx.example.conf` and `start.sh`.

Claude UI integration URLs:
- `https://mcp.mammoth.io/transformations/mcp`
- `https://mcp.mammoth.io/import/mcp`
- `https://mcp.mammoth.io/admin/mcp`

## Adding a New Tool

1. Add the tool function to the appropriate file in `tools/` (or create a new file)
2. Follow the standard pattern:
   ```python
   from mammoth_mcp.helpers import get_manager, handle_errors, log_tool_call, run_sync, success_response
   from mammoth_mcp.server import mcp

   @mcp.tool()
   @log_tool_call
   @handle_errors
   async def tool_name(ctx: Context, param: type) -> dict[str, Any]:
       """Description. Args: param: description."""
       manager = await get_manager(ctx)
       result = await run_sync(manager.client.sub_client.method, param)
       return success_response(result, "message")
   ```
3. If new file: add module name to the appropriate profile(s) in `TOOL_PROFILES` in `server.py`
4. Update `instructions.py` if the tool needs special LLM guidance
5. Update `tools/help.py` if adding a new help topic

## Conventions

- All SDK calls go through `run_sync()` to avoid blocking the asyncio event loop
- `get_manager(ctx)` returns the `ClientManager` (handles both stdio and remote mode)
- `handle_errors` decorator catches SDK exceptions and returns structured error responses
- `log_tool_call` decorator logs tool invocations with timing
- `success_response(data, message)` formats consistent tool responses
- Tool docstrings become the tool's description in MCP — keep them concise
- Use `Args:` format in docstrings for parameter descriptions (FastMCP parses these)
