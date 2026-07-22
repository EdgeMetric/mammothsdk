"""Handlers for the ``notification`` command family (workspace-scoped).

Notifications belong to the authenticated workspace; the SDK client already
carries the workspace id, so handlers never forward it explicitly, even when
the underlying SDK signature accepts one. Handlers dispatch through the
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
from mammoth_cli.runtime.session import open_service, resolved_project

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
    """Build the common envelope metadata for a notification command.

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


def notification_list(invocation: Invocation) -> HandlerResult:
    """List notifications in the active workspace, optionally filtered."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(
        document,
        kwargs,
        (
            "fields",
            "project_id",
            "last_updated_at__gte",
            "status",
            "is_read",
            "notification_scope",
            "limit",
            "offset",
            "sort",
        ),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def notification_update(invocation: Invocation) -> HandlerResult:
    """Apply a JSON Patch to one notification. Notification id is positional."""
    notification_id = _require_int_positional(invocation, "notification id")
    document = invocation.load_input()
    patch = _require_field(document, "patch")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), notification_id=notification_id, patch=patch)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def notification_update_batch(invocation: Invocation) -> HandlerResult:
    """Apply a JSON Patch across notifications in the active workspace."""
    document = invocation.load_input()
    patch = _require_field(document, "patch")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), patch=patch)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def notification_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one notification by id. Prompt or ``--yes`` required."""
    notification_id = _require_int_positional(invocation, "notification id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete notification {notification_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), notification_id=notification_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def notification_delete_batch(invocation: Invocation) -> HandlerResult:
    """Delete several notifications by id or filter. Prompt or ``--yes`` required."""
    document = invocation.load_input() or {}
    ids = document.get("ids")
    if ids:
        action = f"delete {len(ids)} notifications"
    else:
        action = "delete notifications matching the given filter"
    enforce_confirmation(invocation, policy=POLICY_PROMPT_OR_YES, action=action)
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("ids", "last_updated_at__lt", "is_read"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
