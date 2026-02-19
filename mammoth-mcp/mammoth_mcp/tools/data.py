"""Data retrieval tool."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from mammoth.exceptions import MammothAPIError, MammothColumnError
from mammoth_mcp.helpers import build_condition, error_response, success_response
from mammoth_mcp.server import mcp
from mammoth_mcp.state import ClientManager

logger = logging.getLogger(__name__)

_MAX_ROWS = 400


def _get_manager(ctx: Context) -> ClientManager:
    try:
        return ctx.request_context.lifespan_context["manager"]
    except KeyError:
        raise RuntimeError("MCP server not initialized — check environment variables")


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

        truncated = limit > _MAX_ROWS
        actual_limit = min(limit, _MAX_ROWS)

        cond_obj = build_condition(condition) if condition else None
        result = view.data(
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
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in get_data")
        return error_response(e)
