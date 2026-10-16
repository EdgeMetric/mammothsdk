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


#: Backend codes a get answers for an id that no longer exists, besides a 404: the
#: dataset get route answers ``400 4DSET001`` for a deleted dataset, and the dataview get
#: ``400 4DTVW019`` for a deleted view (it raises it when the view record comes back empty,
#: apiv2 dataview controller ``get``).
_GONE_BACKEND_CODES = frozenset({"4DSET001", "4DTVW019"})


def _is_gone(error: CliError) -> bool:
    return (
        error.code == CODE_RESOURCE_NOT_FOUND
        or (error.details or {}).get("backend_code") in _GONE_BACKEND_CODES
    )


def _still_there(record: Any, resource_id: int) -> bool:
    return isinstance(record, dict) and str(record.get("id")) == str(resource_id)


def ensure_deleted(
    service: Any,
    *,
    noun: str,
    resource_id: int,
    read_symbol: str,
    read_kwargs: dict[str, Any],
    responses: tuple[Any, ...],
    recovery_commands: list[str] | None = None,
) -> None:
    """Raise unless the resource is gone after a delete.

    Args:
        service: The open service.
        noun: ``dataset``, ``view`` or ``project``, for the message.
        resource_id: The id that was deleted.
        read_symbol: The SDK ``get`` that reads one such resource.
        read_kwargs: Its arguments.
        responses: What the delete (and its job) returned, searched for a dependency map.
        recovery_commands: Runnable commands that help clear the blockers.

    Raises:
        CliError: ``has_dependents`` when the server reported what depends on it,
            otherwise ``delete_not_applied``; the resource is still there either way.
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
            if _is_gone(error):
                return
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
