"""Aggregate transformation tools — pivot, window, crosstab, unnest, fill, limit, dedup."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import (
    build_condition,
    error_response,
    format_view_info,
    resolve_enum,
    success_response,
)
from mammoth_mcp.server import mcp
from mammoth_mcp.state import ClientManager


def _get_manager(ctx: Context) -> ClientManager:
    return ctx.request_context.lifespan_context["manager"]


@mcp.tool()
def transform_aggregate(
    ctx: Context,
    view_id: int,
    type: str,
    dataset_id: int | None = None,
    # pivot
    group_by: list[str] | None = None,
    aggregations: list[dict[str, Any]] | None = None,
    condition: dict[str, Any] | None = None,
    # window
    function: str | None = None,
    column: str | None = None,
    new_column: str | None = None,
    column_type: str = "NUMERIC",
    existing_column: str | None = None,
    partition_by: list[str] | None = None,
    order_by: list[list[str]] | None = None,
    range_type: str = "UNBOUNDED",
    # crosstab
    rows: list[str] | None = None,
    pivot_column: str | None = None,
    select: dict[str, Any] | None = None,
    # unnest
    columns: list[str] | None = None,
    label_column: str = "Label",
    value_column: str = "Value",
    # fill_missing
    direction: str | None = None,
    # limit_rows
    n: int | None = None,
    bottom: bool = False,
    # discard_duplicates
    ignore_columns: list[str] | None = None,
) -> dict[str, Any]:
    """Apply aggregation and reshaping transformations to a view.

    Args:
        view_id: The dataview ID.
        type: Operation type — one of: pivot, window, crosstab, unnest, fill_missing, limit_rows, discard_duplicates.
        dataset_id: The dataset ID (auto-detected if not provided).
        group_by: (pivot) List of column names to group by.
        aggregations: (pivot) List of aggregation specs, e.g. [{"column": "Sales", "function": "SUM", "as": "Total Sales"}].
        condition: (pivot) Optional filter condition as JSON.
        function: (window) Window function — ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, SUM, AVG, MIN, MAX, COUNT, FIRST_VALUE, LAST_VALUE, etc.
        column: (window, fill_missing) Source column display name.
        new_column: (window) Name for the result column.
        column_type: (window) Column type for new column (default NUMERIC).
        existing_column: (window) Existing column to overwrite.
        partition_by: (window, fill_missing as single string) List of column names to partition by.
        order_by: (window, fill_missing, limit_rows) Sort spec as list of [column, direction] pairs, e.g. [["Sales", "DESC"]].
        range_type: (window) Window range — UNBOUNDED or RUNNING (default UNBOUNDED).
        rows: (crosstab) List of column names for row grouping.
        pivot_column: (crosstab) Column whose values become new columns.
        select: (crosstab) Aggregation spec, e.g. {"column": "Sales", "function": "SUM"}.
        columns: (unnest) List of column names to unpivot.
        label_column: (unnest) Name for the label column (default "Label").
        value_column: (unnest) Name for the value column (default "Value").
        direction: (fill_missing) Fill direction — FIRST_VALUE or LAST_VALUE.
        n: (limit_rows) Number of rows to keep.
        bottom: (limit_rows) Keep bottom N instead of top N (default false).
        ignore_columns: (discard_duplicates) Columns to ignore when detecting duplicates.
    """
    try:
        from mammoth import (
            ColumnType,
            FillDirection,
            SortDirection,
            WindowFunction,
            WindowRange,
        )

        manager = _get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        op = type.lower()

        if op == "pivot":
            if not group_by or not aggregations:
                return error_response(ValueError("group_by and aggregations are required for pivot"))
            cond = build_condition(condition) if condition else None
            view.pivot(group_by=group_by, aggregations=aggregations, condition=cond)

        elif op == "window":
            if not function:
                return error_response(ValueError("function is required for window"))
            wf = resolve_enum(WindowFunction, function)
            ct = resolve_enum(ColumnType, column_type)
            wr = resolve_enum(WindowRange, range_type)
            view.window(
                function=wf,
                column=column,
                new_column=new_column,
                column_type=ct,
                existing_column=existing_column,
                partition_by=partition_by,
                order_by=order_by,
                range_type=wr,
            )

        elif op == "crosstab":
            if not rows or not pivot_column or not select:
                return error_response(ValueError("rows, pivot_column, and select are required for crosstab"))
            view.crosstab(rows=rows, pivot_column=pivot_column, select=select)

        elif op == "unnest":
            if not columns:
                return error_response(ValueError("columns is required for unnest"))
            view.unnest(columns=columns, label_column=label_column, value_column=value_column)

        elif op == "fill_missing":
            if not column or not direction:
                return error_response(ValueError("column and direction are required for fill_missing"))
            fd = resolve_enum(FillDirection, direction)
            pb = partition_by[0] if partition_by else None
            view.fill_missing(column=column, direction=fd, partition_by=pb, order_by=order_by)

        elif op == "limit_rows":
            if n is None:
                return error_response(ValueError("n is required for limit_rows"))
            view.limit_rows(n=n, bottom=bottom, order_by=order_by)

        elif op == "discard_duplicates":
            view.discard_duplicates(ignore_columns=ignore_columns)

        else:
            return error_response(
                ValueError(
                    f"Unknown type '{type}'. Use: pivot, window, crosstab, unnest, "
                    "fill_missing, limit_rows, discard_duplicates"
                )
            )

        return success_response(format_view_info(view), f"{op} applied successfully")
    except Exception as e:
        return error_response(e)
