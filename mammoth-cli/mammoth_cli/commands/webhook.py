"""Handlers for the ``webhook`` command family (workspace-scoped).

Webhook datasets are HTTP endpoints that receive data into the platform. The
backing SDK methods never accept a ``project_id`` or ``workspace_id`` keyword
argument — they read both from state already carried by the underlying
client — so handlers here never forward either explicitly, even though the
active project id is still reported in the envelope metadata. Handlers
dispatch through the generic
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


def _int_positional(invocation: Invocation, name: str) -> int | None:
    """Parse the first positional argument as an int, or return None if absent.

    Args:
        invocation: The current command's resolved global options.
        name: A human-readable name for the argument, used in error messages.

    Returns:
        The parsed integer, or None when no positional argument was given.

    Raises:
        CliError: ``invalid_argument`` when the positional is not an integer.
    """
    if not invocation.extra_args:
        return None
    raw = invocation.extra_args[0]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Return the first positional argument, parsed as a required int.

    Args:
        invocation: The current command's resolved global options.
        name: A human-readable name for the argument, used in error messages.

    Returns:
        The parsed integer id.

    Raises:
        CliError: ``missing_argument`` when no positional was given;
            ``invalid_argument`` when it is not an integer.
    """
    value = _int_positional(invocation, name)
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
    """Build the common envelope metadata for a webhook command.

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


def webhook_list(invocation: Invocation) -> HandlerResult:
    """List webhook datasets. ``limit``/``offset`` come from ``--input``."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("limit", "offset"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def webhook_get(invocation: Invocation) -> HandlerResult:
    """Get one webhook by id. The webhook id is a required positional."""
    webhook_id = _require_int_positional(invocation, "webhook id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), webhook_id=webhook_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def webhook_create(invocation: Invocation) -> HandlerResult:
    """Create a webhook. Name comes from a positional or the ``name`` field."""
    document = invocation.load_input() or {}
    name = (invocation.extra_args[0] if invocation.extra_args else None) or document.get("name")
    kwargs: dict[str, Any] = {}
    if name:
        kwargs["name"] = name
    _forward_optional(document, kwargs, ("mode", "folder_resource_id", "origins", "is_secure"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def webhook_update(invocation: Invocation) -> HandlerResult:
    """Update a webhook. The webhook id is positional; other fields optional."""
    webhook_id = _require_int_positional(invocation, "webhook id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"webhook_id": webhook_id}
    _forward_optional(document, kwargs, ("mode", "origins", "is_secure"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def webhook_delete(invocation: Invocation) -> HandlerResult:
    """Delete one webhook by id. Prompt or ``--yes`` required."""
    webhook_id = _require_int_positional(invocation, "webhook id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete webhook {webhook_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), webhook_id=webhook_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def webhook_send(invocation: Invocation) -> HandlerResult:
    """Send data to a webhook via POST. ``webhook_uri``/``data`` are required."""
    document = invocation.load_input()
    webhook_uri = _require_field(document, "webhook_uri")
    data_field = _require_field(document, "data")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), webhook_uri=webhook_uri, data=data_field)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def webhook_send_get(invocation: Invocation) -> HandlerResult:
    """Send data to a webhook via GET. ``webhook_uri`` is required, ``params`` optional."""
    document = invocation.load_input()
    webhook_uri = _require_field(document, "webhook_uri")
    assert document is not None
    kwargs: dict[str, Any] = {"webhook_uri": webhook_uri}
    _forward_optional(document, kwargs, ("params",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
