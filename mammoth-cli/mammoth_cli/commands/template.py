"""Handlers for the ``template`` command family.

None of these commands are project-scoped: every handler resolves an
authenticated service and dispatches to the public SDK method named by the
command's reviewed manifest ``sdk_symbol``, using the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam. A template id
comes from the first CLI positional argument; a create/update payload comes
from the strict ``--input`` document's ``body`` field.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service

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
    """Parse the first positional argument as an int, or raise a usage error."""
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


def _meta(invocation: Invocation, workspace_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a template command (no project scope)."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": None,
    }


def template_create(invocation: Invocation) -> HandlerResult:
    """Create a template. Payload comes from the ``body`` input field."""
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), body=body)
    return data, _meta(invocation, auth.workspace_id)


def template_delete(invocation: Invocation) -> HandlerResult:
    """Delete a template by id. Prompt or ``--yes`` required."""
    template_id = _require_int_positional(invocation, "template id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete template {template_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), template_id=template_id)
    return data, _meta(invocation, auth.workspace_id)


def template_get(invocation: Invocation) -> HandlerResult:
    """Get one template by id."""
    template_id = _require_int_positional(invocation, "template id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), template_id=template_id)
    return data, _meta(invocation, auth.workspace_id)


def template_list(invocation: Invocation) -> HandlerResult:
    """List templates."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def template_update(invocation: Invocation) -> HandlerResult:
    """Update a template. Template id is positional; payload is the ``body`` field."""
    template_id = _require_int_positional(invocation, "template id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), template_id=template_id, body=body)
    return data, _meta(invocation, auth.workspace_id)
