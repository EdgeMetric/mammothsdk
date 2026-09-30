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

import json
from datetime import UTC, datetime
from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
)
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

# How the activity log keys an entry's resource: ``<type>_<id>``. A bare id names no
# type, so the backend's exact match on it finds nothing and reads as "no activity".
_RESOURCE_TYPES = (
    ("dataview", "a view"),
    ("datasource", "a dataset"),
    ("project", "a project"),
    ("dashboard", "a dashboard"),
    ("automation", "an automation"),
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


def _refuse_bare_resource_id(document: dict[str, Any]) -> None:
    """Refuse a ``resource_id`` that is a bare id: it matches no log entry.

    Raises:
        CliError: ``invalid_argument`` naming each typed form, with the retry for a
            view and for a dataset as recovery commands.
    """
    resource = str(document.get("resource_id", "")).strip()
    if not resource.isdigit():
        return
    forms = "; ".join(f"{kind}_{resource} for {label}" for kind, label in _RESOURCE_TYPES)
    retries = [
        json.dumps({**document, "resource_id": f"{kind}_{resource}"})
        for kind, _ in _RESOURCE_TYPES[:2]
    ]
    raise CliError(
        code=CODE_INVALID_ARGUMENT,
        message=(
            f"resource_id {resource} is a bare id, which no activity entry has: the log"
            f" keys each resource by its type — {forms}."
        ),
        exit_status=EXIT_USAGE,
        recovery_commands=[f"mammoth activity list --input '{retry}'" for retry in retries],
    )


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


_WORKSPACE_USERS_SYMBOL = "mammoth.api.workspace.WorkspaceAPI.list_users"
_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
_EPOCH = "1970-01-01 00:00:00"


def _close_time_window(kwargs: dict[str, Any]) -> str | None:
    """Give a lone ``start_time`` or ``end_time`` its missing bound; say so.

    The backend applies the time filter only when BOTH bounds are present
    (activity_logs/manager.py ``_get_time_filters``) and otherwise lists the
    latest entries of all time -- so "what changed today" with only a
    ``start_time`` answered from the wrong window.
    """
    start, end = kwargs.get("start_time"), kwargs.get("end_time")
    if bool(start) == bool(end):
        return None
    if start:
        kwargs["end_time"] = datetime.now(UTC).strftime(_TIME_FORMAT)
        return f"end_time was not given; the window runs to now ({kwargs['end_time']} UTC)."
    kwargs["start_time"] = _EPOCH
    return f"start_time was not given; the window starts at {_EPOCH} UTC."


def _local_time(stamp: Any) -> str | None:
    """A ``created_at`` (UTC if it has no offset) as ISO in this machine's timezone."""
    if not isinstance(stamp, str):
        return None
    try:
        moment = datetime.fromisoformat(stamp)
    except ValueError:
        return stamp
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone().isoformat(timespec="seconds")


def _user_emails(service: Any) -> dict[Any, str]:
    """Workspace users by id; empty when the caller may not list them."""
    try:
        users = service.call(_WORKSPACE_USERS_SYMBOL)
    except Exception:  # noqa: BLE001 -- a name is a convenience; the id is always shown
        return {}
    return {u["id"]: u["email"] for u in users if isinstance(u, dict) and u.get("email")}


def _change(entry: dict[str, Any], emails: dict[Any, str]) -> dict[str, Any]:
    """One log entry as a line of a change list: when, who, what, on which object."""
    details = entry.get("details") if isinstance(entry.get("details"), dict) else {}
    primary = entry.get("primary_object") if isinstance(entry.get("primary_object"), dict) else {}
    user_id = entry.get("user_id")
    change = {
        "when": _local_time(entry.get("created_at")),
        "user_id": user_id,
        "user": emails.get(user_id),
        "action": entry.get("name_key"),
        "category": entry.get("category"),
        "object": {"name": primary.get("name"), "resource_id": primary.get("resource_id")},
        "result": entry.get("result"),
    }
    if details.get("task_name"):
        change["task"] = details["task_name"]
    return change


def _with_changes(service: Any, data: Any, note: str | None) -> Any:
    """Add ``changes``: each entry with its time, user and action (no entry dropped)."""
    logs = data.get("activity_logs") if isinstance(data, dict) else None
    if not isinstance(logs, list):
        return data
    emails = _user_emails(service)
    changes = [_change(entry, emails) for entry in logs if isinstance(entry, dict)]
    extra = {"time_window_note": note} if note else {}
    return {**data, "changes": changes, **extra}


def activity_list(invocation: Invocation) -> HandlerResult:
    """List activity logs in the active workspace, with optional filters.

    ``changes`` lists each entry with its ``when`` (ISO, this machine's UTC
    offset), ``user_id`` and ``user``, ``action``, ``object`` and ``result``,
    so "who changed this view today" is answered from the list, not from its
    absence.
    """
    document = _bound_document(invocation)
    _refuse_bare_resource_id(document)
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, _LIST_OPTIONAL)
    note = _close_time_window(kwargs)
    with open_service(invocation) as (service, auth):
        data = _with_changes(service, service.call(_symbol(invocation), **kwargs), note)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def activity_export(invocation: Invocation) -> HandlerResult:
    """Export activity logs from the active workspace, with optional filters."""
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, _EXPORT_OPTIONAL)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
