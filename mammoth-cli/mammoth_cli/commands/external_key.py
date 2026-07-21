"""Handlers for the ``external-key`` command family (workspace-scoped).

External keys are LLM-provider API keys stored against the active workspace;
the SDK's ``ExternalKeysAPI`` takes no ``project_id`` at all, so these
handlers never resolve or forward a project. Handlers dispatch through the
generic :meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the
public SDK method named by the command's reviewed manifest ``sdk_symbol``.

Creating a key carries a secret (``secure_key``); per the reviewed manifest,
all identifying and secret fields for creation (``key_type``, ``key_name``,
``secure_key``) are read exclusively from the strict ``--input`` document,
never from a CLI positional, so a secret can never land in shell history or a
process list.
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
    """Return the first positional argument as an int, or raise ``missing_argument``."""
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
    """Copy any of ``fields`` present in ``document`` into ``kwargs``."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for an external-key command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def external_key_list(invocation: Invocation) -> HandlerResult:
    """List all external API keys in the active workspace."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def external_key_get(invocation: Invocation) -> HandlerResult:
    """Get one external API key by id."""
    key_id = _require_int_positional(invocation, "key id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), key_id=key_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def external_key_create(invocation: Invocation) -> HandlerResult:
    """Create an external (LLM provider) API key.

    ``key_type``, ``key_name``, and ``secure_key`` are required ``--input``
    fields; a positional is never accepted for this command so a secret can
    never appear in shell history. High-impact: requires ``--yes --confirm
    WORKSPACE_ID``.
    """
    document = invocation.load_input()
    key_type = _require_field(document, "key_type")
    key_name = _require_field(document, "key_name")
    secure_key = _require_field(document, "secure_key")
    kwargs: dict[str, Any] = {
        "key_type": key_type,
        "key_name": key_name,
        "secure_key": secure_key,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("description", "model_id", "model_settings"))
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"create an external key in workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def external_key_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one external API key by id. Prompt or ``--yes`` required."""
    key_id = _require_int_positional(invocation, "key id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete external key {key_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), key_id=key_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
