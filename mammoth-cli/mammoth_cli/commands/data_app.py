"""Handlers for the ``data-app`` command family.

Data apps are standalone resources: no reviewed manifest signature in this
family takes a ``project_id``, and ``list`` is the only command that accepts a
``workspace_id`` at all — and per the SDK client convention it is never
forwarded explicitly, since the authenticated client already carries the
workspace. The active project (if any) is still reported in the envelope
metadata for context, mirroring the read handlers in
:mod:`mammoth_cli.commands.file`. Every ``data_app_id`` comes from the first
CLI positional argument; a nested per-app identifier (a job id or a user's
email) comes from the second. Handlers dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
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


def _int_positional_at(invocation: Invocation, index: int, name: str) -> int | None:
    """Parse the positional argument at ``index`` as an int, or return None."""
    if len(invocation.extra_args) <= index:
        return None
    raw = invocation.extra_args[index]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code="invalid_argument",
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional_at(invocation: Invocation, index: int, name: str) -> int:
    """Return the required positional argument at ``index`` as an int, or raise."""
    value = _int_positional_at(invocation, index, name)
    if value is None:
        raise CliError(
            code="missing_argument",
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Return the required first positional argument as an int, or raise."""
    return _require_int_positional_at(invocation, 0, name)


def _require_string_positional_at(invocation: Invocation, index: int, name: str) -> str:
    """Return the required positional argument at ``index``, or raise usage."""
    if len(invocation.extra_args) <= index:
        raise CliError(
            code="missing_argument",
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return invocation.extra_args[index]


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


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy each of ``fields`` present in ``document`` into ``kwargs``, unchanged."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for a data-app command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def data_app_list(invocation: Invocation) -> HandlerResult:
    """List data apps. The workspace is always the authenticated client's own."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def data_app_get(invocation: Invocation) -> HandlerResult:
    """Get one data app by id."""
    data_app_id = _require_int_positional(invocation, "data app id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), data_app_id=data_app_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def data_app_create(invocation: Invocation) -> HandlerResult:
    """Create a data app. The creation payload is the required ``body`` field."""
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), body=body)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def data_app_update(invocation: Invocation) -> HandlerResult:
    """Update a data app's settings. Data app id is positional; body is required input."""
    data_app_id = _require_int_positional(invocation, "data app id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), data_app_id=data_app_id, body=body)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def data_app_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one data app by id. Prompt or ``--yes`` required."""
    data_app_id = _require_int_positional(invocation, "data app id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete data app {data_app_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), data_app_id=data_app_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def data_app_active_job(invocation: Invocation) -> HandlerResult:
    """Get the currently active job for a data app, if any."""
    data_app_id = _require_int_positional(invocation, "data app id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), data_app_id=data_app_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def data_app_job(invocation: Invocation) -> HandlerResult:
    """Get one job for a data app. Data app id and job id are both positional."""
    data_app_id = _require_int_positional_at(invocation, 0, "data app id")
    job_id = _require_int_positional_at(invocation, 1, "job id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), data_app_id=data_app_id, job_id=job_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def data_app_pipeline_changes(invocation: Invocation) -> HandlerResult:
    """Get pending pipeline changes for a data app's source dataview."""
    data_app_id = _require_int_positional(invocation, "data app id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), data_app_id=data_app_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def data_app_share(invocation: Invocation) -> HandlerResult:
    """Share a data app with a user. Data app id is positional; body is required input."""
    data_app_id = _require_int_positional(invocation, "data app id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), data_app_id=data_app_id, body=body)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def data_app_upload(invocation: Invocation) -> HandlerResult:
    """Upload a file to a data app. Data app id is positional; file is required input."""
    data_app_id = _require_int_positional(invocation, "data app id")
    document = invocation.load_input()
    file = _require_field(document, "file")
    kwargs: dict[str, Any] = {"data_app_id": data_app_id, "file": file}
    assert document is not None
    _forward_optional(document, kwargs, ("append_to_ds_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def data_app_user_list(invocation: Invocation) -> HandlerResult:
    """List users a data app is shared with."""
    data_app_id = _require_int_positional(invocation, "data app id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), data_app_id=data_app_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def data_app_user_remove(invocation: Invocation) -> HandlerResult:
    """Remove a shared user from a data app. Prompt or ``--yes`` required.

    The data app id is the first positional argument; the user's email is the
    second.
    """
    data_app_id = _require_int_positional_at(invocation, 0, "data app id")
    email = _require_string_positional_at(invocation, 1, "email")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"remove user {email} from data app {data_app_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), data_app_id=data_app_id, email=email)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
