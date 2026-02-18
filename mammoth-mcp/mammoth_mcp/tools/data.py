"""Data retrieval tool."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import build_condition, error_response, success_response
from mammoth_mcp.server import mcp
from mammoth_mcp.state import ClientManager


def _get_manager(ctx: Context) -> ClientManager:
    return ctx.request_context.lifespan_context["manager"]


@mcp.tool()
def get_data(
    ctx: Context,
    view_id: int,
    limit: int = 100,
    offset: int = 1,
    columns: list[str] | None = None,
    condition: dict[str, Any] | None = None,
    sort: str | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Fetch rows from a view with optional filtering, column selection, and pagination.

    Args:
        view_id: The dataview ID to fetch data from.
        limit: Number of rows to return (default 100, max 400).
        offset: 1-indexed starting row (default 1).
        columns: List of column display names to include (default all).
        condition: Filter condition as a JSON object. Simple: {"column": "Sales", "operator": "GTE", "value": 1000}. Compound: {"logic": "AND", "conditions": [...]}.
        sort: Sort specification string (e.g. "column_name:asc").
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    try:
        manager = _get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)

        cond_obj = build_condition(condition) if condition else None
        result = view.data(
            limit=min(limit, 400),
            offset=offset,
            columns=columns,
            condition=cond_obj,
            sort=sort,
        )
        return success_response(result)
    except Exception as e:
        return error_response(e)
