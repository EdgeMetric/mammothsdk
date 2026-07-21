"""Read-only handlers for the ``project`` command family.

Each handler receives the typed
:class:`~mammoth_cli.runtime.invocation.Invocation`, opens an authenticated
:class:`~mammoth_cli.services.protocol.MammothService`, and dispatches to the
public SDK method named by the command's reviewed manifest ``sdk_symbol``. No
handler constructs a client or reads process state directly; project ids come
from a positional argument or the resolved active project, and multi-field
input comes from the strict ``--input`` document.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError, missing_project_error
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project

HandlerResult = tuple[Any, dict[str, Any]]


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


def _string_positional(invocation: Invocation) -> str | None:
    """Return the first positional argument, or None if absent."""
    return invocation.extra_args[0] if invocation.extra_args else None


def _int_positional(invocation: Invocation, name: str) -> int | None:
    """Parse the first positional argument as an int, or return None if absent."""
    if not invocation.extra_args:
        return None
    raw = invocation.extra_args[0]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code="invalid_argument",
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _project_id(invocation: Invocation) -> int:
    """Resolve the target project id from a positional or the active project."""
    explicit = _int_positional(invocation, "project id")
    if explicit is not None:
        return explicit
    resolved = resolved_project(invocation)
    if resolved is None:
        raise missing_project_error()
    return resolved


def _require_input_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code="missing_field",
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _meta(invocation: Invocation, auth_workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for a project command."""
    return {
        "profile": invocation.profile,
        "workspace_id": auth_workspace_id,
        "project_id": project_id,
    }


def project_list(invocation: Invocation) -> HandlerResult:
    """List projects in the active workspace."""
    document = invocation.load_input() or {}
    limit = int(document.get("limit", 100))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), limit=limit)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def project_get(invocation: Invocation) -> HandlerResult:
    """Get one project by id (positional or active project)."""
    project_id = _project_id(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_pending_changes(invocation: Invocation) -> HandlerResult:
    """Report a project's pending pipeline changes."""
    project_id = _project_id(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_resource_status(invocation: Invocation) -> HandlerResult:
    """Report the status of a project's resources."""
    project_id = _project_id(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_resource_dependencies(invocation: Invocation) -> HandlerResult:
    """Report dependencies for the given resource ids in a project."""
    project_id = _project_id(invocation)
    document = invocation.load_input()
    resource_ids = _require_input_field(document, "resource_ids")
    kwargs: dict[str, Any] = {"project_id": project_id, "resource_ids": resource_ids}
    if document is not None and "is_recursive" in document:
        kwargs["is_recursive"] = document["is_recursive"]
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_publish_credentials(invocation: Invocation) -> HandlerResult:
    """Report publish credentials for a project's ODBC endpoint."""
    project_id = _project_id(invocation)
    document = invocation.load_input()
    odbc_type = _require_input_field(document, "odbc_type")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id, odbc_type=odbc_type)
    return data, _meta(invocation, auth.workspace_id, project_id)


_CREATE_OPTIONAL = ("color", "project_access")
_UPDATE_OPTIONAL = ("name", "color")


def project_create(invocation: Invocation) -> HandlerResult:
    """Create a project. Name comes from a positional or the ``name`` field."""
    document = invocation.load_input() or {}
    name = _string_positional(invocation) or document.get("name")
    if not name:
        raise CliError(
            code="missing_argument",
            message="A project name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the name as a positional argument or a 'name' input field.",
        )
    kwargs: dict[str, Any] = {"name": name}
    for field in _CREATE_OPTIONAL:
        if field in document:
            kwargs[field] = document[field]
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def project_update(invocation: Invocation) -> HandlerResult:
    """Update a project's name or color from the ``--input`` document."""
    project_id = _project_id(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"project_id": project_id}
    for field in _UPDATE_OPTIONAL:
        if field in document:
            kwargs[field] = document[field]
    if len(kwargs) == 1:
        raise CliError(
            code="missing_field",
            message="Provide at least one of 'name' or 'color' to update.",
            exit_status=EXIT_USAGE,
            hint="Pass fields via --input.",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_delete(invocation: Invocation) -> HandlerResult:
    """Delete one project (positional or active). Prompt or ``--yes`` required."""
    project_id = _project_id(invocation)
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete project {project_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_bulk_delete(invocation: Invocation) -> HandlerResult:
    """Delete several projects by id. Prompt or ``--yes`` required."""
    document = invocation.load_input()
    project_ids = _require_input_field(document, "project_ids")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete {len(project_ids)} projects",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_ids=project_ids)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def project_bulk_update(invocation: Invocation) -> HandlerResult:
    """Apply a bulk patch across projects. High-impact: ``--yes --confirm WS``."""
    document = invocation.load_input()
    patch_data = _require_input_field(document, "patch_data")
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"bulk-update projects in workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), patch_data=patch_data)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def project_sample_flow(invocation: Invocation) -> HandlerResult:
    """Create a sample flow in a project (positional or active)."""
    project_id = _project_id(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"project_id": project_id}
    if "label_resource_id" in document:
        kwargs["label_resource_id"] = document["label_resource_id"]
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)
