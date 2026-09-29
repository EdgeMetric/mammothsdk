"""Name what a ``--dry-run`` command would change, from the reads that already exist.

The report's ``targets`` list is what an approval card is rendered from, so a
target without a real display name is never returned: every id is read through
its resource's own ``get`` command (the SDK symbol comes from the manifest) and
the name is taken from that response's *real* shape -- several routes wrap the
record (``{"dataset": {...}}``), others return it flat, and two SDK methods
return a typed model instead of a mapping.

Which command changes which resource is :data:`COMMAND_TARGETS`. A ``destructive``
command that is not in it has no verified read that names its targets, so its
dry run fails loud (:func:`unresolvable_error`) instead of reporting ``[]``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_RESOURCE_NOT_FOUND,
    EXIT_NOT_FOUND,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.services.protocol import MammothService

CODE_TARGETS_UNRESOLVABLE = "dry_run_targets_unresolvable"
DATAVIEW_GET = "mammoth.api.dataviews.DataviewsAPI.get"


@dataclass(frozen=True)
class Reader:
    """How to read one resource's display name.

    Attributes:
        get_command: Manifest id of the resource's ``get`` command, whose
            ``sdk_symbol`` is called; ``None`` when ``symbol`` is given.
        id_arg: The SDK keyword that takes the resource id.
        scope_args: SDK keywords copied from the reported call's arguments
            (the parent dataset, the project).
        wrap: The key the response nests the record under, if any.
        name_key: The field holding the display name.
        symbol: An explicit SDK symbol, for a resource whose manifest ``get``
            resolves its parent by discovery.
        name_join: Fields joined with a space when the record has no single
            name field (a user has ``first_name`` and ``last_name``).
        id_as_str: Whether the SDK takes the id as a string.
    """

    get_command: str | None
    id_arg: str
    scope_args: tuple[str, ...] = ()
    wrap: str | None = None
    name_key: str = "name"
    symbol: str | None = None
    name_join: tuple[str, ...] = ()
    id_as_str: bool = False


#: Resource kind -> reader. Shapes checked against the apiv2 response models:
#: ``DatasetDetails``/``BatchDetails``/``FileDetails``/``FolderDetails``/
#: ``WebhookDetails``/``AutomationDetails`` wrap; ``DataviewInfo``,
#: ``ParameterDetailResponse``, ``SnippetDetailResponse``, ``WorkflowResponse``,
#: ``DataAppDetails``, ``ScheduleSchemaFields`` and the dashboard meta types
#: are flat (a dashboard's name is ``title``, a schedule's ``task_name``, an
#: external key's ``key_name`` inside ``external_key``).
READERS: dict[str, Reader] = {
    "dataset": Reader("dataset.get", "dataset_id", ("project_id",), wrap="dataset"),
    "view": Reader(None, "dataview_id", ("dataset_id", "project_id"), symbol=DATAVIEW_GET),
    "batch": Reader("batch.get", "batch_id", ("dataset_id", "project_id"), wrap="batch"),
    "file": Reader("file.get", "file_id"),
    "folder": Reader("folder.get", "folder_id", ("project_id",)),
    "webhook": Reader("webhook.get", "webhook_id", wrap="webhook"),
    "parameter": Reader("parameter.get", "parameter_id"),
    "snippet": Reader("snippet.get", "snippet_id"),
    "automation": Reader("automation.get", "automation_id", wrap="automation"),
    "external-key": Reader("external-key.get", "key_id", wrap="external_key", name_key="key_name"),
    "schedule": Reader("schedule.get", "schedule_id", ("project_id",), name_key="task_name"),
    "workflow": Reader("workflow.get", "workflow_id", ("project_id",)),
    "data-app": Reader("data-app.get", "data_app_id"),
    "dashboard": Reader("dashboard.get", "dashboard_id", name_key="title"),
    "project": Reader("project.get", "project"),
    # ``WorkspaceAPI.get_user`` reads the member list (``__full``) and returns the
    # entry: flat, with ``first_name``/``last_name``/``email`` and no ``name``.
    "user": Reader(
        "workspace.user.get", "user_id", name_join=("first_name", "last_name"), id_as_str=True
    ),
}

#: Command -> (resource kind, the reported-call argument holding its id or ids).
#: Every ``destructive`` command whose targets a verified read can name, plus
#: ``project.delete``. The rest of the destructive set is listed in the
#: module docstring's failure mode, not here.
COMMAND_TARGETS: dict[str, tuple[str, str]] = {
    "dataset.delete": ("dataset", "dataset_id"),
    "dataset.bulk-delete": ("dataset", "dataset_ids"),
    "dataset.file-settings.undo": ("dataset", "dataset_id"),
    "view.delete": ("view", "view_id"),
    "view.bulk-delete": ("view", "dataview_ids"),
    "batch.delete": ("batch", "batch_id"),
    "batch.bulk-delete": ("batch", "ids"),
    "file.delete": ("file", "file_id"),
    "file.bulk-delete": ("file", "file_ids"),
    "folder.delete": ("folder", "folder_ids"),
    "folder.bulk-delete": ("folder", "folder_ids"),
    "webhook.delete": ("webhook", "webhook_id"),
    "parameter.delete": ("parameter", "parameter_id"),
    "snippet.delete": ("snippet", "snippet_id"),
    "automation.delete": ("automation", "automation_id"),
    "external-key.delete": ("external-key", "key_id"),
    "schedule.delete": ("schedule", "schedule_id"),
    "workflow.delete": ("workflow", "workflow_id"),
    "data-app.delete": ("data-app", "data_app_id"),
    "dashboard.delete": ("dashboard", "dashboard_id"),
    "project.delete": ("project", "project_id"),
    "project.bulk-delete": ("project", "project_ids"),
    "workspace.user.remove": ("user", "user_id"),
    "workspace.user.remove-batch": ("user", "ids"),
}


def unresolvable_error(command_id: str, reason: str) -> CliError:
    """The fail-loud error for a command whose targets cannot be named."""
    return CliError(
        code=CODE_TARGETS_UNRESOLVABLE,
        message=f"Cannot name what '{command_id}' would change: {reason}.",
        exit_status=EXIT_USAGE,
        hint=(
            "Run the resource's own get/list command to confirm the target, then "
            "run the real command with --yes; nothing was changed."
        ),
        details={"command_id": command_id},
    )


def _ids(value: Any) -> list[int]:
    """Return ``value`` as a list of ids (an int, a list or comma string, or nothing)."""
    if isinstance(value, bool):
        return []
    if isinstance(value, int):
        return [value]
    if isinstance(value, str):
        return [int(part) for part in value.split(",") if part.strip().isdigit()]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, int) and not isinstance(item, bool)]
    return []


def _name_of(record: Any, reader: Reader) -> object:
    """Read the display name from a response in the shape its route returns."""
    if reader.name_join and isinstance(record, Mapping):
        parts = [str(record.get(key) or "").strip() for key in reader.name_join]
        return " ".join(part for part in parts if part) or record.get("email")
    if isinstance(record, Mapping):
        body = record.get(reader.wrap) if reader.wrap else record
        return body.get(reader.name_key) if isinstance(body, Mapping) else None
    return getattr(record, reader.name_key, None)


def _read_name(
    service: MammothService,
    kind: str,
    target_id: int,
    arguments: Mapping[str, Any],
) -> dict[str, Any]:
    reader = READERS[kind]
    manifest = command_by_id(reader.get_command) if reader.get_command else None
    symbol = reader.symbol or str((manifest or {}).get("sdk_symbol") or "")
    scope = {key: arguments[key] for key in reader.scope_args if arguments.get(key) is not None}
    sent_id = str(target_id) if reader.id_as_str else target_id
    record = service.call(symbol, **{reader.id_arg: sent_id}, **scope)
    name = _name_of(record, reader)
    if not isinstance(name, str) or not name:
        raise CliError(
            code=CODE_RESOURCE_NOT_FOUND,
            message=(
                f"Could not resolve the name of {kind} {target_id} for the dry-run "
                f"report: '{symbol}' returned no '{reader.name_key}'."
            ),
            exit_status=EXIT_NOT_FOUND,
            hint=f"Check the id with `mammoth {kind} get {target_id}`; nothing was changed.",
            details={"type": kind, "id": target_id},
        )
    return {"type": kind, "id": target_id, "name": name}


def _target_spec(command_id: str, would_call: Mapping[str, Any]) -> tuple[str, str] | None:
    """The (kind, id argument) a command changes, or None when it names none.

    Raises:
        CliError: ``dry_run_targets_unresolvable`` for a destructive command
            with no verified reader.
    """
    if command_id in COMMAND_TARGETS:
        return COMMAND_TARGETS[command_id]
    record = command_by_id(command_id) or {}
    if record.get("mutation_class") == "destructive":
        raise unresolvable_error(command_id, "no read command names this command's targets")
    family = command_id.split(".", 1)[0]
    if family == "dataset":
        return "dataset", "dataset_id"
    if family == "view" and would_call.get("view_id") is not None:
        return "view", "view_id"
    return None


def resolve_targets(
    service: MammothService, command_id: str, would_call: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Name every resource the reported call would change.

    Args:
        service: An open service (its dry-run gate lets these reads through).
        command_id: The dry-run command's manifest id.
        would_call: The ``would_call`` block of the dry-run report.

    Returns:
        ``[{"type", "id", "name"}, ...]`` in argument order; empty only for a
        non-destructive command that changes no addressable resource.

    Raises:
        CliError: ``dry_run_targets_unresolvable`` when a destructive command
            cannot be named (no verified reader, or no ids in the call);
            ``resource_not_found`` when an id has no readable name.
    """
    spec = _target_spec(command_id, would_call)
    if spec is None:
        return []
    kind, id_arg = spec
    arguments = would_call.get("arguments") or {}
    ids = _ids(arguments.get(id_arg, would_call.get(id_arg)))
    if arguments.get("invite_ids"):
        raise unresolvable_error(command_id, "pending invites have no read that names them")
    if not ids:
        raise unresolvable_error(
            command_id, f"the call carries no explicit '{id_arg}' ids (it may target every {kind})"
        )
    if kind == "view" and not isinstance(
        arguments.get("dataset_id", would_call.get("dataset_id")), int
    ):
        raise unresolvable_error(command_id, f"the parent dataset of view {ids[0]} is unknown")
    parent = {**arguments}
    if "dataset_id" not in parent and would_call.get("dataset_id") is not None:
        parent["dataset_id"] = would_call["dataset_id"]
    return [_read_name(service, kind, item, parent) for item in ids]
