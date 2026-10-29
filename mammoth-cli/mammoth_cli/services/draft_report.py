"""Honest sample reports for connector draft reads (issues #356 and #357).

A per-parent table is previewed on a sample of its parents, and a source preview can return
fewer rows than asked. Both answers used to read as if they were the whole: ``total: 20`` was
the sample size, not the number of parents. These helpers add what the sample is.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import CliError

#: Connector draft reads whose per-parent (``each``) sources are described as a sample.
EACH_REPORTED = frozenset({"connector.draft.get", "connector.draft.source.list"})
PREVIEW_COMMAND = "connector.draft.source.preview"
_DRAFT_SOURCES_SYMBOL = "mammoth.api.connector_drafts.ConnectorDraftsAPI.sources"
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


#: ``each`` keys that name the parent source (besides any key containing "parent").
_PARENT_KEYS = frozenset({"source", "source_id", "from"})


def _names_parent(key: str) -> bool:
    """Whether the ``each`` key ``key`` is one that names the parent source."""
    lowered = key.lower()
    return "parent" in lowered or lowered in _PARENT_KEYS


def _parents_total(each: dict[str, Any], siblings: list[Any]) -> int | None:
    """The row count of the parent source ``each`` points at, or None when it is not known."""
    by_ref = {
        str(item[field]): item
        for item in siblings
        if isinstance(item, dict)
        for field in ("id", "name")
        if item.get(field) is not None
    }
    for key, value in each.items():
        if not _names_parent(key):
            continue
        parent = by_ref.get(value) if isinstance(value, str) else None
        if parent is not None:
            if parent.get("has_more"):
                # The parent was read to its limit: its row_count is a floor, not a total.
                return None
            count = parent.get("row_count")
            return count if isinstance(count, int) and not isinstance(count, bool) else None
    return None


def with_preview_cap(service: Any, draft_id: Any, source_id: Any, requested: Any, data: Any) -> Any:
    """Report a source preview that came back short of its limit while the source has more.

    The draft's source list is read once to tell a small source from a capped preview. When
    that read fails the preview stands and carries ``cap_unchecked`` (the reason), so
    "not capped" is never confused with "could not check".

    Args:
        service: The open service.
        draft_id: The draft the preview belongs to.
        source_id: The source previewed.
        requested: The ``limit`` asked for, or None when none was.
        data: The preview answer (``columns``, ``rows``, ``row_count``).

    Returns:
        ``data`` with ``capped``, ``limit_requested``, ``limit_applied``, ``source_row_count``
        and a hint added when the rows came back short and the source holds more;
        ``cap_unchecked`` when the source list could not be read; else unchanged.
    """
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(requested, int) or not isinstance(rows, list) or len(rows) >= requested:
        return data
    try:
        listed = service.call(_DRAFT_SOURCES_SYMBOL, draft_id=draft_id)
    except CliError as error:
        return {**data, "cap_unchecked": error.message}
    listed = listed.model_dump(mode="json") if hasattr(listed, "model_dump") else listed
    sources = listed.get("sources") if isinstance(listed, dict) else None
    source = next(
        (
            item
            for item in sources or []
            if isinstance(item, dict) and str(item.get("id")) == str(source_id)
        ),
        None,
    )
    return _cap_note(data, requested, source)


def _cap_note(data: dict[str, Any], requested: int, source: dict[str, Any] | None) -> Any:
    """``data`` with the cap keys added when the source holds more rows than came back."""
    rows = data["rows"]
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
