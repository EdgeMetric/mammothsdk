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
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from mammoth_cli.services.stored_stats import stored_facts

#: Characters of ``data`` a list may use; the agent tool caps a whole result at 4,000.
LIST_DATA_BUDGET = 3500
#: ``fields`` asked of the dataset list route: everything the summary shows.
DATASET_LIST_FIELDS = (
    "id,name,created_at,updated_at,status,stats,sources,data_schema,additional_info"
)

_MAX_COLUMNS = 4
#: Columns whose stored sample values a view summary shows, and values per column.
_SAMPLE_COLUMNS = 6
_SAMPLE_VALUES = 2
_MAX_CELL_CHARS = 12
#: Room reserved per view for its sample values, added after the size check.
SAMPLE_ALLOWANCE = 150
#: Room reserved per dataset for its ``views`` list, added after the size check.
VIEWS_ALLOWANCE = 60
#: Concurrent stored-stats reads for one list.
_STATS_WORKERS = 8
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


def compact_columns(columns: list[tuple[str, Any]], limit: int | None = _MAX_COLUMNS) -> str:
    """``"Order ID:text, Sales:numeric (+15 more)"`` -- names and types, capped.

    ``limit=None`` lists every column.
    """
    cap = len(columns) if limit is None else limit
    shown = [f"{name}:{_type_word(kind)}" for name, kind in columns[:cap]]
    extra = len(columns) - cap
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


def attach_views(
    items: list[dict[str, Any]], read_views: Callable[[int], list[dict[str, Any]]]
) -> None:
    """Give each dataset summary its ``views`` as ``[{id, name}]`` (in place).

    One read per item, run concurrently. A dataset whose views cannot be read
    says why instead of showing none.
    """

    def one(item: dict[str, Any]) -> Any:
        try:
            return [{"id": v.get("id"), "name": v.get("name")} for v in read_views(item["id"])]
        except Exception as exc:  # noqa: BLE001 -- one unreadable dataset must not sink the list
            return f"unavailable: {str(exc)[:80]}"

    with ThreadPoolExecutor(max_workers=_STATS_WORKERS) as pool:
        for item, found in zip(items, pool.map(one, items), strict=True):
            item["views"] = found


def name_matches(records: list[dict[str, Any]], needle: str) -> list[dict[str, Any]]:
    """Records whose name contains ``needle``, case-insensitively, in list order."""
    lowered = needle.lower()
    return [r for r in records if isinstance(r.get("name"), str) and lowered in r["name"].lower()]


def _name_hit(record: dict[str, Any]) -> dict[str, Any]:
    """One name-search row: identity and size only (no column list, so many rows fit)."""
    stats = record.get("stats") if isinstance(record.get("stats"), dict) else {}
    hit: dict[str, Any] = {
        "id": record.get("id"),
        "name": record.get("name"),
        **_size(stats.get("row_count"), stats.get("column_count")),
    }
    if record.get("status") not in (None, "ready"):
        hit["status"] = record["status"]
    return {k: v for k, v in hit.items() if v is not None}


def search_page(
    records: list[dict[str, Any]], needle: str, offset: int, limit: int | None
) -> dict[str, Any]:
    """One page of a name search over ``records`` (paged over the matches, not the project)."""
    matches = name_matches(records, needle)
    end = None if limit is None else offset + limit
    kept, _omitted = fit_budget([_name_hit(r) for r in matches[offset:end]])
    result: dict[str, Any] = {"datasets": kept, "shown": len(kept), "matched": len(matches)}
    if offset + len(kept) < len(matches):
        result["more"] = True
        result["next_offset"] = offset + len(kept)
    return result


def view_summary(
    view: dict[str, Any],
    dataset: dict[str, Any] | None,
    dataset_id: Any,
    all_columns: bool = False,
) -> dict[str, Any]:
    """Summary of one view, naming its dataset (a bare ``View 1`` says nothing).

    ``all_columns`` lists every column with its type instead of the first few.
    """
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
        "columns": (
            compact_columns(columns, None if all_columns else _MAX_COLUMNS) if columns else None
        ),
    }
    if view.get("pipeline_status") not in (None, "ready"):
        summary["pipeline_status"] = view["pipeline_status"]
    return {k: v for k, v in summary.items() if v is not None}


def json_size(value: Any) -> int:
    """Characters ``value`` takes in a compact JSON envelope."""
    return len(json.dumps(value, separators=(",", ":"), default=str))


def fit_budget(
    items: list[dict[str, Any]],
    budget: int = LIST_DATA_BUDGET,
    overhead: int = 200,
    per_item: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Keep leading items while they fit ``budget``; return them and how many were cut.

    The first item is always kept, so a single oversized record still shows.
    ``per_item`` reserves room for fields added to each kept item afterwards.
    """
    kept: list[dict[str, Any]] = []
    used = overhead
    for item in items:
        size = json_size(item) + 1 + per_item
        if kept and used + size > budget:
            break
        kept.append(item)
        used += size
    return kept, len(items) - len(kept)


def _cell_text(stored: Any) -> str:
    """A stored sample as text: the inner ``value`` of a ``{"value": ...}`` record."""
    inner = stored.get("value", stored) if isinstance(stored, dict) else stored
    return str(inner)[:_MAX_CELL_CHARS]


def sample_values(payload: Any, metadata: list[Any]) -> dict[str, list[str]]:
    """Stored per-column sample values (first columns only) from a stats payload.

    These are values the backend keeps per column, not one real row.
    """
    columns = [
        (str(c["display_name"]), c["internal_name"])
        for c in metadata
        if isinstance(c, dict) and c.get("display_name") and c.get("internal_name")
    ]
    facts, _rows = stored_facts(payload, dict(columns))
    found: dict[str, list[str]] = {}
    for name, _internal in columns[:_SAMPLE_COLUMNS]:
        values = facts.get(name, {}).get("sample")
        if values:
            found[name] = [_cell_text(v) for v in values[:_SAMPLE_VALUES]]
    return found


def _view_samples(
    view: dict[str, Any], read_stats: Callable[[dict[str, Any]], Any]
) -> dict[str, list[str]] | str:
    """One view's stored samples, or why they are not available (never a silent gap)."""
    try:
        found = sample_values(read_stats(view), view.get("metadata") or [])
    except Exception as exc:  # noqa: BLE001 -- one unreadable view must not sink the list
        return f"unavailable: {str(exc)[:80]}"
    return found or "none stored"


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
        cost = sum(json_size(s) + SAMPLE_ALLOWANCE + 1 for _v, s in pairs)
        if chosen and used + cost > LIST_DATA_BUDGET:
            return chosen, dataset_id, 0
        if not chosen and cost > LIST_DATA_BUDGET - used:
            fitted: list[tuple[dict[str, Any], dict[str, Any]]] = []
            for pair in pairs:
                step = json_size(pair[1]) + SAMPLE_ALLOWANCE + 1
                if fitted and used + step > LIST_DATA_BUDGET:
                    break
                fitted.append(pair)
                used += step
            return fitted, None, len(pairs) - len(fitted)
        chosen.extend(pairs)
        used += cost
    return chosen, None, 0


def compact_view_list(
    views: list[dict[str, Any]],
    datasets: dict[Any, dict[str, Any]],
    read_stats: Callable[[dict[str, Any]], Any],
    all_columns: bool = False,
) -> dict[str, Any]:
    """Summaries of ``views`` (records with renames applied), within the output cap.

    Sizes and columns come from the records already fetched. Each kept view then
    gets ``sample_values`` from the backend's stored column stats via ``read_stats``
    (one stored-stats read per kept view, run concurrently; no query runs).
    Returns ``{"dataviews", "shown"}`` plus
    ``first_dropped_dataset`` / ``views_omitted`` when something was cut, for the
    caller to turn into a way to the next page.
    """
    groups: dict[Any, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for ds_id, group in _group_by_dataset(views).items():
        groups[ds_id] = [
            (v, view_summary(v, datasets.get(ds_id), ds_id, all_columns)) for v in group
        ]
    chosen, dropped_dataset, omitted = _choose_views(groups)
    with ThreadPoolExecutor(max_workers=_STATS_WORKERS) as pool:
        samples = list(pool.map(lambda pair: _view_samples(pair[0], read_stats), chosen))
    items = [
        {**summary, "sample_values": found}
        for (_v, summary), found in zip(chosen, samples, strict=True)
    ]
    kept, cut = fit_budget(items)
    result: dict[str, Any] = {"dataviews": kept, "shown": len(kept)}
    if dropped_dataset is not None:
        result["first_dropped_dataset"] = dropped_dataset
    if omitted or cut:
        result["views_omitted"] = omitted + cut
    return result
