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
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from mammoth._pure.resolve import (
    build_as_column,
    build_condition,
    next_internal_name,
    resolve_column,
    resolve_columns,
    resolve_order_by,
)
from mammoth.exceptions import MammothValidationError
from mammoth.models.exports import (
    AddExportSpec,
    DashboardSpecKey,
    ExportTargetKey,
    HandlerType,
    TriggerType,
)
from mammoth.models.pipeline import (
    AggregateFunction,
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
    SaveAsDatasetMode,
    SetValue,
    SmallLargeFunction,
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

    Two destination modes per :class:`~mammoth.models.pipeline.CopySpec`:

    * **AS** (default): ``as_name`` is set (or defaults to ``"<source> Copy"``).
      The item emits ``{"SOURCE": ..., "AS": {...}}``.
    * **DESTINATION**: ``destination`` is set to an existing column name.
      The item emits ``{"SOURCE": ..., "DESTINATION": "<resolved_internal>"}``.

    Setting both ``as_name`` and ``destination`` on the same spec raises
    :exc:`ValueError`.
    """
    copy_items: list[dict[str, Any]] = []
    for c in copies:
        if c.as_name is not None and c.destination is not None:
            raise ValueError(
                f"CopySpec for source '{c.source}': 'as_name' and 'destination' are mutually "
                "exclusive — set one or the other, not both."
            )
        item: dict[str, Any] = {"SOURCE": resolve_column(c.source, col_map, internal_names)}
        if c.destination is not None:
            item["DESTINATION"] = resolve_column(c.destination, col_map, internal_names)
        else:
            item["AS"] = build_as_column(c.as_name or f"{c.source} Copy", c.type, name_gen=name_gen)
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
            built_cond = build_condition(v.condition, col_map, column_types)
            if isinstance(built_cond, dict):
                built_cond["FILTER_TYPE"] = FilterType.SHOW.value
            item["CONDITION"] = built_cond
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
        DateComponent.YEAR_MONTH_NUMBER.value,
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


# NumberFormat() defaults, emitted explicitly: the backend AsNewColumnLargeSmall
# requires a FORMAT key and prod SMALL/LARGE tasks always carry a full format
# block, so the populated default avoids any execution-time key lookups.
_DEFAULT_NUMBER_FORMAT: dict[str, Any] = {
    "comma_separated": False,
    "currency_symbol": "",
    "decimal_spec": 0,
    "is_percentage": False,
    "enabled": True,
    "numtype": "float",
}


def build_small_large_params(
    function: SmallLargeFunction,
    values: Sequence[str | int | float],
    index: int,
    col_map: dict[str, str],
    internal_names: list[str],
    new_column: str | None = None,
    existing_column: str | None = None,
    column_type: ColumnType = ColumnType.NUMERIC,
    number_format: dict[str, Any] | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a SMALL / LARGE task payload — the Nth smallest/largest value per row.

    SMALL/LARGE scans a set of value sources (other columns and/or numeric
    constants) on each row and writes the *index*-th smallest (SMALL) or largest
    (LARGE) of them. ``index`` is 1-based: ``index=1`` is the most extreme value.

    Args:
        function: SMALL (nth smallest) or LARGE (nth largest).
        values: The value sources to rank, in any order. A ``str`` is a column
            (display name, resolved to its internal name); an ``int``/``float`` is
            a numeric constant participating in the comparison.
        index: 1-based rank to pick (1 = most extreme). Must be >= 1.
        col_map: display-name -> internal-name mapping.
        internal_names: all internal names (for pass-through resolution).
        new_column: create a new column for the result (mutually exclusive with
            *existing_column*).
        existing_column: overwrite this existing column instead.
        column_type: type of the result column when creating one (default NUMERIC).
        number_format: optional NumberFormat override for a new column; defaults to
            the standard numeric format.
        name_gen: optional internal-name generator for the new column.

    Returns:
        ``{"SMALL"|"LARGE": {VALUES, INDEX, AS|DESTINATION}}``.

    Raises:
        MammothValidationError: empty *values*, *index* < 1, a value source that is
            neither a column name nor a number, or a new/existing-column selection
            that is not exactly one.
    """
    if not values:
        raise MammothValidationError("small_large requires at least one value source")
    if index < 1:
        raise MammothValidationError(f"small_large index must be 1-based (>= 1), got {index}")
    if bool(new_column) == bool(existing_column):
        raise MammothValidationError(
            "small_large requires exactly one of new_column or existing_column"
        )

    built_values: list[dict[str, Any]] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise MammothValidationError(
                "small_large value source must be a column name (str) or a numeric constant"
            )
        if isinstance(value, str):
            built_values.append(
                {"TYPE": "COLUMN", "VALUE": resolve_column(value, col_map, internal_names)}
            )
        else:
            built_values.append({"TYPE": "NUMBER", "VALUE": value})

    spec: dict[str, Any] = {"VALUES": built_values, "INDEX": index}
    if new_column:
        as_col = build_as_column(new_column, column_type.value, name_gen=name_gen)
        as_col["FORMAT"] = (
            number_format if number_format is not None else dict(_DEFAULT_NUMBER_FORMAT)
        )
        spec["AS"] = as_col
    elif existing_column:
        spec["DESTINATION"] = resolve_column(existing_column, col_map, internal_names)
    return {function.value: spec}


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


# CROSSTAB SELECT functions whose backend keyword differs from the SDK enum
# value. The crosstab DuckDB op checks ``"DISTINCT_COUNT"`` (dba_const.py),
# whereas the shared :class:`AggregateFunction` enum spells it COUNT_DISTINCT.
_CROSSTAB_FUNCTION_KEYWORD = {AggregateFunction.COUNT_DISTINCT: "DISTINCT_COUNT"}

# Aggregations the CROSSTAB DuckDB op can execute. Functions outside this set
# (MEDIAN, FIRST, LAST, CONCAT) are rejected by the SDK before any API call
# rather than failing opaquely in the backend.
_CROSSTAB_FUNCTIONS = frozenset(
    {
        AggregateFunction.COUNT,
        AggregateFunction.COUNT_DISTINCT,
        AggregateFunction.SUM,
        AggregateFunction.AVG,
        AggregateFunction.MIN,
        AggregateFunction.MAX,
        AggregateFunction.STDDEV,
        AggregateFunction.VARIANCE,
    }
)


# Validation messages (module-level for consistency + drift-free test asserts).
# Templates carry ``{}`` placeholders filled via ``.format()`` at raise time.
ERR_CROSSTAB_DATASET_NAME = "Crosstab `dataset_name` must be a non-empty string."
ERR_CROSSTAB_EMPTY_SELECT = "Crosstab requires at least one aggregation in `select`."
ERR_CROSSTAB_UNSUPPORTED_FN = (
    "Crosstab does not support the {fn} function. Supported functions: {supported}."
)
ERR_CROSSTAB_COUNT_WITH_COLUMN = (
    "Crosstab COUNT counts rows and takes no value column; omit `column` (got {column!r})."
)
ERR_CROSSTAB_MISSING_COLUMN = "Crosstab {fn} requires a value `column` to aggregate."


def _validate_crosstab_select(specs: list[CrosstabSpec]) -> None:
    """Reject crosstab aggregations the backend cannot execute.

    Raises:
        MammothValidationError: If *specs* is empty, names an unsupported
            function, gives COUNT a value column, or omits the value column a
            non-COUNT aggregation requires.
    """
    if not specs:
        raise MammothValidationError(ERR_CROSSTAB_EMPTY_SELECT)
    for s in specs:
        if s.function not in _CROSSTAB_FUNCTIONS:
            supported = sorted(f.value for f in _CROSSTAB_FUNCTIONS)
            raise MammothValidationError(
                ERR_CROSSTAB_UNSUPPORTED_FN.format(fn=s.function.value, supported=supported),
                {"function": s.function.value, "supported": supported},
            )
        if s.function is AggregateFunction.COUNT and s.column is not None:
            raise MammothValidationError(
                ERR_CROSSTAB_COUNT_WITH_COLUMN.format(column=s.column),
                {"function": "COUNT", "column": s.column},
            )
        if s.function is not AggregateFunction.COUNT and s.column is None:
            raise MammothValidationError(
                ERR_CROSSTAB_MISSING_COLUMN.format(fn=s.function.value),
                {"function": s.function.value},
            )


def _crosstab_axis_item(
    name: str, col_map: dict[str, str], internal_names: list[str], column_types: dict[str, str]
) -> dict[str, str]:
    """One ROWS/COLUMNS entry: internal column name + its live type."""
    return {
        "COLUMN": resolve_column(name, col_map, internal_names),
        "TYPE": column_types.get(name, "TEXT"),
    }


def build_crosstab_params(
    rows: list[str],
    pivot_column: str,
    select: CrosstabSpec | list[CrosstabSpec],
    dataset_name: str,
    col_map: dict[str, str],
    internal_names: list[str],
    column_types: dict[str, str],
    save_as_mode: SaveAsDatasetMode = SaveAsDatasetMode.REPLACE,
    target_ds_id: int | None = None,
) -> dict[str, Any]:
    """Build the ``target_properties`` for a CROSSTAB (group-and-pivot) export.

    A crosstab materialises a NEW dataset, so the backend routes it through the
    internal-dataset export handler (not a pipeline add-task). This returns the
    ``target_properties`` payload; the caller wraps it in an export spec.

    *select* may be a single :class:`CrosstabSpec` or a list (one output value
    column per spec). Each SELECT item carries ``COLUMN`` only when its
    :attr:`CrosstabSpec.column` is set (omitted for COUNT). ``COLUMNS_USED``
    maps every referenced internal name to its display name and type.
    """
    if not dataset_name:
        raise MammothValidationError(ERR_CROSSTAB_DATASET_NAME)
    specs = [select] if isinstance(select, CrosstabSpec) else select
    _validate_crosstab_select(specs)
    select_items: list[dict[str, Any]] = []
    for s in specs:
        item: dict[str, Any] = {
            "FUNCTION": _CROSSTAB_FUNCTION_KEYWORD.get(s.function, s.function.value)
        }
        if s.column is not None:
            item["COLUMN"] = resolve_column(s.column, col_map, internal_names)
        select_items.append(item)

    referenced = [*rows, pivot_column, *(s.column for s in specs if s.column is not None)]
    columns_used = {
        resolve_column(name, col_map, internal_names): {
            "display_name": name,
            "internal_name": resolve_column(name, col_map, internal_names),
            "type": column_types.get(name, "TEXT"),
        }
        for name in referenced
    }

    return {
        "DS_NAME": dataset_name,
        "TARGET_DS_ID": target_ds_id,
        "SAVE_AS_DS_MODE": save_as_mode.value,
        "COLUMNS_USED": columns_used,
        "TRANSFORM": {
            "CROSSTAB": {
                "ROWS": [
                    _crosstab_axis_item(r, col_map, internal_names, column_types) for r in rows
                ],
                "COLUMNS": [
                    _crosstab_axis_item(pivot_column, col_map, internal_names, column_types)
                ],
                "SELECT": select_items,
            }
        },
    }


ERR_BRANCHOUT_DATASET_NAME = "Branch-out `dataset_name` must be a non-empty string."
ERR_BRANCHOUT_APPEND_NO_TARGET = (
    "APPEND mode needs an existing `target_ds_id` to append into; "
    "pass target_ds_id, or use REPLACE to create a new dataset."
)


def build_branch_out_params(
    dataset_name: str,
    target_ds_id: int | None = None,
    save_as_mode: SaveAsDatasetMode = SaveAsDatasetMode.REPLACE,
    column_mapping: dict[str, str] | None = None,
    label_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Build the ``target_properties`` for a branch-out (save-as-dataset) export.

    Branch-out copies the view's data into a Mammoth dataset via the same
    internal-dataset export handler as crosstab, but with NO transform.

    ``target_ds_id`` None creates a new dataset named *dataset_name*; an int
    replaces/appends into that existing dataset (per *save_as_mode*).
    *column_mapping* maps source -> destination column names (empty = all
    columns). ``TRANSFORM`` is explicitly ``None`` — the backend treats a
    non-dict transform as "plain copy".

    Raises:
        MammothValidationError: If *dataset_name* is empty, or APPEND mode is
            requested without a *target_ds_id* to append into.
    """
    if not dataset_name:
        raise MammothValidationError(ERR_BRANCHOUT_DATASET_NAME)
    if save_as_mode is SaveAsDatasetMode.APPEND and target_ds_id is None:
        raise MammothValidationError(
            ERR_BRANCHOUT_APPEND_NO_TARGET,
            {"save_as_mode": save_as_mode.value, "target_ds_id": None},
        )
    return {
        "DS_NAME": dataset_name,
        "TARGET_DS_ID": target_ds_id,
        "SAVE_AS_DS_MODE": save_as_mode.value,
        "COLUMN_MAPPING": column_mapping or {},
        "TARGET_DS_LABEL_IDS": label_ids,
        "TRANSFORM": None,
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


def build_sql_params(query: str, intent: str | None = None) -> dict[str, Any]:
    """Build a SQL (raw query) task payload.

    When ``intent`` is given — the plain-English request the query was generated
    from — it is carried alongside the query under ``INTENT``, mirroring a
    UI-authored SQL rule so the pipeline card can show the intent next to the
    generated query. Omitted/empty intent yields a query-only payload (the prior
    shape), keeping every existing caller unchanged.
    """
    sql: dict[str, str] = {"USER_QUERY": query}
    if intent:
        sql["INTENT"] = intent
    return {"SQL": sql}


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


# ---------------------------------------------------------------------------
# Export + dashboard generation (pipeline-tail specs, not transform tasks)
# ---------------------------------------------------------------------------

_DASHBOARD_INTENT_MIN_LEN = 10

# Default ports per SQL/transfer handler — emitted only when the caller omits port.
_K = ExportTargetKey
_DB_EXPORT_REQUIRED = (_K.HOST, _K.USERNAME, _K.PASSWORD, _K.DATABASE, _K.TABLE)


@dataclass(frozen=True)
class _TargetContract:
    """Declarative ``target_properties`` contract for one export handler.

    Encodes the *correct* wire keys (the SDK's value-add: ftp uses ``domain`` /
    ``directory`` / ``file``, email uses ``emails``, sftp uses ``directory`` — not
    the ``host`` / ``path`` / ``recipients`` the older View methods sent). The
    builder validates a caller's dict against this instead of guessing.
    """

    required: tuple[str, ...]
    optional: tuple[str, ...] = ()
    defaults: Mapping[str, Any] = field(default_factory=dict)
    # bigquery / generic_rest_api carry open-ended (auth-/identity-specific) keys;
    # those handlers opt out of the unknown-key check rather than enumerate them all.
    allow_extra: bool = False


_EXPORT_CONTRACTS: dict[HandlerType, _TargetContract] = {
    HandlerType.POSTGRES: _TargetContract(_DB_EXPORT_REQUIRED, (_K.PORT,), {_K.PORT: 5432}),
    HandlerType.MYSQL: _TargetContract(_DB_EXPORT_REQUIRED, (_K.PORT,), {_K.PORT: 3306}),
    HandlerType.MSSQL: _TargetContract(_DB_EXPORT_REQUIRED, (_K.PORT,), {_K.PORT: 1433}),
    HandlerType.REDSHIFT: _TargetContract(_DB_EXPORT_REQUIRED, (_K.PORT,), {_K.PORT: 5439}),
    HandlerType.S3: _TargetContract(
        (_K.FILE,), (_K.FILE_TYPE, _K.INCLUDE_HIDDEN, _K.IS_FORMAT_SET, _K.USE_FORMAT)
    ),
    HandlerType.EMAIL: _TargetContract((_K.EMAILS,), (_K.MESSAGE, _K.RESOURCE, _K.SUBJECT)),
    HandlerType.FTP: _TargetContract(
        (_K.DOMAIN, _K.USERNAME, _K.PASSWORD, _K.DIRECTORY, _K.FILE), (_K.PORT,), {_K.PORT: 21}
    ),
    HandlerType.SFTP: _TargetContract(
        (_K.HOST, _K.USERNAME),
        (
            _K.PORT,
            _K.PASSWORD,
            _K.DIRECTORY,
            _K.FILE_NAME,
            _K.SSH_KEY_AUTHENTICATION,
            _K.PRIVATE_KEY,
            _K.PASSPHRASE,
            _K.RANDOMIZE_FILE_NAME,
        ),
        {_K.PORT: 22},
    ),
    HandlerType.ELASTICSEARCH: _TargetContract(
        (_K.HOST, _K.USERNAME, _K.PASSWORD, _K.INDEX, _K.CONNECTION),
        (_K.PORT, _K.CHUNKSIZE),
        {_K.PORT: 9243, _K.CHUNKSIZE: 200},
    ),
    HandlerType.AZURE_BLOB: _TargetContract(
        (_K.STORAGE_ACCOUNT_NAME, _K.TENANT_ID, _K.CLIENT_ID, _K.CLIENT_SECRET, _K.CONTAINER_NAME),
        (_K.FOLDER_PATH, _K.FILE_NAME),
    ),
    HandlerType.SHAREPOINT: _TargetContract(
        (_K.TENANT_ID, _K.CLIENT_ID, _K.CLIENT_SECRET, _K.SITE_URL),
        (_K.DOCUMENT_LIBRARY, _K.FOLDER_PATH, _K.FILE_NAME),
    ),
    HandlerType.ONEDRIVE: _TargetContract(
        (_K.TENANT_ID, _K.CLIENT_ID, _K.CLIENT_SECRET, _K.USER_ID),
        (_K.FOLDER_PATH, _K.FILE_NAME),
    ),
    HandlerType.BIGQUERY: _TargetContract(
        (_K.SELECTED_PROFILE, _K.SELECTED_IDENTITY, _K.TABLE),
        (_K.EXPORT_TYPE, _K.UPSERT_KEYS, _K.PARTITION, _K.DATABASE, _K.HOST),
        allow_extra=True,
    ),
    HandlerType.GENERIC_REST_API_EXPORT: _TargetContract(
        (_K.BASE_URL, _K.ENDPOINT_PATH),
        (
            _K.AUTH_TYPE,
            _K.HTTP_METHOD,
            _K.WRAP_PATH,
            _K.BATCH_SIZE,
            _K.TIMEOUT_SECONDS,
            _K.RATE_LIMIT_RPS,
            _K.SSL_VERIFY,
            _K.DEFAULT_HEADERS,
            _K.REQUEST_HEADERS,
            _K.QUERY_PARAMS,
            _K.EXTRA_BODY_FIELDS,
        ),
        allow_extra=True,
    ),
    HandlerType.PUBLISHDB: _TargetContract(
        (_K.ODBC_TYPE, _K.TABLE), (_K.DATABASE, _K.PROJECT_ID, _K.DATASET)
    ),
    HandlerType.TABLEAU_SERVER: _TargetContract(
        (_K.SERVER_URL, _K.TOKEN_NAME, _K.TOKEN_SECRET),
        (_K.SITE_NAME, _K.PROJECT_NAME, _K.DATASOURCE_NAME, _K.CA_BUNDLE_PATH),
    ),
}


def _is_blank(value: Any) -> bool:
    """A value counts as missing if it is None, blank/whitespace, or an empty collection."""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _coerce_handler(handler_type: HandlerType | str) -> HandlerType:
    if isinstance(handler_type, HandlerType):
        return handler_type
    try:
        return HandlerType(handler_type)
    except ValueError:
        raise MammothValidationError(
            f"unknown export handler {handler_type!r}; expected one of "
            f"{', '.join(sorted(h.value for h in HandlerType))}"
        ) from None


def _validate_target(
    handler: HandlerType, contract: _TargetContract, target_properties: Mapping[str, Any]
) -> dict[str, Any]:
    target = dict(target_properties)
    missing = [key for key in contract.required if _is_blank(target.get(key))]
    if missing:
        raise MammothValidationError(
            f"export to {handler.value!r} requires {', '.join(missing)} in target_properties"
        )
    if not contract.allow_extra:
        allowed = set(contract.required) | set(contract.optional) | set(contract.defaults)
        unknown = sorted(key for key in target if key not in allowed)
        if unknown:
            raise MammothValidationError(
                f"export to {handler.value!r} got unexpected target_properties keys: "
                f"{', '.join(unknown)}; allowed: {', '.join(sorted(allowed))}"
            )
    for key, value in contract.defaults.items():
        target.setdefault(key, value)
    return target


def build_export_spec(
    handler_type: HandlerType | str,
    target_properties: Mapping[str, Any],
    *,
    dataview_id: int,
    run_immediately: bool = True,
    end_of_pipeline: bool = True,
    sequence: int | None = None,
    trigger_id: int | None = None,
    condition: Mapping[str, Any] | None = None,
    additional_properties: Mapping[str, Any] | None = None,
    validate_only: bool = False,
) -> dict[str, Any]:
    """Build the envelope for adding a pipeline export action to a View.

    Validates *target_properties* against the destination's contract — every
    required key present and non-empty, the correct key names used, and (for the
    well-defined handlers) no stray keys — then applies any port/format defaults
    and returns the dict ``ActionTriggerManager.add_action_trigger`` consumes.

    Args:
        handler_type: Destination handler (``HandlerType`` or its string value,
            e.g. ``"mysql"``, ``"s3"``, ``"email"``).
        target_properties: Destination configuration. Keys are handler-specific
            (see the per-handler contracts); credentials are passed through here
            and split into the encrypted trigger store by the backend.
        dataview_id: The View to export from.
        run_immediately: Execute the export as soon as it is added.
        end_of_pipeline: Run after all transforms. Mutually exclusive with
            *sequence* (provide one or the other, not both).
        sequence: Pipeline position when not end-of-pipeline.
        trigger_id: Existing trigger id when editing an export (None creates one).
        condition: Optional row-filter condition; empty means no filter.
        additional_properties: Optional handler metadata.
        validate_only: Validate the config without writing data.

    Returns:
        The export envelope dict (``AddExportSpec.model_dump()`` shape).

    Raises:
        MammothValidationError: unknown handler, a missing/empty required key, an
            unexpected key for a well-defined handler, or *sequence* combined with
            *end_of_pipeline*.
    """
    handler = _coerce_handler(handler_type)
    contract = _EXPORT_CONTRACTS.get(handler)
    if contract is None:
        supported = ", ".join(sorted(h.value for h in _EXPORT_CONTRACTS))
        raise MammothValidationError(
            f"export handler {handler.value!r} is not supported by build_export_spec; "
            f"supported handlers: {supported}"
        )
    if sequence is not None and end_of_pipeline:
        raise MammothValidationError(
            "export accepts either end_of_pipeline=True or a sequence position, not both"
        )
    target = _validate_target(handler, contract, target_properties)
    spec = AddExportSpec(
        DATAVIEW_ID=dataview_id,
        handler_type=handler,
        trigger_type=TriggerType.PIPELINE,
        target_properties=target,
        additional_properties=dict(additional_properties or {}),
        condition=dict(condition or {}),
        run_immediately=run_immediately,
        validate_only=validate_only,
        end_of_pipeline=end_of_pipeline,
        sequence=sequence,
        TRIGGER_ID=trigger_id,
    )
    return spec.model_dump()


def build_dashboard_gen_spec(
    intent: str,
    source: Sequence[int],
    *,
    enable_filters: bool = True,
    enable_pages: bool = False,
) -> dict[str, Any]:
    """Build the spec for AI dashboard generation from one or more Views.

    Args:
        intent: Natural-language description of the dashboard to build. Must be at
            least ``_DASHBOARD_INTENT_MIN_LEN`` characters (the backend rejects
            shorter prompts).
        source: View ids the dashboard draws from. Non-empty; every id positive.
        enable_filters: Generate interactive filters (default True).
        enable_pages: Generate multiple dashboard pages (default False).

    Returns:
        ``{"params": {"intent", "source", "enable_filters", "enable_pages"}}``.

    Raises:
        MammothValidationError: intent too short, empty source, or a non-positive
            / non-integer source id.
    """
    if _is_blank(intent) or len(intent.strip()) < _DASHBOARD_INTENT_MIN_LEN:
        raise MammothValidationError(
            f"dashboard intent must be at least {_DASHBOARD_INTENT_MIN_LEN} characters"
        )
    source_ids = list(source)
    if not source_ids:
        raise MammothValidationError("dashboard source must list at least one View id")
    bad = [s for s in source_ids if isinstance(s, bool) or not isinstance(s, int) or s <= 0]
    if bad:
        raise MammothValidationError(f"dashboard source ids must be positive integers; got {bad}")
    return {
        DashboardSpecKey.PARAMS: {
            DashboardSpecKey.INTENT: intent.strip(),
            DashboardSpecKey.SOURCE: source_ids,
            DashboardSpecKey.ENABLE_FILTERS: enable_filters,
            DashboardSpecKey.ENABLE_PAGES: enable_pages,
        }
    }
