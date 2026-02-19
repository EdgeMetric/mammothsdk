"""Value transformation tools — filter, set, math, text, replace, split, substring."""

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
    resolve_enum,
    success_response,
)
from mammoth_mcp.server import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def transform_values(
    ctx: Context,
    view_id: int,
    type: str,
    dataset_id: int | None = None,
    # filter_rows
    condition: dict[str, Any] | None = None,
    filter_type: str = "SHOW",
    prompt: str = "",
    # set_values
    values: list[dict[str, Any]] | None = None,
    new_column: str | None = None,
    column_type: str = "TEXT",
    existing_column: str | None = None,
    # math
    expression: str | None = None,
    # text_transform
    columns: list[str] | None = None,
    case: str | None = None,
    trim: bool = False,
    # replace_values
    find: str | None = None,
    replace: str | None = None,
    match_case: bool = False,
    match_words: bool = False,
    # bulk_replace
    mapping: list[dict[str, Any]] | None = None,
    # split_column
    column: str | None = None,
    delimiter: str | None = None,
    new_columns: list[dict[str, str]] | None = None,
    # substring
    direction: str | None = None,
    num_char: int | None = None,
    char_position: int | None = None,
    regex_pattern: str | None = None,
    regex_invert: bool = False,
) -> dict[str, Any]:
    """Apply value-level transformations to a view.

    Args:
        view_id: The dataview ID.
        type: Operation type — one of: filter_rows, set_values, math, text_transform, replace_values, bulk_replace, split_column, substring.
        dataset_id: The dataset ID (auto-detected if not provided).
        condition: (filter_rows, set_values, etc.) Filter condition as JSON. Simple: {"column": "Sales", "operator": "GTE", "value": 1000}. Compound: {"logic": "AND", "conditions": [...]}.
        filter_type: (filter_rows) SHOW to keep matching rows, REMOVE to discard them (default SHOW).
        prompt: (filter_rows) Natural-language description of the filter (optional).
        values: (set_values) List of value specs, e.g. [{"value": "High", "condition": {"column": "Sales", "operator": "GTE", "value": 10000}}, {"value": "Low"}].
        new_column: (set_values, math, substring) Name for a new result column.
        column_type: (set_values) Column type for new column — TEXT, NUMERIC, or DATE (default TEXT).
        existing_column: (set_values, math, substring) Existing column to overwrite.
        expression: (math) Math expression string, e.g. "Price * Quantity".
        columns: (text_transform, replace_values, bulk_replace) List of column display names.
        case: (text_transform) Case transformation — UPPER, LOWER, or TITLE.
        trim: (text_transform) Whether to trim whitespace (default false).
        find: (replace_values) Text to find.
        replace: (replace_values) Replacement text.
        match_case: (replace_values, bulk_replace) Case-sensitive matching (default false).
        match_words: (replace_values, bulk_replace) Whole-word matching (default false).
        mapping: (bulk_replace) List of bulk mapping specs, e.g. [{"search": ["val1", "val2"], "replace": "replacement"}].
        column: (split_column, substring) Source column display name.
        delimiter: (split_column) Delimiter to split on.
        new_columns: (split_column) List of new column specs, e.g. [{"name": "First", "type": "TEXT"}].
        direction: (substring) Extraction direction — START, END, LEFT, or RIGHT.
        num_char: (substring) Number of characters (use with START/END).
        char_position: (substring) Character position (use with LEFT/RIGHT).
        regex_pattern: (substring) Regex pattern for extraction.
        regex_invert: (substring) Invert regex match (default false).
    """
    try:
        from mammoth import ColumnType, FilterType, SubstringDirection, TextCase

        manager = await get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        op = type.lower()

        if op == "filter_rows":
            if not condition:
                return error_response(ValueError("condition is required for filter_rows"))
            cond = build_condition(condition)
            ft = resolve_enum(FilterType, filter_type)
            view.filter_rows(cond, filter_type=ft, prompt=prompt)

        elif op == "set_values":
            if not values:
                return error_response(ValueError("values is required for set_values"))
            from mammoth import SetValue

            sv_list = []
            for v in values:
                cond = build_condition(v["condition"]) if v.get("condition") else None
                sv_list.append(SetValue(value=v["value"], condition=cond))

            ct = resolve_enum(ColumnType, column_type)
            global_cond = build_condition(condition) if condition else None
            view.set_values(
                values=sv_list,
                new_column=new_column,
                column_type=ct,
                existing_column=existing_column,
                condition=global_cond,
            )

        elif op == "math":
            if not expression:
                return error_response(ValueError("expression is required for math"))
            ct = resolve_enum(ColumnType, column_type) if column_type != "TEXT" else ColumnType.NUMERIC
            cond = build_condition(condition) if condition else None
            view.math(
                expression=expression,
                new_column=new_column,
                column_type=ct,
                existing_column=existing_column,
                condition=cond,
            )

        elif op == "text_transform":
            if not columns:
                return error_response(ValueError("columns is required for text_transform"))
            tc = resolve_enum(TextCase, case) if case else None
            cond = build_condition(condition) if condition else None
            view.text_transform(columns=columns, case=tc, trim=trim, condition=cond)

        elif op == "replace_values":
            if not columns or find is None or replace is None:
                return error_response(ValueError("columns, find, and replace are required for replace_values"))
            cond = build_condition(condition) if condition else None
            view.replace_values(
                columns=columns,
                find=find,
                replace=replace,
                match_case=match_case,
                match_words=match_words,
                condition=cond,
            )

        elif op == "bulk_replace":
            if not columns or not mapping:
                return error_response(ValueError("columns and mapping are required for bulk_replace"))
            cond = build_condition(condition) if condition else None
            view.bulk_replace(
                columns=columns,
                mapping=mapping,
                match_case=match_case,
                match_words=match_words,
                condition=cond,
            )

        elif op == "split_column":
            if not column or not delimiter or not new_columns:
                return error_response(ValueError("column, delimiter, and new_columns are required for split_column"))
            view.split_column(column=column, delimiter=delimiter, new_columns=new_columns)

        elif op == "substring":
            if not column:
                return error_response(ValueError("column is required for substring"))
            dir_enum = resolve_enum(SubstringDirection, direction) if direction else None
            cond = build_condition(condition) if condition else None
            view.substring(
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

        else:
            return error_response(
                ValueError(
                    f"Unknown type '{type}'. Use: filter_rows, set_values, math, text_transform, "
                    "replace_values, bulk_replace, split_column, substring"
                )
            )

        return success_response(format_view_info(view), f"{op} applied successfully")
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in transform_values")
        return error_response(e)
