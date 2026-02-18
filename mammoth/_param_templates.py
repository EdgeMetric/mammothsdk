"""Task parameter template builders for Mammoth pipeline operations.

Standalone equivalents of the backend's param_templates.py builders,
using inline string constants instead of CommonConstants imports.

Each function returns a task parameter dict ready to be submitted to
the pipeline API via ``view._add_task()`` or ``client.pipeline.add_task()``.

Example:
    from mammoth._param_templates import set_params, select_params

    # Build a SET task payload
    payload = set_params(
        set_values={"AS": {"COLUMN": "Status", "TYPE": "TEXT"},
                     "VALUES": [{"PROVIDER_TYPE": "FIXED", "PROVIDER": "Active"}]},
        version=2,
    )

    # Build a SELECT (filter) task payload
    payload = select_params("ALL", condition={"column_1": {"GTE": {"VALUE": 100}}})
"""

from __future__ import annotations

from typing import Any


def _attach_metadata(
    params: dict[str, Any],
    dataview_id: int | None,
    sequence_number: int | None,
) -> dict[str, Any]:
    """Attach optional DATAVIEW_ID and SEQUENCE_NUMBER to a params dict."""
    if dataview_id is not None:
        params["DATAVIEW_ID"] = dataview_id
    if sequence_number is not None:
        params["SEQUENCE_NUMBER"] = sequence_number
    return params


def _attach_condition(params: dict[str, Any], condition: dict[str, Any] | None) -> dict[str, Any]:
    """Attach an optional CONDITION to a params dict."""
    if condition is not None:
        params["CONDITION"] = condition
    return params


def add_column_params(
    columns: list[dict[str, Any]],
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build an ADD_COLUMN task payload.

    Args:
        columns: List of column specs, each with COLUMN, TYPE, and optional INTERNAL_NAME.
        dataview_id: Target dataview ID (optional).
        sequence_number: Pipeline sequence number (optional).

    Returns:
        Task parameter dict.

    Example:
        add_column_params([{"COLUMN": "Notes", "TYPE": "TEXT"}])
    """
    params: dict[str, Any] = {"ADD_COLUMN": columns}
    return _attach_metadata(params, dataview_id, sequence_number)


def combine_params(
    sources: list[dict[str, Any]],
    as_column: dict[str, Any] | None = None,
    destination: str | None = None,
    condition: dict[str, Any] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a COMBINE (concatenate columns) task payload.

    Args:
        sources: Alternating COLUMN and STRING items.
        as_column: New column spec (AS dict).
        destination: Internal name of existing column to overwrite.
        condition: Optional condition dict.

    Example:
        combine_params(
            sources=[{"COLUMN": "col_1"}, {"STRING": " - "}, {"COLUMN": "col_2"}],
            as_column={"COLUMN": "Full Name", "TYPE": "TEXT"},
        )
    """
    combine: dict[str, Any] = {"SOURCE": sources}
    if as_column is not None:
        combine["AS"] = as_column
    if destination is not None:
        combine["DESTINATION"] = destination
    params: dict[str, Any] = {"COMBINE": combine}
    _attach_condition(params, condition)
    return _attach_metadata(params, dataview_id, sequence_number)


def convert_params(
    conversions: list[dict[str, Any]],
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a CONVERT (type conversion) task payload.

    Args:
        conversions: List of dicts with SOURCE and TO_TYPE keys.

    Example:
        convert_params([{"SOURCE": "column_1", "TO_TYPE": "NUMERIC"}])
    """
    params: dict[str, Any] = {"CONVERT": conversions}
    return _attach_metadata(params, dataview_id, sequence_number)


def copy_params(
    copies: list[dict[str, Any]],
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a COPY (duplicate columns) task payload.

    Args:
        copies: List of dicts with SOURCE and AS keys.

    Example:
        copy_params([{"SOURCE": "column_1", "AS": {"COLUMN": "Sales Copy", "TYPE": "NUMERIC"}}])
    """
    params: dict[str, Any] = {"COPY": copies}
    return _attach_metadata(params, dataview_id, sequence_number)


def crosstab_params(
    rows: list[dict[str, Any]],
    columns: list[dict[str, Any]],
    select: dict[str, Any] | None,
    distincts: list[dict[str, Any]] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a CROSSTAB task payload.

    Args:
        rows: Row grouping columns.
        columns: Pivot columns.
        select: Aggregation spec with FUNCTION key.
        distincts: Optional distinct column specs.
    """
    crosstab: dict[str, Any] = {
        "ROWS": rows,
        "COLUMNS": columns,
        "SELECT": select,
    }
    if distincts is not None:
        crosstab["DISTINCTS"] = distincts
    params: dict[str, Any] = {"CROSSTAB": crosstab}
    return _attach_metadata(params, dataview_id, sequence_number)


def date_diff_params(
    component: str,
    minuend: dict[str, Any],
    subtrahend: dict[str, Any],
    as_column: dict[str, Any] | None = None,
    destination: str | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a DATE_DIFF task payload.

    Args:
        component: Date unit for difference (e.g. "MONTH", "DAY").
        minuend: End date spec (TYPE + VALUE or SOURCE).
        subtrahend: Start date spec.
        as_column: New column spec.
        destination: Existing column internal name.
    """
    date_diff: dict[str, Any] = {
        "COMPONENT": component,
        "MINUEND": minuend,
        "SUBTRAHEND": subtrahend,
    }
    if as_column is not None:
        date_diff["AS"] = as_column
    if destination is not None:
        date_diff["DESTINATION"] = destination
    params: dict[str, Any] = {"DATE_DIFF": date_diff}
    return _attach_metadata(params, dataview_id, sequence_number)


def delete_params(
    columns: list[str],
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a DELETE (remove columns) task payload.

    Args:
        columns: List of internal column names to delete.
    """
    params: dict[str, Any] = {"DELETE": columns}
    return _attach_metadata(params, dataview_id, sequence_number)


def extract_date_params(
    source: str,
    component: str,
    as_column: dict[str, Any] | None = None,
    destination: str | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build an EXTRACT_DATE task payload.

    Args:
        source: Internal column name of the date column.
        component: Date component to extract (e.g. "year", "month", "weekday_text").
        as_column: New column spec.
        destination: Existing column internal name.
    """
    extract_date: dict[str, Any] = {"SOURCE": source, "COMPONENT": component}
    if as_column is not None:
        extract_date["AS"] = as_column
    if destination is not None:
        extract_date["DESTINATION"] = destination
    params: dict[str, Any] = {"EXTRACT_DATE": extract_date}
    return _attach_metadata(params, dataview_id, sequence_number)


def fill_params(
    column: str,
    with_value: str,
    partition_by: str | None = None,
    order_by: list[list[str]] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a FILL (fill missing values) task payload.

    Args:
        column: Internal column name.
        with_value: Fill direction — "FIRST_VALUE" or "LAST_VALUE".
        partition_by: Internal column name to partition by.
        order_by: Sort order, e.g. [["column_1", "ASC"]].
    """
    fill: dict[str, Any] = {"COLUMN": column, "WITH": with_value}
    if partition_by is not None:
        fill["PARTITION_BY"] = partition_by
    if order_by is not None:
        fill["ORDER_BY"] = order_by
    params: dict[str, Any] = {"FILL": fill}
    return _attach_metadata(params, dataview_id, sequence_number)


def gen_ai_params(
    as_column: dict[str, Any],
    assistant_data: list[str],
    query: str,
    context_columns: list[str],
    context_columns_derivation: bool | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a GEN_AI (AI transformation) task payload.

    Args:
        as_column: New column spec.
        assistant_data: Sample data strings for context.
        query: Natural language prompt (lowercase key).
        context_columns: Internal column names for context (lowercase key).
        context_columns_derivation: Whether to derive from context columns.

    Note:
        ``query`` and ``context_columns`` use **lowercase** keys per AI_KEYWORDS.
    """
    gen_ai: dict[str, Any] = {
        "AS": as_column,
        "ASSISTANT_DATA": assistant_data,
        "query": query,
        "context_columns": context_columns,
    }
    if context_columns_derivation is not None:
        gen_ai["context_columns_derivation"] = context_columns_derivation
    params: dict[str, Any] = {"GEN_AI": gen_ai}
    return _attach_metadata(params, dataview_id, sequence_number)


def increment_date_params(
    source: str,
    delta: dict[str, Any],
    as_column: dict[str, Any] | None = None,
    destination: str | None = None,
    condition: dict[str, Any] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build an INCREMENT_DATE task payload.

    Args:
        source: Internal column name of the date column.
        delta: Date delta dict, e.g. {"YEAR": 1, "MONTH": -3}.
        as_column: New column spec.
        destination: Existing column internal name.
        condition: Optional condition dict.
    """
    increment_date: dict[str, Any] = {"SOURCE": source, "DELTA": delta}
    if as_column is not None:
        increment_date["AS"] = as_column
    if destination is not None:
        increment_date["DESTINATION"] = destination
    params: dict[str, Any] = {"INCREMENT_DATE": increment_date}
    _attach_condition(params, condition)
    return _attach_metadata(params, dataview_id, sequence_number)


def join_params(
    join_id: str,
    foreign_dataview_id: int,
    join_type: str,
    on: list[dict[str, Any]],
    select: list[dict[str, Any]],
    column_prefix: str | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a JOIN task payload.

    Args:
        join_id: Unique join identifier string.
        foreign_dataview_id: Dataview ID to join with.
        join_type: Join type — "INNER", "LEFT", "RIGHT", or "OUTER".
        on: Join keys with LEFT/RIGHT pairs.
        select: Columns to bring in with COLUMN/ALIAS pairs.
        column_prefix: Optional prefix for joined columns.

    Example:
        join_params(
            join_id="abc12",
            foreign_dataview_id=332,
            join_type="LEFT",
            on=[{"LEFT": "column_1", "RIGHT": "column_1"}],
            select=[{"COLUMN": "column_7", "ALIAS": "Category"}],
        )
    """
    join: dict[str, Any] = {
        "JOIN_ID": join_id,
        "DATAVIEW_ID": foreign_dataview_id,
        "TYPE": join_type,
        "ON": on,
        "SELECT": select,
    }
    if column_prefix is not None:
        join["COLUMN_PREFIX"] = column_prefix
    params: dict[str, Any] = {"JOIN": join}
    return _attach_metadata(params, dataview_id, sequence_number)


def json_handle_params(
    source: str,
    json_type: str,
    json_extract: list[dict[str, Any]],
    json_keep_source: bool = False,
    json_object_op_type: str | None = None,
    json_list_op_type: str | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a JSON_HANDLE (JSON extraction) task payload.

    Args:
        source: Internal column name of the JSON column.
        json_type: JSON type — "JSON_OBJECT" or "JSON_LIST".
        json_extract: Extraction specs.
        json_keep_source: Keep original JSON column (default False).
        json_object_op_type: Object operation type (e.g. "JSON_OBJECT_TO_COLUMNS").
        json_list_op_type: List operation type (e.g. "JSON_LIST_TO_ROWS").
    """
    json_handle: dict[str, Any] = {
        "SOURCE": source,
        "TYPE": json_type,
        "JSON_EXTRACT": json_extract,
        "JSON_KEEP_SOURCE": json_keep_source,
    }
    if json_object_op_type is not None:
        json_handle["JSON_OBJECT_OP_TYPE"] = json_object_op_type
    if json_list_op_type is not None:
        json_handle["JSON_LIST_OP_TYPE"] = json_list_op_type
    params: dict[str, Any] = {"JSON_HANDLE": json_handle}
    return _attach_metadata(params, dataview_id, sequence_number)


def limit_params(
    limit: int,
    bottom: bool = False,
    order_by: list[list[str]] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a LIMIT (top/bottom N rows) task payload.

    Args:
        limit: Number of rows to keep.
        bottom: If True, keep bottom N rows.
        order_by: Sort order before limiting.
    """
    params: dict[str, Any] = {
        "LIMIT": {"LIMIT": limit, "BOTTOM": bottom},
    }
    if order_by is not None:
        params["ORDER_BY"] = order_by
    return _attach_metadata(params, dataview_id, sequence_number)


def lookup_params(
    source: str,
    as_column: dict[str, Any] | None = None,
    destination: str | None = None,
    lookup_table: str | None = None,
    key: str | None = None,
    value: str | None = None,
    mapping: dict[str, Any] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a LOOKUP task payload.

    Args:
        source: Internal column name in the source view.
        as_column: New column spec.
        destination: Existing column internal name.
        lookup_table: Dataview ID (as string or int) to look up from.
        key: Key column internal name in the lookup view.
        value: Value column internal name in the lookup view.
        mapping: Optional mapping dict.
    """
    lookup: dict[str, Any] = {"SOURCE": source}
    if as_column is not None:
        lookup["AS"] = as_column
    if destination is not None:
        lookup["DESTINATION"] = destination
    if lookup_table is not None:
        lookup["TABLE"] = lookup_table
    if key is not None:
        lookup["KEY"] = key
    if value is not None:
        lookup["VALUE"] = value
    if mapping is not None:
        lookup["MAPPING"] = mapping
    params: dict[str, Any] = {"LOOKUP": lookup}
    return _attach_metadata(params, dataview_id, sequence_number)


def math_params(
    expression: list[Any],
    as_column: dict[str, Any] | None = None,
    destination: str | None = None,
    condition: dict[str, Any] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a MATH (arithmetic) task payload.

    Args:
        expression: List of expression parts (TYPE/VALUE dicts and nested lists).
        as_column: New column spec.
        destination: Existing column internal name.
        condition: Optional condition dict.
    """
    math: dict[str, Any] = {"EXPRESSION": expression}
    if as_column is not None:
        math["AS"] = as_column
    if destination is not None:
        math["DESTINATION"] = destination
    params: dict[str, Any] = {"MATH": math}
    _attach_condition(params, condition)
    return _attach_metadata(params, dataview_id, sequence_number)


def pivot_params(
    group_by: list[dict[str, Any]],
    select: list[dict[str, Any]],
    categories: dict[str, Any] | None = None,
    derived_select: list[dict[str, Any]] | None = None,
    condition: dict[str, Any] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a PIVOT (group/aggregate) task payload.

    Args:
        group_by: Group-by columns with COLUMN and ORDER keys.
        select: Aggregation specs with FUNCTION, COLUMN, AS, ORDER keys.
        categories: Optional category columns.
        derived_select: Optional derived aggregations.
        condition: Optional condition dict.

    Example:
        pivot_params(
            group_by=[{"COLUMN": "column_7", "ORDER": 0}],
            select=[{"FUNCTION": "SUM", "COLUMN": "column_12", "AS": "Total", "ORDER": 1}],
        )
    """
    pivot: dict[str, Any] = {"GROUP_BY": group_by, "SELECT": select}
    if categories is not None:
        pivot["CATEGORIES"] = categories
    if derived_select is not None:
        pivot["DERIVED_SELECT"] = derived_select
    if condition is not None:
        pivot["CONDITION"] = condition
    params: dict[str, Any] = {"PIVOT": pivot}
    return _attach_metadata(params, dataview_id, sequence_number)


def replace_params(
    source: list[str],
    value_pairs: list[dict[str, Any]] | None = None,
    match_case: bool | None = None,
    match_words: bool | None = None,
    condition: dict[str, Any] | None = None,
    mapping: list[dict[str, Any]] | None = None,
    as_column: dict[str, Any] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a REPLACE (find/replace) task payload.

    Args:
        source: List of internal column names.
        value_pairs: List of SEARCH_VALUE/REPLACE_VALUE dicts.
        match_case: Case-sensitive matching.
        match_words: Whole-word matching.
        condition: Optional condition dict.
        mapping: Bulk replace mapping (for BULK_REPLACE variant).
        as_column: New column spec.
    """
    replace: dict[str, Any] = {"SOURCE": source}
    if match_case is not None:
        replace["MATCH_CASE"] = match_case
    if match_words is not None:
        replace["MATCH_WORDS"] = match_words
    if value_pairs is not None:
        replace["VALUE_PAIR"] = value_pairs
    if mapping is not None:
        replace["MAPPING"] = mapping
    if as_column is not None:
        replace["AS"] = as_column
    params: dict[str, Any] = {"REPLACE": replace}
    _attach_condition(params, condition)
    return _attach_metadata(params, dataview_id, sequence_number)


def select_params(
    select_columns: list[str] | str,
    condition: dict[str, Any] | None = None,
    primary_key: bool | None = None,
    exclude_data: bool | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a SELECT (filter rows) task payload.

    Args:
        select_columns: "ALL" for all columns, or list of internal column names.
        condition: Condition dict with FILTER_TYPE and PROMPT keys.
        primary_key: Whether to use primary key.
        exclude_data: Whether to exclude data.

    Example:
        select_params("ALL", condition={"column_1": {"GTE": {"VALUE": 100}}, "FILTER_TYPE": "SHOW"})
    """
    params: dict[str, Any] = {"SELECT": select_columns}
    if primary_key is not None:
        params["PRIMARY_KEY"] = primary_key
    if exclude_data is not None:
        params["EXCLUDE_DATA"] = exclude_data
    _attach_condition(params, condition)
    return _attach_metadata(params, dataview_id, sequence_number)


def set_params(
    set_values: list[dict[str, Any]] | dict[str, Any],
    condition: dict[str, Any] | None = None,
    task_namespace: str | None = None,
    version: int | None = None,
    task_key_override: str | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a SET (label/insert values) task payload.

    Args:
        set_values: SET spec dict with AS/DESTINATION and VALUES keys,
                    or a list of such dicts.
        condition: Optional condition dict.
        task_namespace: Optional task namespace.
        version: Version number (typically 2).
        task_key_override: Override task key.

    Example:
        set_params(
            set_values={
                "AS": {"COLUMN": "Status", "TYPE": "TEXT"},
                "VALUES": [{"PROVIDER_TYPE": "FIXED", "PROVIDER": "Active"}],
            },
            version=2,
        )
    """
    values = set_values if isinstance(set_values, list) else [set_values]
    params: dict[str, Any] = {"SET": values}
    if task_namespace is not None:
        params["TASK_NAMESPACE"] = task_namespace
    if version is not None:
        params["VERSION"] = version
    if task_key_override is not None:
        params["TASK_KEY"] = task_key_override
    _attach_condition(params, condition)
    return _attach_metadata(params, dataview_id, sequence_number)


def split_params(
    source: str,
    delimiter: str,
    as_columns: list[dict[str, Any]],
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a SPLIT task payload.

    Args:
        source: Internal column name to split.
        delimiter: Delimiter string.
        as_columns: List of new column specs.
    """
    split: dict[str, Any] = {
        "SOURCE": source,
        "DELIMITER": delimiter,
        "AS": as_columns,
    }
    params: dict[str, Any] = {"SPLIT": split}
    return _attach_metadata(params, dataview_id, sequence_number)


def sql_params(
    intent: str | None = None,
    query: str | None = None,
    metadata: list[dict[str, Any]] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a SQL task payload.

    Args:
        intent: Natural language intent.
        query: Raw SQL query.
        metadata: Optional metadata for the query.
    """
    sql: dict[str, Any] = {}
    if intent is not None:
        sql["INTENT"] = intent
    if query is not None:
        sql["QUERY"] = query
    if metadata is not None:
        sql["METADATA"] = metadata
    params: dict[str, Any] = {"SQL": sql}
    return _attach_metadata(params, dataview_id, sequence_number)


def substring_params(
    source: str,
    direction: str | None = None,
    num_char: int | None = None,
    char_position: int | None = None,
    wildcard: str | None = None,
    include_wildcard: bool | None = None,
    regex: dict[str, Any] | None = None,
    as_column: dict[str, Any] | None = None,
    destination: str | None = None,
    condition: dict[str, Any] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a SUBSTRING (text extraction) task payload.

    Args:
        source: Internal column name.
        direction: "LEFT" or "RIGHT" for character-based extraction.
        num_char: Number of characters to extract.
        char_position: Character position to start from.
        wildcard: Wildcard string.
        include_wildcard: Whether to include the wildcard in output.
        regex: Regex extraction spec.
        as_column: New column spec.
        destination: Existing column internal name.
        condition: Optional condition dict.
    """
    substring: dict[str, Any] = {"SOURCE": source}
    if direction is not None:
        substring["DIRECTION"] = direction
    if num_char is not None:
        substring["NUM_CHAR"] = num_char
    if char_position is not None:
        substring["CHAR_POSITION"] = char_position
    if wildcard is not None:
        substring["WILDCARD"] = wildcard
    if include_wildcard is not None:
        substring["INC_WILDCARD"] = include_wildcard
    if regex is not None:
        substring["REGEX"] = regex
    if as_column is not None:
        substring["AS"] = as_column
    if destination is not None:
        substring["DESTINATION"] = destination
    params: dict[str, Any] = {"SUBSTRING": substring}
    _attach_condition(params, condition)
    return _attach_metadata(params, dataview_id, sequence_number)


def text_transform_params(
    sources: list[str],
    trim: bool,
    case: str | None = None,
    condition: dict[str, Any] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a TEXT_TRANSFORM task payload.

    Args:
        sources: List of internal column names.
        trim: Whether to trim whitespace.
        case: Text case — "UPPER", "LOWER", or "TITLE".
        condition: Optional condition dict.
    """
    text_transform: dict[str, Any] = {"SOURCE": sources, "TRIM": trim}
    if case is not None:
        text_transform["CASE"] = case
    params: dict[str, Any] = {"TEXT_TRANSFORM": text_transform}
    _attach_condition(params, condition)
    return _attach_metadata(params, dataview_id, sequence_number)


def unnest_params(
    columns: list[dict[str, Any]],
    label: dict[str, Any],
    value: dict[str, Any],
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build an UNNEST (unpivot) task payload.

    Args:
        columns: Column specs with COLUMN and LABEL keys.
        label: Label column spec (COLUMN, TYPE).
        value: Value column spec (COLUMN, TYPE).

    Example:
        unnest_params(
            columns=[{"COLUMN": "column_4", "LABEL": "Cashier"}],
            label={"COLUMN": "Label", "TYPE": "TEXT"},
            value={"COLUMN": "Value", "TYPE": "TEXT"},
        )
    """
    unnest: dict[str, Any] = {"COLUMNS": columns, "LABEL": label, "VALUE": value}
    params: dict[str, Any] = {"UNNEST": unnest}
    return _attach_metadata(params, dataview_id, sequence_number)


def window_params(
    evaluate: dict[str, Any],
    as_column: dict[str, Any] | None = None,
    destination: str | None = None,
    group_by: list[dict[str, Any]] | None = None,
    order_by: list[list[str]] | None = None,
    range_type: str = "UNBOUNDED",
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a WINDOW (window function) task payload.

    Args:
        evaluate: Evaluation spec with FUNCTION, SOURCES, and ARGUMENTS keys.
        as_column: New column spec.
        destination: Existing column internal name.
        group_by: Partition-by columns with COLUMN key.
        order_by: Sort order, e.g. [["column_1", "DESC"]].
        range_type: Window range — "UNBOUNDED" or "RUNNING".

    Example:
        window_params(
            evaluate={"FUNCTION": "SUM", "SOURCES": "column_1", "ARGUMENTS": ["column_1"]},
            as_column={"COLUMN": "Running Total", "TYPE": "NUMERIC"},
            group_by=[{"COLUMN": "column_2"}],
            order_by=[["column_3", "ASC"]],
        )
    """
    window: dict[str, Any] = {"EVALUATE": evaluate, "RANGE": range_type}
    if as_column is not None:
        window["AS"] = as_column
    if destination is not None:
        window["DESTINATION"] = destination
    if group_by is not None:
        window["GROUP_BY"] = group_by
    if order_by is not None:
        window["ORDER_BY"] = order_by
    params: dict[str, Any] = {"WINDOW": window}
    return _attach_metadata(params, dataview_id, sequence_number)


def discard_duplicates_params(
    ignore_columns: list[str] | None = None,
    dataview_id: int | None = None,
    sequence_number: int | None = None,
) -> dict[str, Any]:
    """Build a DISCARD_DUPLICATES task payload.

    Args:
        ignore_columns: Internal column names to ignore when detecting duplicates.
                        Empty list means consider all columns.

    Example:
        discard_duplicates_params(ignore_columns=["column_4", "column_7"])
    """
    params: dict[str, Any] = {
        "DISCARD_DUPLICATES": True,
        "IGNORE_COLUMNS": ignore_columns or [],
    }
    return _attach_metadata(params, dataview_id, sequence_number)
