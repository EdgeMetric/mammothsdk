# mammoth-mcp

MCP server for [Mammoth Analytics](https://mammoth.io) -- expose data exploration, transformation, and export tools to any MCP-compatible client (Claude Desktop, Claude Code, Claude UI, etc.) via the [Model Context Protocol](https://modelcontextprotocol.io/).

Built on top of the [mammoth-io](https://pypi.org/project/mammoth-io/) Python SDK.

Supports two modes:
- **stdio** -- local single-user mode for Claude Desktop / Claude Code (env var credentials)
- **remote** -- deployed multi-user mode with OAuth 2.0 for Claude UI (each user authenticates with their own Mammoth credentials)

## Installation

```bash
pip install mammoth-mcp
```

Or with Poetry (for development):

```bash
cd mammoth-mcp
poetry install
```

## Quick Start — Stdio Mode (Local)

### Claude Desktop Configuration

Add the following to your Claude Desktop config file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mammoth": {
      "command": "mammoth-mcp",
      "env": {
        "MAMMOTH_API_KEY": "your-api-key",
        "MAMMOTH_API_SECRET": "your-api-secret",
        "MAMMOTH_WORKSPACE_ID": "2",
        "MAMMOTH_PROJECT_ID": "697"
      }
    }
  }
}
```

### Environment Variables (Stdio Mode)

#### Required

| Variable | Description |
|---|---|
| `MAMMOTH_API_KEY` | API key for Mammoth Analytics |
| `MAMMOTH_API_SECRET` | API secret for Mammoth Analytics |
| `MAMMOTH_WORKSPACE_ID` | Workspace ID to connect to |
| `MAMMOTH_PROJECT_ID` | Default project ID |

#### Optional

| Variable | Default | Description |
|---|---|---|
| `MAMMOTH_BASE_URL` | `https://app.mammoth.io/api/v2` | API base URL |
| `MAMMOTH_JOB_TIMEOUT` | `120` | Timeout in seconds for async jobs |

## Remote Deployment (OAuth 2.0)

Deploy as a remote MCP server with OAuth 2.0 authentication for multi-user access via Claude UI.

### Prerequisites

- Python 3.10+, Poetry
- Redis server
- Domain with DNS (e.g. mcp.mammoth.io)
- SSL certificate (Let's Encrypt)

### 1. Clone & Install

```bash
git clone <repo-url>
cd mm-pysdk/mammoth-mcp
poetry install
```

### 2. Configure .env

```bash
cp .env.example .env
```

Edit `.env`:

```
MODE=remote
SERVER_URL=https://mcp.mammoth.io
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
```

### 3. Start Server

```bash
# Using the CLI entry point
poetry run mammoth-mcp

# Or using uvicorn directly (recommended for production)
poetry run uvicorn mammoth_mcp.server:create_app --factory \
    --host 0.0.0.0 --port 8000
```

### 4. Nginx Reverse Proxy

```nginx
server {
    listen 443 ssl http2;
    server_name mcp.mammoth.io;

    ssl_certificate /etc/letsencrypt/live/mcp.mammoth.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcp.mammoth.io/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_buffering off;
    }
}
```

### 5. Route 53

Create an A record: `mcp.mammoth.io` -> `<EC2 Elastic IP>`

### 6. Add to Claude UI

URL: `https://mcp.mammoth.io/mcp`

The OAuth flow will prompt the user for their Mammoth API credentials (API key, secret, workspace ID). Each user gets their own isolated session.

### Remote Mode Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MODE` | `stdio` | Set to `remote` for OAuth mode |
| `SERVER_URL` | `https://mcp.mammoth.io` | Public URL for OAuth redirects |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `AUTH_CODE_TTL` | `300` | Auth code lifetime (seconds) |
| `ACCESS_TOKEN_TTL` | `2592000` | Access token lifetime (30 days) |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server bind port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAMMOTH_BASE_URL` | `https://app.mammoth.io/api/v2` | Default Mammoth API base URL |
| `MAMMOTH_JOB_TIMEOUT` | `120` | Default job timeout (seconds) |

## Available Tools (22)

### Connection & Configuration

| Tool | Description |
|---|---|
| `test_connection` | Test that API credentials are valid and the connection works |
| `set_project` | Set the active project ID for subsequent API calls |
| `parse_mammoth_url` | Extract workspace, project, and view IDs from a Mammoth URL |

### Discovery

| Tool | Description |
|---|---|
| `list_projects` | List all projects in the current workspace |
| `list_datasets` | List all datasets in the current project |
| `get_dataset` | Get detailed info about a dataset, including its views |
| `upload_file` | Upload a CSV or Excel file to create a new dataset |

### Views

| Tool | Description |
|---|---|
| `list_views` | List all views in a dataset |
| `get_view` | Get detailed metadata for a view, including columns and types |
| `create_view` | Create a new view in a dataset |
| `delete_view` | Delete a view |

### Data

| Tool | Description |
|---|---|
| `get_data` | Fetch rows from a view with optional filtering, column selection, and pagination (max 400 rows) |

### Pipeline

| Tool | Description |
|---|---|
| `list_tasks` | List all pipeline transformation steps applied to a view |
| `delete_task` | Delete (undo) a pipeline transformation step from a view |

### Column Transformations

| Tool | Description |
|---|---|
| `transform_columns` | Add, delete, copy, combine, or convert columns. Set `type` to one of: `add_column`, `delete_columns`, `copy_columns`, `combine_columns`, `convert_type` |

### Value Transformations

| Tool | Description |
|---|---|
| `transform_values` | Filter rows, set values, math expressions, text transforms, replace, split, or substring. Set `type` to one of: `filter_rows`, `set_values`, `math`, `text_transform`, `replace_values`, `bulk_replace`, `split_column`, `substring` |

### Aggregate Transformations

| Tool | Description |
|---|---|
| `transform_aggregate` | Pivot, window functions, crosstab, unnest, fill missing, limit rows, or discard duplicates. Set `type` to one of: `pivot`, `window`, `crosstab`, `unnest`, `fill_missing`, `limit_rows`, `discard_duplicates` |

### Advanced Transformations

| Tool | Description |
|---|---|
| `transform_advanced` | Join, lookup, JSON extraction, and date operations. Set `type` to one of: `join`, `lookup`, `json_extract`, `extract_date`, `date_diff`, `increment_date` |

### AI & SQL

| Tool | Description |
|---|---|
| `ai_transform` | Use AI to generate a new column based on a natural language prompt and existing column data |
| `sql_query` | Transform data using natural language intent or raw SQL |

### Export

| Tool | Description |
|---|---|
| `export_data` | Export view data to CSV, S3, email, or another dataset |
| `export_to_database` | Export view data to an external database (Postgres, MySQL, BigQuery, Redshift, Elasticsearch) |

## Resources

The server also exposes two MCP resources:

- `mammoth://config` -- Current connection configuration (no secrets)
- `mammoth://enums` -- All valid enum values for SDK operations

## Related

- [mammoth-io](https://pypi.org/project/mammoth-io/) -- Mammoth Analytics Python SDK
