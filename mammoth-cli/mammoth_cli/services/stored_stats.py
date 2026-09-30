"""Column statistics the backend already stored for a view (no query is run).

``view ai profile`` with action ``stats`` (``POST .../profile_generation``)
returns the level-1 profile synchronously from ``TableItem.stats`` -- the
per-column stats the backend computes after ingest and after each pipeline run
(``transform_common.TableDataItem.update_column_stats``,
``DataviewManager.pipeline_post_exec_tasks``). It holds, per column: the
distinct count, the missing count, min/max (NUMERIC, DATE), numeric summary
moments and a short ``data_sample`` -- but NOT top values with counts, text
min/max or any target comparison.

The stats carry no time. They are refreshed by a background job after a
pipeline run, so they lag a write. The only currency test available is the
row count they were computed over against the live row count.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_RANGE_KEYS = (("col_min", "col_max"), ("min_date", "max_date"))


def stored_facts(
    payload: Any, internal_by_display: Mapping[str, str]
) -> tuple[dict[str, dict[str, Any]], int | None]:
    """``({display name: facts}, rows the stats were computed over)`` from a stats payload.

    Facts use the same keys the fresh queries fill: ``distinct``, ``nulls``
    and, for NUMERIC and DATE, ``min`` and ``max``. Columns the payload lacks
    are absent, never invented. Numeric moments ride along as ``mean`` and
    ``stddev`` when stored.
    """
    profile = payload.get("profile") if isinstance(payload, Mapping) else None
    if not isinstance(profile, Mapping):
        return {}, None
    by_internal = {internal: display for display, internal in internal_by_display.items()}
    facts: dict[str, dict[str, Any]] = {}
    rows: int | None = None
    for key, entry in profile.items():
        display = by_internal.get(key) or _column_name(entry)
        if display is None or display not in internal_by_display:
            continue
        if not isinstance(entry, Mapping):
            continue
        facts[display], entry_rows = _one(entry)
        rows = entry_rows if entry_rows is not None else rows
    return facts, rows


def _column_name(entry: Any) -> str | None:
    return entry.get("column_name") if isinstance(entry, Mapping) else None


def _one(entry: Mapping[str, Any]) -> tuple[dict[str, Any], int | None]:
    schema = _section(entry, "schema_analysis")
    summary = _section(entry, "statistical_summary")
    quality = _section(entry, "quality_metrics")
    perf = _section(entry, "performance_metadata")
    fact: dict[str, Any] = {
        "distinct": int(schema.get("num_unique") or 0),
        "nulls": int(perf.get("missing_count") or 0) + int(quality.get("empty_string_count") or 0),
    }
    for low, high in _RANGE_KEYS:
        if low in summary:
            fact["min"], fact["max"] = summary.get(low), summary.get(high)
    if "col_avg" in summary:
        fact["mean"], fact["stddev"] = summary.get("col_avg"), summary.get("col_stddev")
    if isinstance(summary.get("data_sample"), list):
        fact["sample"] = summary["data_sample"]
    total = perf.get("total_rows")
    return fact, int(total) if isinstance(total, int) and total > 0 else None


def _section(entry: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = entry.get(name)
    return value if isinstance(value, Mapping) else {}


def currency(stored_rows: int | None, live_rows: int) -> dict[str, Any]:
    """Whether the stored stats can be treated as current, and why not if they cannot.

    Equal row counts only rule out added or removed rows; an edit that keeps
    the row count (a fill, a replace) cannot be seen, and the note says so.
    """
    if stored_rows is None:
        return {"current": False, "reason": "the stored stats name no row count"}
    if stored_rows != live_rows:
        return {
            "current": False,
            "reason": (
                f"stored stats cover {stored_rows} rows, the view has {live_rows} now "
                "(they are refreshed by a background job after a pipeline run)"
            ),
        }
    return {
        "current": True,
        "note": (
            "same row count as the view now; a change that keeps the row count "
            "(fill, replace) would not show, and the backend records no as-of time"
        ),
    }
