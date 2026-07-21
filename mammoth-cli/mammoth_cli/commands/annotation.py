"""Handlers for the ``annotation`` command family (project-scoped).

Every annotation operation runs inside a resolved project: the project id
comes from ``--project`` or the active project. An existing annotation is
addressed by a positional ``annotation_id``; creating one addresses its
target via the strict ``--input`` document (``target_type``/``target_id``).
Handlers dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project

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


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Parse the first positional argument as an int, or raise usage."""
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code="missing_argument",
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


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
    """Build the common envelope metadata for an annotation command."""
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


def annotation_comment_add(invocation: Invocation) -> HandlerResult:
    """Add a comment to an annotation. Annotation id is positional; body is required input."""
    project_id = require_project(invocation)
    annotation_id = _require_int_positional(invocation, "annotation id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), annotation_id=annotation_id, body=body, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def annotation_create(invocation: Invocation) -> HandlerResult:
    """Create an annotation on a target. Target and body come from ``--input``."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    target_type = _require_field(document, "target_type")
    target_id = _require_field(document, "target_id")
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            target_type=target_type,
            target_id=target_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def annotation_delete(invocation: Invocation) -> HandlerResult:
    """Delete one annotation by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    annotation_id = _require_int_positional(invocation, "annotation id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete annotation {annotation_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), annotation_id=annotation_id, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def annotation_list(invocation: Invocation) -> HandlerResult:
    """List annotations in the active project, optionally filtered by target."""
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"project_id": project_id}
    _forward_optional(document, kwargs, ("target_type", "target_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def annotation_update(invocation: Invocation) -> HandlerResult:
    """Update an annotation's status. Annotation id is positional; status is required input."""
    project_id = require_project(invocation)
    annotation_id = _require_int_positional(invocation, "annotation id")
    document = invocation.load_input()
    status = _require_field(document, "status")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), annotation_id=annotation_id, status=status, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)
