"""Aggregate transformation tools — pivot, window, crosstab, unnest, fill, limit, dedup."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth import (
    ColumnType,
    FillDirection,
    WindowFunction,
    WindowRange,
)
from mammoth_mcp.helpers import (
    build_condition,
    format_view_info,
    get_manager,
    handle_errors,
    log_tool_call,
    resolve_enum,
    run_sync,
    success_response,
)
from mammoth_mcp.server import mcp


# ── pivot ─────────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def pivot(
    ctx: Context,
    view_id: int,
    group_by: list[str],
    aggregations: list[dict[str, Any]],
    condition: dict[str, Any] | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Group rows and aggregate values (SUM, AVG, COUNT, MAX, MIN). IMPORTANT: Apply LAST — reshapes the data so original row-level columns become unavailable for subsequent tasks. Complete all filtering, calculations, and column operations first. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        group_by: List of column names to group by.
        aggregations: List of aggregation specs, e.g. [{"column": "Sales", "function": "SUM", "as": "Total Sales"}].
        condition: Optional filter condition as JSON.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    cond = build_condition(condition) if condition else None
    await run_sync(view.pivot, group_by=group_by, aggregations=aggregations, condition=cond)
    return success_response(format_view_info(view), "pivot applied successfully")


# ── window ────────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def window(
    ctx: Context,
    view_id: int,
    function: str,
    column: str | None = None,
    new_column: str | None = None,
    column_type: str = "NUMERIC",
    existing_column: str | None = None,
    partition_by: list[str] | None = None,
    order_by: list[list[str]] | None = None,
    range_type: str = "UNBOUNDED",
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Row-aware calculations across partitions without collapsing rows (ROW_NUMBER, RANK, SUM, AVG, LAG, LEAD, etc.). Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        function: Window function — ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, SUM, AVG, MIN, MAX, COUNT, FIRST_VALUE, LAST_VALUE, etc.
        column: Source column display name.
        new_column: Name for the result column.
        column_type: Column type for new column (default NUMERIC).
        existing_column: Existing column to overwrite.
        partition_by: List of column names to partition by.
        order_by: Sort spec as list of [column, direction] pairs, e.g. [["Sales", "DESC"]].
        range_type: Window range — UNBOUNDED or RUNNING (default UNBOUNDED).
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    wf = resolve_enum(WindowFunction, function)
    ct = resolve_enum(ColumnType, column_type)
    wr = resolve_enum(WindowRange, range_type)
    await run_sync(
        view.window,
        function=wf,
        column=column,
        new_column=new_column,
        column_type=ct,
        existing_column=existing_column,
        partition_by=partition_by,
        order_by=order_by,
        range_type=wr,
    )
    return success_response(format_view_info(view), "window applied successfully")


# ── crosstab ──────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def crosstab(
    ctx: Context,
    view_id: int,
    rows: list[str],
    pivot_column: str,
    select: dict[str, Any],
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Pivot a column's distinct values into new column headers with aggregation. IMPORTANT: Apply LAST — reshapes the data so original row-level columns become unavailable for subsequent tasks. Complete all filtering and calculations first. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        rows: List of column names for row grouping.
        pivot_column: Column whose values become new columns.
        select: Aggregation spec, e.g. {"column": "Sales", "function": "SUM"}.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    await run_sync(view.crosstab, rows=rows, pivot_column=pivot_column, select=select)
    return success_response(format_view_info(view), "crosstab applied successfully")


# ── unnest ────────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def unnest(
    ctx: Context,
    view_id: int,
    columns: list[str],
    label_column: str = "Label",
    value_column: str = "Value",
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Transform wide format to long format by stacking columns into rows (unpivot). Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        columns: List of column names to unpivot.
        label_column: Name for the label column (default "Label").
        value_column: Name for the value column (default "Value").
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    await run_sync(view.unnest, columns=columns, label_column=label_column, value_column=value_column)
    return success_response(format_view_info(view), "unnest applied successfully")


# ── fill_missing ──────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def fill_missing(
    ctx: Context,
    view_id: int,
    column: str,
    direction: str,
    partition_by: str | None = None,
    order_by: list[list[str]] | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Fill blank cells by copying from the nearest non-empty cell above (LAST_VALUE) or below (FIRST_VALUE). Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        column: Column to fill.
        direction: Fill direction — FIRST_VALUE or LAST_VALUE.
        partition_by: Column name to group fills within (optional).
        order_by: Sort spec as list of [column, direction] pairs (optional).
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    fd = resolve_enum(FillDirection, direction)
    await run_sync(view.fill_missing, column=column, direction=fd, partition_by=partition_by, order_by=order_by)
    return success_response(format_view_info(view), "fill_missing applied successfully")


# ── limit_rows ────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def limit_rows(
    ctx: Context,
    view_id: int,
    n: int,
    bottom: bool = False,
    order_by: list[list[str]] | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Keep only the top or bottom N rows, optionally sorted. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        n: Number of rows to keep.
        bottom: Keep bottom N instead of top N (default false).
        order_by: Sort spec as list of [column, direction] pairs (optional).
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    await run_sync(view.limit_rows, n=n, bottom=bottom, order_by=order_by)
    return success_response(format_view_info(view), "limit_rows applied successfully")


# ── discard_duplicates ────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def discard_duplicates(
    ctx: Context,
    view_id: int,
    ignore_columns: list[str] | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Remove rows with identical values across all columns. Optionally ignore specific columns. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        ignore_columns: Columns to ignore when detecting duplicates (optional).
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    await run_sync(view.discard_duplicates, ignore_columns=ignore_columns)
    return success_response(format_view_info(view), "discard_duplicates applied successfully")
