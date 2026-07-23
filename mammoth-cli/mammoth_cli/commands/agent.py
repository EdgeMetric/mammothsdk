"""Handlers for the ``agent`` command family (workspace-scoped).

The backing SDK methods never accept a ``project_id`` or ``workspace_id``
keyword argument — a chat scope names its own target (project, dataset, and so
on) and sessions are identified by an opaque ``session_id`` — so handlers here
never forward either explicitly, even though the active project id is still
reported in the envelope metadata. Handlers dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
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
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project

HandlerResult = tuple[Any, dict[str, Any]]


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The dotted SDK symbol recorded in the command's manifest entry.

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
        The first extra argument, or None when none was given.
    """
    return invocation.extra_args[0] if invocation.extra_args else None


def _require_string_positional(invocation: Invocation, name: str) -> str:
    """Return the first positional argument, raising when absent.

    Args:
        invocation: The current command's resolved global options.
        name: A human-readable name for the argument, used in error messages.

    Returns:
        The first extra argument.

    Raises:
        CliError: ``missing_argument`` when no positional was given.
    """
    value = _string_positional(invocation)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


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
    """Build the common envelope metadata for an agent command.

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


def agent_chat(invocation: Invocation) -> HandlerResult:
    """Send a chat message to an agent. ``message``/``scope`` are required."""
    document = invocation.load_input()
    message = _require_field(document, "message")
    scope = _require_field(document, "scope")
    assert document is not None
    kwargs: dict[str, Any] = {"message": message, "scope": scope}
    _forward_optional(document, kwargs, ("agent_key", "session_id", "client_context", "selection"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_session_delete(invocation: Invocation) -> HandlerResult:
    """Delete one agent session by id. Prompt or ``--yes`` required."""
    session_id = _require_string_positional(invocation, "session id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete agent session {session_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), session_id=session_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_session_list(invocation: Invocation) -> HandlerResult:
    """List agent sessions. All fields are optional and come from ``--input``.

    ``workspace_id`` is never forwarded even if present in the input document:
    the authenticated client already scopes every call to its own workspace.
    """
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("agent_key", "limit", "offset", "include_shared"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_session_messages(invocation: Invocation) -> HandlerResult:
    """Get the messages of one agent session by id."""
    session_id = _require_string_positional(invocation, "session id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), session_id=session_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def agent_session_set_visibility(invocation: Invocation) -> HandlerResult:
    """Set an agent session's visibility. ``visibility`` comes from ``--input``."""
    session_id = _require_string_positional(invocation, "session id")
    document = invocation.load_input()
    visibility = _require_field(document, "visibility")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), session_id=session_id, visibility=visibility)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
