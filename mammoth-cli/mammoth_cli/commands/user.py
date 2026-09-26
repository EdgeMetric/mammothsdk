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

from mammoth_cli.errors.envelope import (
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service
from mammoth_cli.services.command_contract import bind_command_inputs

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


def _bound_document(invocation: Invocation) -> dict[str, Any]:
    """Return admitted input after the shared S7 contract binding boundary."""
    return bind_command_inputs(invocation.command_id, invocation.load_input() or {})


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
    """Copy every admitted input field into ``kwargs`` unchanged."""
    for field, value in document.items():
        if field in kwargs and field not in fields:
            continue
        kwargs[field] = value


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
    document = _bound_document(invocation)
    file = (invocation.extra_args[0] if invocation.extra_args else None) or document.get("file")
    if not file:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A file path is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the file path as a positional argument or a 'file' input field.",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), file=file)
        # Avatar upload returns a job handle for the processing job; wait so the
        # caller sees the settled result (no-op for non-job payloads).
        data = service.wait_if_job(data)
    return data, _meta(invocation, auth.workspace_id)


def user_change_password(invocation: Invocation) -> HandlerResult:
    """Change the current user's password. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    document = _bound_document(invocation)
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
    document = _bound_document(invocation)
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
    document = _bound_document(invocation)
    if not document:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="Provide at least one preference field to update.",
            exit_status=EXIT_USAGE,
            hint="Pass fields via --input.",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **document)
    return data, _meta(invocation, auth.workspace_id)


def user_update(invocation: Invocation) -> HandlerResult:
    """Change the current user's own display name (first and/or last name).

    Benign, no confirmation: this changes only the caller's own name, never
    another user's. There is no ``email`` field here -- the backend's own
    self-update route (``PATCH /self``) has no email path; an email change is
    out of scope.
    """
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("first_name", "last_name"))
    if not kwargs:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="Provide first_name and/or last_name to update.",
            exit_status=EXIT_USAGE,
            hint='Pass at least one via --input, for example: --input \'{"first_name": "Jane"}\'.',
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)
