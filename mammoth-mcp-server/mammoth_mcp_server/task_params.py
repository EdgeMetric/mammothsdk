"""Turn a transform operation into the task parameters the pipeline route takes.

Everything a step is built from is read through the SDK, as the caller: the
view's columns, a joined view's columns, and the query the AI writes for an
`sql` step. So a caller who may not see a view cannot build a step on it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from mammoth._pure.builders import (
    build_add_column_params,
    build_bulk_replace_params,
    build_combine_params,
    build_convert_params,
    build_copy_params,
    build_date_diff_params,
    build_delete_params,
    build_discard_duplicates_params,
    build_extract_date_params,
    build_fill_params,
    build_fill_value_params,
    build_filter_params,
    build_gen_ai_params,
    build_increment_date_params,
    build_join_params,
    build_json_extract_params,
    build_limit_params,
    build_lookup_params,
    build_math_params,
    build_pivot_params,
    build_replace_params,
    build_set_params,
    build_small_large_params,
    build_split_params,
    build_sql_params,
    build_substring_params,
    build_text_transform_params,
    build_unnest_params,
    build_window_params,
)
from mammoth._pure.resolve import resolve_column
from mammoth.client import MammothClient
from mammoth.condition import CompoundCondition, Condition, NotCondition
from mammoth.exceptions import MammothValidationError
from mammoth.models.pipeline import (
    AggregationSpec,
    BulkReplaceMapping,
    ConversionSpec,
    CopySpec,
    DateDelta,
    FilterType,
    JoinKeySpec,
    JoinSelectSpec,
    JsonExtractionSpec,
    SetValue,
    SmallLargeFunction,
    SplitColumnSpec,
)
from mammoth.view import View

from .consts import ApiFields, ColumnFields, SqlGenerationFields, TaskFields
from .transform_operations import (
    AddColumnOperation,
    BulkReplaceOperation,
    CombineOperation,
    ComparisonCondition,
    ConditionInput,
    ConvertOperation,
    CopyOperation,
    DateDiffOperation,
    DeleteOperation,
    DiscardDuplicatesOperation,
    ExtractDateOperation,
    FillNullOperation,
    FillOperation,
    GenAiOperation,
    GroupAggregateOperation,
    GroupCondition,
    IncrementDateOperation,
    JoinOperation,
    JsonExtractOperation,
    LimitOperation,
    LookupOperation,
    MathOperation,
    NegateCondition,
    ReplaceOperation,
    SelectRowsOperation,
    SetValuesOperation,
    SmallLargeOperation,
    SplitOperation,
    SqlOperation,
    SubstringOperation,
    TextTransformOperation,
    TransformOperation,
    UnnestOperation,
    WindowOperation,
)

_SQL_GENERATION_FAILED_MESSAGE = (
    "Could not generate a valid SQL query for that intent. Rephrase the "
    "transformation more concretely, or use a structured operation."
)


@dataclass(frozen=True)
class _ColumnContext:
    """A View's column metadata resolved once — the inputs every pysdk pure
    builder takes (mirrors their shared signature in ``mammoth._pure.builders``).

    ``col_map`` maps display→internal name, ``internal_names`` is every internal
    name (pass-through resolution), and ``column_types`` maps display→backend
    type (TEXT/NUMERIC/DATE) — the third input that condition-bearing operations
    (filter/set/math/…) forward to ``build_condition``.
    """

    col_map: dict[str, str]
    internal_names: list[str]
    column_types: dict[str, str]


def _to_column_context(metadata: list[dict[str, Any]]) -> _ColumnContext:
    """Bundle raw column metadata into the builder-context the pure builders take."""
    return _ColumnContext(
        col_map={
            col[ColumnFields.DISPLAY_NAME]: col[ColumnFields.INTERNAL_NAME] for col in metadata
        },
        internal_names=[col[ColumnFields.INTERNAL_NAME] for col in metadata],
        column_types={col[ColumnFields.DISPLAY_NAME]: col[ColumnFields.TYPE] for col in metadata},
    )


async def _column_context(
    client: MammothClient, view_id: int, dataset_id: int | None = None
) -> _ColumnContext:
    """A view's columns after its last step, as the API reports them to this caller.

    The full read lists the columns each step leaves, staged steps included. So
    in draft mode a step can use a column that an earlier staged step adds,
    with nothing run between them. The plain read lists only the columns of
    the data that exists.

    Args:
        client: The caller's SDK client.
        view_id: The view to read.
        dataset_id: The view's dataset. It is looked up when it is not given,
            as for a joined view the caller names by its id alone.
    """
    if dataset_id is None:
        try:
            dataset_id = await client.pipeline.find_dataset_for_dataview(view_id)
        except ValueError as missing:
            # The SDK's own words for a view the project does not hold.
            raise MammothValidationError(str(missing)) from missing
    data = await client.dataviews.get(dataset_id, view_id, fields=ApiFields.FULL)
    return _to_column_context(View(client, data, dataset_id).get_metadata())


# Agent condition `logic` (lowercase, LLM-friendly) -> pysdk CompoundCondition
# logic. A lookup, not a branch, so adding a logic word stays declarative.
_LOGIC_TO_PYSDK = {"and": "AND", "or": "OR"}


def _comparison_to_pysdk(c: ComparisonCondition) -> Condition:
    """A leaf comparison -> a pysdk ``Condition`` (its ``.build`` emits the param)."""
    return Condition(c.column, c.operator, c.value, case_sensitive=c.case_sensitive)


def _group_to_pysdk(c: GroupCondition) -> CompoundCondition:
    """An AND/OR group -> a pysdk ``CompoundCondition`` over converted children."""
    return CompoundCondition(
        _LOGIC_TO_PYSDK[c.logic], [_to_pysdk_condition(x) for x in c.conditions]
    )


def _negate_to_pysdk(c: NegateCondition) -> NotCondition:
    """A negation -> a pysdk ``NotCondition`` wrapping the converted child."""
    return NotCondition(_to_pysdk_condition(c.condition))


# Condition discriminator (``kind``) -> converter. The handler maps the agent's
# validated condition tree onto pysdk condition objects; the builders then call
# their ``.build(col_map, column_types)`` (the EQ/NE-on-TEXT remap lives there).
_CONDITION_CONVERTERS: dict[str, Callable[[Any], Condition | CompoundCondition | NotCondition]] = {
    "compare": _comparison_to_pysdk,
    "group": _group_to_pysdk,
    "not": _negate_to_pysdk,
}


def _to_pysdk_condition(
    cond: ConditionInput,
) -> Condition | CompoundCondition | NotCondition:
    """Recursively map an agent ``ConditionInput`` tree onto pysdk conditions."""
    return _CONDITION_CONVERTERS[cond.kind](cond)


def _build_convert_param(op: ConvertOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``convert`` operation to a backend CONVERT task param."""
    specs = [
        ConversionSpec(column=cv.column, to=cv.to_type, format=cv.date_format)
        for cv in op.conversions
    ]
    return build_convert_params(specs, cols.col_map, cols.internal_names)


def _build_text_transform_param(op: TextTransformOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``text_transform`` operation to a TEXT_TRANSFORM param."""
    return build_text_transform_params(
        op.columns, cols.col_map, cols.internal_names, case=op.case, trim=op.trim
    )


def _build_discard_duplicates_param(
    op: DiscardDuplicatesOperation, cols: _ColumnContext
) -> dict[str, Any]:
    """Map a validated ``discard_duplicates`` operation to a DISCARD_DUPLICATES param."""
    return build_discard_duplicates_params(
        cols.col_map, cols.internal_names, ignore_columns=op.ignore_columns or None
    )


def _build_replace_param(op: ReplaceOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``replace`` operation to a REPLACE param."""
    return build_replace_params(
        op.columns,
        cols.col_map,
        cols.internal_names,
        op.find,
        op.replace,
        match_case=op.match_case,
        match_words=op.match_words,
    )


def _build_fill_null_param(op: FillNullOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``fill_null`` operation to a SET+IS_EMPTY param (literal fill)."""
    return build_fill_value_params(op.column, op.value, cols.col_map, cols.internal_names)


def _build_math_param(op: MathOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``math`` operation to a MATH (computed column) param.

    The expression string is tokenised against the display→internal map by the
    pysdk builder, so the agent writes the formula in display-name terms.
    """
    return build_math_params(
        op.expression,
        cols.col_map,
        new_column=op.new_column,
        column_type=op.column_type,
    )


def _build_combine_param(op: CombineOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``combine`` operation to a COMBINE (concatenate) param."""
    return build_combine_params(
        op.columns,
        cols.col_map,
        cols.internal_names,
        new_column=op.new_column,
        column_type=op.column_type,
        separator=op.separator,
    )


def _build_add_column_param(op: AddColumnOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``add_column`` operation to an ADD_COLUMN param.

    The new column is independent of existing data, so the column context is
    unused here (the uniform ``(op, cols)`` signature keeps the registry flat).
    """
    return build_add_column_params(op.name, column_type=op.column_type)


def _build_copy_param(op: CopyOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``copy`` operation to a COPY (duplicate columns) param.

    A per-copy condition (when present) becomes the pysdk ``CopySpec.condition``,
    so only matching rows carry the copied value into the new column.
    """
    specs = [
        CopySpec(
            source=c.source,
            as_name=c.new_name,
            type=c.column_type,
            condition=_to_pysdk_condition(c.condition) if c.condition else None,
        )
        for c in op.copies
    ]
    return build_copy_params(specs, cols.col_map, cols.internal_names, cols.column_types)


def _build_select_param(op: SelectRowsOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``select`` operation to a SELECT (row filter) param.

    ``keep_matching`` chooses the backend filter direction: SHOW keeps the rows
    that match the condition, REMOVE drops them. The condition tree is converted
    to pysdk objects whose ``.build`` resolves display names + the EQ/NE-on-TEXT
    remap against ``column_types``.
    """
    filter_type = FilterType.SHOW if op.keep_matching else FilterType.REMOVE
    return build_filter_params(
        _to_pysdk_condition(op.condition),
        cols.col_map,
        cols.column_types,
        filter_type,
    )


def _build_set_param(op: SetValuesOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``set`` operation to a SET (label/insert values) param.

    Each value's optional condition becomes a pysdk ``SetValue.condition``; the
    step targets either a new column (``AS`` with a generated internal name) or
    an existing one (``DESTINATION``), per the input's exactly-one invariant.
    """
    values = [
        SetValue(
            v.value,
            condition=_to_pysdk_condition(v.condition) if v.condition else None,
        )
        for v in op.values
    ]
    return build_set_params(
        values,
        cols.col_map,
        new_column=op.new_column,
        column_type=op.column_type,
        existing_column=op.existing_column,
        internal_names=cols.internal_names,
        condition=_to_pysdk_condition(op.condition) if op.condition else None,
        column_types=cols.column_types,
    )


def _build_join_param(
    op: JoinOperation, cols: _ColumnContext, foreign: _ColumnContext
) -> dict[str, Any]:
    """Map a validated ``join`` operation to a JOIN task param.

    ``on[].left`` / ``select`` reference the target View (resolved via ``cols``);
    ``on[].right`` references the foreign View, so the builder is handed its
    display→internal ``foreign_columns`` map. The backend matches ON keys by
    internal name, so this resolution is required, not cosmetic.
    """
    return build_join_params(
        op.foreign_view_id,
        op.join_type,
        [JoinKeySpec(left=k.left, right=k.right) for k in op.on],
        [JoinSelectSpec(column=s.column, alias=s.alias) for s in op.select],
        cols.col_map,
        cols.internal_names,
        foreign_columns=foreign.col_map,
        column_prefix=op.column_prefix,
    )


def _build_lookup_param(
    op: LookupOperation, cols: _ColumnContext, foreign: _ColumnContext
) -> dict[str, Any]:
    """Map a validated ``lookup`` operation to a LOOKUP task param.

    ``source`` is a target column (resolved by the builder via ``cols``). The
    builder passes ``key``/``value`` through verbatim, but the backend resolves
    them in the foreign View's metadata by *internal* name — so we resolve them
    against the foreign column context here before handing them over.
    """
    return build_lookup_params(
        op.source,
        op.foreign_view_id,
        resolve_column(op.key, foreign.col_map, foreign.internal_names),
        resolve_column(op.value, foreign.col_map, foreign.internal_names),
        cols.col_map,
        cols.internal_names,
        new_column=op.new_column,
        existing_column=op.existing_column,
    )


def _build_gen_ai_param(op: GenAiOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``gen_ai`` operation to a GEN_AI (AI column) param.

    The builder resolves ``context_columns`` to internal names; the backend runs
    the generative model per row at execution time using ``prompt``."""
    return build_gen_ai_params(
        op.prompt,
        op.context_columns,
        cols.col_map,
        cols.internal_names,
        new_column=op.new_column,
    )


def _build_delete_param(op: DeleteOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``delete`` operation to a DELETE (remove columns) param."""
    return build_delete_params(op.columns, cols.col_map, cols.internal_names)


def _build_limit_param(op: LimitOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``limit`` operation to a LIMIT (top/bottom N rows) param.

    ``order_by`` is converted to [[column, direction], ...] — the shape
    ``resolve_order_by`` expects; display names are resolved to internals there.
    """
    order_by = [[ob.column, ob.direction.value] for ob in op.order_by] if op.order_by else None
    return build_limit_params(op.n, cols.col_map, bottom=op.bottom, order_by=order_by)


def _build_substring_param(op: SubstringOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``substring`` operation to a SUBSTRING (text extract) param."""
    return build_substring_params(
        op.column,
        cols.col_map,
        cols.internal_names,
        direction=op.direction,
        num_char=op.num_char,
        char_position=op.char_position,
        regex_pattern=op.regex_pattern,
        regex_invert=op.regex_invert,
        new_column=op.new_column,
        existing_column=op.existing_column,
        condition=_to_pysdk_condition(op.condition) if op.condition else None,
        column_types=cols.column_types,
    )


def _build_split_param(op: SplitOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``split`` operation to a SPLIT (delimiter split) param."""
    new_columns = [SplitColumnSpec(name=nc.name, type=nc.column_type) for nc in op.new_columns]
    return build_split_params(
        op.column,
        op.delimiter,
        new_columns,
        cols.col_map,
        cols.internal_names,
    )


def _build_bulk_replace_param(op: BulkReplaceOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``bulk_replace`` operation to a REPLACE+MAPPING param.

    Each ``BulkReplaceMappingInput`` becomes a ``BulkReplaceMapping`` dataclass
    the pysdk builder serialises to the backend MAPPING list.
    """
    mapping = [BulkReplaceMapping(search=m.search, replace=m.replace) for m in op.mapping]
    return build_bulk_replace_params(
        op.columns,
        cols.col_map,
        cols.internal_names,
        mapping,
        match_case=op.match_case,
        match_words=op.match_words,
        condition=_to_pysdk_condition(op.condition) if op.condition else None,
        column_types=cols.column_types,
    )


def _build_fill_param(op: FillOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``fill`` operation to a FILL (propagation fill) param.

    ``order_by`` uses the same [[column, direction], ...] shape as limit.
    """
    order_by = [[ob.column, ob.direction.value] for ob in op.order_by] if op.order_by else None
    return build_fill_params(
        op.column,
        op.direction,
        cols.col_map,
        cols.internal_names,
        partition_by=op.partition_by,
        order_by=order_by,
    )


def _build_extract_date_param(op: ExtractDateOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``extract_date`` operation to an EXTRACT_DATE param."""
    return build_extract_date_params(
        op.column,
        op.component,
        cols.col_map,
        cols.internal_names,
        new_column=op.new_column,
        existing_column=op.existing_column,
    )


def _build_date_diff_param(op: DateDiffOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``date_diff`` operation to a DATE_DIFF param."""
    return build_date_diff_params(
        op.unit,
        op.start,
        op.end,
        cols.col_map,
        cols.internal_names,
        new_column=op.new_column,
        existing_column=op.existing_column,
    )


def _build_increment_date_param(op: IncrementDateOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``increment_date`` operation to an INCREMENT_DATE param.

    ``DateDeltaInput`` fields are mapped onto the pysdk ``DateDelta`` dataclass
    field-for-field (both use the same zero-default, non-zero-only semantics).
    """
    delta = DateDelta(
        years=op.delta.years,
        months=op.delta.months,
        weeks=op.delta.weeks,
        days=op.delta.days,
        hours=op.delta.hours,
        minutes=op.delta.minutes,
        seconds=op.delta.seconds,
    )
    return build_increment_date_params(
        op.column,
        delta,
        cols.col_map,
        cols.internal_names,
        new_column=op.new_column,
        existing_column=op.existing_column,
        condition=_to_pysdk_condition(op.condition) if op.condition else None,
        column_types=cols.column_types,
    )


def _build_small_large_param(op: SmallLargeOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``small_large`` operation to a SMALL/LARGE param.

    The ranked value sources are the source ``columns`` followed by any numeric
    ``constants`` — order is irrelevant to a min/max selection, so they are
    simply concatenated into the builder's ``values`` argument.
    """
    return build_small_large_params(
        function=SmallLargeFunction(op.function),
        values=[*op.columns, *op.constants],
        index=op.index,
        col_map=cols.col_map,
        internal_names=cols.internal_names,
        new_column=op.new_column,
        existing_column=op.existing_column,
    )


def _build_json_extract_param(op: JsonExtractOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``json_extract`` operation to a JSON_HANDLE param.

    ``extractions`` items become ``JsonExtractionSpec`` dataclasses; ``keys``
    is passed through directly for the simpler all-TEXT form.
    """
    extractions = (
        [
            JsonExtractionSpec(key=e.key, as_name=e.as_name, type=e.column_type)
            for e in op.extractions
        ]
        if op.extractions is not None
        else None
    )
    return build_json_extract_params(
        op.column,
        cols.col_map,
        cols.internal_names,
        json_type=op.json_type,
        keys=op.keys,
        extractions=extractions,
        keep_source=op.keep_source,
    )


def _build_group_aggregate_param(
    op: GroupAggregateOperation, cols: _ColumnContext
) -> dict[str, Any]:
    """Map a validated ``group_aggregate`` operation to a PIVOT (group/aggregate) param.

    SHAPE-CHANGING — replaces the dataset with one row per unique group_by
    combination; apply after row-level steps.
    """
    aggregations = [
        AggregationSpec(
            column=a.column,
            function=a.function,
            as_name=a.as_name,
            delimiter=a.delimiter,
        )
        for a in op.aggregations
    ]
    return build_pivot_params(
        op.group_by,
        aggregations,
        cols.col_map,
        cols.internal_names,
        condition=_to_pysdk_condition(op.condition) if op.condition else None,
        column_types=cols.column_types,
    )


def _build_window_param(op: WindowOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``window`` operation to a WINDOW (window function) param.

    ADDITIVE — appends a new column; row count is unchanged.
    ``order_by`` is passed as [[column, direction], ...] — the shape
    ``resolve_order_by`` expects.
    """
    order_by = [[ob.column, ob.direction.value] for ob in op.order_by] if op.order_by else None
    return build_window_params(
        op.function,
        cols.col_map,
        cols.internal_names,
        column=op.column,
        new_column=op.new_column,
        column_type=op.column_type,
        existing_column=op.existing_column,
        partition_by=op.partition_by or None,
        order_by=order_by,
        range_type=op.range_type,
    )


def _build_unnest_param(op: UnnestOperation, cols: _ColumnContext) -> dict[str, Any]:
    """Map a validated ``unnest`` operation to an UNNEST (unpivot) param.

    SHAPE-CHANGING — fans out: each selected column becomes a row pair
    (label + value), multiplying row count.
    """
    return build_unnest_params(
        op.columns,
        cols.col_map,
        cols.internal_names,
        label_column=op.label_column,
        value_column=op.value_column,
    )


async def _build_sql_param(
    client: MammothClient, op: SqlOperation, dataset_id: int, view_id: int
) -> dict[str, Any]:
    """Resolve a plain-English ``sql`` intent into a validated SQL task param.

    The API's AI writes the query and validates it against the view's columns
    and sample values. It is asked for the step after the view's last one, so
    it grounds the query on the data that step leaves. The backend translates
    the query's display names to internal names at run time.

    Raises:
        MammothValidationError: The AI wrote no valid query. The message is the
            AI's own reason, for the caller to rephrase the intent.
    """
    sequence = await client.pipeline.latest_task_sequence(view_id, dataset_id) + 1
    answer = await client.ai.generate_sql(
        op.intent, sequence_number=sequence, dataset_id=dataset_id, dataview_id=view_id
    )
    response = answer.get(SqlGenerationFields.RESPONSE) or {}
    if response.get(SqlGenerationFields.STATUS_CODE) != SqlGenerationFields.SUCCESS:
        raise MammothValidationError(
            response.get(SqlGenerationFields.DETAIL) or _SQL_GENERATION_FAILED_MESSAGE
        )
    return build_sql_params(response[SqlGenerationFields.RESULT])


# Operation discriminator (``operation.op``) -> pure param builder. Adding a
# transform operation is purely additive: a new spec in the ``TransformOperation``
# union (transform_operations.py) + one entry here.
_OPERATION_BUILDERS: dict[str, Callable[..., dict[str, Any]]] = {
    "add_column": _build_add_column_param,
    "bulk_replace": _build_bulk_replace_param,
    "combine": _build_combine_param,
    "convert": _build_convert_param,
    "copy": _build_copy_param,
    "date_diff": _build_date_diff_param,
    "delete": _build_delete_param,
    "discard_duplicates": _build_discard_duplicates_param,
    "extract_date": _build_extract_date_param,
    "fill": _build_fill_param,
    "fill_null": _build_fill_null_param,
    "gen_ai": _build_gen_ai_param,
    "group_aggregate": _build_group_aggregate_param,
    "increment_date": _build_increment_date_param,
    "json_extract": _build_json_extract_param,
    "limit": _build_limit_param,
    "math": _build_math_param,
    "replace": _build_replace_param,
    "select": _build_select_param,
    "set": _build_set_param,
    "small_large": _build_small_large_param,
    "split": _build_split_param,
    "substring": _build_substring_param,
    "text_transform": _build_text_transform_param,
    "unnest": _build_unnest_param,
    "window": _build_window_param,
}


# Multi-view operations live in a separate registry because their builders
# need a third argument: the columns of the second view.
_FOREIGN_OPERATION_BUILDERS: dict[
    str, Callable[[Any, _ColumnContext, _ColumnContext], dict[str, Any]]
] = {
    "join": _build_join_param,
    "lookup": _build_lookup_param,
}


async def build_task_param(
    client: MammothClient, op: TransformOperation, dataset_id: int, view_id: int
) -> dict[str, Any]:
    """Build the pipeline task param that adds one operation to a View.

    Column display names resolve against the columns the API reports for the
    view, so in draft mode a step may reference a column an earlier staged step
    created.

    Args:
        client: The caller's SDK client, in the view's project.
        op: The validated operation.
        dataset_id: The view's dataset.
        view_id: The view the step is for.

    Raises:
        MammothColumnError: The operation names a column the View does not have.
        MammothValidationError: The operation's arguments do not fit together.
    """
    if isinstance(op, SqlOperation):
        param = await _build_sql_param(client, op, dataset_id, view_id)
    else:
        cols = await _column_context(client, view_id, dataset_id)
        if isinstance(op, JoinOperation | LookupOperation):
            foreign = await _column_context(client, op.foreign_view_id)
            param = _FOREIGN_OPERATION_BUILDERS[op.op](op, cols, foreign)
        else:
            param = _OPERATION_BUILDERS[op.op](op, cols)
    param[TaskFields.DATAVIEW_ID] = view_id
    return param
