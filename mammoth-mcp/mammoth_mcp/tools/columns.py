"""Column transformation tools — add, delete, copy, combine, convert."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from mammoth.exceptions import MammothAPIError, MammothColumnError
from mammoth_mcp.helpers import (
    build_condition,
    error_response,
    format_view_info,
    get_manager,
    log_tool_call,
    resolve_enum,
    success_response,
)
from mammoth_mcp.server import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
@log_tool_call
async def transform_columns(
    ctx: Context,
    view_id: int,
    type: str,
    dataset_id: int | None = None,
    # add_column
    column_name: str | None = None,
    column_type: str = "TEXT",
    # delete_columns
    columns: list[str] | None = None,
    # copy_columns
    copies: list[dict[str, Any]] | None = None,
    # combine_columns
    sources: list[str] | None = None,
    new_column: str | None = None,
    existing_column: str | None = None,
    separator: str = " ",
    condition: dict[str, Any] | None = None,
    # convert_type
    conversions: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Apply column structure transformations to a view.

    Args:
        view_id: The dataview ID.
        type: Operation type — one of: add_column, delete_columns, copy_columns, combine_columns, convert_type.
        dataset_id: The dataset ID (auto-detected if not provided).
        column_name: (add_column) Name for the new column.
        column_type: (add_column, combine_columns) Column type — TEXT, NUMERIC, or DATE (default TEXT).
        columns: (delete_columns) List of column display names to delete.
        copies: (copy_columns) List of copy specs, e.g. [{"source": "Sales", "as": "Sales Copy", "type": "NUMERIC"}].
        sources: (combine_columns) List of column display names to concatenate.
        new_column: (combine_columns) Name for the result column.
        existing_column: (combine_columns) Existing column to overwrite instead of creating new.
        separator: (combine_columns) Separator between values (default space).
        condition: (combine_columns) Optional filter condition as JSON.
        conversions: (convert_type) List of conversion specs, e.g. [{"column": "Sales", "to": "NUMERIC"}].
    """
    try:
        from mammoth import ColumnType

        manager = await get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        op = type.lower()

        if op == "add_column":
            if not column_name:
                return error_response(ValueError("column_name is required for add_column"))
            ct = resolve_enum(ColumnType, column_type)
            view.add_column(column_name, ct)

        elif op == "delete_columns":
            if not columns:
                return error_response(ValueError("columns is required for delete_columns"))
            view.delete_columns(columns)

        elif op == "copy_columns":
            if not copies:
                return error_response(ValueError("copies is required for copy_columns"))
            view.copy_columns(copies)

        elif op == "combine_columns":
            if not sources:
                return error_response(ValueError("sources is required for combine_columns"))
            ct = resolve_enum(ColumnType, column_type)
            cond = build_condition(condition) if condition else None
            view.combine_columns(
                sources=sources,
                new_column=new_column,
                column_type=ct,
                existing_column=existing_column,
                separator=separator,
                condition=cond,
            )

        elif op == "convert_type":
            if not conversions:
                return error_response(ValueError("conversions is required for convert_type"))
            view.convert_type(conversions)

        else:
            return error_response(
                ValueError(f"Unknown type '{type}'. Use: add_column, delete_columns, copy_columns, combine_columns, convert_type")
            )

        return success_response(format_view_info(view), f"{op} applied successfully")
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in transform_columns")
        return error_response(e)
