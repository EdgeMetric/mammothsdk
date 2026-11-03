"""Say why a view id is not found: in the project's trash, or gone for good.

mammothsdk#381 item 10: an export's source view that had been deleted came back
only as "not found in any dataset", so the caller could not tell a typo from a
trashed view from one purged for good.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mammoth_cli.errors.envelope import CODE_RESOURCE_NOT_FOUND, CliError

TRASH_LIST_SYMBOL = "mammoth.api.trash.TrashAPI.list"
#: Trashed views read per page, and pages read at most, looking for one id.
_PAGE = 100
_PAGES = 5

Call = Callable[..., Any]


def trashed_view(call: Call, project_id: int, view_id: int) -> dict[str, Any] | None:
    """The project's trash row for ``view_id``, or ``None`` when it is not there.

    Raises:
        CliError: When the trash cannot be read.
        ValueError: When the trash answer carries no item list.
    """
    for page in range(_PAGES):
        listed = call(
            TRASH_LIST_SYMBOL,
            project_id=project_id,
            type="dataview",
            limit=_PAGE,
            offset=page * _PAGE,
        )
        items = listed.get("items") if isinstance(listed, dict) else None
        if not isinstance(items, list):
            # An answer without items says nothing about the view: keep the original error.
            raise ValueError("the trash list has no items")
        for item in items:
            if isinstance(item, dict) and item.get("id") == view_id:
                return item
        if len(items) < _PAGE:
            return None
    return None


def explain_missing_view(call: Call, project_id: Any, view_id: Any, error: CliError) -> CliError:
    """``error`` with what the trash says about ``view_id``; ``error`` itself when the check
    cannot run (not a not-found, no project, or the trash unreadable)."""
    if error.code != CODE_RESOURCE_NOT_FOUND:
        return error
    if not isinstance(project_id, int) or not isinstance(view_id, int):
        return error
    try:
        row = trashed_view(call, project_id, view_id)
    except Exception:  # noqa: BLE001 -- the trash read is advice; the not-found stands
        return error
    details = dict(error.details or {})
    details.update(view_id=view_id, project_id=project_id)
    if row is None:
        return CliError(
            code=CODE_RESOURCE_NOT_FOUND,
            message=(
                f"View {view_id} is not in project {project_id}, nor in its trash: it was "
                "deleted for good (the trash keeps views for 30 days), or it belongs to "
                "another project."
            ),
            exit_status=error.exit_status,
            hint=error.hint,
            details={**details, "in_trash": False},
            recovery_commands=list(error.recovery_commands or []),
        )
    dataset_id = row.get("dataset_id")
    by = (
        (row.get("trashed_by") or {}).get("name")
        if isinstance(row.get("trashed_by"), dict)
        else None
    )
    when = str(row.get("trashed_at") or "")[:10]
    days = row.get("days_until_purge")
    message = f"View {view_id} ({row.get('name')}) is in project {project_id}'s trash"
    message += f": trashed {when}" if when else ""
    message += f" by {by}" if by else ""
    message += f"; it is deleted for good in {days} days." if days is not None else "."
    restore = f"mammoth view restore {view_id} {dataset_id} --project {project_id}"
    return CliError(
        code=CODE_RESOURCE_NOT_FOUND,
        message=message,
        exit_status=error.exit_status,
        hint="Restore it to use it again; anything built on it stays broken until then.",
        details={**details, "in_trash": True, "trashed": row},
        recovery_commands=[restore] if dataset_id is not None else [],
    )
