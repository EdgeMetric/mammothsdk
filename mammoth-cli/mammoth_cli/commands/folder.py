"""Handlers for the ``folder`` command family (project-scoped).

Every folder operation runs inside a resolved project: the project id comes
from ``--project`` or the active project, and folder ids come from a positional
argument or the strict ``--input`` document. Handlers dispatch through the
generic :meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the
public SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project

HandlerResult = tuple[Any, dict[str, Any]]


def _symbol(invocation: Invocation) -> str:
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


def _int_positional(invocation: Invocation, name: str) -> int | None:
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
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    if document is None or field not in document:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int) -> dict[str, Any]:
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def folder_list(invocation: Invocation) -> HandlerResult:
    """List folders in the active project."""
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"project_id": project_id}
    _forward_optional(
        document,
        kwargs,
        (
            "limit",
            "offset",
            "sort",
            "names",
            "statuses",
            "fields",
            "folder_ids",
            "created_at",
            "updated_at",
            "created_by",
        ),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def folder_get(invocation: Invocation) -> HandlerResult:
    """Get one folder by id in the active project."""
    project_id = require_project(invocation)
    folder_id = _require_int_positional(invocation, "folder id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"folder_id": folder_id, "project_id": project_id}
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def folder_root(invocation: Invocation) -> HandlerResult:
    """Get the root folder of the active project."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def folder_create(invocation: Invocation) -> HandlerResult:
    """Create a folder. Name comes from a positional or the ``name`` field."""
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    name = (invocation.extra_args[0] if invocation.extra_args else None) or document.get("name")
    if not name:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A folder name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the name as a positional argument or a 'name' input field.",
        )
    kwargs: dict[str, Any] = {"name": name, "project_id": project_id}
    _forward_optional(document, kwargs, ("parent_resource_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def folder_update(invocation: Invocation) -> HandlerResult:
    """Rename a folder. Folder id is positional; new name comes from ``--input``."""
    project_id = require_project(invocation)
    folder_id = _require_int_positional(invocation, "folder id")
    document = invocation.load_input()
    name = _require_field(document, "name")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), folder_id=folder_id, name=name, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def folder_move(invocation: Invocation) -> HandlerResult:
    """Move resources into a target folder in the active project."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    resource_ids = _require_field(document, "resource_ids")
    kwargs: dict[str, Any] = {"resource_ids": resource_ids, "project_id": project_id}
    assert document is not None
    _forward_optional(document, kwargs, ("target_folder_resource_id", "source_folder_resource_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def folder_trash(invocation: Invocation) -> HandlerResult:
    """Move one folder to the project trash (reversible)."""
    project_id = require_project(invocation)
    folder_id = _require_int_positional(invocation, "folder id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), folder_id=folder_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def folder_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one folder by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    folder_id = _require_int_positional(invocation, "folder id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete folder {folder_id}"
    )
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"folder_ids": [folder_id], "project_id": project_id}
    _forward_optional(document, kwargs, ("check_dependency", "remove_contents"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def folder_bulk_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete several folders by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    folder_ids = _require_field(document, "folder_ids")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete {len(folder_ids)} folders",
    )
    kwargs: dict[str, Any] = {"folder_ids": folder_ids, "project_id": project_id}
    assert document is not None
    _forward_optional(document, kwargs, ("check_dependency", "remove_contents"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)
