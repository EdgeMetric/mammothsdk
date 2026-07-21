"""Handlers for the ``trash`` command family (project-scoped).

Every trash operation runs inside a resolved project: the project id comes
from ``--project`` or the active project. Bulk item lists for ``add`` and
``restore`` come from the strict ``--input`` document; list filters are all
optional and forwarded only when present. Handlers dispatch through the
generic :meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the
public SDK method named by the command's reviewed manifest ``sdk_symbol``.
All three commands carry a ``none`` confirmation policy: moving to trash and
restoring from trash are both reviewed as benign, reversible mutations.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project

HandlerResult = tuple[Any, dict[str, Any]]

_LIST_OPTIONAL = (
    "type",
    "sort",
    "order",
    "limit",
    "offset",
    "q",
    "trashed_by",
    "trashed_after",
    "trashed_before",
    "expiring_within_days",
    "folder_path",
    "folder_root",
)


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command."""
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code="sdk_symbol_unresolved",
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code="missing_field",
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a trash command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy each present field from ``document`` into ``kwargs`` unchanged."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def trash_add(invocation: Invocation) -> HandlerResult:
    """Move resources to trash in bulk. ``items`` is required via ``--input``."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    items = _require_field(document, "items")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), items=items, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def trash_list(invocation: Invocation) -> HandlerResult:
    """List trashed resources in the active project, with optional filters."""
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"project_id": project_id}
    _forward_optional(document, kwargs, _LIST_OPTIONAL)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def trash_restore(invocation: Invocation) -> HandlerResult:
    """Restore resources from trash in bulk. ``items`` is required via ``--input``."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    items = _require_field(document, "items")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), items=items, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)
