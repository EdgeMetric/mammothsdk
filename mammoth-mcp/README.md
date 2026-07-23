# mammoth-mcp

MCP server for [Mammoth Analytics](https://mammoth.io) -- expose data exploration, transformation, and export tools to any MCP-compatible client (Claude Desktop, Claude Code, Claude UI, etc.) via the [Model Context Protocol](https://modelcontextprotocol.io/).

Built on top of the [mammoth-io](https://pypi.org/project/mammoth-io/) Python SDK.

## Architecture: Progressive Disclosure

The server starts with **~15 core tools** for connection, discovery, views, data, pipeline, and help. Additional capabilities (~138 tools) are organized into **4 tool groups** that Claude can enable on demand via meta-tools — no user configuration needed.

| Core Tools (always loaded) | Purpose |
|---|---|
| `test_connection`, `set_project`, `parse_mammoth_url` | Auth & navigation |
| `list_projects`, `list_datasets`, `get_dataset`, `upload_file` | Browse workspace + bring data in |
| `list_views`, `get_view` | Discover views |
| `get_data`, `export_data` | Peek at data + take data out |
| `list_tasks` | Discover pipeline state |
| `get_help` | Guidance |
| `list_tool_groups`, `enable_tool_group` | Progressive disclosure meta-tools |

| Discoverable Group | ~Tools | What's in it |
|---|---|---|
| `transformations` | ~37 | Create/delete views, filter, set values, math, text, dates, joins, pivot, window, AI, SQL, draft mode, undo tasks |
| `import` | ~30 | Webhooks, cloud connectors, file management, batch imports |
| `exports` | ~6 | Database, FTP/SFTP exports, export management, publish |
| `admin` | ~65 | Workspace/user management, dashboards, automations, API keys, AI profiling |

**Total: ~15 core + ~138 group = ~153 tools.** All SDK functions exposed.

### Deployment modes

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

Add the server to your Claude Desktop config file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mammoth": {
      "command": "mammoth-mcp",
      "env": {
        "MAMMOTH_API_KEY": "your-api-key",
        "MAMMOTH_API_SECRET": "your-api-secret",
        "MAMMOTH_WORKSPACE_ID": "2"
      }
    }
  }
}
```

That's it — one server, all capabilities. Claude will enable tool groups as needed.

### Environment Variables (Stdio Mode)

#### Required

| Variable | Description |
|---|---|
| `MAMMOTH_API_KEY` | API key for Mammoth Analytics |
| `MAMMOTH_API_SECRET` | API secret for Mammoth Analytics |
| `MAMMOTH_WORKSPACE_ID` | Workspace ID to connect to |

#### Optional

| Variable | Default | Description |
|---|---|---|
| `MAMMOTH_PROJECT_ID` | *(none)* | Default project ID |
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
ENCRYPTION_KEY=<generate-with-fernet>
LOG_LEVEL=INFO
```

### 3. Start the Server

```bash
# Start (single process)
./start.sh

# Check status
./start.sh status

# Stop
./start.sh stop

# Restart
./start.sh restart
```

Or start manually:

```bash
MODE=remote PORT=8000 \
  poetry run uvicorn mammoth_mcp.server:create_app --factory \
    --host 0.0.0.0 --port 8000
```

### 4. Nginx Reverse Proxy

Route traffic to the MCP server. Replace `<PRIVATE_IP>` with your server's private IP.

```nginx
upstream mammoth_mcp {
    server <PRIVATE_IP>:8000;
    keepalive 32;
}

server {
    listen 443 ssl;
    http2 on;

    server_name mcp.mammoth.io;

    ssl_certificate     /etc/letsencrypt/live/mammoth.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mammoth.io/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://mammoth_mcp;

        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection        "";

        proxy_connect_timeout 75s;
        proxy_read_timeout    86400s;
        proxy_send_timeout    300s;

        proxy_buffering off;
    }
}
```

### 5. Route 53

Create an A record: `mcp.mammoth.io` -> `<EC2 Elastic IP>`

### 6. Add to Claude UI

Register a single integration:

| Integration Name | MCP Server URL |
|---|---|
| Mammoth Analytics | `https://mcp.mammoth.io/mcp` |

The OAuth flow will prompt the user for their Mammoth API credentials.

## Claude UI — End User Installation Guide

Once the remote server is deployed, any user with a Mammoth account can connect it to Claude in a few clicks.

### Step 1: Open Integrations

1. Go to [claude.ai](https://claude.ai) and sign in.
2. Click your **profile icon** (bottom-left) → **Settings** → **Integrations**.

### Step 2: Add the MCP Server

1. Click **"Add more integrations"**.
2. Select **"Add custom integration"** (bottom of the integration catalog).
3. Enter the integration details:
   - **Name**: `Mammoth Analytics`
   - **MCP Server URL**: `https://mcp.mammoth.io/mcp`
4. Click **"Add"**.

### Step 3: Authenticate

1. Claude will open the Mammoth OAuth page in a new window.
2. Enter your Mammoth credentials:
   - **API Key**: Your Mammoth API key
   - **API Secret**: Your Mammoth API secret
   - **Workspace ID**: The workspace you want to connect to
3. Click **"Authorize"** — the window will close and you'll be redirected back to Claude.

### Step 4: Start Using

1. Open a **new chat** in Claude.
2. You should see the Mammoth integration icon in the chat toolbar — click to verify the connection shows as active.
3. Try a prompt like:
   - *"List the projects in my Mammoth workspace"*
   - *"Show me view 12345"* (replace with a real view ID)
   - *"What datasets do I have?"*

Claude will automatically enable tool groups (transformations, import, exports, admin) as needed for your requests.

### Troubleshooting Connection Issues

| Issue | Fix |
|-------|-----|
| Integration not appearing | Refresh the page. Check that the integration is listed in Settings → Integrations. |
| OAuth page won't load | Verify the server is running: `./start.sh status`. Check SSL certificate. |
| "Invalid credentials" error | Double-check your API key, secret, and workspace ID in Mammoth settings. |
| Tools not showing in chat | Start a **new** chat after adding the integration. Existing chats may not pick up new integrations. |
| Connection times out | Check that nginx has `proxy_read_timeout 86400`. |

### Remote Mode Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MODE` | `stdio` | Set to `remote` for OAuth mode |
| `SERVER_URL` | `https://mcp.mammoth.io` | Public URL for OAuth redirects |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `ENCRYPTION_KEY` | *(required)* | Fernet key for credential encryption |
| `AUTH_CODE_TTL` | `300` | Auth code lifetime (seconds) |
| `ACCESS_TOKEN_TTL` | `2592000` | Access token lifetime (30 days) |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server bind port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAMMOTH_BASE_URL` | `https://app.mammoth.io/api/v2` | Default Mammoth API base URL |
| `MAMMOTH_JOB_TIMEOUT` | `120` | Default job timeout (seconds) |

## Available Tools

### Core Tools (~15, always loaded)

#### Connection & Configuration

| Tool | Description |
|---|---|
| `test_connection` | Test that API credentials are valid and the connection works |
| `set_project` | Set the active project ID for subsequent API calls |
| `parse_mammoth_url` | Extract workspace, project, and view IDs from a Mammoth URL |

#### Discovery

| Tool | Description |
|---|---|
| `list_projects` | List all projects in the current workspace |
| `list_datasets` | List all datasets in the current project |
| `get_dataset` | Get detailed info about a dataset, including its views |
| `upload_file` | Upload a CSV or Excel file to create a new dataset |

#### Views

| Tool | Description |
|---|---|
| `list_views` | List all views in a dataset |
| `get_view` | Get detailed metadata for a view, including columns and types |

#### Data

| Tool | Description |
|---|---|
| `get_data` | Fetch rows from a view (max 400 rows per call) |
| `export_data` | Export view data to CSV, S3, email, or another dataset |

#### Pipeline

| Tool | Description |
|---|---|
| `list_tasks` | List all pipeline transformation steps applied to a view |

#### Meta

| Tool | Description |
|---|---|
| `list_tool_groups` | List available tool groups and their enabled/disabled status |
| `enable_tool_group` | Enable a tool group to make its tools available |

#### Help

| Tool | Description |
|---|---|
| `get_help` | Get detailed guidance on a Mammoth topic |

### Transformations Group (~37 tools)

Enabled via `enable_tool_group("transformations")`. Data transformation, view management, and pipeline control.

#### View Management

| Tool | Description |
|---|---|
| `create_view` | Create a new view in a dataset |
| `delete_view` | Delete a view |

#### Column Transformations

| Tool | Description |
|---|---|
| `add_column` | Create a new empty column of a specified data type |
| `delete_columns` | Permanently delete one or more columns from the view |
| `copy_columns` | Duplicate columns with new names and optional type changes |
| `combine_columns` | Merge multiple column values into a single column with a separator |
| `convert_type` | Change column types: TEXT, NUMERIC, DATE, DATETIME |

#### Value Transformations

| Tool | Description |
|---|---|
| `filter_rows` | Keep or remove rows matching a condition |
| `set_values` | Populate or annotate columns with conditional values |
| `math_transform` | Perform arithmetic using column values, constants, and functions |
| `text_transform` | Standardize text — change case and/or trim whitespace |
| `replace_values` | Find and replace text in one or more columns |
| `bulk_replace` | Replace multiple value variations with standardized values |
| `split_column` | Split a text column by delimiter into multiple new columns |
| `substring` | Extract substrings using position-based slicing, delimiters, or regex |

#### Aggregate Transformations

| Tool | Description |
|---|---|
| `pivot` | Group rows and aggregate values (SUM, AVG, COUNT, MAX, MIN) |
| `window` | Row-aware calculations across partitions (ROW_NUMBER, RANK, SUM, LAG, LEAD, etc.) |
| `crosstab` | Pivot a column's distinct values into new column headers with aggregation |
| `unnest` | Transform wide format to long format by stacking columns into rows |
| `fill_missing` | Fill blank cells by copying from the nearest non-empty cell above or below |
| `limit_rows` | Keep only the top or bottom N rows, optionally sorted |
| `discard_duplicates` | Remove rows with identical values across all columns |

#### Advanced Transformations

| Tool | Description |
|---|---|
| `join_views` | Combine with another view using LEFT, RIGHT, INNER, or OUTER join |
| `lookup` | VLOOKUP-style: fetch a single column from a reference view by key |
| `json_extract` | Parse JSON text into structured columns (objects) or rows (lists) |
| `extract_date` | Extract a component from a date column (year, month, day, weekday, etc.) |
| `date_diff` | Calculate time difference between two date columns |
| `increment_date` | Add or subtract time units from a date column |

#### AI & SQL

| Tool | Description |
|---|---|
| `ai_transform` | Use AI to generate a new column based on a natural language prompt |
| `sql_query` | Transform data using natural language intent or raw SQL |

#### Draft Mode & Pipeline

| Tool | Description |
|---|---|
| `delete_task` | Delete (undo) a pipeline transformation step from a view |
| `enter_draft_mode` | Enter draft mode — transformations queue without executing |
| `submit_draft` | Execute all queued draft transformations |
| `discard_draft` | Cancel all queued draft transformations |
| `set_auto_run` | Enable or disable auto-run on a view's pipeline |
| `preview_task` | Preview a transformation's output without applying it |
| `get_pipeline` | Get the full pipeline definition for a view |
| `get_task` | Get the full specification of a single pipeline task |

### Import Group (~30 tools)

Enabled via `enable_tool_group("import")`. Data ingestion from external sources.

#### Webhooks

| Tool | Description |
|---|---|
| `list_webhooks` | List all webhooks in the workspace |
| `create_webhook` | Create a new webhook dataset for receiving data via HTTP |
| `get_webhook` | Get details of a specific webhook |
| `update_webhook` | Update a webhook's settings |
| `delete_webhook` | Delete a webhook |
| `send_webhook_data` | Send data to a webhook endpoint (POST or GET) |

#### Connectors

| Tool | Description |
|---|---|
| `list_connectors` | List available connector types (Salesforce, Snowflake, etc.) |
| `get_connector` | Get details of a connector type |
| `list_active_connectors` | List connectors with active connections |
| `list_connections` | List all connections for a connector type |
| `create_connection` | Create a new connection to a cloud data source |
| `get_connection` | Get details of a connection |
| `update_connection` | Update a connection's configuration |
| `delete_connection` | Delete a connection |
| `list_connector_datasets` | List dataset configurations for a connection |
| `create_connector_dataset` | Create a dataset import from a connection |
| `get_connector_dataset` | Get dataset configuration details |
| `update_connector_dataset` | Update a dataset configuration |
| `delete_connector_dataset` | Delete a dataset configuration |

#### File Management

| Tool | Description |
|---|---|
| `list_files` | List uploaded files in the workspace |
| `get_file` | Get details of an uploaded file |
| `delete_file` | Delete an uploaded file |
| `extract_sheets` | Extract specific sheets from an Excel file into separate datasets |
| `set_file_password` | Unlock a password-protected file |
| `upload_folder` | Upload all files in a local folder |

#### Batches

| Tool | Description |
|---|---|
| `list_batches` | List all batches for a dataset |
| `get_batch` | Get batch details |
| `create_batch` | Create a new batch import for a dataset |
| `update_batch` | Update a batch configuration |
| `delete_batch` | Delete a batch |

### Exports Group (~6 tools)

Enabled via `enable_tool_group("exports")`. Database and file server exports.

| Tool | Description |
|---|---|
| `export_to_database` | Export to Postgres, MySQL, BigQuery, Redshift, Elasticsearch |
| `export_to_ftp` | Export view data to an FTP server |
| `export_to_sftp` | Export view data to an SFTP server |
| `list_exports` | List all exports configured on a view |
| `delete_export` | Delete an export from a view's pipeline |
| `publish_to_db` | Publish view data to internal database for dashboards |

### Admin Group (~65 tools)

Enabled via `enable_tool_group("admin")`. Workspace administration and management.

#### Organization

| Tool | Description |
|---|---|
| `list_folders` | List all folders in the workspace |
| `create_folder` | Create a new folder |
| `delete_folder` | Delete folders |
| `move_to_folder` | Move resources into a folder |
| `get_project` | Get project details |
| `create_project` | Create a new project |
| `update_project` | Update a project's name or color |
| `delete_project` | Delete a project and all contents |
| `add_project_users` | Add users to a project |
| `remove_project_users` | Remove users from a project |
| `browse_project` | Browse a project's contents |
| `create_dataset` | Create a new dataset programmatically |
| `update_dataset` | Update a dataset's metadata |
| `delete_dataset` | Delete a dataset and all its views |
| `browse_dataset` | Browse a dataset's contents |
| `get_file_settings` | Get file-level settings for a dataset |
| `bulk_delete_views` | Delete multiple views at once |

#### Dashboards

| Tool | Description |
|---|---|
| `list_dashboards` | List all dashboards |
| `create_dashboard` | Create a new dashboard |
| `get_dashboard` | Get dashboard details |
| `update_dashboard` | Update a dashboard |
| `delete_dashboard` | Delete a dashboard |
| `share_dashboard` | Share a dashboard with users or publish |
| `list_dashboard_sources` | List available data sources for dashboards |
| `query_dashboard` | Query dashboard draft data using SQL |
| `get_dashboard_analytics` | Get dashboard usage analytics |
| `get_dashboard_by_url` | Look up a dashboard by its public URL |
| `query_published_dashboard` | Query published dashboard data |

#### Automations & Schedules

| Tool | Description |
|---|---|
| `list_automations` | List all automations |
| `create_automation` | Create a new automation |
| `get_automation` | Get automation details |
| `update_automation` | Update an automation |
| `delete_automation` | Delete an automation |
| `list_schedules` | List all schedules |
| `create_schedule` | Create a new schedule |
| `get_schedule` | Get schedule details |
| `update_schedule` | Update a schedule |
| `delete_schedule` | Delete a schedule |

#### Workspace & Users

| Tool | Description |
|---|---|
| `list_workspaces` | List all accessible workspaces |
| `get_workspace` | Get workspace details |
| `update_workspace` | Update workspace settings |
| `list_workspace_users` | List workspace users |
| `get_workspace_user` | Get user details |
| `update_workspace_user` | Update a user's role or settings |
| `get_user_profile` | Get current user's profile |
| `update_user_profile` | Update current user's profile |
| `get_user_preferences` | Get current user's preferences |
| `update_user_preferences` | Update current user's preferences |

#### API Keys & Client Apps

| Tool | Description |
|---|---|
| `list_external_keys` | List external API keys (OpenAI, etc.) |
| `get_external_key` | Get an external key's details |
| `create_external_key` | Create a new external API key |
| `delete_external_key` | Delete an external API key |
| `list_client_apps` | List API tokens / client applications |
| `create_client_app` | Create a new API token pair |
| `get_client_app` | Get client app details |
| `update_client_app` | Update a client app |
| `delete_client_app` | Delete a client app and revoke tokens |

#### AI Features

| Tool | Description |
|---|---|
| `generate_profile` | AI-powered data profiling for a view |
| `get_suggestions` | AI transformation suggestions |
| `generate_data` | Generate synthetic data using AI |
| `get_data_gen_info` | Get data generation metadata |
| `ai_query_gen` | Generate SQL from natural language for connected databases |

#### Monitoring

| Tool | Description |
|---|---|
| `list_activity_logs` | List workspace activity logs (audit trail) |
| `export_activity_logs` | Export activity logs to file |
| `list_reports` | List workspace usage reports |

## Resources

The server exposes two MCP resources:

- `mammoth://config` -- Current connection configuration (no secrets)
- `mammoth://enums` -- All valid enum values for SDK operations

## Related

- [mammoth-io](https://pypi.org/project/mammoth-io/) -- Mammoth Analytics Python SDK
