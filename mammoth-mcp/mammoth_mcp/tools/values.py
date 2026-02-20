"""Value transformation tools — filter, set, math, text, replace, split, substring."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth import (
    ColumnType,
    FilterType,
    SetValue,
    SubstringDirection,
    TextCase,
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

# ── filter_rows ───────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def filter_rows(
    ctx: Context,
    view_id: int,
    condition: dict[str, Any],
    filter_type: str = "SHOW",
    prompt: str = "",
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Keep or remove rows matching a condition. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        condition: Filter condition as JSON. Simple: {"column": "Sales", "operator": "GTE", "value": 1000}. Compound: {"logic": "AND", "conditions": [...]}.
        filter_type: SHOW to keep matching rows, REMOVE to discard them (default SHOW).
        prompt: Natural-language description of the filter (optional).
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    cond = build_condition(condition)
    ft = resolve_enum(FilterType, filter_type)
    await run_sync(view.filter_rows, cond, filter_type=ft, prompt=prompt)
    return success_response(format_view_info(view), "filter_rows applied successfully")


# ── set_values ────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def set_values(
    ctx: Context,
    view_id: int,
    values: list[dict[str, Any]],
    new_column: str | None = None,
    column_type: str = "TEXT",
    existing_column: str | None = None,
    condition: dict[str, Any] | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Populate or annotate columns with conditional values. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        values: List of value specs, e.g. [{"value": "High", "condition": {"column": "Sales", "operator": "GTE", "value": 10000}}, {"value": "Low"}].
        new_column: Name for a new result column.
        column_type: Column type for new column — TEXT, NUMERIC, or DATE (default TEXT).
        existing_column: Existing column to overwrite.
        condition: Optional global filter condition as JSON.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    sv_list = []
    for v in values:
        cond = build_condition(v["condition"]) if v.get("condition") else None
        sv_list.append(SetValue(value=v["value"], condition=cond))
    ct = resolve_enum(ColumnType, column_type)
    global_cond = build_condition(condition) if condition else None
    await run_sync(
        view.set_values,
        values=sv_list,
        new_column=new_column,
        column_type=ct,
        existing_column=existing_column,
        condition=global_cond,
    )
    return success_response(format_view_info(view), "set_values applied successfully")


# ── math_transform ────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def math_transform(
    ctx: Context,
    view_id: int,
    expression: str,
    new_column: str | None = None,
    column_type: str = "NUMERIC",
    existing_column: str | None = None,
    condition: dict[str, Any] | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Perform arithmetic using column values, constants, and functions (SUM, AVG, MIN, MAX, COUNT, INT, ABS). Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        expression: Math expression string, e.g. "Price * Quantity".
        new_column: Name for a new result column.
        column_type: Column type for new column (default NUMERIC).
        existing_column: Existing column to overwrite.
        condition: Optional filter condition as JSON.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    ct = resolve_enum(ColumnType, column_type)
    cond = build_condition(condition) if condition else None
    await run_sync(
        view.math,
        expression=expression,
        new_column=new_column,
        column_type=ct,
        existing_column=existing_column,
        condition=cond,
    )
    return success_response(format_view_info(view), "math_transform applied successfully")


# ── text_transform ────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def text_transform(
    ctx: Context,
    view_id: int,
    columns: list[str],
    case: str | None = None,
    trim: bool = False,
    condition: dict[str, Any] | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Standardize text — change case (UPPER, LOWER, TITLE) and/or trim whitespace. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        columns: List of column display names.
        case: Case transformation — UPPER, LOWER, or TITLE.
        trim: Whether to trim whitespace (default false).
        condition: Optional filter condition as JSON.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    tc = resolve_enum(TextCase, case) if case else None
    cond = build_condition(condition) if condition else None
    await run_sync(view.text_transform, columns=columns, case=tc, trim=trim, condition=cond)
    return success_response(format_view_info(view), "text_transform applied successfully")


# ── replace_values ────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def replace_values(
    ctx: Context,
    view_id: int,
    columns: list[str],
    find: str,
    replace: str,
    match_case: bool = False,
    match_words: bool = False,
    condition: dict[str, Any] | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Find and replace text in one or more columns. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        columns: List of column display names.
        find: Text to find.
        replace: Replacement text.
        match_case: Case-sensitive matching (default false).
        match_words: Whole-word matching (default false).
        condition: Optional filter condition as JSON.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    cond = build_condition(condition) if condition else None
    await run_sync(
        view.replace_values,
        columns=columns,
        find=find,
        replace=replace,
        match_case=match_case,
        match_words=match_words,
        condition=cond,
    )
    return success_response(format_view_info(view), "replace_values applied successfully")


# ── bulk_replace ──────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def bulk_replace(
    ctx: Context,
    view_id: int,
    columns: list[str],
    mapping: list[dict[str, Any]],
    match_case: bool = True,
    match_words: bool = False,
    condition: dict[str, Any] | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Replace multiple value variations with standardized values. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        columns: List of column display names.
        mapping: List of bulk mapping specs, e.g. [{"search": ["val1", "val2"], "replace": "replacement"}].
        match_case: Case-sensitive matching (default true).
        match_words: Whole-word matching (default false).
        condition: Optional filter condition as JSON.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    cond = build_condition(condition) if condition else None
    await run_sync(
        view.bulk_replace,
        columns=columns,
        mapping=mapping,
        match_case=match_case,
        match_words=match_words,
        condition=cond,
    )
    return success_response(format_view_info(view), "bulk_replace applied successfully")


# ── split_column ──────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def split_column(
    ctx: Context,
    view_id: int,
    column: str,
    delimiter: str,
    new_columns: list[dict[str, str]],
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Split a text column by delimiter into multiple new columns. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        column: Source column display name.
        delimiter: Delimiter to split on.
        new_columns: List of new column specs, e.g. [{"name": "First", "type": "TEXT"}].
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    await run_sync(view.split_column, column=column, delimiter=delimiter, new_columns=new_columns)
    return success_response(format_view_info(view), "split_column applied successfully")


# ── substring ─────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def substring(
    ctx: Context,
    view_id: int,
    column: str,
    direction: str | None = None,
    num_char: int | None = None,
    char_position: int | None = None,
    regex_pattern: str | None = None,
    regex_invert: bool = False,
    new_column: str | None = None,
    existing_column: str | None = None,
    condition: dict[str, Any] | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Extract substrings using position-based slicing, delimiters, or regex. Adds a reversible pipeline task (undo with delete_task).

    Args:
        view_id: The dataview ID.
        column: Source column display name.
        direction: Extraction direction — START, END, LEFT, or RIGHT.
        num_char: Number of characters (use with START/END).
        char_position: Character position (use with LEFT/RIGHT).
        regex_pattern: Regex pattern for extraction.
        regex_invert: Invert regex match (default false).
        new_column: Name for a new result column.
        existing_column: Existing column to overwrite.
        condition: Optional filter condition as JSON.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    dir_enum = resolve_enum(SubstringDirection, direction) if direction else None
    cond = build_condition(condition) if condition else None
    await run_sync(
        view.substring,
        column=column,
        direction=dir_enum,
        num_char=num_char,
        char_position=char_position,
        regex_pattern=regex_pattern,
        regex_invert=regex_invert,
        new_column=new_column,
        existing_column=existing_column,
        condition=cond,
    )
    return success_response(format_view_info(view), "substring applied successfully")
