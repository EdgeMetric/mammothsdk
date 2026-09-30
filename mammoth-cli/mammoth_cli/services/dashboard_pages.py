"""Check what ``dashboard pages add`` actually built.

The add-pages route keeps every requested page even when it refuses the
page's charts (for example a ``pie`` the data does not support); the refusal
is only prose in ``message`` ("Couldn't do: ..."). An agent that reads
``added_page_ids`` sees success and leaves empty pages on the dashboard. This
module names the refusals, finds the new pages that asked for charts and got
none, and removes those pages with one canvas save.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

CANVAS_GET = "mammoth.api.dashboards.DashboardsAPI.canvas_get"
CANVAS_SAVE = "mammoth.api.dashboards.DashboardsAPI.canvas_save"

_REFUSED = re.compile(r"Couldn[’']t do:\s*(?P<notes>.+?)[._\s]*$", re.DOTALL)


def refused_notes(message: Any) -> list[str]:
    """Return the server's "Couldn't do" notes from an add-pages ``message``."""
    if not isinstance(message, str):
        return []
    match = _REFUSED.search(message)
    if match is None:
        return []
    return [note.strip() for note in match.group("notes").split(";") if note.strip()]


def _as_list(added_ids: Any) -> list[Any]:
    """Return ``added_page_ids`` as a list (empty when the server sent none)."""
    return list(added_ids) if isinstance(added_ids, list) else []


def _dump(value: Any) -> Any:
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def _requested_charts(page: Mapping[str, Any]) -> bool:
    charts = page.get("charts")
    return isinstance(charts, list) and bool(charts) and not page.get("focus")


def _empty(page: Mapping[str, Any]) -> bool:
    return not page.get("added") and not page.get("focus")


def check_added_pages(
    service: Any,
    dashboard_id: int,
    requested: Sequence[Mapping[str, Any]],
    data: Any,
) -> Any:
    """Add ``chart_check`` to an add-pages result and drop pages left empty.

    Args:
        service: The session service.
        dashboard_id: The dashboard the pages were added to.
        requested: ``body.params.pages`` as sent, in order.
        data: The add-pages response (``added_page_ids``, ``message``, ...).

    Returns:
        ``data`` unchanged when no new page asked for charts; otherwise with
        ``chart_check``: ``refused`` (the server's notes),
        ``removed_pages`` (new pages that asked for charts and got none, now
        removed) and, when a removal was needed but failed, ``fix``. After a
        removal, ``sequence`` and ``bake_job_id`` are those of the save.
    """
    data = _dump(data)
    if not isinstance(data, dict):
        return data
    refused = refused_notes(data.get("message"))
    added_ids = data.get("added_page_ids")
    # Pages come back in request order; only a page that asked for charts
    # (and has no focus, whose built-in charts always render) can be empty.
    candidates = {
        page_id: page
        for page_id, page in zip(_as_list(added_ids), requested, strict=False)
        if isinstance(page, Mapping) and _requested_charts(page)
    }
    if not candidates:
        return data
    check: dict[str, Any] = {"refused": refused, "removed_pages": []}
    if not refused:
        data["chart_check"] = check
        return data
    canvas_doc = _dump(service.call(CANVAS_GET, dashboard_id=dashboard_id))
    canvas = canvas_doc.get("canvas") if isinstance(canvas_doc, dict) else None
    pages = canvas.get("pages") if isinstance(canvas, dict) else None
    if not isinstance(canvas, dict) or not isinstance(pages, list):
        data["chart_check"] = check
        return data
    empty = [
        page
        for page in pages
        if isinstance(page, dict) and page.get("id") in candidates and _empty(page)
    ]
    if not empty:
        data["chart_check"] = check
        return data
    removed = [{"id": page.get("id"), "title": page.get("title")} for page in empty]
    empty_ids = {page.get("id") for page in empty}
    kept = [page for page in pages if not (isinstance(page, dict) and page.get("id") in empty_ids)]
    canvas = {**canvas, "pages": kept}
    if canvas.get("active_page_id") in empty_ids:
        canvas["active_page_id"] = next(
            (page.get("id") for page in kept if isinstance(page, dict)), None
        )
    meta = canvas_doc.get("meta") if isinstance(canvas_doc, dict) else None
    params: dict[str, Any] = {"canvas": canvas}
    if isinstance(meta, dict) and isinstance(meta.get("sequence"), int):
        params["base_sequence"] = meta["sequence"]
    try:
        saved = _dump(service.call(CANVAS_SAVE, dashboard_id=dashboard_id, body={"params": params}))
    except Exception as exc:  # noqa: BLE001 - the pages were added; report, do not fail
        check["empty_pages"] = removed
        check["fix"] = (
            f"The pages {', '.join(str(p['id']) for p in removed)} have no charts and could "
            f"not be removed ({exc}). Remove them: mammoth dashboard canvas get {dashboard_id}, "
            "delete them from canvas.pages, then dashboard canvas save."
        )
        data["chart_check"] = check
        return data
    check["removed_pages"] = removed
    if isinstance(saved, dict):
        for key in ("sequence", "bake_job_id"):
            if key in saved:
                data[key] = saved[key]
    data["added_page_ids"] = [
        page_id for page_id in _as_list(added_ids) if page_id not in empty_ids
    ]
    data["chart_check"] = check
    return data
