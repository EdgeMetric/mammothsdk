"""Handlers for the ``automation`` command family (workspace-scoped).

Automations belong to the authenticated workspace; the SDK client already
carries the workspace (and active project) context, so handlers never
construct or forward those ids explicitly. An automation id always comes from
the first CLI positional argument; structured fields (``tasks``,
``conditions``, ``patch``, etc.) come from the strict ``--input`` document.
Handlers dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
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
from mammoth_cli.runtime.confirm import (
    POLICY_PROMPT_OR_YES,
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project

HandlerResult = tuple[Any, dict[str, Any]]


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The dotted SDK symbol recorded in the reviewed manifest.

    Raises:
        CliError: ``sdk_symbol_unresolved`` when no symbol is recorded.
    """
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


def _string_positional(invocation: Invocation) -> str | None:
    """Return the first positional argument, or None if absent.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The first positional argument, or None when there is none.
    """
    return invocation.extra_args[0] if invocation.extra_args else None


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Return the first positional argument parsed as a required int.

    Args:
        invocation: The current command's resolved global options.
        name: A human-readable name for the argument, used in error messages.

    Returns:
        The parsed integer id.

    Raises:
        CliError: ``missing_argument`` when no positional was given;
            ``invalid_argument`` when it is not an integer.
    """
    if not invocation.extra_args:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    raw = invocation.extra_args[0]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage.

    Args:
        document: The parsed ``--input`` document, or None when absent.
        field: The required field name.

    Returns:
        The field's value.

    Raises:
        CliError: ``missing_field`` when the document is absent or lacks
            ``field``.
    """
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
    """Copy each present field from ``document`` into ``kwargs``, unchanged.

    Args:
        document: The parsed ``--input`` document.
        kwargs: The keyword-argument mapping being built for the SDK call.
        fields: The optional field names to forward when present.
    """
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for an automation command.

    Args:
        invocation: The current command's resolved global options.
        workspace_id: The authenticated workspace id.
        project_id: The active project id, or None when not resolved.

    Returns:
        The envelope metadata mapping.
    """
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def automation_list(invocation: Invocation) -> HandlerResult:
    """List all automations in the active workspace/project."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def automation_get(invocation: Invocation) -> HandlerResult:
    """Get one automation by id. Automation id is positional."""
    automation_id = _require_int_positional(invocation, "automation id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), automation_id=automation_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def automation_trash(invocation: Invocation) -> HandlerResult:
    """Move one automation to trash (reversible). Automation id is positional."""
    automation_id = _require_int_positional(invocation, "automation id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), automation_id=automation_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def automation_restore(invocation: Invocation) -> HandlerResult:
    """Restore one trashed automation. Automation id is positional."""
    automation_id = _require_int_positional(invocation, "automation id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), automation_id=automation_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def automation_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one automation by id. Prompt or ``--yes`` required."""
    automation_id = _require_int_positional(invocation, "automation id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete automation {automation_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), automation_id=automation_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def automation_create(invocation: Invocation) -> HandlerResult:
    """Create an automation. Name comes from a positional or the ``name`` field.

    ``tasks`` is the only required ``--input`` field; ``description`` defaults to
    an empty string, and ``conditions``/``condition_mode`` are forwarded when
    present. Requires ``--yes``.
    """
    document = invocation.load_input() or {}
    name = _string_positional(invocation) or document.get("name")
    if not name:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="An automation name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the name as a positional argument or a 'name' input field.",
        )
    description = document.get("description", "")
    tasks = _require_field(document, "tasks")
    kwargs: dict[str, Any] = {"name": name, "description": description, "tasks": tasks}
    _forward_optional(document, kwargs, ("conditions", "condition_mode"))
    enforce_confirmation(invocation, policy=POLICY_YES_ALWAYS, action="create an automation")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def automation_update(invocation: Invocation) -> HandlerResult:
    """Apply JSON-patch operations to one automation. Requires ``--yes``.

    Automation id is positional; the non-empty ``patch`` list comes from the
    ``--input`` document.
    """
    automation_id = _require_int_positional(invocation, "automation id")
    document = invocation.load_input()
    patch = _require_field(document, "patch")
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"update automation {automation_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), automation_id=automation_id, patch=patch)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
