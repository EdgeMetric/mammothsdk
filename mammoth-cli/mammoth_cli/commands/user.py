"""Handlers for the ``user`` command family (current-user profile scope).

Every command here targets the *current* authenticated user or the workspace
they act in — never a project. Avatar and account-deletion commands take no
resource id, so their high-impact and destructive confirmations target the
client's own ``auth.workspace_id`` (mirroring ``workspace_delete`` in
``workspace.py``). All other required fields (passwords, preference and
profile updates) come from the strict ``--input`` document. Handlers dispatch
through the generic :meth:`~mammoth_cli.services.protocol.MammothService.call`
seam to the public SDK method named by the command's reviewed manifest
``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
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
    """Copy each present field from ``document`` into ``kwargs`` under the same name."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a user command (no project scope)."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": None,
    }


def user_avatar_delete(invocation: Invocation) -> HandlerResult:
    """Delete the current user's avatar. Prompt or ``--yes`` required."""
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action="delete the current user's avatar",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def user_avatar_upload(invocation: Invocation) -> HandlerResult:
    """Upload the current user's avatar. File comes from a positional or ``file``."""
    document = invocation.load_input() or {}
    file = (invocation.extra_args[0] if invocation.extra_args else None) or document.get("file")
    if not file:
        raise CliError(
            code="missing_argument",
            message="A file path is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the file path as a positional argument or a 'file' input field.",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), file=file)
    return data, _meta(invocation, auth.workspace_id)


def user_change_password(invocation: Invocation) -> HandlerResult:
    """Change the current user's password. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    document = invocation.load_input()
    current_password = _require_field(document, "current_password")
    new_password = _require_field(document, "new_password")
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action="change the current user's password",
            target=str(auth.workspace_id),
        )
        data = service.call(
            _symbol(invocation),
            current_password=current_password,
            new_password=new_password,
        )
    return data, _meta(invocation, auth.workspace_id)


def user_delete_account(invocation: Invocation) -> HandlerResult:
    """Delete the current user's account. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("validate_only",))
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action="delete the current user's account",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def user_get(invocation: Invocation) -> HandlerResult:
    """Get the current user's profile."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def user_preference_get(invocation: Invocation) -> HandlerResult:
    """Get the current user's preferences."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def user_preference_update(invocation: Invocation) -> HandlerResult:
    """Update the current user's preferences from the ``--input`` document."""
    document = invocation.load_input() or {}
    if not document:
        raise CliError(
            code="missing_field",
            message="Provide at least one preference field to update.",
            exit_status=EXIT_USAGE,
            hint="Pass fields via --input.",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **document)
    return data, _meta(invocation, auth.workspace_id)


def user_update(invocation: Invocation) -> HandlerResult:
    """Update the current user's profile. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    document = invocation.load_input() or {}
    if not document:
        raise CliError(
            code="missing_field",
            message="Provide at least one field to update.",
            exit_status=EXIT_USAGE,
            hint="Pass fields via --input.",
        )
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action="update the current user's profile",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **document)
    return data, _meta(invocation, auth.workspace_id)
