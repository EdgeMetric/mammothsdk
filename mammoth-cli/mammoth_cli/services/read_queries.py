"""Read-query helpers that make a read say what it did (PLAN-021 "truth").

Three things a data read must not leave to the caller's imagination:

* a date stored as TEXT is bucketed and range-filtered here, read-only, with the
  detected format stated in the result (see :mod:`mammoth_cli.services.text_dates`);
* ``order_by`` / ``top`` reach the backend as a real SORT + LIMIT, and a ``limit``
  with no sort is flagged as unordered instead of looking like a top-N;
* an empty result names the observed range of the columns it was filtered on.

Every function here either returns the truthful thing or raises a
:class:`~mammoth_cli.errors.envelope.CliError` that says why.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from mammoth.api.dataviews import _add_explore_percentages, _explore_sort_and_limit

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENTS,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.services import text_dates
from mammoth_cli.services.conditions import _resolve_operator

AGGREGATE_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.aggregate"
#: A stored string no date can equal: what a range that matches nothing compiles to.
NO_MATCH = "__no_stored_date_in_range__"
_ISO_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_RANGE_OPERATORS = frozenset({"GT", "GTE", "LT", "LTE", "IN_RANGE"})
_MAX_RANGE_COLUMNS = 3
_MAX_SORT_KEYS = 3
_UNORDERED_NOTE = (
    "'limit' without 'order_by' keeps arbitrary rows, not the top ones. "
    "Pass order_by (and top) to rank."
)


def _fail(message: str, hint: str = "", details: dict[str, Any] | None = None) -> CliError:
    return CliError(
        code=CODE_INVALID_ARGUMENTS,
        message=message,
        exit_status=EXIT_USAGE,
        hint=hint,
        details=details or {},
    )


@dataclass
class ReadContext:
    """What a read needs to ask the backend extra questions about one view."""

    service: Any
    dataset_id: int
    view_id: int
    project_id: int | None
    display_to_internal: dict[str, str]
    column_types: dict[str, str]
    sequence: int | None = None
    requested_format: str | None = None
    assumptions: dict[str, dict[str, Any]] = field(default_factory=dict)
    _days: dict[str, tuple[text_dates.TextDateFormat, dict[str, date | None]]] = field(
        default_factory=dict
    )

    def query(self, **fields: Any) -> dict[str, Any]:
        """Run one aggregate against this view."""
        kwargs: dict[str, Any] = {
            "dataset_id": self.dataset_id,
            "dataview_id": self.view_id,
            "project_id": self.project_id,
            **fields,
        }
        if self.sequence is not None:
            kwargs["sequence"] = self.sequence
        response = self.service.call(AGGREGATE_SYMBOL, **kwargs)
        return response if isinstance(response, dict) else {}

    def internal(self, column: str) -> str:
        return self.display_to_internal.get(column, column)

    def is_text(self, column: str) -> bool:
        return self.column_types.get(column) == "TEXT"

    def column_days(self, column: str) -> tuple[text_dates.TextDateFormat, dict[str, date | None]]:
        """Format and parsed distinct values of a TEXT date column (read once)."""
        if column not in self._days:
            values = self._distinct(column)
            fmt = text_dates.detect_format(values, column, self.requested_format)
            self._days[column] = (fmt, text_dates.parse_all(values, fmt))
            self.assumptions[column] = {
                "column": column,
                "assumed_format": fmt.label,
                "because": fmt.reason,
            }
        return self._days[column]

    def _distinct(self, column: str) -> list[Any]:
        cap = text_dates.MAX_DISTINCT_VALUES
        response = self.query(
            aggregations=[{"function": "COUNT", "as_name": "n"}],
            group_by=[self.internal(column)],
            limit=cap + 1,
        )
        values = [row.get("group_0") for row in _rows(response)]
        if len(values) > cap:
            raise _fail(
                f"Column '{column}' has more than {cap} distinct values, "
                "too many to read as dates.",
                "Filter the view first, or convert the column with 'view transform convert-type'.",
            )
        return values


def _rows(response: dict[str, Any]) -> list[dict[str, Any]]:
    data = response.get("data")
    return [row for row in data if isinstance(row, dict)] if isinstance(data, list) else []


# ---------------------------------------------------------------------------
# text-date conditions
# ---------------------------------------------------------------------------


def _iso_bound(value: Any, column: str) -> date | None:
    if isinstance(value, str) and _ISO_DAY.match(value.strip()):
        try:
            return date.fromisoformat(value.strip())
        except ValueError as exc:
            raise _fail(f"'{value}' is not a real calendar date (column '{column}').") from exc
    return None


def _bounds(leaf: dict[str, Any], operator: str) -> list[date] | None:
    """The ISO date bound(s) of a range/compare leaf, or ``None`` if it is not one."""
    raw = leaf.get("value")
    values = raw if operator == "IN_RANGE" and isinstance(raw, list) else [raw]
    parsed = [_iso_bound(v, str(leaf.get("column"))) for v in values]
    if any(b is None for b in parsed) or (operator == "IN_RANGE" and len(parsed) != 2):
        return None
    return [b for b in parsed if b is not None]


def _tester(operator: str, bounds: list[date]) -> Any:
    low = bounds[0]
    return {
        "GT": lambda d: d > low,
        "GTE": lambda d: d >= low,
        "LT": lambda d: d < low,
        "LTE": lambda d: d <= low,
        "IN_RANGE": lambda d: low <= d <= bounds[-1],
    }[operator]


def _rewrite_leaf(ctx: ReadContext, leaf: dict[str, Any]) -> dict[str, Any]:
    column = str(leaf.get("column"))
    operator = _resolve_operator(leaf.get("operator"))
    if operator not in _RANGE_OPERATORS or not ctx.is_text(column) or leaf.get("value_is_column"):
        return leaf
    bounds = _bounds(leaf, operator)
    if bounds is None:
        return leaf
    fmt, days = ctx.column_days(column)
    matched = text_dates.in_range_values(days, _tester(operator, bounds))
    if len(matched) > text_dates.MAX_DISTINCT_VALUES:
        raise _fail(f"The range on '{column}' matches too many distinct stored dates.")
    return {
        "column": column,
        "operator": "IN_LIST",
        "value": matched or [NO_MATCH],
    }


def resolve_text_date_conditions(ctx: ReadContext, spec: Any) -> Any:
    """Rewrite range/compare leaves on TEXT date columns into exact stored-value lists.

    A leaf ``{"column": C, "operator": GT|GTE|LT|LTE|IN_RANGE, "value": "YYYY-MM-DD"}``
    on a TEXT column is parsed from the column's stored format and compiled to the
    stored strings that satisfy it. Everything else passes through untouched.
    """
    if not isinstance(spec, dict):
        return spec
    for key in ("and", "or"):
        if key in spec and isinstance(spec[key], list):
            return {key: [resolve_text_date_conditions(ctx, item) for item in spec[key]]}
    if "not" in spec:
        return {"not": resolve_text_date_conditions(ctx, spec["not"])}
    return _rewrite_leaf(ctx, spec) if "column" in spec and "operator" in spec else spec


def condition_columns(spec: Any) -> list[str]:
    """Display names of the columns a condition spec filters on, in order."""
    if not isinstance(spec, dict):
        return []
    found: list[str] = []
    for key in ("and", "or"):
        for item in spec.get(key, []) if isinstance(spec.get(key), list) else []:
            found.extend(condition_columns(item))
    if "not" in spec:
        found.extend(condition_columns(spec["not"]))
    if isinstance(spec.get("column"), str):
        found.append(spec["column"])
    return list(dict.fromkeys(found))


# ---------------------------------------------------------------------------
# bucketing a TEXT date in a pivot
# ---------------------------------------------------------------------------


def text_date_group_levels(group_by: Any, column_types: dict[str, str]) -> dict[int, str]:
    """Fail loud on a ``truncate`` the column type cannot take; return the TEXT ones.

    Maps a group_by position to its bucket level for every ``{"column", "truncate"}``
    entry on a TEXT column. A truncate on a NUMERIC column (or ``resolution`` on a
    non-NUMERIC one) is refused with the reason -- never silently ignored.
    """
    levels: dict[int, str] = {}
    for index, item in enumerate(group_by if isinstance(group_by, list) else []):
        if not isinstance(item, dict):
            continue
        column = str(item.get("column"))
        kind = column_types.get(column, "")
        if item.get("truncate") is not None:
            if kind == "TEXT":
                levels[index] = text_dates.require_level(item["truncate"])
            elif kind not in ("DATE", ""):
                raise _fail(
                    f"'truncate' buckets a DATE column; '{column}' is {kind}.",
                    "Use 'resolution' for a NUMERIC column.",
                )
        if item.get("resolution") is not None and kind not in ("NUMERIC", ""):
            raise _fail(
                f"'resolution' buckets a NUMERIC column; '{column}' is {kind}.",
                "Use 'truncate' for a DATE column.",
            )
    return levels


@dataclass(frozen=True)
class _Plan:
    aggregations: list[dict[str, Any]]
    functions: dict[str, str]
    averages: dict[str, str]


def _plan_aggregations(aggregations: list[dict[str, Any]]) -> _Plan:
    """Turn the requested aggregates into ones that can be recombined per bucket."""
    planned: list[dict[str, Any]] = []
    functions: dict[str, str] = {}
    averages: dict[str, str] = {}
    hidden: list[dict[str, Any]] = []
    for index, agg in enumerate(aggregations):
        function = str(agg.get("function") or "").upper()
        key = f"agg_{index}"
        if function == "AVG":
            planned.append({**agg, "function": "SUM"})
            functions[key] = "SUM"
            hidden.append(
                {"function": "COUNT", "column": agg.get("column"), "as_name": f"n_{index}"}
            )
            averages[key] = f"agg_{len(aggregations) + len(hidden) - 1}"
        elif function in text_dates.ADDITIVE_FUNCTIONS:
            planned.append(agg)
            functions[key] = function
        else:
            raise _fail(
                f"{function} cannot be computed per month/year of a TEXT date: it cannot be "
                "recombined from the stored-value groups.",
                "Use SUM, COUNT, MIN, MAX or AVG, or convert the column with "
                "'view transform convert-type'.",
            )
    for offset, _item in enumerate(hidden):
        functions[f"agg_{len(aggregations) + offset}"] = "COUNT"
    return _Plan([*planned, *hidden], functions, averages)


def _finish_averages(rows: list[dict[str, Any]], averages: dict[str, str]) -> None:
    for row in rows:
        for total_key, count_key in averages.items():
            count = row.pop(count_key, None)
            total = row.get(total_key)
            row[total_key] = total / count if count and total is not None else None


def pivot_with_text_dates(
    ctx: ReadContext,
    *,
    aggregations: list[dict[str, Any]],
    group_by: list[Any],
    levels: dict[int, str],
    condition: Any,
) -> dict[str, Any]:
    """Run a PIVOT whose group_by buckets a TEXT date, regrouped in the CLI.

    ``aggregations`` and ``group_by`` use internal column names, ``group_by`` with
    the TEXT date entry already reduced to its plain column. The backend groups by
    the raw stored string; the CLI parses it (format stated in ``ctx.assumptions``)
    and regroups by ``level``.
    """
    if len(levels) != 1:
        raise _fail("Bucket at most one TEXT date column per query.")
    ((position, level),) = levels.items()
    display = next(
        (d for d, i in ctx.display_to_internal.items() if i == group_by[position]),
        group_by[position],
    )
    fmt, days = ctx.column_days(display)
    plan = _plan_aggregations(aggregations)
    fields: dict[str, Any] = {"aggregations": plan.aggregations, "group_by": group_by}
    if condition is not None:
        fields["condition"] = condition
    response = ctx.query(**fields)
    rows = _rows(response)
    if len(rows) >= 40000:
        raise _fail("The grouped result hit the 40000-row backend cap; narrow it with a condition.")
    others = [f"group_{i}" for i in range(len(group_by)) if i != position]
    regrouped = text_dates.rebucket(
        rows,
        date_key=f"group_{position}",
        other_keys=others,
        functions=plan.functions,
        days=days,
        level=level,
    )
    _finish_averages(regrouped, plan.averages)
    ctx.assumptions[display]["bucket"] = f"{level} (period start date, ISO)"
    return {**response, "data": regrouped, "row_count": len(regrouped)}


def apply_explore_order(
    rows: list[dict[str, Any]], sort: str | None, page: tuple[int | None, int | None]
) -> list[dict[str, Any]]:
    """Percentages, order and paging for a bucketed explore, like the SDK's own."""
    _add_explore_percentages(rows)
    return _explore_sort_and_limit(rows, "DATE", sort, page)


# ---------------------------------------------------------------------------
# order_by / top
# ---------------------------------------------------------------------------


def _sort_entry(item: Any, labels: dict[str, str]) -> tuple[str, str]:
    if isinstance(item, str):
        column, _, direction = item.rpartition(" ")
        if direction.lower() in ("asc", "desc") and column:
            item = {"column": column, "direction": direction}
        else:
            item = {"column": item}
    if not isinstance(item, dict) or "column" not in item:
        raise _fail('Each order_by entry is a column label or {"column": ..., "direction": ...}.')
    label = str(item["column"])
    direction = str(item.get("direction", "desc")).upper()
    if label not in labels:
        raise _fail(
            f"order_by column '{label}' is not a column of this result.",
            f"Order by one of: {', '.join(labels)}.",
        )
    if direction not in ("ASC", "DESC"):
        raise _fail(f"order_by direction must be asc or desc, got {item.get('direction')!r}.")
    return labels[label], direction


def parse_order(
    document: dict[str, Any], as_map: dict[str, str]
) -> tuple[list[list[str]] | None, int | None]:
    """Resolve ``order_by`` and ``top`` to backend SORT pairs and a row limit.

    ``as_map`` maps internal result names (``agg_0``/``group_0``) to the labels the
    caller sees. ``top`` is a limit that requires an order; giving both ``top`` and
    ``limit`` is refused as ambiguous.
    """
    order_by, top, limit = document.get("order_by"), document.get("top"), document.get("limit")
    if top is not None and limit is not None:
        raise _fail("Pass either 'top' or 'limit', not both.", "'top' is 'limit' after 'order_by'.")
    if top is not None and not order_by:
        raise _fail("'top' needs 'order_by': the top N of what?", 'Add "order_by": ["Total desc"].')
    sort: list[list[str]] | None = None
    if order_by:
        entries = order_by if isinstance(order_by, list) else [order_by]
        if len(entries) > _MAX_SORT_KEYS:
            raise _fail(f"order_by takes at most {_MAX_SORT_KEYS} columns.")
        labels = {label: internal for internal, label in as_map.items()}
        sort = [list(_sort_entry(entry, labels)) for entry in entries]
    return sort, (int(top) if top is not None else None)


def mark_unordered(document: dict[str, Any], data: Any) -> Any:
    """Flag a limited, unsorted result so it cannot pass for a ranking."""
    if document.get("limit") is None or document.get("order_by") or not isinstance(data, dict):
        return data
    return {**data, "ordered": False, "note": _UNORDERED_NOTE}


def sort_locally(rows: list[dict[str, Any]], sort: list[list[str]] | None) -> list[dict[str, Any]]:
    """Apply backend-style SORT pairs to already-fetched rows (blanks last)."""
    ordered = list(rows)
    for internal, direction in reversed(sort or []):
        present = [r for r in ordered if r.get(internal) is not None]
        blank = [r for r in ordered if r.get(internal) is None]
        ordered = sorted(present, key=lambda r: r[internal], reverse=direction == "DESC") + blank
    return ordered


# ---------------------------------------------------------------------------
# empty result: say what the data covers
# ---------------------------------------------------------------------------


def _column_range(ctx: ReadContext, column: str) -> dict[str, Any] | None:
    kind = ctx.column_types.get(column, "")
    if kind == "TEXT":
        try:
            fmt, days = ctx.column_days(column)
        except CliError:
            return None
        found = text_dates.observed_range(days)
        return {"column": column, "type": f"TEXT date ({fmt.label})", **found} if found else None
    if kind not in ("DATE", "NUMERIC"):
        return None
    internal = ctx.internal(column)
    response = ctx.query(
        aggregations=[
            {"function": "MIN", "column": internal, "as_name": "min"},
            {"function": "MAX", "column": internal, "as_name": "max"},
        ]
    )
    rows = _rows(response)
    if not rows:
        return None
    return {
        "column": column,
        "type": kind,
        "min": rows[0].get("agg_0"),
        "max": rows[0].get("agg_1"),
    }


def with_observed_range(ctx: ReadContext, data: Any, columns: list[str]) -> Any:
    """On an empty result, add the observed min/max of the filtered/date columns."""
    rows = data.get("data") if isinstance(data, dict) else None
    if not isinstance(data, dict) or rows != [] or not columns:
        return data
    ranges = [r for c in columns[:_MAX_RANGE_COLUMNS] if (r := _column_range(ctx, c))]
    if not ranges:
        return data
    return {
        **data,
        "empty_result": "No rows matched. The data covers, per filtered/date column:",
        "observed_range": ranges,
    }


def with_assumptions(ctx: ReadContext, data: Any) -> Any:
    """Attach the text-date formats a read assumed, so the answer can state them."""
    if not ctx.assumptions or not isinstance(data, dict):
        return data
    return {**data, "text_dates": list(ctx.assumptions.values())}
