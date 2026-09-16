"""Handlers for the ``activity`` command family (workspace-scoped).

Activity logs belong to the authenticated workspace; the SDK client already
carries the workspace id, so handlers never forward it explicitly. Both
commands are read-only: ``list`` returns a page of log entries and ``export``
kicks off a workspace export job. All filters are optional and forwarded only
when present in the strict ``--input`` document. Handlers dispatch through the
generic :meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the
public SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import CODE_SDK_SYMBOL_UNRESOLVED, EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project
from mammoth_cli.services.command_contract import bind_command_inputs

HandlerResult = tuple[Any, dict[str, Any]]

_LIST_OPTIONAL = (
    "limit",
    "offset",
    "sort",
    "project_id",
    "categories",
    "activities",
    "resource_id",
    "result",
    "start_time",
    "end_time",
    "origin",
    "user_ids",
    "parent_id",
    "search_text",
)

_EXPORT_OPTIONAL = (
    "format",
    "start_time",
    "end_time",
    "categories",
    "activities",
    "user_ids",
)


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The dotted SDK symbol recorded in the command manifest.

    Raises:
        CliError: ``sdk_symbol_unresolved`` when the manifest has no symbol
            for this command.
    """
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
    document = bind_command_inputs(invocation.command_id, invocation.load_input() or {})
    # ``workspace_id`` remains a legacy-admitted filter for compatibility with
    # the public command contract, but the authenticated service already owns
    # workspace scope and the SDK method must never receive this override.
    document.pop("workspace_id", None)
    return document


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy every admitted input field into ``kwargs`` unchanged.

    Args:
        document: The parsed ``--input`` document.
        kwargs: The keyword-argument mapping being built for the SDK call.
        fields: The optional field names to forward when present.
    """
    for field, value in document.items():
        if field in kwargs and field not in fields:
            continue
        kwargs[field] = value


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for an activity command.

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


def activity_list(invocation: Invocation) -> HandlerResult:
    """List activity logs in the active workspace, with optional filters."""
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, _LIST_OPTIONAL)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def activity_export(invocation: Invocation) -> HandlerResult:
    """Export activity logs from the active workspace, with optional filters."""
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, _EXPORT_OPTIONAL)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
