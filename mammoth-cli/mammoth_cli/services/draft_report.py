"""Honest sample reports for connector draft reads (issues #356 and #357).

A per-parent table is previewed on a sample of its parents, and a source preview can return
fewer rows than asked. Both answers used to read as if they were the whole: ``total: 20`` was
the sample size, not the number of parents. These helpers add what the sample is.
"""

from __future__ import annotations

from typing import Any

#: Marks that a preview returned fewer rows than asked while the source holds more.
HINT_CAPPED = (
    "The server returned fewer rows than asked for; a preview is a sample. "
    "Save the draft to read every row."
)


def with_each_reports(data: Any) -> Any:
    """Describe the sample behind every per-parent (``each``) source in ``data``.

    Args:
        data: A draft, a source list, or one source, as the API returned it.

    Returns:
        ``data`` with ``sampled``, ``parents_total`` and ``summary`` added to each ``each``
        block; anything else is returned unchanged.
    """
    if not isinstance(data, dict):
        return data
    sources = data.get("sources")
    if isinstance(sources, list):
        return {
            **data,
            "sources": [_with_report(source, sources) for source in sources],
        }
    return _with_report(data, [])


def _with_report(source: Any, siblings: list[Any]) -> Any:
    """``source`` with its ``each`` block explained (unchanged when it has none)."""
    each = source.get("each") if isinstance(source, dict) else None
    if not isinstance(each, dict) or not isinstance(each.get("total"), int):
        return source
    sampled = each["total"]
    parents = _parents_total(each, siblings) if each.get("capped") else sampled
    return {**source, "each": {**each, **_report(each, sampled, parents)}}


def _report(each: dict[str, Any], sampled: int, parents: int | None) -> dict[str, Any]:
    """The added keys: the sample, the real parent count (or None), and one sentence."""
    read, failed = each.get("read"), each.get("failed")
    outcome = (
        f"{read} read, {failed} failed"
        if isinstance(read, int) and isinstance(failed, int)
        else None
    )
    if not each.get("capped"):
        head = f"read all {sampled} parents"
    elif parents is not None:
        head = f"sampled {sampled} of {parents} parents"
    else:
        head = f"capped at {sampled} parents, total unknown"
    return {
        "sampled": sampled,
        "parents_total": parents,
        "summary": head + (f"; {outcome}" if outcome else ""),
    }


def _parents_total(each: dict[str, Any], siblings: list[Any]) -> int | None:
    """The row count of the parent source ``each`` points at, or None when it is not known."""
    by_ref = {
        str(item[field]): item
        for item in siblings
        if isinstance(item, dict)
        for field in ("id", "name")
        if item.get(field) is not None
    }
    for value in each.values():
        parent = by_ref.get(value) if isinstance(value, str) else None
        if parent is not None:
            count = parent.get("row_count")
            return count if isinstance(count, int) and not isinstance(count, bool) else None
    return None


def with_preview_cap(data: Any, requested: int | None, source: dict[str, Any] | None) -> Any:
    """Say so when a source preview returned fewer rows than asked and the source has more.

    Args:
        data: The preview answer (``columns``, ``rows``, ``row_count``).
        requested: The ``limit`` asked for, or None when none was.
        source: The source's own record from the draft's source list, or None when unread.

    Returns:
        ``data`` with ``capped``, ``limit_requested``, ``limit_applied`` and a hint added
        when the rows came back short of the limit and the source holds more; else unchanged.
    """
    if not isinstance(data, dict) or requested is None:
        return data
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) >= requested:
        return data
    total = source.get("row_count") if isinstance(source, dict) else None
    more = bool(isinstance(source, dict) and source.get("has_more")) or (
        isinstance(total, int) and total > len(rows)
    )
    if not more:
        return data
    capped: dict[str, Any] = {
        "capped": True,
        "limit_requested": requested,
        "limit_applied": len(rows),
        "hint": HINT_CAPPED,
    }
    if isinstance(total, int):
        capped["source_row_count"] = total
    return {**data, **capped}
