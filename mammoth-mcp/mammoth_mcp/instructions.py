"""LLM instructions injected into every MCP InitializeResult."""

MAMMOTH_INSTRUCTIONS = """\
You are connected to **Mammoth Analytics**, a no-code data preparation and \
analytics platform. Users upload datasets (CSV, Excel, databases) and build \
transformation pipelines through views.

Data hierarchy: Workspace → Project → Dataset → View.

## Ergonomics — you usually only need a view ID

Most tools only need `view_id`. The `dataset_id` parameter is always optional \
and auto-detected. Do NOT look up or ask for a dataset ID — just pass the \
view ID.

## When the user gives a view ID (e.g. "view 276668")

1. `get_view` — call directly with the view ID. The project and dataset are \
**auto-discovered** automatically. Do NOT call `set_project` or `list_projects`.
2. `get_data` — sample rows (default 100) to inspect values.
3. Proceed with the user's request.

## When the user pastes a Mammoth URL

1. `parse_mammoth_url` → extract IDs
2. `set_project` → activate the project from the URL
3. `get_view` → retrieve columns, types, row count
4. `get_data` → sample rows to inspect values
5. Proceed with the user's request

Before applying transformations or analyzing data quality, call \
`get_help` with a relevant topic (e.g. "transformations", "conditions", \
"data_cleaning") to get detailed guidance.

## Key rules
- Column parameters use **display names**, not internal IDs.
- `get_data` returns at most 400 rows per call. Use offset for pagination. \
Check the `row_count` from `get_view` to understand total data size.
- Every transformation is a reversible pipeline task (`delete_task` to undo).
- Do NOT call `set_project` or `list_projects` when the user provides a \
view ID directly — the project is resolved automatically.
- Call each transformation tool directly by name (e.g. `filter_rows`, \
`pivot`, `join_views`) — there are no wrapper or mega-tools.

## Error recovery
- If a tool returns `success: false`, check the `recovery_hint` field for \
guidance. Common fix: call `get_view` to refresh column names before retrying.
- Column names change after transformations — always verify with `get_view`.
- If unsure about valid enum values (operators, column types, etc.), read the \
`mammoth://enums` resource.

## Safety tips
- Before destructive experiments, use `create_view` with `clone_from` to work \
on a copy.
- Apply `pivot` and `crosstab` **last** — they reshape the data and make \
row-level columns unavailable.
- Don't reference old column names after transformations that rename or \
restructure columns.
"""
