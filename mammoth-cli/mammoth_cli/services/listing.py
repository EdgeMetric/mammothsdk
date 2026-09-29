"""Compact, self-describing summaries for ``dataset list`` and ``view list``.

A list of ``{id, name}`` cannot tell an agent which of two look-alike datasets is
the one the user means (PLAN-021: near-duplicate names, leftover data, three
"View 1"s). These summaries carry what the backend already stores and returns in
its list payloads -- size, times, how the data got there, the columns and their
types -- so the choice is made from data, and are cut to fit the agent tool
output cap, with the cut stated and the way to the next page given.

Pure functions over the payloads; no requests.
"""

from __future__ import annotations

import json
from typing import Any

#: Characters of ``data`` a list may use; the agent tool caps a whole result at 4,000.
LIST_DATA_BUDGET = 3500
#: ``fields`` asked of the dataset list route: everything the summary shows.
DATASET_LIST_FIELDS = (
    "id,name,created_at,updated_at,status,stats,sources,data_schema,additional_info"
)

_MAX_COLUMNS = 4
_SOURCE_KINDS = {
    "file": "file",
    "cloud": "connector",
    "sketch": "created in Mammoth",
    "append": "append",
    "abstract": "abstract",
}


def _stamp(value: Any) -> str | None:
    """A stored ISO timestamp cut to the minute (``2026-09-28T14:03``)."""
    return str(value)[:16] if value else None


def _times(created: Any, updated: Any) -> dict[str, str]:
    """Created and updated stamps; ``updated`` is left out when it equals ``created``."""
    made, changed = _stamp(created), _stamp(updated)
    found = {"created": made} if made else {}
    if changed and changed != made:
        found["updated"] = changed
    return found


def _type_word(column_type: Any) -> str:
    return str(column_type or "?").lower()


def compact_columns(columns: list[tuple[str, Any]]) -> str:
    """``"Order ID:text, Sales:numeric (+15 more)"`` -- names and types, capped."""
    shown = [f"{name}:{_type_word(kind)}" for name, kind in columns[:_MAX_COLUMNS]]
    extra = len(columns) - _MAX_COLUMNS
    return ", ".join(shown) + (f" (+{extra} more)" if extra > 0 else "")


def source_of(dataset: dict[str, Any]) -> str:
    """How the dataset's data arrived: the stored source type and, for a file, its name."""
    info = dataset.get("additional_info")
    if isinstance(info, dict) and info.get("DATAVIEW_ID") is not None:
        return f"export of view {info['DATAVIEW_ID']}"
    sources = dataset.get("sources")
    first = sources[0] if isinstance(sources, list) and sources else None
    if not isinstance(first, dict):
        return "unknown"
    raw_kind = first.get("type")
    if not raw_kind:
        return "unknown"
    kind = _SOURCE_KINDS.get(str(raw_kind), str(raw_kind))
    details = first.get("details")
    label = (
        details.get("file_name") or details.get("connector_key")
        if isinstance(details, dict)
        else None
    )
    return f"{kind}: {label}" if label else kind


def _size(rows: Any, columns: Any) -> dict[str, Any]:
    """``{"rows": n, "cols": m}`` for whichever counts the record carries."""
    return {k: v for k, v in (("rows", rows), ("cols", columns)) if v is not None}


def dataset_summary(record: dict[str, Any]) -> dict[str, Any]:
    """Summary of one dataset-list item, from the fields the list route returns."""
    raw_stats, raw_schema = record.get("stats"), record.get("data_schema")
    stats = raw_stats if isinstance(raw_stats, dict) else {}
    schema = raw_schema if isinstance(raw_schema, list) else []
    columns = [
        (c["c_name"], c.get("c_type")) for c in schema if isinstance(c, dict) and c.get("c_name")
    ]
    summary: dict[str, Any] = {
        "id": record.get("id"),
        "name": record.get("name"),
        **_size(stats.get("row_count"), stats.get("column_count")),
        **_times(record.get("created_at"), record.get("updated_at")),
        "source": source_of(record),
        "columns": compact_columns([(str(n), t) for n, t in columns]) if columns else None,
    }
    if record.get("status") not in (None, "ready"):
        summary["status"] = record["status"]
    return {k: v for k, v in summary.items() if v is not None}


def view_summary(
    view: dict[str, Any], dataset: dict[str, Any] | None, dataset_id: Any
) -> dict[str, Any]:
    """Summary of one view, naming its dataset (a bare ``View 1`` says nothing)."""
    raw_metadata = view.get("metadata")
    metadata = raw_metadata if isinstance(raw_metadata, list) else []
    columns = [
        (str(c["display_name"]), c.get("type"))
        for c in metadata
        if isinstance(c, dict) and c.get("display_name")
    ]
    summary: dict[str, Any] = {
        "id": view.get("id"),
        "name": view.get("name"),
        "dataset_id": dataset_id,
        "dataset_name": dataset.get("name") if dataset else None,
        **_size(view.get("row_count"), view.get("column_count")),
        **_times(view.get("created_at"), view.get("data_updated_at") or view.get("updated_at")),
        "source": source_of(dataset) if dataset else None,
        "columns": compact_columns(columns) if columns else None,
    }
    if view.get("pipeline_status") not in (None, "ready"):
        summary["pipeline_status"] = view["pipeline_status"]
    return {k: v for k, v in summary.items() if v is not None}


def json_size(value: Any) -> int:
    """Characters ``value`` takes in a compact JSON envelope."""
    return len(json.dumps(value, separators=(",", ":"), default=str))


def fit_budget(
    items: list[dict[str, Any]], budget: int = LIST_DATA_BUDGET, overhead: int = 200
) -> tuple[list[dict[str, Any]], int]:
    """Keep leading items while they fit ``budget``; return them and how many were cut.

    The first item is always kept, so a single oversized record still shows.
    """
    kept: list[dict[str, Any]] = []
    used = overhead
    for item in items:
        size = json_size(item) + 1
        if kept and used + size > budget:
            break
        kept.append(item)
        used += size
    return kept, len(items) - len(kept)


def _dataset_of(view: dict[str, Any]) -> Any:
    return view.get("dataset_id") if view.get("dataset_id") is not None else view.get("ds_id")


def _group_by_dataset(
    views: list[dict[str, Any]],
) -> dict[Any, list[dict[str, Any]]]:
    groups: dict[Any, list[dict[str, Any]]] = {}
    for view in views:
        groups.setdefault(_dataset_of(view), []).append(view)
    return groups


def _choose_views(
    groups: dict[Any, list[tuple[dict[str, Any], dict[str, Any]]]],
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], Any, int]:
    """Whole datasets while they fit; a partial first dataset if it alone overflows.

    Returns the chosen (view, summary) pairs, the dataset id of the first dataset
    left out entirely (or ``None``), and how many views of a partial first dataset
    were cut.
    """
    chosen: list[tuple[dict[str, Any], dict[str, Any]]] = []
    used = 200
    for dataset_id, pairs in groups.items():
        cost = sum(json_size(s) + 1 for _v, s in pairs)
        if chosen and used + cost > LIST_DATA_BUDGET:
            return chosen, dataset_id, 0
        if not chosen and cost > LIST_DATA_BUDGET - used:
            fitted: list[tuple[dict[str, Any], dict[str, Any]]] = []
            for pair in pairs:
                step = json_size(pair[1]) + 1
                if fitted and used + step > LIST_DATA_BUDGET:
                    break
                fitted.append(pair)
                used += step
            return fitted, None, len(pairs) - len(fitted)
        chosen.extend(pairs)
        used += cost
    return chosen, None, 0


def compact_view_list(
    views: list[dict[str, Any]], datasets: dict[Any, dict[str, Any]]
) -> dict[str, Any]:
    """Summaries of ``views`` (records with renames applied), within the output cap.

    Built only from the records already fetched: no per-view backend call.
    Returns ``{"dataviews", "shown"}`` plus
    ``first_dropped_dataset`` / ``views_omitted`` when something was cut, for the
    caller to turn into a way to the next page.
    """
    groups: dict[Any, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for ds_id, group in _group_by_dataset(views).items():
        groups[ds_id] = [(v, view_summary(v, datasets.get(ds_id), ds_id)) for v in group]
    chosen, dropped_dataset, omitted = _choose_views(groups)
    kept, cut = fit_budget([summary for _view, summary in chosen])
    result: dict[str, Any] = {"dataviews": kept, "shown": len(kept)}
    if dropped_dataset is not None:
        result["first_dropped_dataset"] = dropped_dataset
    if omitted or cut:
        result["views_omitted"] = omitted + cut
    return result
