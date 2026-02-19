"""Column transformation tools — add, delete, copy, combine, convert."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from mammoth import ColumnType
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


# ── add_column ────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
async def add_column(
    ctx: Context,
    view_id: int,
    column_name: str,
    column_type: str = "TEXT",
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Create a new empty column of a specified data type.

    Args:
        view_id: The dataview ID.
        column_name: Name for the new column.
        column_type: Column type — TEXT, NUMERIC, or DATE (default TEXT).
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    try:
        manager = await get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        ct = resolve_enum(ColumnType, column_type)
        view.add_column(column_name, ct)
        return success_response(format_view_info(view), "add_column applied successfully")
    except (MammothAPIError, MammothColumnError, ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in add_column")
        return error_response(e)


# ── delete_columns ────────────────────────────────────────────


@mcp.tool()
@log_tool_call
async def delete_columns(
    ctx: Context,
    view_id: int,
    columns: list[str],
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Permanently delete one or more columns from the view.

    Args:
        view_id: The dataview ID.
        columns: List of column display names to delete.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    try:
        manager = await get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        view.delete_columns(columns)
        return success_response(format_view_info(view), "delete_columns applied successfully")
    except (MammothAPIError, MammothColumnError, ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in delete_columns")
        return error_response(e)


# ── copy_columns ──────────────────────────────────────────────


@mcp.tool()
@log_tool_call
async def copy_columns(
    ctx: Context,
    view_id: int,
    copies: list[dict[str, Any]],
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Duplicate columns — create copies with new names and optional type changes.

    Args:
        view_id: The dataview ID.
        copies: List of copy specs, e.g. [{"source": "Sales", "as": "Sales Copy", "type": "NUMERIC"}].
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    try:
        manager = await get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        view.copy_columns(copies)
        return success_response(format_view_info(view), "copy_columns applied successfully")
    except (MammothAPIError, MammothColumnError, ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in copy_columns")
        return error_response(e)


# ── combine_columns ───────────────────────────────────────────


@mcp.tool()
@log_tool_call
async def combine_columns(
    ctx: Context,
    view_id: int,
    sources: list[str],
    new_column: str | None = None,
    column_type: str = "TEXT",
    existing_column: str | None = None,
    separator: str = " ",
    condition: dict[str, Any] | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Merge multiple column values into a single column with a separator.

    Args:
        view_id: The dataview ID.
        sources: List of column display names to concatenate.
        new_column: Name for the result column.
        column_type: Column type — TEXT, NUMERIC, or DATE (default TEXT).
        existing_column: Existing column to overwrite instead of creating new.
        separator: Separator between values (default space).
        condition: Optional filter condition as JSON.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    try:
        manager = await get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
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
        return success_response(format_view_info(view), "combine_columns applied successfully")
    except (MammothAPIError, MammothColumnError, ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in combine_columns")
        return error_response(e)


# ── convert_type ──────────────────────────────────────────────


@mcp.tool()
@log_tool_call
async def convert_type(
    ctx: Context,
    view_id: int,
    conversions: list[dict[str, str]],
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Change column types: TEXT, NUMERIC, DATE, DATETIME.

    Args:
        view_id: The dataview ID.
        conversions: List of conversion specs, e.g. [{"column": "Sales", "to": "NUMERIC"}].
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    try:
        manager = await get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        view.convert_type(conversions)
        return success_response(format_view_info(view), "convert_type applied successfully")
    except (MammothAPIError, MammothColumnError, ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in convert_type")
        return error_response(e)
