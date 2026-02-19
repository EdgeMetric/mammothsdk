"""Advanced transformation tools — join, lookup, JSON, date operations."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from mammoth.exceptions import MammothAPIError, MammothColumnError
from mammoth_mcp.helpers import (
    error_response,
    format_view_info,
    resolve_enum,
    success_response,
)
from mammoth_mcp.server import mcp
from mammoth_mcp.state import ClientManager

logger = logging.getLogger(__name__)


def _get_manager(ctx: Context) -> ClientManager:
    try:
        return ctx.request_context.lifespan_context["manager"]
    except KeyError:
        raise RuntimeError("MCP server not initialized — check environment variables")


@mcp.tool()
def transform_advanced(
    ctx: Context,
    view_id: int,
    type: str,
    dataset_id: int | None = None,
    # join
    foreign_view_id: int | None = None,
    join_type: str | None = None,
    on: list[dict[str, str]] | None = None,
    select: list[str] | list[dict[str, str]] | None = None,
    column_prefix: str | None = None,
    # lookup
    source: str | None = None,
    lookup_view_id: int | None = None,
    key: str | None = None,
    value: str | None = None,
    new_column: str | None = None,
    existing_column: str | None = None,
    # json_extract
    column: str | None = None,
    json_type: str = "OBJECT",
    keys: list[str] | None = None,
    extractions: list[dict[str, str]] | None = None,
    keep_source: bool = False,
    # extract_date
    component: str | None = None,
    # date_diff
    start: str | None = None,
    end: str | None = None,
    # increment_date
    delta: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Apply advanced transformations — join, lookup, JSON extraction, and date operations.

    Args:
        view_id: The dataview ID.
        type: Operation type — one of: join, lookup, json_extract, extract_date, date_diff, increment_date.
        dataset_id: The dataset ID (auto-detected if not provided).
        foreign_view_id: (join) ID of the view to join with.
        join_type: (join) Join type — INNER, LEFT, RIGHT, or OUTER.
        on: (join) Join keys, e.g. [{"left": "Customer ID", "right": "Customer ID"}].
        select: (join) Columns to bring from foreign view — list of names or [{"column": "Name", "alias": "Customer Name"}].
        column_prefix: (join) Prefix for joined columns (optional).
        source: (lookup) Source column display name in this view.
        lookup_view_id: (lookup) ID of the view to look up from.
        key: (lookup) Key column name in the lookup view.
        value: (lookup) Value column name in the lookup view.
        new_column: (lookup, json_extract, extract_date, date_diff, increment_date) Name for the result column.
        existing_column: (lookup, extract_date, date_diff, increment_date) Existing column to overwrite.
        column: (json_extract, extract_date, increment_date) Source column display name.
        json_type: (json_extract) JSON structure type — OBJECT or LIST (default OBJECT).
        keys: (json_extract) Simple list of keys to extract as TEXT columns.
        extractions: (json_extract) Advanced extraction specs, e.g. [{"key": "name", "as": "Name", "type": "TEXT"}].
        keep_source: (json_extract) Keep the original JSON column (default false).
        component: (extract_date, date_diff) Date component — year, month, day, hour, minute, second, week, quarter, weekday_text, month_text, etc. For date_diff: YEAR, MONTH, DAY, HOUR, MINUTE, SECOND.
        start: (date_diff) Start date column display name.
        end: (date_diff) End date column display name.
        delta: (increment_date) Delta spec, e.g. {"DAYS": 30} or {"MONTHS": -1, "YEARS": 2}.
    """
    try:
        from mammoth import DateComponent, DateDiffUnit, JoinType, JsonType

        manager = _get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        op = type.lower()

        if op == "join":
            if not foreign_view_id or not join_type or not on or not select:
                return error_response(
                    ValueError("foreign_view_id, join_type, on, and select are required for join")
                )
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
                # Fall back to using raw view ID
                view.join(
                    foreign_view=foreign_view_id,
                    join_type=jt,
                    on=on,
                    select=select,
                    column_prefix=column_prefix,
                )

        elif op == "lookup":
            if not source or not lookup_view_id or not key or not value:
                return error_response(
                    ValueError("source, lookup_view_id, key, and value are required for lookup")
                )
            view.lookup(
                source=source,
                lookup_view_id=lookup_view_id,
                key=key,
                value=value,
                new_column=new_column,
                existing_column=existing_column,
            )

        elif op == "json_extract":
            if not column:
                return error_response(ValueError("column is required for json_extract"))
            jt_enum = resolve_enum(JsonType, json_type)
            view.json_extract(
                column=column,
                json_type=jt_enum,
                keys=keys,
                extractions=extractions,
                keep_source=keep_source,
            )

        elif op == "extract_date":
            if not column or not component:
                return error_response(ValueError("column and component are required for extract_date"))
            dc = resolve_enum(DateComponent, component)
            view.extract_date(
                column=column,
                component=dc,
                new_column=new_column,
                existing_column=existing_column,
            )

        elif op == "date_diff":
            if not component or not start or not end:
                return error_response(ValueError("component, start, and end are required for date_diff"))
            ddu = resolve_enum(DateDiffUnit, component)
            view.date_diff(
                component=ddu,
                start=start,
                end=end,
                new_column=new_column,
                existing_column=existing_column,
            )

        elif op == "increment_date":
            if not column or not delta:
                return error_response(ValueError("column and delta are required for increment_date"))
            view.increment_date(
                column=column,
                delta=delta,
                new_column=new_column,
                existing_column=existing_column,
            )

        else:
            return error_response(
                ValueError(
                    f"Unknown type '{type}'. Use: join, lookup, json_extract, "
                    "extract_date, date_diff, increment_date"
                )
            )

        return success_response(format_view_info(view), f"{op} applied successfully")
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in transform_advanced")
        return error_response(e)
