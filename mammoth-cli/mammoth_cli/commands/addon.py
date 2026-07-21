"""Handlers for the ``addon`` command family.

None of these commands are project-scoped: every mutation acts on the
workspace's addon set (connector addons, storage, and user seats) resolved
from the caller's credentials. ``addon list`` is a plain read. Every mutation
is ``high_impact`` and requires ``--yes --confirm WORKSPACE_ID``, enforced
against the authenticated ``auth.workspace_id`` after the service is opened
(mirroring ``project.py``'s ``project_bulk_update`` and ``workspace.py``'s
``workspace_update``). All request fields come from the strict ``--input``
document; none of these commands take a positional argument. Handlers
dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import POLICY_CONFIRM_TARGET, enforce_confirmation
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
    """Build the common envelope metadata for an addon command (no project scope)."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": None,
    }


def addon_connector_add(invocation: Invocation) -> HandlerResult:
    """Add one or more connector addons. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("connector_id", "connector_ids"))
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"add connector addon(s) to workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def addon_connector_remove(invocation: Invocation) -> HandlerResult:
    """Remove one or more connector addons. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("connector_id", "connector_ids"))
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"remove connector addon(s) from workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def addon_list(invocation: Invocation) -> HandlerResult:
    """List active addons for the workspace."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def addon_storage_add(invocation: Invocation) -> HandlerResult:
    """Add storage capacity. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    document = invocation.load_input()
    additional_storage_gb = _require_field(document, "additional_storage_gb")
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"add storage to workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(
            _symbol(invocation), additional_storage_gb=additional_storage_gb
        )
    return data, _meta(invocation, auth.workspace_id)


def addon_storage_remove(invocation: Invocation) -> HandlerResult:
    """Remove storage capacity. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    document = invocation.load_input()
    removal_storage_gb = _require_field(document, "removal_storage_gb")
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"remove storage from workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), removal_storage_gb=removal_storage_gb)
    return data, _meta(invocation, auth.workspace_id)


def addon_user_add(invocation: Invocation) -> HandlerResult:
    """Add user seats. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("user_count",))
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"add user seats to workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def addon_user_remove(invocation: Invocation) -> HandlerResult:
    """Remove user seats. High-impact: ``--yes --confirm WORKSPACE_ID``."""
    document = invocation.load_input()
    user_count = _require_field(document, "user_count")
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"remove user seats from workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), user_count=user_count)
    return data, _meta(invocation, auth.workspace_id)
