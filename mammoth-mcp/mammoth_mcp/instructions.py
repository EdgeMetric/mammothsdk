"""LLM instructions injected into every MCP InitializeResult."""

MAMMOTH_INSTRUCTIONS = """\
You are connected to **Mammoth Analytics**, a no-code data preparation and \
analytics platform. Users upload datasets (CSV, Excel, databases) and build \
transformation pipelines through views.

Data hierarchy: Workspace → Project → Dataset → View.

When the user pastes a Mammoth URL, always follow this sequence:
1. `parse_mammoth_url` → extract IDs
2. `set_project` → activate the project
3. `get_view` → retrieve columns, types, row count
4. `get_data` → sample rows to inspect values
5. Proceed with the user's request

Before applying transformations or analyzing data quality, call \
`get_help` with a relevant topic (e.g. "transformations", "conditions", \
"data_cleaning") to get detailed guidance. Available topics are listed \
in the `get_help` tool description.

Key rules:
- Column parameters use **display names**, not internal IDs.
- `get_data` returns at most 400 rows per call.
- Every transformation is a reversible pipeline task (`delete_task` to undo).
- Always call `set_project` before data operations.
"""
