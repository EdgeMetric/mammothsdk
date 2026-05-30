"""Pure per-operation parameter builders for Mammoth pipeline tasks.

Each ``build_<op>_params`` function:
  - Accepts the **typed spec** dataclasses (``ConversionSpec``, ``CopySpec``,
    ``SetValue``, ...) and enum-typed params — the same inputs the public
    :class:`~mammoth.view.View` methods take, *after* dict→spec normalization.
  - Takes ``col_map`` (display->internal), ``internal_names`` (all internal
    names, for pass-through resolution) and, where conditions are involved,
    ``column_types`` (display->type, forwarded to ``Condition.build``).
  - Accepts an optional ``name_gen`` callable for deterministic internal-name
    generation (used in tests and agent code; defaults to the random scheme).
  - Returns the exact dict that ``View._add_task()`` expects — byte-identical
    to what the corresponding ``_mixins`` method emits, except for the
    deliberate backend-conformance corrections noted inline (CONVERT ``FORMAT``
    dict, UNNEST/JSON_HANDLE ``INTERNAL_NAME``, literal-fill as SET+IS_EMPTY).
  - Has NO side effects and NO imports of HTTP/client/View code.

Enum-typed fields are emitted via their ``.value`` so the payload carries plain
backend strings. Inputs are the enums themselves (``ColumnType``, ``FilterType``,
``DateComponent``, ...) — never bare strings; the typed contract is the point.

Typical agent usage::

    from mammoth._pure.builders import build_convert_params
    from mammoth.models.pipeline import ConversionSpec, ColumnType

    columns = {"Sales": "column_1", "Region": "column_2"}
    spec = build_convert_params(
        [ConversionSpec(column="Sales", to=ColumnType.NUMERIC)], columns, ["column_1"],
    )
    # -> {"CONVERT": [{"SOURCE": "column_1", "TO_TYPE": "NUMERIC"}]}
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from mammoth._pure.resolve import (
    build_as_column,
    build_condition,
    next_internal_name,
    resolve_column,
    resolve_columns,
    resolve_order_by,
)
from mammoth.models.pipeline import (
    AggregationSpec,
    BulkReplaceMapping,
    ColumnType,
    ConversionSpec,
    CopySpec,
    CrosstabSpec,
    DateComponent,
    DateDelta,
    DateDiffUnit,
    FillDirection,
    FilterType,
    JoinKeySpec,
    JoinSelectSpec,
    JoinType,
    JsonExtractionSpec,
    JsonOpType,
    JsonType,
    SetValue,
    SplitColumnSpec,
    SubstringDirection,
    TextCase,
    WindowFunction,
    WindowRange,
)

if TYPE_CHECKING:
    from mammoth.condition import CompoundCondition, Condition, NotCondition
    from mammoth.models.pipeline import SortDirection

    ConditionLike = Condition | CompoundCondition | NotCondition | dict[str, Any]
    OrderBy = list[list[str | SortDirection]]


# ---------------------------------------------------------------------------
# Column operations
# ---------------------------------------------------------------------------


def build_add_column_params(
    name: str,
    column_type: ColumnType = ColumnType.TEXT,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build an ADD_COLUMN task payload (empty new column)."""
    return {
        "ADD_COLUMN": [
            {
                "COLUMN": name,
                "TYPE": column_type.value,
                "INTERNAL_NAME": next_internal_name(name_gen),
            }
        ]
    }


def build_delete_params(
    columns: list[str],
    col_map: dict[str, str],
    internal_names: list[str],
) -> dict[str, Any]:
    """Build a DELETE (remove columns) task payload."""
    return {"DELETE": resolve_columns(columns, col_map, internal_names)}


def build_copy_params(
    copies: list[CopySpec],
    col_map: dict[str, str],
    internal_names: list[str],
    column_types: dict[str, str] | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a COPY (duplicate columns) task payload (VERSION 2).

    Each copy carries its own optional CONDITION (backend per-item form).
    """
    copy_items: list[dict[str, Any]] = []
    for c in copies:
        item: dict[str, Any] = {
            "SOURCE": resolve_column(c.source, col_map, internal_names),
            "AS": build_as_column(c.as_name or f"{c.source} Copy", c.type, name_gen=name_gen),
        }
        if c.condition is not None:
            item["CONDITION"] = build_condition(c.condition, col_map, column_types)
        copy_items.append(item)
    return {"COPY": copy_items, "VERSION": 2}


def build_combine_params(
    sources: list[str],
    col_map: dict[str, str],
    internal_names: list[str],
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.TEXT,
    existing_column: str | None = None,
    separator: str = " ",
    condition: ConditionLike | None = None,
    column_types: dict[str, str] | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a COMBINE (concatenate columns) task payload."""
    source_specs: list[dict[str, str]] = []
    for i, s in enumerate(sources):
        source_specs.append({"COLUMN": resolve_column(s, col_map, internal_names)})
        if i < len(sources) - 1:
            source_specs.append({"STRING": separator})

    combine_spec: dict[str, Any] = {"SOURCE": source_specs}
    if new_column:
        combine_spec["AS"] = build_as_column(new_column, column_type, name_gen=name_gen)
    elif existing_column:
        combine_spec["DESTINATION"] = resolve_column(existing_column, col_map, internal_names)

    spec: dict[str, Any] = {"COMBINE": combine_spec}
    built = build_condition(condition, col_map, column_types)
    if built is not None:
        spec["CONDITION"] = built
    return spec


def build_convert_params(
    conversions: list[ConversionSpec],
    col_map: dict[str, str],
    internal_names: list[str],
) -> dict[str, Any]:
    """Build a CONVERT (type conversion) task payload.

    ``FORMAT`` is emitted as a dict ``{"date_format": <fmt>}`` (backend
    CONVERT validator requires a dict, not a bare string).
    """
    convert_items: list[dict[str, Any]] = []
    for c in conversions:
        item: dict[str, Any] = {
            "SOURCE": resolve_column(c.column, col_map, internal_names),
            "TO_TYPE": c.to.value,
        }
        if c.format is not None:
            item["FORMAT"] = {"date_format": c.format}
        convert_items.append(item)
    return {"CONVERT": convert_items}


# ---------------------------------------------------------------------------
# Filter / Set operations
# ---------------------------------------------------------------------------


def build_filter_params(
    condition: ConditionLike,
    col_map: dict[str, str],
    column_types: dict[str, str] | None = None,
    filter_type: FilterType = FilterType.SHOW,
    prompt: str = "",
) -> dict[str, Any]:
    """Build a SELECT (filter rows) task payload."""
    built = build_condition(condition, col_map, column_types)
    if isinstance(built, dict):
        built["FILTER_TYPE"] = filter_type.value
        built["PROMPT"] = prompt
    return {"SELECT": "ALL", "CONDITION": built}


def build_set_params(
    values: list[SetValue],
    col_map: dict[str, str],
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.TEXT,
    existing_column: str | None = None,
    internal_names: list[str] | None = None,
    condition: ConditionLike | None = None,
    column_types: dict[str, str] | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a SET (label/insert values) task payload (VERSION 2)."""
    _internal_names: list[str] = internal_names or []
    value_items: list[dict[str, Any]] = []
    for v in values:
        item: dict[str, Any] = {"PROVIDER_TYPE": "FIXED", "PROVIDER": v.value}
        if v.condition is not None:
            item["CONDITION"] = build_condition(v.condition, col_map, column_types)
        value_items.append(item)

    set_dict: dict[str, Any] = {"VALUES": value_items}
    if new_column:
        set_dict["AS"] = build_as_column(new_column, column_type, name_gen=name_gen)
    elif existing_column:
        set_dict["DESTINATION"] = resolve_column(existing_column, col_map, _internal_names)

    spec: dict[str, Any] = {"SET": set_dict, "VERSION": 2}
    built = build_condition(condition, col_map, column_types)
    if built is not None:
        spec["CONDITION"] = built
    return spec


# ---------------------------------------------------------------------------
# Math
# ---------------------------------------------------------------------------


def build_math_params(
    expression: str,
    col_map: dict[str, str],
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.NUMERIC,
    existing_column: str | None = None,
    internal_names: list[str] | None = None,
    condition: ConditionLike | None = None,
    column_types: dict[str, str] | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a MATH (arithmetic) task payload from a string expression."""
    from mammoth._expression_parser import parse_expression

    _internal_names: list[str] = internal_names or []
    math_spec: dict[str, Any] = {"EXPRESSION": parse_expression(expression, col_map)}
    if new_column:
        math_spec["AS"] = build_as_column(new_column, column_type, name_gen=name_gen)
    elif existing_column:
        math_spec["DESTINATION"] = resolve_column(existing_column, col_map, _internal_names)

    spec: dict[str, Any] = {"MATH": math_spec}
    built = build_condition(condition, col_map, column_types)
    if built is not None:
        spec["CONDITION"] = built
    return spec


# ---------------------------------------------------------------------------
# Text operations
# ---------------------------------------------------------------------------


def build_text_transform_params(
    columns: list[str],
    col_map: dict[str, str],
    internal_names: list[str],
    case: TextCase | None = None,
    trim: bool = False,
    condition: ConditionLike | None = None,
    column_types: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a TEXT_TRANSFORM task payload."""
    tt_spec: dict[str, Any] = {
        "SOURCE": resolve_columns(columns, col_map, internal_names),
        "TRIM": trim,
    }
    if case is not None:
        tt_spec["CASE"] = case.value

    spec: dict[str, Any] = {"TEXT_TRANSFORM": tt_spec}
    built = build_condition(condition, col_map, column_types)
    if built is not None:
        spec["CONDITION"] = built
    return spec


def build_replace_params(
    columns: list[str],
    col_map: dict[str, str],
    internal_names: list[str],
    find: str,
    replace: str,
    match_case: bool = False,
    match_words: bool = False,
    condition: ConditionLike | None = None,
    column_types: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a REPLACE (find/replace) task payload."""
    replace_spec: dict[str, Any] = {
        "SOURCE": resolve_columns(columns, col_map, internal_names),
        "VALUE_PAIR": [{"SEARCH_VALUE": find, "REPLACE_VALUE": replace}],
        "MATCH_CASE": match_case,
        "MATCH_WORDS": match_words,
    }
    spec: dict[str, Any] = {"REPLACE": replace_spec}
    built = build_condition(condition, col_map, column_types)
    if built is not None:
        spec["CONDITION"] = built
    return spec


def build_bulk_replace_params(
    columns: list[str],
    col_map: dict[str, str],
    internal_names: list[str],
    mapping: list[BulkReplaceMapping],
    match_case: bool = True,
    match_words: bool = False,
    condition: ConditionLike | None = None,
    column_types: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a REPLACE with MAPPING (bulk find/replace) task payload."""
    mapping_specs = [{"SEARCH_VALUE": m.search, "REPLACE_VALUE": m.replace} for m in mapping]
    replace_spec: dict[str, Any] = {
        "SOURCE": resolve_columns(columns, col_map, internal_names),
        "MAPPING": mapping_specs,
        "MATCH_CASE": match_case,
        "MATCH_WORDS": match_words,
    }
    spec: dict[str, Any] = {"REPLACE": replace_spec}
    built = build_condition(condition, col_map, column_types)
    if built is not None:
        spec["CONDITION"] = built
    return spec


def build_split_params(
    column: str,
    delimiter: str,
    new_columns: list[SplitColumnSpec],
    col_map: dict[str, str],
    internal_names: list[str],
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a SPLIT task payload."""
    return {
        "SPLIT": {
            "SOURCE": resolve_column(column, col_map, internal_names),
            "DELIMITER": delimiter,
            "AS": [build_as_column(nc.name, nc.type, name_gen=name_gen) for nc in new_columns],
        }
    }


def build_substring_params(
    column: str,
    col_map: dict[str, str],
    internal_names: list[str],
    direction: SubstringDirection | None = None,
    num_char: int | None = None,
    char_position: int | None = None,
    regex_pattern: str | None = None,
    regex_invert: bool = False,
    new_column: str | None = None,
    existing_column: str | None = None,
    condition: ConditionLike | None = None,
    column_types: dict[str, str] | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a SUBSTRING (text extraction) task payload."""
    sub_spec: dict[str, Any] = {"SOURCE": resolve_column(column, col_map, internal_names)}
    if regex_pattern is not None:
        sub_spec["REGEX"] = {"EXPRESSION": regex_pattern, "INVERT": regex_invert}
    if direction is not None:
        sub_spec["DIRECTION"] = direction.value
    if num_char is not None:
        sub_spec["NUM_CHAR"] = num_char
    if char_position is not None:
        sub_spec["CHAR_POSITION"] = char_position

    if new_column:
        sub_spec["AS"] = build_as_column(new_column, "TEXT", name_gen=name_gen)
    elif existing_column:
        sub_spec["DESTINATION"] = resolve_column(existing_column, col_map, internal_names)

    spec: dict[str, Any] = {"SUBSTRING": sub_spec}
    built = build_condition(condition, col_map, column_types)
    if built is not None:
        spec["CONDITION"] = built
    return spec


# ---------------------------------------------------------------------------
# Date operations
# ---------------------------------------------------------------------------

_TEXT_DATE_COMPONENTS = frozenset(
    {
        DateComponent.WEEKDAY_TEXT.value,
        DateComponent.MONTH_TEXT.value,
        DateComponent.MONTH_DAY_YEAR_HOUR_MINUTE_SECOND.value,
        DateComponent.YEAR_MONTH_DAY_AS_DATE.value,
    }
)


def build_extract_date_params(
    column: str,
    component: DateComponent,
    col_map: dict[str, str],
    internal_names: list[str],
    new_column: str | None = None,
    existing_column: str | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build an EXTRACT_DATE task payload."""
    output_type = "TEXT" if component.value in _TEXT_DATE_COMPONENTS else "NUMERIC"
    ed_spec: dict[str, Any] = {
        "SOURCE": resolve_column(column, col_map, internal_names),
        "COMPONENT": component.value,
    }
    if new_column:
        ed_spec["AS"] = build_as_column(new_column, output_type, name_gen=name_gen)
    elif existing_column:
        ed_spec["DESTINATION"] = resolve_column(existing_column, col_map, internal_names)
    return {"EXTRACT_DATE": ed_spec}


def build_date_diff_params(
    component: DateDiffUnit,
    start: str,
    end: str,
    col_map: dict[str, str],
    internal_names: list[str],
    new_column: str | None = None,
    existing_column: str | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a DATE_DIFF task payload."""
    dd_spec: dict[str, Any] = {
        "COMPONENT": component.value,
        "MINUEND": {"TYPE": "COLUMN", "VALUE": resolve_column(end, col_map, internal_names)},
        "SUBTRAHEND": {"TYPE": "COLUMN", "VALUE": resolve_column(start, col_map, internal_names)},
    }
    if new_column:
        dd_spec["AS"] = build_as_column(new_column, "NUMERIC", name_gen=name_gen)
    elif existing_column:
        dd_spec["DESTINATION"] = resolve_column(existing_column, col_map, internal_names)
    return {"DATE_DIFF": dd_spec}


def build_increment_date_params(
    column: str,
    delta: DateDelta,
    col_map: dict[str, str],
    internal_names: list[str],
    new_column: str | None = None,
    existing_column: str | None = None,
    condition: ConditionLike | None = None,
    column_types: dict[str, str] | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build an INCREMENT_DATE task payload."""
    id_spec: dict[str, Any] = {
        "SOURCE": resolve_column(column, col_map, internal_names),
        "DELTA": delta.to_dict(),
    }
    if new_column:
        id_spec["AS"] = build_as_column(new_column, "DATE", name_gen=name_gen)
    elif existing_column:
        id_spec["DESTINATION"] = resolve_column(existing_column, col_map, internal_names)
    spec: dict[str, Any] = {"INCREMENT_DATE": id_spec}
    built = build_condition(condition, col_map, column_types)
    if built is not None:
        spec["CONDITION"] = built
    return spec


# ---------------------------------------------------------------------------
# Row operations
# ---------------------------------------------------------------------------


def build_fill_params(
    column: str,
    direction: FillDirection,
    col_map: dict[str, str],
    internal_names: list[str],
    partition_by: str | None = None,
    order_by: OrderBy | None = None,
) -> dict[str, Any]:
    """Build a FILL (fill missing by propagation) task payload."""
    fill_spec: dict[str, Any] = {
        "COLUMN": resolve_column(column, col_map, internal_names),
        "WITH": direction.value,
    }
    if partition_by:
        fill_spec["PARTITION_BY"] = resolve_column(partition_by, col_map, internal_names)
    if order_by:
        fill_spec["ORDER_BY"] = resolve_order_by(order_by, col_map)
    return {"FILL": fill_spec}


def build_fill_value_params(
    column: str,
    value: Any,
    col_map: dict[str, str],
    internal_names: list[str],
) -> dict[str, Any]:
    """Build a SET task that writes *value* into *column* where the cell is empty.

    The backend FILL task only honours directional ``WITH`` values; a bare
    literal is silently dropped (data corruption). The correct way to fill
    nulls with a constant is a VERSION-2 SET task with an IS_EMPTY condition on
    the target column — exactly what this function emits.
    """
    internal = resolve_column(column, col_map, internal_names)
    return {
        "SET": {
            "DESTINATION": internal,
            "VALUES": [
                {
                    "PROVIDER_TYPE": "FIXED",
                    "PROVIDER": value,
                    "CONDITION": {internal: {"IS_EMPTY": True}},
                }
            ],
        },
        "VERSION": 2,
    }


def build_limit_params(
    n: int,
    col_map: dict[str, str],
    bottom: bool = False,
    order_by: OrderBy | None = None,
) -> dict[str, Any]:
    """Build a LIMIT (top/bottom N rows) task payload."""
    spec: dict[str, Any] = {"LIMIT": {"LIMIT": n, "BOTTOM": bottom}}
    if order_by:
        spec["ORDER_BY"] = resolve_order_by(order_by, col_map)
    return spec


def build_discard_duplicates_params(
    col_map: dict[str, str],
    internal_names: list[str],
    ignore_columns: list[str] | None = None,
) -> dict[str, Any]:
    """Build a DISCARD_DUPLICATES task payload."""
    resolved = resolve_columns(ignore_columns, col_map, internal_names) if ignore_columns else []
    return {"DISCARD_DUPLICATES": True, "IGNORE_COLUMNS": resolved}


def build_unnest_params(
    columns: list[str],
    col_map: dict[str, str],
    internal_names: list[str],
    label_column: str = "Label",
    value_column: str = "Value",
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build an UNNEST (unpivot) task payload.

    The LABEL and VALUE output-column dicts each carry ``INTERNAL_NAME``
    (backend UNNEST validator KeyErrors without it).
    """
    internal_to_display = {v: k for k, v in col_map.items()}
    col_specs: list[dict[str, str]] = []
    for c in columns:
        internal = resolve_column(c, col_map, internal_names)
        display = c if c in col_map else internal_to_display.get(internal, c)
        col_specs.append({"COLUMN": internal, "LABEL": display})

    return {
        "UNNEST": {
            "COLUMNS": col_specs,
            "LABEL": {
                "COLUMN": label_column,
                "TYPE": "TEXT",
                "INTERNAL_NAME": next_internal_name(name_gen),
            },
            "VALUE": {
                "COLUMN": value_column,
                "TYPE": "TEXT",
                "INTERNAL_NAME": next_internal_name(name_gen),
            },
        }
    }


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def build_pivot_params(
    group_by: list[str],
    aggregations: list[AggregationSpec],
    col_map: dict[str, str],
    internal_names: list[str],
    condition: ConditionLike | None = None,
    column_types: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a PIVOT (group/aggregate) task payload."""
    group_specs = [
        {"COLUMN": resolve_column(g, col_map, internal_names), "ORDER": idx}
        for idx, g in enumerate(group_by)
    ]
    base_order = len(group_by)
    select_specs: list[dict[str, Any]] = []
    for idx, agg in enumerate(aggregations):
        func_str = agg.function.value
        sel: dict[str, Any] = {
            "ORDER": base_order + idx,
            "FUNCTION": func_str,
            "COLUMN": resolve_column(agg.column, col_map, internal_names),
            "AS": agg.as_name or f"{func_str}_{agg.column}",
        }
        if agg.delimiter is not None:
            sel["DELIMITER"] = agg.delimiter
        select_specs.append(sel)

    pivot_spec: dict[str, Any] = {"GROUP_BY": group_specs, "SELECT": select_specs}
    built = build_condition(condition, col_map, column_types)
    if built is not None:
        pivot_spec["CONDITION"] = built
    return {"PIVOT": pivot_spec}


def build_window_params(
    function: WindowFunction,
    col_map: dict[str, str],
    internal_names: list[str],
    column: str | None = None,
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.NUMERIC,
    existing_column: str | None = None,
    partition_by: list[str] | None = None,
    order_by: OrderBy | None = None,
    range_type: WindowRange = WindowRange.UNBOUNDED,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a WINDOW (window function) task payload."""
    evaluate: dict[str, Any] = {"FUNCTION": function.value}
    if column:
        resolved = resolve_column(column, col_map, internal_names)
        evaluate["SOURCES"] = resolved
        evaluate["ARGUMENTS"] = [resolved]

    window_spec: dict[str, Any] = {"EVALUATE": evaluate, "RANGE": range_type.value}
    if new_column:
        window_spec["AS"] = build_as_column(new_column, column_type, name_gen=name_gen)
    elif existing_column:
        window_spec["DESTINATION"] = resolve_column(existing_column, col_map, internal_names)
    if partition_by:
        window_spec["GROUP_BY"] = [
            {"COLUMN": resolve_column(p, col_map, internal_names)} for p in partition_by
        ]
    if order_by:
        window_spec["ORDER_BY"] = resolve_order_by(order_by, col_map)
    return {"WINDOW": window_spec}


def build_crosstab_params(
    rows: list[str],
    pivot_column: str,
    select: CrosstabSpec,
    col_map: dict[str, str],
    internal_names: list[str],
    column_types: dict[str, str],
) -> dict[str, Any]:
    """Build a CROSSTAB (pivot table) parameter dict.

    The SELECT clause carries ``COLUMN`` when :attr:`CrosstabSpec.column` is set
    (omitted for count-style aggregations that take no value column).
    """
    select_spec: dict[str, Any] = {"FUNCTION": select.function.value}
    if select.column is not None:
        select_spec["COLUMN"] = resolve_column(select.column, col_map, internal_names)
    return {
        "CROSSTAB": {
            "ROWS": [
                {
                    "COLUMN": resolve_column(r, col_map, internal_names),
                    "TYPE": column_types.get(r, "TEXT"),
                }
                for r in rows
            ],
            "COLUMNS": [
                {
                    "COLUMN": resolve_column(pivot_column, col_map, internal_names),
                    "TYPE": column_types.get(pivot_column, "TEXT"),
                }
            ],
            "SELECT": select_spec,
        }
    }


# ---------------------------------------------------------------------------
# Advanced operations
# ---------------------------------------------------------------------------


def build_join_params(
    foreign_view_id: int,
    join_type: JoinType,
    on: list[JoinKeySpec],
    select: Sequence[str | JoinSelectSpec],
    col_map: dict[str, str],
    internal_names: list[str],
    foreign_columns: dict[str, str] | None = None,
    column_prefix: str | None = None,
    join_id: str | None = None,
) -> dict[str, Any]:
    """Build a JOIN task payload.

    *select* items may be display-name strings (resolved via *foreign_columns*
    when provided) or :class:`JoinSelectSpec` objects. *join_id* defaults to a
    fresh 8-char id; pass an explicit value for deterministic output.
    """
    on_specs = [
        {
            "LEFT": resolve_column(j.left, col_map, internal_names),
            "RIGHT": (
                foreign_columns[j.right]
                if foreign_columns and j.right in foreign_columns
                else j.right
            ),
        }
        for j in on
    ]

    select_specs: list[dict[str, str]] = []
    for s in select:
        if isinstance(s, str):
            col = foreign_columns[s] if foreign_columns and s in foreign_columns else s
            select_specs.append({"COLUMN": col, "ALIAS": s})
        else:
            col = s.column
            alias = s.alias or col
            if foreign_columns and col in foreign_columns:
                col = foreign_columns[col]
            select_specs.append({"COLUMN": col, "ALIAS": alias})

    join_spec: dict[str, Any] = {
        "JOIN_ID": join_id or str(uuid.uuid4())[:8],
        "DATAVIEW_ID": foreign_view_id,
        "TYPE": join_type.value,
        "ON": on_specs,
        "SELECT": select_specs,
    }
    if column_prefix:
        join_spec["COLUMN_PREFIX"] = column_prefix
    return {"JOIN": join_spec}


def build_lookup_params(
    source: str,
    lookup_view_id: int,
    key: str,
    value: str,
    col_map: dict[str, str],
    internal_names: list[str],
    new_column: str | None = None,
    existing_column: str | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a LOOKUP task payload."""
    lookup_spec: dict[str, Any] = {
        "DATAVIEW_ID": lookup_view_id,
        "SOURCE": resolve_column(source, col_map, internal_names),
        "KEY": key,
        "VALUE": value,
    }
    if new_column:
        lookup_spec["AS"] = build_as_column(new_column, "TEXT", name_gen=name_gen)
    elif existing_column:
        lookup_spec["DESTINATION"] = resolve_column(existing_column, col_map, internal_names)
    return {"LOOKUP": lookup_spec}


_JSON_TYPE_MAP: dict[JsonType, tuple[str, JsonOpType, str]] = {
    JsonType.OBJECT: ("JSON_OBJECT", JsonOpType.JSON_OBJECT_TO_COLUMNS, "JSON_OBJECT_OP_TYPE"),
    JsonType.LIST: ("JSON_LIST", JsonOpType.JSON_LIST_TO_ROWS, "JSON_LIST_OP_TYPE"),
}


def build_json_extract_params(
    column: str,
    col_map: dict[str, str],
    internal_names: list[str],
    json_type: JsonType = JsonType.OBJECT,
    keys: list[str] | None = None,
    extractions: list[JsonExtractionSpec] | None = None,
    keep_source: bool = False,
    op_type: JsonOpType | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a JSON_HANDLE (JSON extraction) task payload.

    Each extraction item carries ``INTERNAL_NAME`` (backend JSON_HANDLE
    validator requires it) and a ``TYPE`` in {NUMERIC, TEXT}.
    """
    extract_specs: list[dict[str, str]] = []
    if extractions:
        for e in extractions:
            extract_specs.append(
                {
                    "COLUMN": e.as_name or e.key,
                    "KEY": e.key,
                    "TYPE": e.type.value,
                    "INTERNAL_NAME": next_internal_name(name_gen),
                }
            )
    elif keys:
        for k in keys:
            extract_specs.append(
                {
                    "COLUMN": k,
                    "KEY": k,
                    "TYPE": "TEXT",
                    "INTERNAL_NAME": next_internal_name(name_gen),
                }
            )

    backend_type, default_op, op_key = _JSON_TYPE_MAP[json_type]
    json_handle_spec: dict[str, Any] = {
        "SOURCE": resolve_column(column, col_map, internal_names),
        "TYPE": backend_type,
        "JSON_EXTRACT": extract_specs,
        "JSON_KEEP_SOURCE": keep_source,
        op_key: (op_type or default_op).value,
    }
    return {"JSON_HANDLE": json_handle_spec}


def build_gen_ai_params(
    prompt: str,
    context_columns: list[str],
    col_map: dict[str, str],
    internal_names: list[str],
    new_column: str = "AI Result",
    assistant_data: list[str] | None = None,
    context_columns_derivation: bool | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a GEN_AI (AI transformation) task payload."""
    gen_ai_spec: dict[str, Any] = {
        "AS": build_as_column(new_column, "TEXT", name_gen=name_gen),
        "ASSISTANT_DATA": assistant_data or [],
        "query": prompt,
        "context_columns": resolve_columns(context_columns, col_map, internal_names),
    }
    if context_columns_derivation is not None:
        gen_ai_spec["context_columns_derivation"] = context_columns_derivation
    return {"GEN_AI": gen_ai_spec}


def build_sql_params(query: str) -> dict[str, Any]:
    """Build a SQL (raw query) task payload."""
    return {"SQL": {"USER_QUERY": query}}


# ---------------------------------------------------------------------------
# Date normalization (CONVERT to DATE with format)
# ---------------------------------------------------------------------------


def build_date_normalize_params(
    column: str,
    col_map: dict[str, str],
    internal_names: list[str],
    target_type: ColumnType = ColumnType.DATE,
    formats: list[str] | None = None,
) -> dict[str, Any]:
    """Build a CONVERT task payload that normalizes a column to DATE.

    ``TO_TYPE`` must be DATE (the only valid date type in Mammoth). When
    *formats* is given, FORMAT is emitted as a dict ``{"date_format": <fmt>}``
    (only the first format string is sent). Raises ``ValueError`` for any
    non-DATE target.
    """
    if target_type is not ColumnType.DATE:
        raise ValueError(
            f"build_date_normalize_params: target_type must be ColumnType.DATE, "
            f"got {target_type.value!r}."
        )
    convert_item: dict[str, Any] = {
        "SOURCE": resolve_column(column, col_map, internal_names),
        "TO_TYPE": ColumnType.DATE.value,
    }
    if formats:
        convert_item["FORMAT"] = {"date_format": formats[0]}
    return {"CONVERT": [convert_item]}
