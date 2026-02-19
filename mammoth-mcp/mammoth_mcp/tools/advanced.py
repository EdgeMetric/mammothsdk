"""Advanced transformation tools — join, lookup, JSON, date operations."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth import DateComponent, DateDiffUnit, JoinType, JsonType
from mammoth_mcp.helpers import (
    format_view_info,
    get_manager,
    handle_errors,
    log_tool_call,
    resolve_enum,
    success_response,
)
from mammoth_mcp.server import mcp


# ── join_views ────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def join_views(
    ctx: Context,
    view_id: int,
    foreign_view_id: int,
    join_type: str,
    on: list[dict[str, str]],
    select: list[str] | list[dict[str, str]],
    column_prefix: str | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Combine with another view using LEFT, RIGHT, INNER, or OUTER join. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        foreign_view_id: ID of the view to join with.
        join_type: Join type — INNER, LEFT, RIGHT, or OUTER.
        on: Join keys, e.g. [{"left": "Customer ID", "right": "Customer ID"}].
        select: Columns to bring from foreign view — list of names or [{"column": "Name", "alias": "Customer Name"}].
        column_prefix: Prefix for joined columns (optional).
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    jt = resolve_enum(JoinType, join_type)
    # Try to get the foreign view for display-name resolution
    try:
        foreign_view = manager.get_view(foreign_view_id)
        view.join(
            foreign_view=foreign_view,
            join_type=jt,
            on=on,
            select=select,
            column_prefix=column_prefix,
        )
    except Exception:
        view.join(
            foreign_view=foreign_view_id,
            join_type=jt,
            on=on,
            select=select,
            column_prefix=column_prefix,
        )
    return success_response(format_view_info(view), "join_views applied successfully")


# ── lookup ────────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def lookup(
    ctx: Context,
    view_id: int,
    source: str,
    lookup_view_id: int,
    key: str,
    value: str,
    new_column: str | None = None,
    existing_column: str | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """VLOOKUP-style: fetch a single column from a reference view by matching a shared key. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        source: Source column display name in this view.
        lookup_view_id: ID of the view to look up from.
        key: Key column name in the lookup view.
        value: Value column name in the lookup view.
        new_column: Name for the result column.
        existing_column: Existing column to overwrite.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    view.lookup(
        source=source,
        lookup_view_id=lookup_view_id,
        key=key,
        value=value,
        new_column=new_column,
        existing_column=existing_column,
    )
    return success_response(format_view_info(view), "lookup applied successfully")


# ── json_extract ──────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def json_extract(
    ctx: Context,
    view_id: int,
    column: str,
    json_type: str = "OBJECT",
    keys: list[str] | None = None,
    extractions: list[dict[str, str]] | None = None,
    keep_source: bool = False,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Parse JSON text into structured columns (objects) or rows (lists). Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        column: Source column display name containing JSON.
        json_type: JSON structure type — OBJECT or LIST (default OBJECT).
        keys: Simple list of keys to extract as TEXT columns.
        extractions: Advanced extraction specs, e.g. [{"key": "name", "as": "Name", "type": "TEXT"}].
        keep_source: Keep the original JSON column (default false).
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    jt_enum = resolve_enum(JsonType, json_type)
    view.json_extract(
        column=column,
        json_type=jt_enum,
        keys=keys,
        extractions=extractions,
        keep_source=keep_source,
    )
    return success_response(format_view_info(view), "json_extract applied successfully")


# ── extract_date ──────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def extract_date(
    ctx: Context,
    view_id: int,
    column: str,
    component: str,
    new_column: str | None = None,
    existing_column: str | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Extract a component from a date column (year, month, day, hour, weekday, quarter, etc.). Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        column: Source date column display name.
        component: Date component — year, month, day, hour, minute, second, week, quarter, weekday_text, month_text, etc.
        new_column: Name for the result column.
        existing_column: Existing column to overwrite.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    dc = resolve_enum(DateComponent, component)
    view.extract_date(
        column=column,
        component=dc,
        new_column=new_column,
        existing_column=existing_column,
    )
    return success_response(format_view_info(view), "extract_date applied successfully")


# ── date_diff ─────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def date_diff(
    ctx: Context,
    view_id: int,
    component: str,
    start: str,
    end: str,
    new_column: str | None = None,
    existing_column: str | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Calculate time difference between two date columns. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        component: Difference unit — YEAR, MONTH, DAY, HOUR, MINUTE, SECOND.
        start: Start date column display name.
        end: End date column display name.
        new_column: Name for the result column.
        existing_column: Existing column to overwrite.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    ddu = resolve_enum(DateDiffUnit, component)
    view.date_diff(
        component=ddu,
        start=start,
        end=end,
        new_column=new_column,
        existing_column=existing_column,
    )
    return success_response(format_view_info(view), "date_diff applied successfully")


# ── increment_date ────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def increment_date(
    ctx: Context,
    view_id: int,
    column: str,
    delta: dict[str, int],
    new_column: str | None = None,
    existing_column: str | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Add or subtract time units from a date column. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        column: Source date column display name.
        delta: Delta spec, e.g. {"DAYS": 30} or {"MONTHS": -1, "YEARS": 2}.
        new_column: Name for the result column.
        existing_column: Existing column to overwrite.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    view.increment_date(
        column=column,
        delta=delta,
        new_column=new_column,
        existing_column=existing_column,
    )
    return success_response(format_view_info(view), "increment_date applied successfully")
