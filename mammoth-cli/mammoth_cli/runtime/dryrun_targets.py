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


@dataclass(frozen=True)
class Sub:
    """A target that is not a top-level resource, named through its parent.

    The name is ``<parent name> › <kind> <label>``; a resource with no name
    field is labelled by its own identifier, never left nameless.

    Attributes:
        kind: The target's ``type`` in the report.
        ids_arg: The reported-call argument holding its id (or ids).
        parent: The :data:`READERS` kind of the resource it belongs to.
        parent_id_arg: The argument holding the parent's id.
        source: Manifest command whose read confirms the target and yields its
            label (a ``get``, or a ``list`` when ``container`` is given).
        forward: Argument names passed on to that read.
        container: The list response key holding the items (``""`` for a bare
            list); items are matched on ``id_field``.
        id_field: The item field carrying the id in a list read.
        label_paths: Dotted paths into the read, first non-empty wins; with
            ``label_fmt`` all of them are formatted together.
        label_fmt: Format for the joined ``label_paths`` values.
        name_fmt: Overrides the default name layout.
        optional: The id may be absent (the call then covers every one).
    """

    kind: str
    ids_arg: str
    parent: str | None = None
    parent_id_arg: str = ""
    source: str | None = None
    forward: tuple[str, ...] = ()
    container: str | None = None
    id_field: str = "id"
    label_paths: tuple[str, ...] = ("name",)
    label_fmt: str = ""
    name_fmt: str = ""
    optional: bool = False


_VIEW_FWD = ("dataset_id", "dataview_id", "project_id")

#: A pending workspace invite, named by its email from ``workspace invite list``.
_INVITE_SUB = Sub(
    "invite",
    "invite_ids",
    source="workspace.invite.list",
    container="invites",
    label_paths=("email",),
    name_fmt="invite for {label}",
)

#: Command -> the sub-resources it changes. Shapes verified live on koyal:
#: task ``params.SEQUENCE_NUMBER``/``params.TASK_KEY``; version ``name``;
#: agent session ``title``; parameter group ``name``; tag ``name``; context
#: ``name``; custom style ``label``; both flat or listed as noted per entry.
SUBS: dict[str, tuple[Sub, ...]] = {
    "view.task.delete": (
        Sub(
            "step",
            "task_id",
            "view",
            "dataview_id",
            "view.task.get",
            ("dataview_id", "dataset_id"),
            label_paths=("params.SEQUENCE_NUMBER", "params.TASK_KEY"),
            label_fmt="{}: {}",
        ),
    ),
    "view.version.delete": (
        Sub("version", "version_id", "view", "dataview_id", "view.version.get", _VIEW_FWD),
    ),
    "view.checkpoint.delete": (
        Sub("checkpoint", "checkpoint_id", "view", "dataview_id", "view.checkpoint.get", _VIEW_FWD),
    ),
    "view.data-check.delete": (
        Sub("data check", "data_check_id", "view", "dataview_id", "view.data-check.get", _VIEW_FWD),
    ),
    "view.derivative.delete": (
        Sub(
            "derivative",
            "derivative_id",
            "view",
            "dataview_id",
            "view.derivative.list",
            ("dataset_id", "dataview_id", "project_id"),
            container="derivatives",
        ),
    ),
    "view.conditional-format.delete-all": (
        Sub(
            "conditional format rule",
            "rule_id",
            "view",
            "dataview_id",
            optional=True,
            name_fmt="{parent} › conditional format {label}",
        ),
    ),
    "view.draft.discard": (
        Sub("draft", "view_id", "view", "view_id", name_fmt="{parent} › unsaved draft changes"),
    ),
    "agent.action.delete": (
        Sub(
            "agent action",
            "action_id",
            source="agent.action.list",
            container="actions",
            forward=("session_id",),
            label_paths=("name", "kind"),
            name_fmt="what agent action {action_id} made: {label}",
        ),
    ),
    "agent.session.delete": (
        Sub(
            "agent session",
            "session_id",
            source="agent.session.list",
            container="sessions",
            id_field="session_id",
            label_paths=("title",),
        ),
    ),
    "annotation.delete": (
        Sub(
            "annotation",
            "annotation_id",
            source="annotation.list",
            container="",
            forward=("project_id",),
            label_paths=("body", "text"),
        ),
    ),
    "parameter.group.delete": (
        Sub(
            "parameter group",
            "group_id",
            source="parameter.group.list",
            container="items",
            forward=("project_id",),
        ),
    ),
    "dashboard.context.delete": (
        Sub("context", "context_id", source="dashboard.context.list", container="contexts"),
    ),
    "dashboard.signature.delete": (
        Sub("signature", "signature_id", source="dashboard.signature.list", container="signatures"),
    ),
    "dashboard.style.custom.delete": (
        Sub(
            "custom style",
            "style_id",
            source="dashboard.style.custom.list",
            container="styles",
            label_paths=("label", "name"),
        ),
    ),
    "dashboard.tags.delete": (
        Sub("tag", "tag_id", source="dashboard.tags.list", container="tags"),
    ),
    "dashboard.tags.merge": (
        Sub("tag", "tag_id", source="dashboard.tags.list", container="tags"),
        Sub("tag", "target_id", source="dashboard.tags.list", container="tags"),
    ),
    "dashboard.template.delete": (
        Sub(
            "dashboard template",
            "template_id",
            source="dashboard.template.get",
            label_paths=("title", "name", "label"),
        ),
    ),
    "dashboard.template.thumbnail.clear": (
        Sub(
            "dashboard template picture",
            "template_id",
            source="dashboard.template.get",
            label_paths=("title", "name", "label"),
            name_fmt="picture of dashboard template {label}",
        ),
    ),
    "support.template.discard": (
        Sub(
            "curated template",
            "slug",
            source="support.template.list",
            container="templates",
            id_field="slug",
            label_paths=("title", "slug"),
        ),
    ),
    "workflow.cleanup": (
        Sub(
            "ghost workflows",
            "project_id",
            "project",
            "project_id",
            name_fmt="ghost (orphaned skeleton) workflows in {parent}",
        ),
    ),
    "template.delete": (
        Sub("template", "template_id", source="template.get", label_paths=("name", "title")),
    ),
    "dashboard.qa.session.delete": (
        Sub(
            "Q&A session",
            "session_id",
            "dashboard",
            "dashboard_id",
            "dashboard.qa.session.get",
            ("dashboard_id",),
            label_paths=("title", "session.title"),
        ),
    ),
    "dashboard.qa.comment.delete": (
        Sub(
            "Q&A comment",
            "comment_id",
            "dashboard",
            "dashboard_id",
            name_fmt="{parent} › Q&A session {session_id} › comment {label}",
        ),
    ),
    "client-app.delete": (
        Sub("client app", "client_key", source="client-app.get", label_paths=("app_name", "name")),
    ),
    "token.revoke": (
        Sub("client app", "client_key", source="client-app.get", label_paths=("app_name", "name")),
    ),
    "connector.connection.delete": (
        Sub(
            "connection",
            "connection_key",
            source="connector.connection.get",
            forward=("connector_key", "project_id"),
            label_paths=("name", "connection_name"),
            name_fmt="{connector_key} › connection {label}",
        ),
    ),
    "connector.ds-config.delete": (
        Sub(
            "data source config",
            "ds_config_key",
            source="connector.ds-config.get",
            forward=("connector_key", "connection_key", "project_id"),
            label_paths=("name", "ds_config_name"),
            name_fmt="{connector_key} › {connection_key} › config {label}",
        ),
    ),
    "connector.ds-config.delete-all": (
        Sub(
            "data source config",
            "config_ids",
            name_fmt="{connector_key} › {connection_key} › config {label}",
        ),
    ),
    "data-app.user.remove": (
        Sub(
            "data app user",
            "email",
            "data-app",
            "data_app_id",
            name_fmt="{label} › access to {parent}",
        ),
    ),
    "workspace.invite.delete": (_INVITE_SUB,),
    "workspace.invite.revoke": (_INVITE_SUB,),
    "notification.delete": (Sub("notification", "notification_id"),),
    "notification.delete-batch": (Sub("notification", "ids"),),
}


#: Command -> (resource kind, the reported-call argument holding its id or ids).
#: Every ``destructive`` command whose targets a verified read can name, plus
#: ``project.delete``. The rest of the destructive set is listed in the
#: module docstring's failure mode, not here.
COMMAND_TARGETS: dict[str, tuple[str, str]] = {
    "dataset.delete": ("dataset", "dataset_id"),
    "dataset.bulk-delete": ("dataset", "dataset_ids"),
    "dataset.file-settings.undo": ("dataset", "dataset_id"),
    "dataset.broken-rows.resolve": ("dataset", "dataset_id"),
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


#: Commands that make a new resource and change no existing one: nothing to name.
CREATES_ONLY: frozenset[str] = frozenset({"dataset.create", "dataset.create-from-pdf"})


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


#: Resource kinds one bulk request can name, and the resource type the route calls each.
BULK_TYPES: dict[str, str] = {"dataset": "datasource", "view": "dataview", "folder": "label"}
_BULK_SYMBOL = "mammoth.api.browse.BrowseAPI.resources_bulk"


def _read_names(
    service: MammothService, kind: str, ids: list[int], arguments: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Name every id of ``kind``: one bulk request per 100 ids where the route knows the kind.

    An id the bulk read does not return (missing, or not readable by the
    caller) is read on its own, so the error it raises is the resource's own.
    """
    if kind not in BULK_TYPES or len(ids) < 2:
        return [_read_name(service, kind, item, arguments) for item in ids]
    scope = {"project_id": arguments["project_id"]} if arguments.get("project_id") else {}
    rows = service.call(_BULK_SYMBOL, items=[(BULK_TYPES[kind], item) for item in ids], **scope)
    names = {row.get("object_id"): row.get("name") for row in rows if isinstance(row, Mapping)}
    return [
        (
            {"type": kind, "id": item, "name": names[item]}
            if isinstance(names.get(item), str) and names[item]
            else _read_name(service, kind, item, arguments)
        )
        for item in ids
    ]


def _path(record: Any, dotted: str) -> object:
    """Follow ``a.b`` through nested mappings (or attributes)."""
    for part in dotted.split("."):
        record = record.get(part) if isinstance(record, Mapping) else getattr(record, part, None)
    return record


def _label(record: Any, sub: Sub) -> str | None:
    """The sub-resource's own label from its read, or None when it has none."""
    values = [_path(record, path) for path in sub.label_paths]
    if sub.label_fmt:
        return sub.label_fmt.format(*values) if all(v not in (None, "") for v in values) else None
    return next((str(v) for v in values if isinstance(v, str) and v), None)


def _items(value: Any) -> list[int | str]:
    """The ids in an argument: one id, or a list of them."""
    raw = value if isinstance(value, list) else [value]
    return [item for item in raw if isinstance(item, (int, str)) and not isinstance(item, bool)]


def _symbol_of(command: str) -> str:
    return str((command_by_id(command) or {}).get("sdk_symbol") or "")


def _parent_name(
    service: MammothService, kind: str, parent_id: int, args: Mapping[str, Any]
) -> str:
    """The parent resource's name; a view with no known dataset is found by discovery."""
    if kind == "view" and not isinstance(args.get("dataset_id"), int):
        record = service.call(_symbol_of("view.get"), view_id=parent_id)
        name = _name_of(record, READERS["view"])
        if not isinstance(name, str) or not name:
            raise _unresolved_name("view", parent_id, "ViewsResource.get", "name")
        return name
    return str(_read_name(service, kind, parent_id, args)["name"])


def _unresolved_name(kind: str, target_id: object, symbol: str, key: str) -> CliError:
    return CliError(
        code=CODE_RESOURCE_NOT_FOUND,
        message=(
            f"Could not resolve {kind} {target_id} for the dry-run report: "
            f"'{symbol}' found no '{key}'."
        ),
        exit_status=EXIT_NOT_FOUND,
        hint=f"Check the id with `mammoth {kind.split()[0]} list`; nothing was changed.",
        details={"type": kind, "id": target_id},
    )


def _container_items(listed: Any, container: str) -> list[Any]:
    """The items of a list read: a bare list, a mapping, or a typed SDK model."""
    if isinstance(listed, list):
        return listed
    held = (
        listed.get(container) if isinstance(listed, Mapping) else getattr(listed, container, None)
    )
    return held if isinstance(held, list) else []


def _sub_record(
    service: MammothService,
    sub: Sub,
    target: object,
    args: Mapping[str, Any],
    lists: dict[str, Any],
) -> Any:
    """Read the sub-resource (or find it in its list); None when nothing is declared.

    A list read serves every target of the call, so it is made once (``lists``).
    """
    if sub.source is None:
        return None
    symbol = _symbol_of(sub.source)
    kwargs = {key: args[key] for key in sub.forward if args.get(key) is not None}
    if sub.container is None:
        return service.call(symbol, **{sub.ids_arg: target}, **kwargs)
    if symbol not in lists:
        lists[symbol] = service.call(symbol, **kwargs)
    listed = lists[symbol]
    items = _container_items(listed, sub.container)
    found = next((i for i in items if str(_path(i, sub.id_field)) == str(target)), None)
    if found is None:
        raise _unresolved_name(sub.kind, target, symbol, sub.id_field)
    return found


def _sub_targets(
    service: MammothService, command_id: str, sub: Sub, args: Mapping[str, Any]
) -> list[dict[str, Any]]:
    ids = _items(args.get(sub.ids_arg))
    if not ids and sub.optional:
        ids = ["all"]
    if not ids:
        raise unresolvable_error(command_id, f"the call carries no '{sub.ids_arg}' to name")
    parent = ""
    if sub.parent:
        parent_ids = _ids(args.get(sub.parent_id_arg))
        if not parent_ids:
            raise unresolvable_error(command_id, f"the {sub.parent} id is unknown")
        parent = f"\u201c{_parent_name(service, sub.parent, parent_ids[0], args)}\u201d"
    targets = []
    lists: dict[str, Any] = {}
    for target in ids:
        record = _sub_record(service, sub, target, args, lists) if target != "all" else None
        label = _label(record, sub) if target != "all" else None
        shown = f"\u201c{label}\u201d" if label else str(target)
        layout = sub.name_fmt or ("{parent} \u203a {kind} {label}" if parent else "{kind} {label}")
        name = layout.format(**{**args, "parent": parent, "kind": sub.kind, "label": shown})
        targets.append({"type": sub.kind, "id": target, "name": name})
    return targets


def _avatar_target(service: MammothService) -> list[dict[str, Any]]:
    """``user avatar delete`` changes the caller's own profile picture."""
    record = service.call(_symbol_of("user.get"))
    who = " ".join(str(_path(record, key) or "") for key in ("first_name", "last_name")).strip()
    who = who or str(_path(record, "email") or "")
    if not who:
        raise _unresolved_name("user", "self", _symbol_of("user.get"), "first_name")
    return [{"type": "user avatar", "id": _path(record, "id"), "name": f"profile picture of {who}"}]


def _target_spec(command_id: str, would_call: Mapping[str, Any]) -> tuple[str, str] | None:
    """The (kind, id argument) a command changes, or None when it names none.

    Raises:
        CliError: ``dry_run_targets_unresolvable`` for a destructive command
            with no verified reader.
    """
    if command_id in COMMAND_TARGETS:
        return COMMAND_TARGETS[command_id]
    if command_id in CREATES_ONLY:
        return None
    record = command_by_id(command_id) or {}
    if record.get("mutation_class") == "destructive":
        raise unresolvable_error(command_id, "no read command names this command's targets")
    family = command_id.split(".", 1)[0]
    if family == "dataset":
        return "dataset", "dataset_id"
    if family == "view" and would_call.get("view_id") is not None:
        return "view", "view_id"
    return None


def _remove_batch_invites(
    service: MammothService, command_id: str, arguments: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """The pending invites a ``user remove-batch`` call deletes, named by email."""
    invite_ids = _ids(arguments.get("invite_ids"))
    if not invite_ids:
        return []
    return _sub_targets(service, command_id, _INVITE_SUB, {"invite_ids": invite_ids})


def _patched_dataset_ids(patch_data: Any) -> list[int]:
    """The dataset ids a bulk patch renames: the keys of each operation's ``value``."""
    operations = patch_data if isinstance(patch_data, list) else [patch_data]
    found: list[int] = []
    for operation in operations:
        value = operation.get("value") if isinstance(operation, Mapping) else None
        if isinstance(value, Mapping):
            found.extend(int(key) for key in value if str(key).isdigit())
    return list(dict.fromkeys(found))


def _bulk_update_targets(
    service: MammothService, command_id: str, arguments: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Name the datasets a ``dataset bulk-update`` patch changes, from its own ``patch_data``."""
    ids = _patched_dataset_ids(arguments.get("patch_data"))
    if not ids:
        raise unresolvable_error(
            command_id,
            "'patch_data' names no dataset; pass "
            '{"op": "replace", "path": "name", "value": {"<dataset_id>": "<new name>"}}',
        )
    return _read_names(service, "dataset", ids, arguments)


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
    arguments = would_call.get("arguments") or {}
    if command_id == "user.avatar.delete":
        return _avatar_target(service)
    if command_id == "dataset.bulk-update":
        return _bulk_update_targets(service, command_id, arguments)
    if command_id in SUBS:
        scope = {k: v for k, v in would_call.items() if k in ("view_id", "dataset_id")}
        merged = {**scope, **arguments}
        return [
            t for sub in SUBS[command_id] for t in _sub_targets(service, command_id, sub, merged)
        ]
    spec = _target_spec(command_id, would_call)
    if spec is None:
        return []
    kind, id_arg = spec
    ids = _ids(arguments.get(id_arg, would_call.get(id_arg)))
    invites = _remove_batch_invites(service, command_id, arguments)
    if not ids and invites:
        return invites
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
    return _read_names(service, kind, ids, parent) + invites


#: Deletes whose dry run also lists what depends on the resource: command ->
#: the reported-call arguments holding the resource ids. A step or column
#: delete changes a view, so the view's dependents are what could break.
DEPENDENT_IDS: dict[str, tuple[str, ...]] = {
    "dataset.delete": ("dataset_id",),
    "dataset.bulk-delete": ("dataset_ids",),
    "view.delete": ("view_id",),
    "view.bulk-delete": ("dataview_ids",),
    "view.task.delete": ("dataview_id", "view_id"),
    "view.transform.delete-columns": ("dataview_id", "view_id"),
}
_DEPENDENCIES_SYMBOL = "mammoth.api.projects.ProjectsAPI.resource_dependencies"


def resolve_dependents(
    service: MammothService,
    command_id: str,
    would_call: Mapping[str, Any],
    project_id: int | None,
) -> dict[str, Any] | None:
    """What depends on the resources a delete would change, or None for other commands.

    Never raises: a read that fails is reported as ``checked: false`` with the
    error, so the confirm step never mistakes "not looked up" for "nothing
    depends on it".
    """
    keys = DEPENDENT_IDS.get(command_id)
    if keys is None:
        return None
    arguments = {
        **{k: v for k, v in would_call.items() if k in keys},
        **(would_call.get("arguments") or {}),
    }
    ids = [str(item) for key in keys for item in _ids(arguments.get(key))]
    if not ids or project_id is None:
        reason = "no project is active" if project_id is None else "the call names no resource id"
        return {"checked": False, "error": f"could not look up dependents: {reason}"}
    try:
        graph = service.call(_DEPENDENCIES_SYMBOL, project_id=project_id, resource_ids=ids)
    except Exception as exc:  # noqa: BLE001 -- the dry run itself must still report
        return {"checked": False, "resource_ids": ids, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "checked": True,
        "resource_ids": ids,
        "dependencies": graph,
        "note": "Deleting these can break what depends on them; check this before you confirm.",
    }
