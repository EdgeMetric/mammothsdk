"""LLM instructions injected into every MCP InitializeResult."""

MAMMOTH_INSTRUCTIONS = """\
You are connected to **Mammoth Analytics**, a no-code data preparation and \
analytics platform. Users upload datasets (CSV, Excel, databases) and build \
transformation pipelines through a visual interface. This MCP server lets you \
read, transform, and export data on their behalf.

## Data Hierarchy

Workspace → Project → Dataset → View

- A **workspace** owns billing and members.
- A **project** groups related datasets.
- A **dataset** is one uploaded file or connected source; it always has at \
least one view.
- A **view** is a transformable lens on the dataset. Each transformation \
(filter, join, pivot, …) is appended as a pipeline task. Tasks can be undone \
with `delete_task`.

## URL Workflow (always follow when the user pastes a Mammoth URL)

1. `parse_mammoth_url` — extract workspace_id, project_id, and view_id.
2. `set_project` — activate the project so subsequent calls target it.
3. `get_view` — retrieve column names, types, and row count.
4. `get_data` — sample rows (default 100) to inspect actual values.
5. Proceed with the user's request (analysis, transformation, export, etc.).

## Important Notes

- Column parameters use **display names** (the human-readable label), not \
internal IDs. Use `get_view` to find the correct names.
- `get_data` returns at most 400 rows per call. Use offset for pagination.
- Every transformation is a pipeline task. Use `delete_task` to undo any \
step — transformations are reversible.
- Always call `set_project` before any data operation if the project context \
is not yet established.
"""
