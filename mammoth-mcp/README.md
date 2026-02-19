# mammoth-mcp

MCP server for [Mammoth Analytics](https://mammoth.io) -- expose data exploration, transformation, and export tools to any MCP-compatible client (Claude Desktop, Claude Code, etc.) via the [Model Context Protocol](https://modelcontextprotocol.io/).

Built on top of the [mammoth-io](https://pypi.org/project/mammoth-io/) Python SDK.

## Installation

```bash
pip install mammoth-mcp
```

## Claude Desktop Configuration

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

## Environment Variables

### Required

| Variable | Description |
|---|---|
| `MAMMOTH_API_KEY` | API key for Mammoth Analytics |
| `MAMMOTH_API_SECRET` | API secret for Mammoth Analytics |
| `MAMMOTH_WORKSPACE_ID` | Workspace ID to connect to |
| `MAMMOTH_PROJECT_ID` | Default project ID |

### Optional

| Variable | Default | Description |
|---|---|---|
| `MAMMOTH_BASE_URL` | `https://app.mammoth.io/api/v2` | API base URL |
| `MAMMOTH_JOB_TIMEOUT` | `120` | Timeout in seconds for async jobs |

## Available Tools

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
