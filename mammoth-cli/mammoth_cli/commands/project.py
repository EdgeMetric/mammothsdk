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
