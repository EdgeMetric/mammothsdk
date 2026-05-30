# CLAUDE.md — mammoth-mcp

MCP server for Mammoth Analytics. Exposes SDK functionality as MCP tools for Claude Desktop, Claude Code, and Claude UI.

## Commands

```bash
# Install
cd mammoth-mcp && poetry install

# Run (stdio mode — local dev)
poetry run mammoth-mcp

# Run (remote mode — server)
MODE=remote PORT=8000 \
  poetry run uvicorn mammoth_mcp.server:create_app --factory --host 0.0.0.0 --port 8000

# Run (remote mode — production)
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

### Tool Loading

All 152 tools are loaded at startup from 24 tool modules — no progressive disclosure.
`server.py` imports all modules via `_ALL_MODULES` list at module load time.

### Key Files

| File | Purpose |
|------|---------|
| `server.py` | FastMCP server, lifespan, ASGI app factory, core tool loading |
| `tool_groups.py` | Legacy — no longer used (all tools loaded at startup) |
| `settings.py` | Pydantic settings from `.env` / environment |
| `instructions.py` | Unified LLM instructions (injected into every MCP session) |
| `helpers.py` | `get_manager`, `handle_errors`, `log_tool_call`, `run_sync`, `success_response` |
| `state.py` | `ClientManager` (wraps SDK client), `UserClientRegistry` (remote mode) |
| `oauth_provider.py` | OAuth 2.0 provider + login page (remote mode only) |
| `token_store.py` | Redis token storage with Fernet encryption (remote mode only) |
| `rate_limit.py` | Per-user rate limiting middleware (remote mode only) |
| `config.py` | `MammothConfig` dataclass for stdio credentials |
| `tools/` | One file per tool module (24 files), loaded by core or group |

### Modes

- **stdio** — local single-user. Credentials from env vars. Used by Claude Desktop / Claude Code.
- **remote** — deployed multi-user. OAuth 2.0 with Redis token store. Used by Claude UI. Each user authenticates with their own Mammoth API key/secret.

### Deployment (Remote Mode)

Single uvicorn instance behind nginx:
```
mcp.mammoth.io/ → localhost:8000
```

Claude UI integration URL: `https://mcp.mammoth.io/mcp`

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
3. If new file: add the module name to `_ALL_MODULES` in `server.py`
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
