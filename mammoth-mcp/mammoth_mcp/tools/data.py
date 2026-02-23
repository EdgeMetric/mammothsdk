"""Data retrieval tool."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import (
    build_condition,
    get_manager,
    handle_errors,
    log_tool_call,
    run_sync,
    success_response,
)
from mammoth_mcp.server import mcp

_MAX_ROWS = 400


@mcp.tool()
@log_tool_call
@handle_errors
async def get_data(
    ctx: Context,
    view_id: int,
    limit: int = 100,
    offset: int = 1,
    columns: list[str] | None = None,
    condition: dict[str, Any] | None = None,
    sort: str | None = None,
) -> dict[str, Any]:
    """Fetch actual row data from a view with optional filtering, column selection, and pagination. Returns row values, not metadata — use get_view for column info and row count.

    Args:
        view_id: The dataview ID to fetch data from.
        limit: Number of rows to return (default 100, max 400).
        offset: 1-indexed starting row (default 1).
        columns: List of column display names to include (default all).
        condition: Filter condition as a JSON object. Simple: {"column": "Sales", "operator": "GTE", "value": 1000}. Compound: {"logic": "AND", "conditions": [...]}.
        sort: Sort specification string (e.g. "column_name:asc").
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)

    truncated = limit > _MAX_ROWS
    actual_limit = min(limit, _MAX_ROWS)

    cond_obj = build_condition(condition) if condition else None
    result = await run_sync(
        view.data,
        limit=actual_limit,
        offset=offset,
        columns=columns,
        condition=cond_obj,
        sort=sort,
    )

    message = None
    if truncated:
        message = f"(Note: results limited to {_MAX_ROWS} rows. Request fewer rows for faster responses.)"

    return success_response(result, message)
