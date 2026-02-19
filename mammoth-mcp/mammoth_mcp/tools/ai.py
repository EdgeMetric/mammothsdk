"""AI-powered transformation tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import (
    format_view_info,
    get_manager,
    handle_errors,
    log_tool_call,
    success_response,
)
from mammoth_mcp.server import mcp


@mcp.tool()
@log_tool_call
@handle_errors
async def ai_transform(
    ctx: Context,
    view_id: int,
    prompt: str,
    context_columns: list[str],
    new_column: str = "AI Result",
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Use AI to generate a new column based on a natural language prompt and existing column data. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        prompt: Natural language instruction for the AI (e.g. "Classify the sentiment of the review").
        context_columns: List of column display names to provide as context to the AI.
        new_column: Name for the AI output column (default "AI Result").
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    view.gen_ai(
        prompt=prompt,
        context_columns=context_columns,
        new_column=new_column,
    )
    return success_response(format_view_info(view), "AI transform applied")


@mcp.tool()
@log_tool_call
@handle_errors
async def sql_query(
    ctx: Context,
    view_id: int,
    intent: str | None = None,
    raw_sql: str | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Transform data using SQL — either natural language intent or raw SQL. Adds a reversible pipeline task (undo with delete_task).

    Provide either `intent` (natural language, auto-generates SQL) or `raw_sql` (direct SQL query).

    Args:
        view_id: The dataview ID.
        intent: Natural language description of the query (e.g. "count employees by department").
        raw_sql: Raw SQL query string to apply directly.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)

    if intent:
        generated_sql = view.generate_sql(intent)
        return success_response(
            {"generated_sql": generated_sql, "view": format_view_info(view)},
            "SQL generated and applied",
        )
    elif raw_sql:
        view.add_sql(raw_sql)
        return success_response(format_view_info(view), "SQL query applied")
    else:
        raise ValueError("Either intent or raw_sql must be provided")
