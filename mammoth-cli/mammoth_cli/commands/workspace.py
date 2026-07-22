"""Handlers for the ``workspace`` command family.

None of these commands are project-scoped: every handler resolves an
authenticated service and dispatches to the public SDK method named by the
command's reviewed manifest ``sdk_symbol``, using the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam. A handful of
commands target a single, specific workspace (``get``, ``delete``,
``reactivate``, ``update``); for those, the workspace id comes from the first
CLI positional when given, and is otherwise left unset so the SDK falls back
to the client's own workspace. All other required fields (tokens, bodies,
patch lists, email lists) come from the strict ``--input`` document.
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


def _string_positional(invocation: Invocation) -> str | None:
    """Return the first positional argument, or None if absent."""
    return invocation.extra_args[0] if invocation.extra_args else None


def _require_string_positional(invocation: Invocation, name: str) -> str:
    """Return the first positional argument, or raise a usage error."""
    value = _string_positional(invocation)
    if not value:
        raise CliError(
            code="missing_argument",
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


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


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy each present field from ``document`` into ``kwargs`` under the same name."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a workspace command (no project scope)."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": None,
    }


def workspace_accept_invite(invocation: Invocation) -> HandlerResult:
    """Accept a pending workspace invite using a token from ``--input``."""
    document = invocation.load_input()
    token = _require_field(document, "token")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), token=token)
    return data, _meta(invocation, auth.workspace_id)


def workspace_app_usage(invocation: Invocation) -> HandlerResult:
    """Report app usage stats for the current workspace."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def workspace_check_expression(invocation: Invocation) -> HandlerResult:
    """Ask the AI assistant to check an expression. Payload comes from ``--input``."""
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), body=body)
    return data, _meta(invocation, auth.workspace_id)


def workspace_create(invocation: Invocation) -> HandlerResult:
    """Create a new workspace. Payload comes from the ``body`` input field."""
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), body=body)
    return data, _meta(invocation, auth.workspace_id)


def workspace_delete(invocation: Invocation) -> HandlerResult:
    """Delete a workspace. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    explicit = _int_positional(invocation, "workspace id")
    with open_service(invocation) as (service, auth):
        target_id = explicit if explicit is not None else auth.workspace_id
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"delete workspace {target_id}",
            target=str(target_id),
        )
        kwargs: dict[str, Any] = {}
        if explicit is not None:
            kwargs["workspace_id"] = explicit
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def workspace_get(invocation: Invocation) -> HandlerResult:
    """Get one workspace by id (positional), or the client's own workspace."""
    explicit = _int_positional(invocation, "workspace id")
    kwargs: dict[str, Any] = {}
    if explicit is not None:
        kwargs["workspace_id"] = explicit
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def workspace_list(invocation: Invocation) -> HandlerResult:
    """List accessible workspaces."""
    document = invocation.load_input() or {}
    limit = int(document.get("limit", 100))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), limit=limit)
    return data, _meta(invocation, auth.workspace_id)


def workspace_llm_task(invocation: Invocation) -> HandlerResult:
    """Submit a unified LLM task. ``task_type`` and ``params`` come from ``--input``."""
    document = invocation.load_input()
    task_type = _require_field(document, "task_type")
    params = _require_field(document, "params")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), task_type=task_type, params=params)
    return data, _meta(invocation, auth.workspace_id)


def workspace_reactivate(invocation: Invocation) -> HandlerResult:
    """Reactivate a deactivated workspace. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    explicit = _int_positional(invocation, "workspace id")
    with open_service(invocation) as (service, auth):
        target_id = explicit if explicit is not None else auth.workspace_id
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"reactivate workspace {target_id}",
            target=str(target_id),
        )
        kwargs: dict[str, Any] = {}
        if explicit is not None:
            kwargs["workspace_id"] = explicit
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def workspace_segment_list(invocation: Invocation) -> HandlerResult:
    """List split-test segments for the workspace."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def workspace_segment_update(invocation: Invocation) -> HandlerResult:
    """Update split-test segments. ``patch`` comes from ``--input``."""
    document = invocation.load_input()
    patch = _require_field(document, "patch")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), patch=patch)
    return data, _meta(invocation, auth.workspace_id)


def workspace_storage_breakdown(invocation: Invocation) -> HandlerResult:
    """Report a breakdown of storage usage for the workspace."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("limit", "offset"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def workspace_update(invocation: Invocation) -> HandlerResult:
    """Patch workspace settings. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    explicit = _int_positional(invocation, "workspace id")
    document = invocation.load_input()
    patches = _require_field(document, "patches")
    with open_service(invocation) as (service, auth):
        target_id = explicit if explicit is not None else auth.workspace_id
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"update workspace {target_id}",
            target=str(target_id),
        )
        kwargs: dict[str, Any] = {"patches": patches}
        if explicit is not None:
            kwargs["workspace_id"] = explicit
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def workspace_user_add(invocation: Invocation) -> HandlerResult:
    """Invite one or more users to the workspace."""
    document = invocation.load_input()
    email_ids = _require_field(document, "email_ids")
    kwargs: dict[str, Any] = {"email_ids": email_ids}
    assert document is not None
    _forward_optional(document, kwargs, ("projects",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def workspace_user_get(invocation: Invocation) -> HandlerResult:
    """Get one workspace user by id (positional), in the client's own workspace."""
    user_id = _require_string_positional(invocation, "user id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), user_id=user_id)
    return data, _meta(invocation, auth.workspace_id)


def workspace_user_list(invocation: Invocation) -> HandlerResult:
    """List users in the client's own workspace."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def workspace_user_remove(invocation: Invocation) -> HandlerResult:
    """Remove a single user from the workspace. Prompt or ``--yes`` required."""
    user_id = _require_int_positional(invocation, "user id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"remove user {user_id} from the workspace",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), user_id=user_id)
    return data, _meta(invocation, auth.workspace_id)


def workspace_user_remove_batch(invocation: Invocation) -> HandlerResult:
    """Remove several users and/or pending invites. Prompt or ``--yes`` required."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("ids", "invite_ids"))
    if not kwargs:
        raise CliError(
            code="missing_field",
            message="Provide at least one of 'ids' or 'invite_ids' to remove.",
            exit_status=EXIT_USAGE,
            hint="Pass fields via --input.",
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action="remove users or invites from the workspace",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def workspace_user_update(invocation: Invocation) -> HandlerResult:
    """Update a user's role. High-impact: ``--yes --confirm USER_ID``."""
    user_id = _require_string_positional(invocation, "user id")
    document = invocation.load_input()
    patches = _require_field(document, "patches")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"update user {user_id}",
        target=user_id,
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), user_id=user_id, patches=patches)
    return data, _meta(invocation, auth.workspace_id)


def workspace_user_update_batch(invocation: Invocation) -> HandlerResult:
    """Update workspace users via JSON-patch operations. ``patches`` from ``--input``."""
    document = invocation.load_input()
    patches = _require_field(document, "patches")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), patches=patches)
    return data, _meta(invocation, auth.workspace_id)
