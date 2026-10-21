"""Join snapshot, key-overlap and dry-run preview helpers."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.view._common import (
    _DATA_PAGE_SYMBOL,
    _DATAVIEW_GET_SYMBOL,
    _DISPLAY_NAME_KEY,
    _INTERNAL_NAME_KEY,
    _MAX_UNMATCHED_KEYS,
    _METADATA_KEY,
    _ROWS_KEY,
    apply_column_renames,
)
from mammoth_cli.commands.view.column_checks import (
    _column_profile,
)
from mammoth_cli.commands.view.columns import (
    _relabel_columns,
)
from mammoth_cli.commands.view.settle import (
    wait_for_pipeline_to_settle,
)
from mammoth_cli.services import read_queries
from mammoth_cli.services.conditions import compile_condition


def join_snapshot(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> dict[str, Any]:
    """Row count, columns and the first data page of a view (best effort)."""
    snapshot: dict[str, Any] = {"row_count": None, "columns": {}, "rows": []}
    try:
        info = apply_column_renames(
            service.call(
                _DATAVIEW_GET_SYMBOL,
                dataset_id=dataset_id,
                dataview_id=dataview_id,
                project_id=project_id,
            )
        )
        if isinstance(info, dict):
            snapshot["row_count"] = info.get("row_count")
            snapshot["columns"] = {
                c.get(_INTERNAL_NAME_KEY): c.get(_DISPLAY_NAME_KEY)
                for c in info.get(_METADATA_KEY) or []
                if isinstance(c, dict)
            }
            page = service.call(
                _DATA_PAGE_SYMBOL,
                dataset_id=dataset_id,
                dataview_id=dataview_id,
                project_id=project_id,
            )
            page = _relabel_columns(
                service, dataset_id, dataview_id, project_id, page, snapshot["columns"]
            )
            rows = page.get(_ROWS_KEY) if isinstance(page, dict) else None
            snapshot["rows"] = [r for r in rows or [] if isinstance(r, dict)]
    except Exception:  # noqa: BLE001 -- the check is advice; the join already ran
        return snapshot
    return snapshot


def join_after_snapshot(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None, before: Any
) -> dict[str, Any]:
    """The view once the join has run, with ``unmatched_total`` counted over every row.

    A first-page sample says nothing about the rest of the view: a join whose
    first 400 rows all matched once reported a 100% match on a view where a
    quarter of the keys were blank.
    """
    wait_for_pipeline_to_settle(service, dataset_id, dataview_id)
    snapshot = join_snapshot(service, dataset_id, dataview_id, project_id)
    known = before.get("columns", {}) if isinstance(before, dict) else {}
    added = [internal for internal in snapshot["columns"] if internal not in known]
    if added:
        snapshot["unmatched_total"] = _count_all_blank(
            service, dataset_id, dataview_id, project_id, added
        )
        # A large view reads no row count right after the join; without one the
        # whole-view blank count was dropped for a first-page sample (UQA-RT8-01).
        if snapshot["row_count"] is None:
            snapshot["row_count"] = _count_rows(service, dataset_id, dataview_id, project_id)
    return snapshot


def _count_all_blank(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None, internals: list[str]
) -> int | None:
    """Rows where every one of ``internals`` is blank; ``None`` when the count could not run."""
    condition = compile_condition(
        {"and": [{"column": name, "operator": "IS_EMPTY"} for name in internals]}
    )
    return _count_rows(service, dataset_id, dataview_id, project_id, condition.build())


def _count_rows(
    service: Any,
    dataset_id: int,
    dataview_id: int,
    project_id: int | None,
    condition: dict[str, Any] | None = None,
) -> int | None:
    """Rows of the view matching ``condition`` (all rows without one); ``None`` when the
    count could not run."""
    try:
        result = service.call(
            read_queries.AGGREGATE_SYMBOL,
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
            aggregations=[{"function": "COUNT", "as_name": "rows"}],
            condition=condition,
        )
    except Exception:  # noqa: BLE001 -- the check is advice; the join already ran
        return None
    if not isinstance(result, dict):
        return None
    rows = [row for row in result.get("data") or [] if isinstance(row, dict)]
    return int(rows[0].get("agg_0") or 0) if rows else 0


def _match_counts(
    after: dict[str, Any], added: list[str], rows: list[dict[str, Any]]
) -> tuple[int, int, bool] | None:
    """``(unmatched, checked, whole_view)``: the full count when there is one, else the sample."""
    total, after_n = after.get("unmatched_total"), after.get("row_count")
    if isinstance(total, int) and isinstance(after_n, int) and after_n > 0:
        return total, after_n, True
    if not added or not rows:
        return None
    unmatched = sum(1 for r in rows if all(r.get(c) in (None, "") for c in added))
    return unmatched, len(rows), False


#: Most distinct key values read per side for a dry-run key overlap.
_JOIN_PREVIEW_KEYS = 10000


def _unmatched(counts: dict[Any, int], other: set[Any]) -> list[str]:
    """Keys of ``counts`` absent from ``other`` (blank keys always), most rows first."""
    missing = [k for k in counts if k in (None, "") or k not in other]
    missing.sort(key=lambda key: -counts[key])
    return [str(k) for k in missing[:_MAX_UNMATCHED_KEYS]]


def key_overlap(left_counts: dict[Any, int], right_counts: dict[Any, int]) -> dict[str, Any]:
    """Match rate of each side against the other (blank keys never match).

    ``unmatched_keys`` are left keys with no right partner, ``right_unmatched_keys``
    the reverse, each most rows first: both lists show a spelling mismatch
    (``EIRE`` here, ``Ireland`` there) that one side alone would hide.
    """
    right_keys, left_keys = set(right_counts), set(left_counts)
    total = sum(left_counts.values())
    matched = sum(
        n for key, n in left_counts.items() if key not in (None, "") and key in right_keys
    )
    right_total = sum(right_counts.values())
    right_matched = sum(
        n for key, n in right_counts.items() if key not in (None, "") and key in left_keys
    )
    return {
        "rows_checked": total,
        "matched_rows": matched,
        "unmatched_rows": total - matched,
        "match_rate": round(matched / total, 3) if total else None,
        "unmatched_keys": _unmatched(left_counts, right_keys),
        "right_rows_checked": right_total,
        "right_match_rate": round(right_matched / right_total, 3) if right_total else None,
        "right_unmatched_rows": right_total - right_matched,
        "right_unmatched_key_count": sum(
            1 for key in right_counts if key in (None, "") or key not in left_keys
        ),
        "right_unmatched_keys": _unmatched(right_counts, left_keys),
    }


def _key_values(
    service: Any, dataset_id: int, view_id: int, project_id: int | None, column: str
) -> tuple[dict[Any, int], bool]:
    """``({key value: rows}, truncated)`` of one display-named column, via one aggregate."""
    mapping, _types = _column_profile(service, dataset_id, view_id, project_id)
    internal = next((i for i, display in mapping.items() if display == column), column)
    result = service.call(
        read_queries.AGGREGATE_SYMBOL,
        dataset_id=dataset_id,
        dataview_id=view_id,
        project_id=project_id,
        aggregations=[{"function": "COUNT", "as_name": "n"}],
        group_by=[internal],
        limit=_JOIN_PREVIEW_KEYS + 1,
    )
    rows = [r for r in (result or {}).get("data") or [] if isinstance(r, dict)]
    counts = {r.get("group_0"): int(r.get("agg_0") or 0) for r in rows[:_JOIN_PREVIEW_KEYS]}
    return counts, len(rows) > _JOIN_PREVIEW_KEYS


def join_dry_run_preview(
    service: Any,
    left: tuple[int, int],
    right: tuple[int, int],
    document: dict[str, Any],
    project_id: int | None,
) -> dict[str, Any]:
    """Key overlap of the join a dry run describes: reads both key columns, writes nothing.

    ``left``/``right`` are ``(dataset_id, view_id)``. Never raises: a failed
    read comes back as ``{"checked": False, "error": ...}``.
    """
    try:
        on = document.get("on")
        pair = on[0] if isinstance(on, list) and on and isinstance(on[0], dict) else {}
        if not pair.get("left") or not pair.get("right"):
            return {"checked": False, "error": "the join has no left/right key to compare"}
        left_counts, left_cut = _key_values(service, *left, project_id, str(pair["left"]))
        right_counts, right_cut = _key_values(service, *right, project_id, str(pair["right"]))
    except Exception as exc:  # noqa: BLE001 -- the dry run itself must still report
        return {"checked": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "checked": True,
        "left_key": pair["left"],
        "right_key": pair["right"],
        **key_overlap(left_counts, right_counts),
        "truncated": left_cut or right_cut,
        "note": (
            "Key overlap by exact value, before any write, for each side: a low match_rate "
            "or keys unmatched on both sides (EIRE / Ireland) mean compare type, case, "
            "padding and spelling of the two key columns, or ask the user how they relate."
        ),
    }


_RIGHT_CHECK_FIELDS = (
    "right_rows_checked",
    "right_match_rate",
    "right_unmatched_rows",
    "right_unmatched_key_count",
    "right_unmatched_keys",
)


def with_join_check(
    data: Any,
    before: Any,
    after: dict[str, Any],
    document: dict[str, Any],
    right: dict[str, Any] | None = None,
) -> Any:
    """Add ``join_check`` (row counts, columns added, match rate) to a join result.

    ``unmatched_rows`` counts rows where every added column is blank: for a
    LEFT join these are rows whose key found no match in the other view. It is
    counted over the whole view when ``after`` carries ``unmatched_total``
    (see :func:`join_after_snapshot`), else over the sampled first page.
    ``right`` is a :func:`join_dry_run_preview` of the same join: its right-side
    fields (keys only the other view has) are copied in, so a LEFT join does not
    hide them.
    """
    if not isinstance(data, dict) or not isinstance(before, dict):
        return data
    added = [
        name
        for internal, name in after.get("columns", {}).items()
        if internal not in before.get("columns", {}) and isinstance(name, str)
    ]
    rows = after.get("rows") or []
    check: dict[str, Any] = {
        "rows_before": before.get("row_count"),
        "rows_after": after.get("row_count"),
        "columns_added": added,
        "rows_checked": len(rows),
    }
    notes: list[str] = []
    on = document.get("on")
    left_key = None
    if isinstance(on, list) and on and isinstance(on[0], dict):
        left_key = on[0].get("left")
    counts = _match_counts(after, added, rows)
    if counts is not None:
        unmatched, checked, whole_view = counts
        check.update(
            unmatched_rows=unmatched,
            match_rate=round((checked - unmatched) / checked, 3),
            rows_checked=checked,
        )
        if unmatched:
            missing = [r for r in rows if all(r.get(c) in (None, "") for c in added)]
            keys = sorted({str(r.get(left_key)) for r in missing if left_key in r})
            check["unmatched_keys"] = keys[:_MAX_UNMATCHED_KEYS]
            notes.append(
                f"{unmatched} of {checked} rows found no match. If that is more "
                "than a few, compare the key columns in both views (type, case, "
                "padding) before you build on this; otherwise say so in your report."
            )
        if not whole_view:
            notes.append(f"Match rate is from the first {checked} rows only, not the whole view.")
    before_n, after_n = check["rows_before"], check["rows_after"]
    if isinstance(before_n, int) and isinstance(after_n, int):
        if after_n > before_n:
            notes.append(
                f"The join added {after_n - before_n} rows: a key repeats in the other "
                "view, so matching rows repeat. Totals over this view count them twice; "
                "use view transform lookup for one value per key."
            )
        elif after_n < before_n:
            notes.append(
                f"{before_n - after_n} rows had no match and were dropped "
                "(an INNER join keeps matched rows only)."
            )
    if right and right.get("checked"):
        check.update({k: right[k] for k in _RIGHT_CHECK_FIELDS})
        if right["right_unmatched_key_count"]:
            notes.append(
                f"{right['right_unmatched_key_count']} key(s) in the other view found no "
                "partner here (right_unmatched_keys lists the first ones); report them "
                "as well as the unmatched rows on this side."
            )
    if notes:
        check["notes"] = notes
    return {**data, "join_check": check}
