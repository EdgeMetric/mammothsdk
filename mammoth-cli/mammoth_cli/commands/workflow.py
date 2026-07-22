"""Handlers for the ``workflow`` command family (project-scoped).

Every workflow operation runs inside a resolved project: the project id comes
from ``--project`` or the active project, and workflow/block ids come from a
positional argument or the strict ``--input`` document. Block-scoped commands
take the workflow id as the first positional and the block id as the second,
mirroring ``batch.py``'s dataset/batch pair. Handlers dispatch through the
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

_CREATE_OPTIONAL = ("shape", "purpose", "seed_datasource_id")
_UPDATE_OPTIONAL = ("name", "purpose", "pipeline_summary", "notes")
_BLOCK_ADD_OPTIONAL = ("display_name", "connection_type", "position_hint")


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


def _string_positional(invocation: Invocation) -> str | None:
    """Return the first positional argument, or None if absent."""
    return invocation.extra_args[0] if invocation.extra_args else None


def _int_positional_at(invocation: Invocation, index: int, name: str) -> int | None:
    """Parse the positional argument at ``index`` as an int, or return None."""
    if len(invocation.extra_args) <= index:
        return None
    raw = invocation.extra_args[index]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional_at(invocation: Invocation, index: int, name: str) -> int:
    """Return the required positional argument at ``index`` as an int, or raise."""
    value = _int_positional_at(invocation, index, name)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy each of ``fields`` from ``document`` into ``kwargs`` when present."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a workflow command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def workflow_list(invocation: Invocation) -> HandlerResult:
    """List workflows in the active project."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_get(invocation: Invocation) -> HandlerResult:
    """Get one workflow by id in the active project."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), workflow_id=workflow_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_graph(invocation: Invocation) -> HandlerResult:
    """Get the active project's workflow graph."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_cleanup(invocation: Invocation) -> HandlerResult:
    """Clean up ghost (orphaned skeleton) workflows in the active project."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_workspace_datasets(invocation: Invocation) -> HandlerResult:
    """List workspace datasets available to workflows in the active project."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_workspace_exports(invocation: Invocation) -> HandlerResult:
    """List workspace exports available to workflows in the active project."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_workspace_sources(invocation: Invocation) -> HandlerResult:
    """List workspace sources available to workflows in the active project."""
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_create(invocation: Invocation) -> HandlerResult:
    """Create a workflow. Name comes from a positional or the ``name`` field."""
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    name = _string_positional(invocation) or document.get("name")
    if not name:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A workflow name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the name as a positional argument or a 'name' input field.",
        )
    kwargs: dict[str, Any] = {"name": name, "project_id": project_id}
    _forward_optional(document, kwargs, _CREATE_OPTIONAL)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_update(invocation: Invocation) -> HandlerResult:
    """Update a workflow's metadata. Workflow id is positional."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"workflow_id": workflow_id, "project_id": project_id}
    _forward_optional(document, kwargs, _UPDATE_OPTIONAL)
    if len(kwargs) == 2:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=(
                "Provide at least one of 'name', 'purpose', 'pipeline_summary', "
                "or 'notes' to update."
            ),
            exit_status=EXIT_USAGE,
            hint="Pass fields via --input.",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_delete(invocation: Invocation) -> HandlerResult:
    """Delete one workflow by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete workflow {workflow_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), workflow_id=workflow_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_from_template(invocation: Invocation) -> HandlerResult:
    """Instantiate a workflow from a workspace template.

    ``template_id`` is positional; the new workflow name is an input field.
    """
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    workflow_name = document.get("workflow_name")
    if not workflow_name:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A workflow name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass 'workflow_name' via --input.",
        )
    template_id = invocation.positional("template_id")
    if template_id is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT, message="A template id is required.", exit_status=EXIT_USAGE
        )
    template_id = int(template_id)
    kwargs: dict[str, Any] = {
        "template_id": template_id,
        "workflow_name": workflow_name,
        "project_id": project_id,
    }
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_canvas(invocation: Invocation) -> HandlerResult:
    """Update a workflow's canvas state. Workflow id is positional."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    document = invocation.load_input()
    canvas_state = _require_field(document, "canvas_state")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            workflow_id=workflow_id,
            canvas_state=canvas_state,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_block_add(invocation: Invocation) -> HandlerResult:
    """Add a skeleton block to a workflow. Workflow id is positional."""
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    document = invocation.load_input()
    block_type = _require_field(document, "block_type")
    kwargs: dict[str, Any] = {
        "workflow_id": workflow_id,
        "block_type": block_type,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, _BLOCK_ADD_OPTIONAL)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_block_auth(invocation: Invocation) -> HandlerResult:
    """Patch a workflow block's auth credentials.

    The workflow id is the first positional and the block id is the second.
    """
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    block_id = _require_int_positional_at(invocation, 1, "block id")
    document = invocation.load_input()
    auth_data = _require_field(document, "auth_data")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            workflow_id=workflow_id,
            block_id=block_id,
            auth_data=auth_data,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_block_config(invocation: Invocation) -> HandlerResult:
    """Promote a configured skeleton block to a real resource.

    The workflow id is the first positional and the block id is the second.
    """
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    block_id = _require_int_positional_at(invocation, 1, "block id")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), workflow_id=workflow_id, block_id=block_id, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def workflow_block_type(invocation: Invocation) -> HandlerResult:
    """Patch a workflow block's connector/handler type.

    The workflow id is the first positional and the block id is the second.
    """
    project_id = require_project(invocation)
    workflow_id = _require_int_positional_at(invocation, 0, "workflow id")
    block_id = _require_int_positional_at(invocation, 1, "block id")
    document = invocation.load_input()
    connection_type = _require_field(document, "connection_type")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            workflow_id=workflow_id,
            block_id=block_id,
            connection_type=connection_type,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)
