"""Upload preview and view profile helpers."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.view._common import (
    _DATA_PAGE_SYMBOL,
    _DATAVIEW_GET_SYMBOL,
    _DATAVIEW_LIST_SYMBOL,
    _DISPLAY_NAME_KEY,
    _INTERNAL_NAME_KEY,
    _METADATA_KEY,
    _ROWS_KEY,
    apply_column_renames,
)
from mammoth_cli.commands.view.column_checks import (
    _check_columns,
)
from mammoth_cli.commands.view.columns import (
    _relabel_columns,
)
from mammoth_cli.commands.view.listing import (
    view_freshness,
)
from mammoth_cli.services.dashboard_review import UPLOAD_NOTE, upload_hints

#: Rows an upload shows of each new view (enough to see keys and formats).
_UPLOAD_SAMPLE_ROWS = 3


def _select_view(views: list[Any], view_id: int | None) -> dict[str, Any] | None:
    """The view with ``view_id``, or the first (most recent) one when none is named."""
    if view_id is None:
        first: dict[str, Any] = views[0]
        return first
    return next((v for v in views if isinstance(v, dict) and v.get("id") == view_id), None)


def upload_preview(
    service: Any, dataset_id: int, project_id: int | None, view_id: int | None = None
) -> dict[str, Any]:
    """A view of a dataset (the first unless ``view_id``): columns, types, sample rows, warnings.

    ``before_dashboard`` names the columns to add before any dashboard is
    made (revenue from a unit price and a quantity), since a dashboard does
    not see columns added after it.

    An agent that has just uploaded files tends to read the local copies
    instead of the data in Mammoth, and so misses what Mammoth made of them
    (a price read as TEXT, blanks). The upload result carries the answer.
    Best effort, but never silent: a preview that could not be built comes
    back as ``{"preview_error": reason}`` (no ``view_id``), and one that was
    built says so with ``column_checks`` and an always-present
    ``column_warnings`` list.
    """
    try:
        listing = service.call(_DATAVIEW_LIST_SYMBOL, dataset_id=dataset_id, project_id=project_id)
        views = listing.get("dataviews") if isinstance(listing, dict) else None
        if not isinstance(views, list) or not views or not isinstance(views[0], dict):
            return {"preview_error": f"dataset {dataset_id} has no view to preview"}
        chosen = _select_view(views, view_id)
        if chosen is None:
            return {"preview_error": f"dataset {dataset_id} has no view {view_id}"}
        # A dataset with more than one live view has one previewed here; the
        # rest are named (id + name) so a caller (``project.check``) can say
        # a view besides the one checked exists, rather than silently acting
        # on the single view this function happens to preview.
        other_views = [
            {"id": other.get("id"), "name": other.get("name")}
            for other in views
            if other is not chosen and isinstance(other, dict) and isinstance(other.get("id"), int)
        ]
        record = apply_column_renames(chosen)
        view_id = record.get("id")
        if not isinstance(view_id, int):
            return {"preview_error": f"dataset {dataset_id}'s first view has no id"}
        mapping: dict[str, str] = {}
        types: dict[str, str] = {}
        for column in record.get(_METADATA_KEY) or []:
            if not isinstance(column, dict):
                continue
            internal = column.get(_INTERNAL_NAME_KEY)
            display = column.get(_DISPLAY_NAME_KEY)
            if isinstance(internal, str) and isinstance(display, str):
                mapping[internal] = display
                types[display] = str(column.get("type") or "")
        page = service.call(
            _DATA_PAGE_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
        )
        page = _relabel_columns(service, dataset_id, view_id, project_id, page, mapping)
        rows = page.get(_ROWS_KEY) if isinstance(page, dict) else None
        rows = [row for row in rows or [] if isinstance(row, dict)]
    except Exception as exc:  # noqa: BLE001 -- a preview must never fail the upload
        return {"preview_error": f"{type(exc).__name__}: {exc}"}
    checks, warnings = _check_columns(rows, types, view_id, dataset_id, project_id=project_id)
    preview: dict[str, Any] = {
        "view_id": view_id,
        "view_name": record.get("name"),
        "row_count": record.get("row_count"),
        "columns": types,
        "sample_rows": rows[:_UPLOAD_SAMPLE_ROWS],
        "column_checks": {**checks, "scope": "first_page"},
        "column_warnings": warnings,
        "freshness": view_freshness(record),
    }
    try:
        text_numbers = [
            str(w.get("column"))
            for w in warnings
            if isinstance(w, dict) and w.get("issue") == "numbers_stored_as_text"
        ]
        hints = upload_hints(
            view_id, record.get(_METADATA_KEY) or [], rows, dataset_id, text_numbers
        )
    except Exception:  # noqa: BLE001
        hints = []
    if hints:
        preview["before_dashboard"] = {"warnings": hints, "note": UPLOAD_NOTE}
    if other_views:
        preview["other_views"] = other_views
    return preview


def view_profiles(
    service: Any, dataset_id: int, view_id: int, project_id: int | None
) -> list[dict[str, Any]] | None:
    """Column profile of a view (types and blank shares) for the dashboard check."""
    from mammoth_cli.services.dashboard_review import profiles_from_view

    try:
        info = apply_column_renames(
            service.call(
                _DATAVIEW_GET_SYMBOL,
                dataset_id=dataset_id,
                dataview_id=view_id,
                project_id=project_id,
            )
        )
        metadata = [c for c in (info or {}).get(_METADATA_KEY) or [] if isinstance(c, dict)]
        mapping = {
            c[_INTERNAL_NAME_KEY]: c[_DISPLAY_NAME_KEY]
            for c in metadata
            if isinstance(c.get(_INTERNAL_NAME_KEY), str)
            and isinstance(c.get(_DISPLAY_NAME_KEY), str)
        }
        page = service.call(
            _DATA_PAGE_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
        )
        page = _relabel_columns(service, dataset_id, view_id, project_id, page, mapping)
        rows = page.get(_ROWS_KEY) if isinstance(page, dict) else None
        return profiles_from_view(metadata, rows or [])
    except Exception:  # noqa: BLE001 -- advice only
        return None
