"""``view data explore`` handler and its text-date helpers."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.view._common import (
    _forward_optional,
    _read_meta,
    _require_int_positional_at,
    _resolve_dataset_id,
    _symbol,
)
from mammoth_cli.commands.view.column_checks import (
    _column_profile_with_currency,
)
from mammoth_cli.commands.view.columns import (
    _measures,
    _relabel_columns,
    _resolved_aggregate_item,
    _with_currency,
)
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENTS,
    CODE_MISSING_ARGUMENT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import (
    open_service,
    require_project,
)
from mammoth_cli.services import read_queries, text_dates
from mammoth_cli.services.conditions import CONDITION_KWARG, compile_condition
from mammoth_cli.services.read_queries import ReadContext


def _require_string_positional_at(invocation: Invocation, index: int, name: str) -> str:
    """Return the positional argument at ``index`` as a nonblank string, or raise."""
    if len(invocation.extra_args) <= index or not str(invocation.extra_args[index]).strip():
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return str(invocation.extra_args[index])


def _explore_wants_text_dates(document: dict[str, Any], column: str, stored: str) -> bool:
    """Whether this explore buckets a TEXT column of dates; fail loud on a type it cannot honour.

    The column's stored type decides how it is read. A ``column_type`` that
    disagrees is refused with the reason (a read cannot re-type a column), except
    DATE over a TEXT column, which is parsed from the data. A bucket ``level`` on
    a TEXT column means the same.
    """
    requested = str(document.get("column_type") or "").upper()
    level = document.get("level")
    if requested and stored and requested != stored:
        if stored == "TEXT" and requested == "DATE":
            return True
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message=f"column_type {requested} does not match '{column}', which is stored as "
            f"{stored}; a read cannot re-type a column.",
            exit_status=EXIT_USAGE,
            hint="Drop column_type (the stored type is used), or convert the column with "
            "'view transform convert-type' (a pipeline write).",
        )
    if level is not None and stored and stored not in ("DATE", "NUMERIC", "TEXT"):
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message=f"'level' buckets a DATE, NUMERIC or TEXT-date column; '{column}' is {stored}.",
            exit_status=EXIT_USAGE,
        )
    return stored == "TEXT" and level is not None


def _explore_text_dates(
    reads: ReadContext, document: dict[str, Any], internal_column: str, metric: Any
) -> dict[str, Any]:
    """Explore a TEXT column of dates: count per ``level`` bucket, parsed from the data."""
    level = text_dates.require_level(document.get("level"))
    aggregations: list[dict[str, Any]] = [{"function": "COUNT", "as_name": "count"}]
    if metric is not None:
        aggregations.append(metric)
    condition = None
    if document.get(CONDITION_KWARG) is not None:
        spec = read_queries.resolve_text_date_conditions(reads, document[CONDITION_KWARG])
        condition = compile_condition(spec).build(
            reads.display_to_internal or None, reads.column_types or None
        )
    response = read_queries.pivot_with_text_dates(
        reads,
        aggregations=aggregations,
        group_by=[internal_column],
        levels={0: level},
        condition=condition,
    )
    page = (document.get("offset"), document.get("limit"))
    rows = read_queries.apply_explore_order(
        response["data"],
        document.get("sort"),
        page,
        bool(document.get("cumulative")),
        document.get("percentage_of"),
    )
    return {**response, "data": rows}


def _explore_range(
    reads: ReadContext, document: dict[str, Any], column: str, text_dates_read: bool
) -> dict[str, Any]:
    """The explored column's exact earliest and latest value, under the explore condition."""
    condition = None
    if document.get(CONDITION_KWARG) is not None:
        spec = read_queries.resolve_text_date_conditions(reads, document[CONDITION_KWARG])
        condition = compile_condition(spec).build(
            reads.display_to_internal or None, reads.column_types or None
        )
    return read_queries.explore_range(reads, column, condition, text_dates_read)


def view_data_explore(invocation: Invocation) -> HandlerResult:
    """Read one column's values: top values, distribution, trend over time, date range (read-only; this is not an Explore card, it opens and changes no card in the UI, that is ``view explore-panel set``): DATE counts per ``level`` bucket (AUTO, SECOND to MILLENNIUM), NUMERIC per power-of-10 ``level``, TEXT top values (``limit`` 20), each with ``count`` and ``percentage``; ``metric`` (a column plus SUM/AVG/MIN/MAX/STDDEV/COUNT/DISTINCT_COUNT) adds a per-bucket value, ``percentage_of`` "metric" shares by it, ``sort`` count_/value_/metric_ + asc/desc, ``condition`` filters first (include, exclude, blanks, range, contains; an exclude drops blank rows the card keeps, so or it with IS_EMPTY; drill down = finer ``level`` + ``condition`` on the bucket), ``limit``/``offset`` page, ``range`` true adds the exact earliest and latest value, ``cumulative`` a running total; ``-o csv`` saves the values; to put it on a dashboard say it in words to 'dashboard chat edit'.

    Read-only: computes and returns the result without adding a task to the
    view's pipeline or otherwise changing it. Buckets by the column's type --
    a DATE column by ``level`` (default "AUTO"; or DAY/WEEK/MONTH/QUARTER/
    YEAR/...) for a trend "over time"/"by month"/"by year"; a NUMERIC column
    by ``level`` resolution (default "AUTO") for a distribution/histogram; any
    other column (TEXT) as its top values by count, ``limit`` (default 20).
    A TEXT column of dates with a ``level`` (or ``column_type`` DATE) is parsed
    from the data -- the format is detected and stated in ``text_dates``, and an
    ambiguous or unreadable column fails loud.
    Every bucket carries ``count`` and ``percentage`` of the column's total.
    A TEXT column also carries ``spelling_variants``: how many groups of one value
    spelled several ways its values hold (``view data profile`` lists them).
    An optional ``metric`` ``{"column": ..., "function": ...}`` (SUM, COUNT,
    AVG, MIN, MAX, STDDEV or DISTINCT_COUNT) adds a second aggregate per bucket over another column,
    and an optional ``condition`` filters rows first -- same as ``view data
    aggregate``, which this command wraps for the raw PIVOT shape. A date range
    is one ``and`` condition (``>=`` a start, ``<=`` an end); one year is
    ``{"column": ..., "operator": "=", "value": 2017, "component": "year"}``.
    ``percentage_of: "metric"`` makes ``percentage`` each bucket's share of the ``metric`` total
    (default: of the count). ``sort`` ``metric_desc``/``metric_asc`` ranks by the ``metric``.
    ``range: true`` adds ``range`` {column, type, min, max}: the exact earliest and latest
    value of a DATE (or NUMERIC) column under the same ``condition``. Excluding a value
    (NE, NOT_IN_LIST, ``not``) also drops blank rows, but the card keeps them: write
    ``or`` of the exclusion and IS_EMPTY on that column to match the card. Blank buckets
    sort last here, first in the card. ``-o csv`` prints the buckets as CSV.
    ``cumulative: true`` adds a running total of the metric (of ``count`` without
    one) over the buckets in date order, whatever ``sort`` or ``limit`` shows:
    the answer to "cumulative / running total through X". Figures are rounded for
    display (2 decimals; 4 below 1). Never use
    ``view transform pivot`` just to explore a column; it mutates the
    pipeline.
    """  # noqa: E501
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    column_arg = _require_string_positional_at(invocation, 1, "column")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document, 2)
        meta = _read_meta(service, invocation, auth.workspace_id, dataset_id, view_id, project_id)
        internal_to_display, column_types, currencies = _column_profile_with_currency(
            service, dataset_id, view_id, project_id
        )
        display_to_internal = {
            display: internal for internal, display in internal_to_display.items()
        }
        internal_column = display_to_internal.get(column_arg, column_arg)
        column_type = column_types.get(column_arg, "")
        reads = ReadContext(
            service,
            dataset_id,
            view_id,
            project_id,
            display_to_internal,
            column_types,
            document.get("sequence"),
            document.get("text_date_format"),
        )
        bucket_dates = _explore_wants_text_dates(document, column_arg, column_type)
        as_map: dict[str, str] = {"group_0": "bucket", "agg_0": "count"}
        metric = document.get("metric")
        resolved_metric = None
        if isinstance(metric, dict):
            resolved_metric = _resolved_aggregate_item(metric, display_to_internal)
            as_map["agg_1"] = resolved_metric["as_name"]
        if document.get("cumulative"):
            as_map["cumulative"] = f"{as_map.get('agg_1', 'count')} (running total)"
        if bucket_dates:
            data = _explore_text_dates(reads, document, internal_column, resolved_metric)
        else:
            data = _explore_on_backend(
                invocation, reads, document, (internal_column, column_type), resolved_metric
            )
        data = _relabel_columns(service, dataset_id, view_id, project_id, data, as_map)
        range_columns = read_queries.condition_columns(document.get(CONDITION_KWARG))
        if bucket_dates:
            range_columns.append(column_arg)
        data = read_queries.with_observed_range(reads, data, list(dict.fromkeys(range_columns)))
        if document.get("range") and isinstance(data, dict):
            data = {**data, "range": _explore_range(reads, document, column_arg, bucket_dates)}
        data = read_queries.with_assumptions(reads, data)
        if not bucket_dates:
            data = read_queries.with_variant_hint(reads, data, column_arg)
        data = _with_currency(data, _measures(document), currencies)
    return read_queries.round_result_rows(data), meta


def _explore_on_backend(
    invocation: Invocation,
    reads: ReadContext,
    document: dict[str, Any],
    column: tuple[str, str],
    metric: dict[str, Any] | None,
) -> Any:
    """Explore a DATE, NUMERIC or plain TEXT column through the SDK's own bucketing."""
    kwargs: dict[str, Any] = {
        "dataset_id": reads.dataset_id,
        "dataview_id": reads.view_id,
        "project_id": reads.project_id,
        "column": column[0],
        "column_type": column[1],
    }
    if metric is not None:
        kwargs["metric"] = metric
    if document.get(CONDITION_KWARG) is not None:
        spec = read_queries.resolve_text_date_conditions(reads, document[CONDITION_KWARG])
        kwargs[CONDITION_KWARG] = compile_condition(spec).build(
            reads.display_to_internal or None, reads.column_types or None
        )
    _forward_optional(
        document,
        kwargs,
        ("level", "sequence", "limit", "offset", "sort", "cumulative", "percentage_of"),
    )
    return reads.service.call(_symbol(invocation), **kwargs)
