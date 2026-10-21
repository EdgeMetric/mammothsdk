"""Column profile and column-warning checks attached to view reads."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.view._common import (
    _DISPLAY_NAME_KEY,
    _INTERNAL_NAME_KEY,
    _ROWS_KEY,
)
from mammoth_cli.commands.view.columns import (
    _column_currencies,
    _dataview_info,
    _metadata_of,
    _relabel_columns,
)
from mammoth_cli.services.data_quality import column_warnings, duplicate_rows_fact


def _column_profile(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> tuple[dict[str, str], dict[str, str]]:
    """One metadata read: internal-to-display names, and display name to type."""
    mapping, types, _currencies = _column_profile_with_currency(
        service, dataset_id, dataview_id, project_id
    )
    return mapping, types


def _column_profile_with_currency(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """One metadata read: internal-to-display names, display name to type, and display
    name to the currency its format sets."""
    return _profile_of_info(_dataview_info(service, dataset_id, dataview_id, project_id))


def _profile_of_info(
    info: dict[str, Any],
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """:func:`_column_profile_with_currency` from an already-read dataview info."""
    mapping: dict[str, str] = {}
    types: dict[str, str] = {}
    for column in _metadata_of(info):
        internal = column.get(_INTERNAL_NAME_KEY)
        display = column.get(_DISPLAY_NAME_KEY)
        if isinstance(internal, str) and isinstance(display, str):
            mapping[internal] = display
            types[display] = str(column.get("type") or "")
    return mapping, types, _column_currencies(info)


def _relabel_and_check(
    service: Any,
    dataset_id: int,
    view_id: int,
    project_id: int | None,
    data: Any,
    mapping: dict[str, str] | None = None,
    types: dict[str, str] | None = None,
    whole_view: bool = False,
) -> Any:
    """Relabel a data page to display names and add ``column_warnings`` and ``duplicates``.

    Only read-only data reads call this, so a dates-as-text finding carries no convert fix.

    The metadata read happens only when the page has rows and the caller has
    not read it already (one read serves both the names and the types).
    """
    rows = data.get(_ROWS_KEY) if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        data = _relabel_columns(service, dataset_id, view_id, project_id, data, mapping)
        return _with_column_warnings(
            data, types or {}, view_id, dataset_id, read_only=True, project_id=project_id
        )
    if mapping is None or types is None:
        mapping, types = _column_profile(service, dataset_id, view_id, project_id)
    data = _relabel_columns(service, dataset_id, view_id, project_id, data, mapping)
    data = _with_column_warnings(
        data, types, view_id, dataset_id, read_only=True, project_id=project_id
    )
    return _with_duplicates_fact(data, view_id, dataset_id, whole_view, project_id=project_id)


def _with_duplicates_fact(
    data: Any,
    view_id: int,
    dataset_id: int | None,
    whole_view: bool,
    *,
    project_id: int | None = None,
) -> Any:
    """Add ``duplicates``: the read's own statement about exact duplicate rows."""
    if not isinstance(data, dict) or not isinstance(data.get(_ROWS_KEY), list):
        return data
    fact = duplicate_rows_fact(
        data[_ROWS_KEY], view_id, dataset_id, whole_view=whole_view, project_id=project_id
    )
    return {**data, "duplicates": fact} if fact is not None else data


#: Issue types ``column_warnings`` looks for; ``column_checks.checked`` names them.
COLUMN_CHECK_ISSUES = (
    "numbers_stored_as_text",
    "dates_stored_as_text",
    "variant_spellings",
    "renamed_label",
    "blank_values",
    "duplicate_rows",
)


def _with_column_warnings(
    data: Any,
    types: dict[str, str],
    view_id: int,
    dataset_id: int | None = None,
    read_only: bool = False,
    project_id: int | None = None,
) -> Any:
    """Add ``column_checks`` (always) and ``column_warnings`` (when found).

    ``column_checks`` says the page was checked, over how many rows and for
    which issues, so an absent ``column_warnings`` reads as "clean" and never
    as "not checked". A check that throws is reported in ``column_checks.error``.
    """
    if not isinstance(data, dict) or not isinstance(data.get(_ROWS_KEY, []), list):
        return data
    checks, warnings = _check_columns(
        data.get(_ROWS_KEY) or [], types, view_id, dataset_id, read_only, project_id
    )
    out = {**data, "column_checks": checks}
    return {**out, "column_warnings": warnings} if warnings else out


def _check_columns(
    rows: list[Any],
    types: dict[str, str],
    view_id: int,
    dataset_id: int | None,
    read_only: bool = False,
    project_id: int | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run ``column_warnings`` and describe what was checked (never raises)."""
    checks: dict[str, Any] = {
        "scope": "page",
        "rows_checked": len(rows),
        "checked": list(COLUMN_CHECK_ISSUES) if rows and types else [],
        "found": 0,
    }
    warnings: list[dict[str, Any]] = []
    if rows and types:
        try:
            warnings = column_warnings(rows, types, view_id, dataset_id, read_only, project_id)
        except Exception as exc:  # noqa: BLE001 -- a presentation aid must not fail the read
            checks["checked"] = []
            checks["error"] = f"{type(exc).__name__}: {exc}"
    checks["found"] = len(warnings)
    return checks, warnings
