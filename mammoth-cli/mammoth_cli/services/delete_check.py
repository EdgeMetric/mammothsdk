"""Confirm a delete took effect: the resource is gone, or the delete is reported as refused.

A DELETE can be acknowledged (200, a job that settles) while the resource stays,
for instance when a view's join still reads the dataset. The server then returns a
map of what depends on it instead of removing it. Reporting that as a success, with
``verified: true``, would tell the caller a dataset is gone when it is not.
"""

from __future__ import annotations

import time
from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_RESOURCE_NOT_FOUND,
    EXIT_API,
    EXIT_CONFLICT,
    CliError,
)

CODE_HAS_DEPENDENTS = "has_dependents"
CODE_DELETE_NOT_APPLIED = "delete_not_applied"
CODE_DELETE_UNVERIFIED = "delete_unverified"
#: A removal can lag the acknowledgement a little; reread this often, this far apart.
_RECHECK_ATTEMPTS = 4
_RECHECK_DELAY_S = 1.0


def find_dependents(response: Any, resource_id: int) -> Any:
    """The dependency map the server keyed by ``resource_id`` in ``response``, or ``None``."""
    key = str(resource_id)
    if isinstance(response, dict):
        found = response.get(key)
        if isinstance(found, (dict, list)) and found:
            return found
        for value in response.values():
            nested = find_dependents(value, resource_id)
            if nested is not None:
                return nested
    elif isinstance(response, list):
        for value in response:
            nested = find_dependents(value, resource_id)
            if nested is not None:
                return nested
    return None


#: Backend codes that mean "this id does not exist (any more)", each with the noun and the list
#: command a hint names. A get answers them for an id that is gone, besides a 404: the dataset
#: and file get routes answer ``400 4DSET001`` / ``4FILE001``, the dataview get ``400 4DTVW019``
#: (raised when the view record comes back empty, apiv2 dataview controller ``get``), the
#: automation get ``4AUTO001`` (``invalid_automation_id``) or ``4AUTO005`` and the dashboard
#: routes ``4DASH001``. ``services.mapping`` maps these to ``resource_not_found`` from the same
#: table, so a read of a deleted id and a delete's read-back agree.
GONE_BACKEND_CODES: dict[str, tuple[str, str]] = {
    "4DSET001": ("dataset", "dataset list"),
    "4FILE001": ("file", "file list"),
    "4DTVW019": ("view", "view list DATASET_ID"),
    "4AUTO001": ("automation", "automation list"),
    "4AUTO005": ("automation", "automation list"),
    "4DASH001": ("dashboard", "dashboard list"),
}
#: What a read-back that was refused with a permission denial looks like.
_FORBIDDEN_STATUS = 403
_FORBIDDEN_BACKEND_CODE = "4PERM002"


def _is_forbidden(error: CliError) -> bool:
    """Whether ``error`` is a permission denial (HTTP 403 or the generic 4PERM002)."""
    details = error.details or {}
    return (
        details.get("status_code") == _FORBIDDEN_STATUS
        or details.get("backend_code") == _FORBIDDEN_BACKEND_CODE
    )


def _is_gone(error: CliError, *, forbidden_means_gone: bool = False) -> bool:
    """Whether a read-back error says the just-deleted resource is gone.

    A permission denial counts only when ``forbidden_means_gone`` is set: the dashboard routes
    check permission before existence, so a deleted dashboard answers 403, but a real denial
    looks the same. The caller sets the flag only when it read the resource with these
    credentials before deleting it.
    """
    details = error.details or {}
    return (
        error.code == CODE_RESOURCE_NOT_FOUND
        or details.get("backend_code") in GONE_BACKEND_CODES
        or (forbidden_means_gone and _is_forbidden(error))
    )


#: Flags and ``status`` words by which a read of a trashed record says it is in the trash.
_TRASHED_FLAGS = ("is_trashed", "trashed", "is_deleted", "deleted")
_TRASHED_STATUSES = frozenset({"trashed", "deleted"})


def _still_there(record: Any, resource_id: int) -> bool:
    """Whether ``record`` is the live resource: a trashed one counts as deleted."""
    if hasattr(record, "model_dump"):
        record = record.model_dump()
    if not isinstance(record, dict):
        return False
    if isinstance(record.get("automation"), dict):
        # The automation get wraps the record: ``{"automation": {...}}``.
        record = record["automation"]
    status = record.get("status")
    if any(record.get(flag) is True for flag in _TRASHED_FLAGS) or (
        isinstance(status, str) and status.lower() in _TRASHED_STATUSES
    ):
        return False
    return str(record.get("id")) == str(resource_id)


def ensure_deleted(
    service: Any,
    *,
    noun: str,
    resource_id: int,
    read_symbol: str,
    read_kwargs: dict[str, Any],
    responses: tuple[Any, ...],
    recovery_commands: list[str] | None = None,
    forbidden_means_gone: bool = False,
) -> None:
    """Raise unless the resource is gone after a delete.

    Args:
        service: The open service.
        noun: ``dataset``, ``view``, ``file``, ``automation`` or ``dashboard``, for the message.
        resource_id: The id that was deleted.
        read_symbol: The SDK ``get`` that reads one such resource.
        read_kwargs: Its arguments.
        responses: What the delete (and its job) returned, searched for a dependency map.
        recovery_commands: Runnable commands that help clear the blockers.
        forbidden_means_gone: Whether a 403 on the read-back proves the delete. Set it only
            when the caller read the resource with the same credentials just before deleting
            it and the delete call succeeded, so the access was there a moment ago.

    Raises:
        CliError: ``has_dependents`` when the server reported what depends on it,
            otherwise ``delete_not_applied``; the resource is still there either way.
            ``delete_unverified`` when the read-back was refused with a 403 that
            ``forbidden_means_gone`` does not vouch for: whether it is gone is not known.
    """
    dependents = next(
        (found for found in (find_dependents(r, resource_id) for r in responses) if found), None
    )
    # With a dependency map the server has said why it stayed: no point waiting.
    for attempt in range(1 if dependents is not None else _RECHECK_ATTEMPTS):
        if attempt:
            time.sleep(_RECHECK_DELAY_S)
        try:
            record = service.call(read_symbol, **read_kwargs)
        except CliError as error:
            if _is_gone(error, forbidden_means_gone=forbidden_means_gone):
                return
            if _is_forbidden(error):
                raise CliError(
                    code=CODE_DELETE_UNVERIFIED,
                    message=(
                        f"The {noun} {resource_id} delete was accepted, but reading it back "
                        "was refused (403), so it is not known whether it is gone."
                    ),
                    exit_status=EXIT_API,
                    hint=f"Check with the {noun} list command, or ask an admin to confirm.",
                    details={f"{noun}_id": resource_id, "deleted": None, "read_back": 403},
                ) from error
            raise
        if not _still_there(record, resource_id):
            return
    if dependents is not None:
        views = sorted(dependents) if isinstance(dependents, dict) else []
        which = f" (dependent views: {', '.join(views)})" if views else ""
        raise CliError(
            code=CODE_HAS_DEPENDENTS,
            message=(
                f"{noun.capitalize()} {resource_id} was not deleted: other resources still "
                f"depend on it{which}."
            ),
            exit_status=EXIT_CONFLICT,
            hint=(
                "Delete or change the dependent views and their steps first, "
                f"then delete the {noun} again."
            ),
            details={f"{noun}_id": resource_id, "dependents": dependents, "deleted": False},
            recovery_commands=recovery_commands or [],
        )
    raise CliError(
        code=CODE_DELETE_NOT_APPLIED,
        message=f"{noun.capitalize()} {resource_id} still exists after the delete was accepted.",
        exit_status=EXIT_API,
        hint=f"Read it again with the {noun} get command; retry the delete if it is still there.",
        details={f"{noun}_id": resource_id, "deleted": False},
    )
