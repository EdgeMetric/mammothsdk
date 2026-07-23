"""Handlers for the ``browse`` command family (resource discovery, read-only).

Every browse operation is a read: it dispatches through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``. Commands
that take a ``project_id`` parameter resolve it from ``--project`` or the
active project (never from a positional); a command's own resource id (for
example ``folder_id``) comes from the first CLI positional. The workspace id
is never forwarded explicitly -- the SDK client already carries it.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project, resolved_project

HandlerResult = tuple[Any, dict[str, Any]]


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command."""
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


def _int_positional(invocation: Invocation, name: str) -> int | None:
    """Parse the first positional argument as an int, or return None if absent."""
    if not invocation.extra_args:
        return None
    raw = invocation.extra_args[0]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Parse the first positional argument as an int, or raise ``missing_argument``."""
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for a browse command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy each field present in ``document`` into ``kwargs`` unchanged."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def browse_folder(invocation: Invocation) -> HandlerResult:
    """Browse resources inside one folder of the active project.

    The folder id is the first positional argument; the project id comes
    from ``--project`` or the active project.
    """
    project_id = require_project(invocation)
    folder_id = _require_int_positional(invocation, "folder id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"folder_id": folder_id, "project_id": project_id}
    _forward_optional(document, kwargs, ("level", "fields"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def browse_project(invocation: Invocation) -> HandlerResult:
    """Browse the contents of the active project (datasets, folders)."""
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"project_id": project_id}
    _forward_optional(
        document, kwargs, ("fields", "name", "browse_type", "sort", "offset", "limit")
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def browse_root(invocation: Invocation) -> HandlerResult:
    """Browse resources across all workspaces the caller has access to."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(
        document,
        kwargs,
        (
            "fields",
            "name",
            "browse_type",
            "created_at",
            "updated_at",
            "sort",
            "offset",
            "limit",
            "ids",
            "include_hidden",
            "level",
            "permissions",
        ),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def browse_workspace(invocation: Invocation) -> HandlerResult:
    """Browse all resources in the active workspace (projects, datasets, folders)."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("level", "fields", "limit"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
