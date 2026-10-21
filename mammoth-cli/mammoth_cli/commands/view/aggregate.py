"""``view data aggregate`` / ``view data compare`` handlers and the aggregate helpers."""

from __future__ import annotations

import dataclasses
from decimal import Decimal, InvalidOperation
from typing import Any

from mammoth_cli.commands.view._common import (
    _ROWS_KEY,
    HandlerResult,
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
    CODE_MISSING_FIELD,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import (
    open_service,
    require_project,
)
from mammoth_cli.services import read_queries
from mammoth_cli.services.conditions import CONDITION_KWARG, compile_condition
from mammoth_cli.services.read_queries import ReadContext


def _build_pivot_fields(
    document: dict[str, Any], column_map: dict[str, str]
) -> tuple[dict[str, Any], dict[str, str]]:
    """Resolve ``aggregations``/``group_by`` into SDK kwargs and an as_map.

    The as_map (``agg_0``/``group_0``/... -> the display label) mirrors the
    internal-name scheme :func:`mammoth.api.dataviews._build_pivot_param`
    assigns from the same list, in the same order — keep the two in step.
    """
    aggregations = document.get("aggregations")
    if not isinstance(aggregations, list) or not aggregations:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="'aggregations' is required for a PIVOT and must be a non-empty list.",
            exit_status=EXIT_USAGE,
            hint='--input \'{"aggregations": [{"column": "Sales", "function": "SUM"}]}\'',
        )
    resolved_aggregations = [_resolved_aggregate_item(agg, column_map) for agg in aggregations]
    as_map = {f"agg_{index}": item["as_name"] for index, item in enumerate(resolved_aggregations)}
    fields: dict[str, Any] = {"aggregations": resolved_aggregations}
    group_by = document.get("group_by")
    if group_by:
        # A string groups by the column's values; {column, truncate|resolution}
        # buckets a DATE (DAY..YEAR) or NUMERIC column first, like Explore.
        columns = [item["column"] if isinstance(item, dict) else item for item in group_by]
        fields["group_by"] = [
            (
                {**item, "column": column_map.get(item["column"], item["column"])}
                if isinstance(item, dict)
                else column_map.get(item, item)
            )
            for item in group_by
        ]
        as_map.update({f"group_{index}": column for index, column in enumerate(columns)})
    return fields, as_map


def _build_metric_fields(
    document: dict[str, Any], column_map: dict[str, str]
) -> tuple[dict[str, Any], dict[str, str]]:
    """Resolve a ``metric`` field into SDK kwargs and an as_map."""
    metric = document.get("metric")
    if not isinstance(metric, dict):
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="'metric' is required and must be an object.",
            exit_status=EXIT_USAGE,
            hint='--input \'{"metric": {"column": "Sales", "function": "SUM"}}\'',
        )
    resolved = _resolved_aggregate_item(metric, column_map)
    return {"metric": resolved}, {"metric": resolved["as_name"]}


_METRIC_ANY_TYPE_FUNCTIONS = frozenset({"COUNT", "DISTINCT_COUNT"})


def _require_numeric_metric(
    document: dict[str, Any], column_types: dict[str, str], view_id: int
) -> None:
    """Refuse a METRIC the backend cannot compute: it stores a NUMERIC value,
    so only COUNT/DISTINCT_COUNT work on a non-numeric column."""
    metric = document.get("metric")
    if not isinstance(metric, dict):
        return
    column = metric.get("column")
    function = str(metric.get("function", "")).upper()
    column_type = column_types.get(str(column), "")
    if function in _METRIC_ANY_TYPE_FUNCTIONS or column_type in ("", "NUMERIC"):
        return
    if column_type == "TEXT":
        hint = (
            f"MIN/MAX of a TEXT column is alphabetical, never chronological. If '{column}' "
            f"holds dates, run: mammoth view data explore {view_id} {column} --input "
            '\'{"column_type": "DATE", "level": "YEAR"}\' for its range by year '
            "(the format is detected from the data and stated in the result)."
        )
    else:
        hint = (
            f"For the latest or earliest value run: mammoth view data explore {view_id} "
            f'{column} --input \'{{"column_type": "{column_type}", "level": "DAY", '
            '"sort": "value_desc", "limit": 1}\' (value_asc for the earliest).'
        )
    raise CliError(
        code=CODE_INVALID_ARGUMENTS,
        message=f"A metric is a number: {function} of the {column_type} column '{column}' "
        "cannot be computed here.",
        exit_status=EXIT_USAGE,
        hint=hint,
    )


def _plain_text_date_groups(
    document: dict[str, Any], levels: dict[int, str], column_types: dict[str, str]
) -> dict[str, Any]:
    """The document with each CLI-bucketed group_by entry reduced to what the backend groups by.

    A TEXT date is grouped by its raw stored string; a DATE column with a ``part``
    by day. The CLI buckets the result afterwards.
    """
    if not levels:
        return document
    group_by = [
        _backend_group(item, column_types) if index in levels else item
        for index, item in enumerate(document["group_by"])
    ]
    return {**document, "group_by": group_by}


def _backend_group(item: dict[str, Any], column_types: dict[str, str]) -> Any:
    if column_types.get(str(item["column"])) == "TEXT":
        return item["column"]
    return {"column": item["column"], "truncate": "DAY"}


def _aggregate_range_columns(document: dict[str, Any], column_types: dict[str, str]) -> list[str]:
    """Columns an empty aggregate should report the observed range of."""
    columns = read_queries.condition_columns(document.get(CONDITION_KWARG))
    for item in document.get("group_by") or []:
        if isinstance(item, dict) and (item.get("truncate") or item.get("part")) is not None:
            columns.append(str(item["column"]))
    return list(dict.fromkeys(columns))


def _reject_order_on_metric(document: dict[str, Any]) -> None:
    if any(document.get(key) is not None for key in ("order_by", "top")):
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message="'order_by' and 'top' rank the rows of a group-by; a single 'metric' has none.",
            exit_status=EXIT_USAGE,
            hint="Use 'aggregations' with 'group_by' to rank groups.",
        )


def _run_aggregate(
    reads: ReadContext,
    symbol: str,
    document: dict[str, Any],
    fields: dict[str, Any],
    order: tuple[list[list[str]] | None, int | None],
    levels: dict[int, str],
) -> Any:
    """Run the aggregate: on the backend, or (a TEXT-date group) bucketed in the CLI."""
    sort, top = order
    limit = top if top is not None else document.get("limit")
    kwargs: dict[str, Any] = {
        "dataset_id": reads.dataset_id,
        "dataview_id": reads.view_id,
        "project_id": reads.project_id,
        **fields,
    }
    condition = None
    if document.get(CONDITION_KWARG) is not None:
        spec = read_queries.resolve_text_date_conditions(reads, document[CONDITION_KWARG])
        condition = compile_condition(spec).build(
            reads.display_to_internal or None, reads.column_types or None
        )
        kwargs[CONDITION_KWARG] = condition
    _forward_optional(document, kwargs, ("sequence",))
    if levels:
        response = read_queries.pivot_with_text_dates(
            reads,
            aggregations=fields["aggregations"],
            group_by=fields["group_by"],
            levels=levels,
            condition=condition,
        )
        rows = read_queries.sort_locally(response["data"], sort)
        return {**response, "data": rows[:limit] if limit else rows}
    if sort:
        kwargs["sort"] = sort
    if limit is not None:
        kwargs["limit"] = limit
    data = reads.service.call(symbol, **kwargs)
    return read_queries.with_leader_share(reads, data, fields, condition, limit)


def view_data_aggregate(invocation: Invocation) -> HandlerResult:
    """Aggregate a dataview's data: a PIVOT group-by or a single METRIC value.

    Read-only: computes and returns the aggregated result without adding a
    task to the view's pipeline or otherwise changing it. Pass exactly one of
    ``aggregations`` (a PIVOT; ``group_by`` is optional) or ``metric`` (a
    METRIC). ``function`` is one of SUM, COUNT, AVG, MIN, MAX, STDDEV, DISTINCT_COUNT. An optional
    ``condition`` filters rows before aggregating, and ``sequence`` pins the
    read to a pipeline step (default: latest). ``order_by`` (result labels,
    ``"Total desc"``) with ``top`` ranks the groups on the backend (and adds
    ``share_of_total``: the filtered total and the share held by the first row and
    by the returned rows); a ``limit`` without ``order_by`` is flagged unordered.
    A ``truncate`` on a TEXT column of dates is bucketed here from the detected
    format, stated in ``text_dates``.
    A group_by ``{"column": ..., "part": weekday|month|quarter|year}`` on a DATE (or
    TEXT-date) column groups by the named part of the date -- ``Monday``..``Sunday``,
    ``January``..``December``, ``Q1``..``Q4``, the year -- in calendar order: the
    read-only way to answer by-weekday and by-month questions.
    Figures are rounded for display (2 decimals; 4 below 1).
    Never use ``view transform pivot`` just to read a number -- it mutates the
    view's pipeline.
    """
    require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    has_pivot = "aggregations" in document or "group_by" in document
    has_metric = "metric" in document
    if has_pivot == has_metric:
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message="Pass exactly one of 'aggregations' (a PIVOT group-by, 'group_by' optional) "
            "or 'metric' (a single METRIC value).",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        source = open_aggregate_source(service, invocation, auth.workspace_id, view_id, document)
        data = aggregate_on(source, _symbol(invocation), document)
    return data, source.meta


@dataclasses.dataclass
class AggregateSource:
    """One view's column names, types and currencies, read once for its aggregates."""

    reads: ReadContext
    currencies: dict[str, str]
    meta: dict[str, Any]


def open_aggregate_source(
    service: Any,
    invocation: Invocation,
    workspace_id: int,
    view_id: int,
    document: dict[str, Any],
) -> AggregateSource:
    """Resolve the view's dataset and read its metadata, as ``view data aggregate`` does.

    ``view data drivers`` and ``view data forecast`` run several aggregates over one
    view through :func:`aggregate_on`; this reads what they share once.
    """
    project_id = require_project(invocation)
    dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
    meta = _read_meta(service, invocation, workspace_id, dataset_id, view_id, project_id)
    internal_to_display, column_types, currencies = _column_profile_with_currency(
        service, dataset_id, view_id, project_id
    )
    display_to_internal = {display: internal for internal, display in internal_to_display.items()}
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
    return AggregateSource(reads, currencies, meta)


def aggregate_on(
    source: AggregateSource, symbol: str, document: dict[str, Any], coverage: bool = True
) -> Any:
    """Run one ``view data aggregate`` document against an opened view, unrounded.

    ``coverage`` False skips the date-coverage read on a non-empty result (a caller
    that already has it from an earlier aggregate over the same view).
    """
    reads = source.reads
    column_types = reads.column_types
    display_to_internal = reads.display_to_internal
    levels: dict[int, str] = {}
    if "aggregations" in document or "group_by" in document:
        levels = read_queries.text_date_group_levels(document.get("group_by"), column_types)
        fields, as_map = _build_pivot_fields(
            _plain_text_date_groups(document, levels, column_types), display_to_internal
        )
    else:
        _reject_order_on_metric(document)
        _require_numeric_metric(document, column_types, reads.view_id)
        fields, as_map = _build_metric_fields(document, display_to_internal)
    order = read_queries.parse_order(document, as_map)
    data = _run_aggregate(reads, symbol, document, fields, order, levels)
    data = _relabel_columns(
        reads.service, reads.dataset_id, reads.view_id, reads.project_id, data, as_map
    )
    data = read_queries.mark_unordered(document, data)
    data = read_queries.with_observed_range(
        reads, data, _aggregate_range_columns(document, column_types), coverage=coverage
    )
    data = read_queries.with_assumptions(reads, data)
    return _with_currency(data, _measures(document), source.currencies)


def view_data_aggregate_rounded(invocation: Invocation) -> HandlerResult:
    """``view data aggregate`` as the user reads it: floats rounded (2 decimals; 4 below 1).

    ``view data compare`` calls :func:`view_data_aggregate` itself, at full precision.
    """
    data, meta = view_data_aggregate(invocation)
    return read_queries.round_result_rows(data), meta


def _compare_key_and_value_columns(document: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return the (key, value) display-column names an aggregate call over
    ``document`` will produce, without making the call -- mirrors the label
    rules :func:`_build_pivot_fields`/:func:`_build_metric_fields` apply.
    """
    group_by = document.get("group_by") or []
    key_columns = [item["column"] if isinstance(item, dict) else item for item in group_by]
    if "metric" in document:
        value_columns = [_resolved_aggregate_item(document["metric"], {})["as_name"]]
    else:
        value_columns = [
            _resolved_aggregate_item(agg, {})["as_name"] for agg in document.get("aggregations", [])
        ]
    return key_columns, value_columns


def _run_aggregate_for_compare(
    invocation: Invocation, view_id: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run ``view data aggregate``'s own handler against one view, for compare."""
    sub_invocation = dataclasses.replace(
        invocation, command_id="view.data.aggregate", extra_args=[str(view_id)], positionals={}
    )
    data, meta = view_data_aggregate(sub_invocation)
    rows = data.get(_ROWS_KEY, [])
    return (rows if isinstance(rows, list) else []), meta


def _index_by_key(
    rows: list[dict[str, Any]], key_columns: list[str]
) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {tuple(row.get(column) for column in key_columns): row for row in rows}


def _require_matched_keys(
    keyed_a: dict[tuple[Any, ...], dict[str, Any]],
    keyed_b: dict[tuple[Any, ...], dict[str, Any]],
    key_columns: list[str],
    view_id_a: int,
    view_id_b: int,
) -> None:
    """Fail loud -- never silently drop -- when a key is on only one side."""
    only_a = sorted(keyed_a.keys() - keyed_b.keys(), key=str)
    only_b = sorted(keyed_b.keys() - keyed_a.keys(), key=str)
    if not only_a and not only_b:
        return

    def _describe(keys: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
        return [dict(zip(key_columns, key, strict=True)) for key in keys[:10]]

    raise CliError(
        code=CODE_INVALID_ARGUMENTS,
        message=(
            f"view {view_id_a} and view {view_id_b} do not share the same "
            f"{'/'.join(key_columns) or 'rows'}: {len(only_a)} only in view {view_id_a}, "
            f"{len(only_b)} only in view {view_id_b}."
        ),
        exit_status=EXIT_USAGE,
        hint="compare only reports a row where both views have the key; reconcile or "
        "narrow with 'condition' before comparing.",
        details={"only_in_first": _describe(only_a), "only_in_second": _describe(only_b)},
    )


def _decimal_or_raise(value: Any, column: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message=f"'{column}' is not numeric ({value!r}); compare only works on "
            "numeric aggregates.",
            exit_status=EXIT_USAGE,
        ) from exc


def _compare_rows(
    keyed_a: dict[tuple[Any, ...], dict[str, Any]],
    keyed_b: dict[tuple[Any, ...], dict[str, Any]],
    key_columns: list[str],
    value_columns: list[str],
) -> list[dict[str, Any]]:
    compared: list[dict[str, Any]] = []
    for key in sorted(keyed_a.keys(), key=str):
        row_a, row_b = keyed_a[key], keyed_b[key]
        entry: dict[str, Any] = dict(zip(key_columns, key, strict=True))
        for column in value_columns:
            value_a = _decimal_or_raise(row_a.get(column), column)
            value_b = _decimal_or_raise(row_b.get(column), column)
            entry[f"{column}_a"] = str(value_a)
            entry[f"{column}_b"] = str(value_b)
            entry[f"{column}_delta"] = str(value_a - value_b)
        compared.append(entry)
    return compared


def view_data_compare(invocation: Invocation) -> HandlerResult:
    """Compare the same PIVOT/METRIC aggregate across two views, joined by key.

    T2-WPP-W8: an agent subtracted two views' totals by hand and mis-stated the
    difference. Compare takes ``view data aggregate``'s exact input shape
    (``aggregations``/``group_by``, or ``metric``) and runs it against both
    views, joining the rows on the group-by key (or as a single row for a bare
    metric) and returning an exact Decimal delta per key -- never ask the
    caller to subtract. A key present on only one side fails loud instead of
    silently reporting a partial diff.
    """
    require_project(invocation)
    view_id_a = _require_int_positional_at(invocation, 0, "first view id")
    view_id_b = _require_int_positional_at(invocation, 1, "second view id")
    document = invocation.load_input() or {}
    key_columns, value_columns = _compare_key_and_value_columns(document)
    rows_a, meta = _run_aggregate_for_compare(invocation, view_id_a)
    rows_b, _meta_b = _run_aggregate_for_compare(invocation, view_id_b)
    keyed_a = _index_by_key(rows_a, key_columns)
    keyed_b = _index_by_key(rows_b, key_columns)
    _require_matched_keys(keyed_a, keyed_b, key_columns, view_id_a, view_id_b)
    compared = _compare_rows(keyed_a, keyed_b, key_columns, value_columns)
    return {_ROWS_KEY: compared}, meta
