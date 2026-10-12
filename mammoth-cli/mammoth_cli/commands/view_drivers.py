"""``view data drivers``: what moved a measure between two periods, and by how much.

Read-only. "Why did revenue drop from July to August?" took the in-product agent
18 hand-built aggregates and 95 s (gap eval 10-10, S03). This answers it in one
aggregate per ``by`` column, never one per period: each groups by the column and
by the date bucket that fits both periods, filtered to the two periods, with a row
count beside the measure. The CLI then splits the buckets into the two periods,
totals them, and ranks each column's groups by how much of the change they carry.

The aggregates run through ``view data aggregate``'s own helpers
(:func:`mammoth_cli.commands.view.aggregate_on`), so column names, TEXT dates,
date coverage and the currency of the measure behave exactly as they do there.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from mammoth_cli.commands.view import (
    _require_int_positional_at,
    aggregate_on,
    open_aggregate_source,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services import period_analysis as pa
from mammoth_cli.services.listing import LIST_DATA_BUDGET, json_size
from mammoth_cli.services.read_queries import AGGREGATE_SYMBOL

HandlerResult = tuple[Any, dict[str, Any]]

#: Contributors listed per ``by`` column, largest change first.
_TOP = 5
_MAX_BY = 3
#: Only an additive measure splits into contributions that add up to the change.
_ADDITIVE = ("SUM", "COUNT")
#: Words of free text counted per period; shorter ones and the common ones below are noise.
_WORD = re.compile(r"[a-z][a-z0-9'-]{3,}")
_COMMON_WORDS = frozenset(
    "that this with from have been were will would could should their there about which when "
    "what then than them they your just into over also only some more most very much many".split()
)
#: Result label of the row count asked for beside the measure.
_ROWS = "__rows"
#: A volume or value move counts as "the" driver when it is at least this many times the other.
_DOMINANT = 2.0

_NOTE = (
    "Lead with the total change: totals.a.value to totals.b.value, delta and delta_pct (a "
    "percentage). Then name the top contributors from each list in contributors with their "
    "share_of_change (a signed percentage of the total delta; groups moving against the "
    "total have the opposite sign, and others_delta is what the groups not listed add up "
    "to). Say whether the change is volume or value: volume_vs_value compares the change "
    "in the row count (count) with the change in value per row, and driven_by names the "
    "larger. For a column of free text, its contributors entry also lists terms: the words "
    "in the most notes in period b against period a (count_a, count_b); name the top term "
    "and its counts as what grew. If partial_period is present, say that period is "
    "incomplete in the data, so the two periods are not like for like. Give amounts in the currency named in "
    "'currency'; when it is null, give plain numbers and never invent a currency."
)


def view_data_drivers(invocation: Invocation) -> HandlerResult:
    """Explain a measure's change between two periods: totals, volume vs value, top contributors."""
    require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    measure = pa.parse_measure(document.get("measure"), _ADDITIVE)
    date_column = pa.require_text(document, "date_column")
    periods = _periods(document.get("compare"))
    by = _by_columns(document.get("by"), date_column)
    conditions = pa.optional_condition(document)
    unit = pa.coarsest_unit(periods)
    with open_service(invocation) as (service, auth):
        source = open_aggregate_source(service, invocation, auth.workspace_id, view_id, document)
        pa.require_columns(source.reads.column_types, date_column, measure.column, *by)
        reads = [
            aggregate_on(
                source,
                AGGREGATE_SYMBOL,
                _by_document(measure, date_column, unit, periods, column, conditions),
                coverage=index == 0,
            )
            for index, column in enumerate(by)
        ]
    return _result(measure, date_column, periods, unit, by, reads), source.meta


def _periods(raw: Any) -> list[pa.Period]:
    if not isinstance(raw, list) or len(raw) != 2:
        raise pa.usage(
            "'compare' takes exactly two periods: [A, B], the change is read from A to B.",
            hint='"compare": ["2026-07", "2026-08"]',
        )
    return [pa.parse_period(item) for item in raw]


def _by_columns(raw: Any, date_column: str) -> list[str]:
    if isinstance(raw, str):
        raw = [raw]
    if (
        not isinstance(raw, list)
        or not 1 <= len(raw) <= _MAX_BY
        or not all(isinstance(c, str) and c.strip() for c in raw)
    ):
        raise pa.usage(
            f"'by' takes 1 to {_MAX_BY} column names to break the change down by.",
            hint='"by": ["store", "category"]',
        )
    if len(set(raw)) != len(raw) or date_column in raw:
        raise pa.usage("'by' columns must be distinct and must not be the date_column.")
    return list(raw)


def _by_document(
    measure: pa.Measure,
    date_column: str,
    unit: str,
    periods: list[pa.Period],
    column: str,
    conditions: dict[str, Any] | None,
) -> dict[str, Any]:
    """One aggregate: the measure and a row count per (column value, date bucket), both periods."""
    aggregations = [measure.aggregation()]
    if measure.function != "COUNT":
        aggregations.append({"function": "COUNT", "as_name": _ROWS})
    in_periods = {"or": [pa.range_condition(date_column, p) for p in periods]}
    return {
        "group_by": [column, {"column": date_column, "truncate": unit}],
        "aggregations": aggregations,
        **pa.with_condition(in_periods, conditions),
    }


def _split(
    data: Any, measure: pa.Measure, date_column: str, column: str, periods: list[pa.Period]
) -> dict[Any, list[list[float]]]:
    """Per group value: [[value, count] for each period], from the date-bucketed rows."""
    groups: dict[Any, list[list[float]]] = {}
    for row in pa.rows(data):
        day = pa.as_date(row.get(date_column))
        if day is None:
            continue
        value = pa.number(row.get(measure.label))
        count = value if measure.function == "COUNT" else pa.number(row.get(_ROWS))
        slots = groups.setdefault(pa.group_label(row.get(column)), [[0.0, 0.0], [0.0, 0.0]])
        for index, period in enumerate(periods):
            if period.contains(day):
                slots[index][0] += value
                slots[index][1] += count
    return groups


def _is_free_text(data: Any, column: str) -> bool:
    """Whether the column holds notes (three words or more), not names or categories."""
    return any(
        isinstance(row.get(column), str) and len(row[column].split()) >= 3 for row in pa.rows(data)
    )


def _terms(
    data: Any, measure: pa.Measure, date_column: str, column: str, periods: list[pa.Period]
) -> list[dict[str, Any]]:
    """Words of a free-text column by number of rows per period, biggest growth first."""
    counts = [Counter[str](), Counter[str]()]
    for row in pa.rows(data):
        day, text = pa.as_date(row.get(date_column)), row.get(column)
        if day is None or not isinstance(text, str):
            continue
        rows = pa.number(row.get(measure.label if measure.function == "COUNT" else _ROWS))
        words = set(_WORD.findall(text.lower())) - _COMMON_WORDS
        for index, period in enumerate(periods):
            if period.contains(day):
                counts[index].update(dict.fromkeys(words, rows))
    grown = sorted(
        (word, int(counts[0][word]), int(count_b))
        for word, count_b in counts[1].items()
        if count_b > counts[0][word]
    )
    grown.sort(key=lambda item: (item[1] - item[2], item[0]))
    return [{"term": w, "count_a": a, "count_b": b} for w, a, b in grown[:_TOP]]


def _pct(new: float, old: float) -> float | None:
    return round((new - old) / abs(old) * 100, 1) if old else None


def _contributors(groups: dict[Any, list[list[float]]], top: int) -> dict[str, Any]:
    total_delta = sum(slots[1][0] - slots[0][0] for slots in groups.values())
    ranked = sorted(
        groups.items(),
        key=lambda item: (-abs(item[1][1][0] - item[1][0][0]), str(item[0])),
    )
    listed = []
    for key, slots in ranked[:top]:
        delta = slots[1][0] - slots[0][0]
        listed.append(
            {
                "group": key,
                "value_a": pa.r2(slots[0][0]),
                "value_b": pa.r2(slots[1][0]),
                "delta": pa.r2(delta),
                "share_of_change": round(delta / total_delta * 100, 1) if total_delta else None,
            }
        )
    block: dict[str, Any] = {"top": listed, "groups": len(groups)}
    if len(ranked) > top:
        block["more"] = len(ranked) - top
        block["others_delta"] = pa.r2(sum(s[1][0] - s[0][0] for _, s in ranked[top:]))
    return block


def _volume_vs_value(
    measure: pa.Measure, value_a: float, value_b: float, count_a: float, count_b: float
) -> dict[str, Any] | None:
    """How much of the change is more or fewer rows, and how much each row's value moved."""
    if measure.function == "COUNT" or min(value_a, value_b, count_a, count_b) <= 0:
        return None
    per_row_a, per_row_b = value_a / count_a, value_b / count_b
    volume, value = math.log(count_b / count_a), math.log(per_row_b / per_row_a)
    if abs(volume) >= _DOMINANT * abs(value):
        driven_by = "volume"
    elif abs(value) >= _DOMINANT * abs(volume):
        driven_by = "value"
    else:
        driven_by = "both" if volume * value >= 0 else "offsetting"
    return {
        "count_delta_pct": _pct(count_b, count_a),
        "value_per_row_a": pa.r2(per_row_a),
        "value_per_row_b": pa.r2(per_row_b),
        "value_per_row_delta_pct": _pct(per_row_b, per_row_a),
        "driven_by": driven_by,
    }


def _partial(periods: list[pa.Period], data: Any) -> list[dict[str, Any]]:
    """Each period the data's date coverage does not span from its first to its last day."""
    first, last = pa.coverage_dates(data)
    found: list[dict[str, Any]] = []
    for period in periods:
        entry: dict[str, Any] = {"period": period.label}
        if last is not None and last < period.end:
            entry["data_through"] = last.isoformat()
            entry["period_ends"] = period.end.isoformat()
        if first is not None and first > period.start:
            entry["data_from"] = first.isoformat()
            entry["period_starts"] = period.start.isoformat()
        if (last is not None and last < period.start) or (first is not None and first > period.end):
            entry["no_data"] = True
        if len(entry) > 1:
            found.append(entry)
    return found


def _result(
    measure: pa.Measure,
    date_column: str,
    periods: list[pa.Period],
    unit: str,
    by: list[str],
    reads: list[Any],
) -> dict[str, Any]:
    splits = [
        _split(data, measure, date_column, c, periods) for c, data in zip(by, reads, strict=True)
    ]
    # Every row lands in exactly one group of each 'by' column: the first one's sums are the totals.
    totals = [[sum(slots[i][j] for slots in splits[0].values()) for j in (0, 1)] for i in (0, 1)]
    (value_a, count_a), (value_b, count_b) = totals
    result: dict[str, Any] = {
        "measure": measure.label,
        "date_column": date_column,
        "periods": {
            key: {"label": p.label, "from": p.start.isoformat(), "to": p.end.isoformat()}
            for key, p in zip(("a", "b"), periods, strict=True)
        },
        "bucketed_by": unit,
        "totals": {
            "a": {"value": pa.r2(value_a), "count": int(count_a)},
            "b": {"value": pa.r2(value_b), "count": int(count_b)},
            "delta": pa.r2(value_b - value_a),
            "delta_pct": _pct(value_b, value_a),
            "count_delta": int(count_b - count_a),
            "count_delta_pct": _pct(count_b, count_a),
        },
    }
    mix = _volume_vs_value(measure, value_a, value_b, count_a, count_b)
    if mix:
        result["volume_vs_value"] = mix
    partial = _partial(periods, reads[0])
    if partial:
        result["partial_period"] = partial
    for key in ("coverage", "observed_range", "text_dates"):
        if isinstance(reads[0], dict) and key in reads[0]:
            result[key] = reads[0][key]
    result.update(pa.money(reads[0]))
    result["note"] = _note(partial, periods, value_a, value_b, count_a, count_b)
    terms = {
        column: _terms(data, measure, date_column, column, periods)
        for column, data in zip(by, reads, strict=True)
        if _is_free_text(data, column)
    }
    return _fit(result, by, splits, terms)


def _note(
    partial: list[dict[str, Any]],
    periods: list[pa.Period],
    value_a: float,
    value_b: float,
    count_a: float,
    count_b: float,
) -> str:
    extra = []
    if not (count_a or count_b or value_a or value_b):
        extra.append(
            f"No rows fall in {periods[0].label} or {periods[1].label}: say so and quote the "
            "data's date range (coverage or observed_range) instead of a change."
        )
    for entry in partial:
        through = entry.get("data_through")
        extra.append(
            f"{entry['period']} is partial: the data "
            + (f"ends {through}" if through else f"starts {entry.get('data_from')}")
            + "."
        )
    return " ".join([_NOTE, *extra])


def _fit(
    result: dict[str, Any],
    by: list[str],
    splits: list[dict[Any, Any]],
    terms: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Add the contributor lists, as many per column as fit the agent tool output cap."""
    note = result.pop("note")
    for top in range(_TOP, 0, -1):
        result["contributors"] = {
            column: _contributors(groups, top) for column, groups in zip(by, splits, strict=True)
        }
        for column, grown in terms.items():
            if grown:
                result["contributors"][column]["terms"] = grown[:top]
        if json_size(result) + len(note) + 12 <= LIST_DATA_BUDGET:
            break
    result["note"] = note
    return result
