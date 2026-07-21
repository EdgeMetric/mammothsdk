"""The command-handler registry.

Maps a manifest ``command_id`` to a handler callable. A handler receives the
typed :class:`~mammoth_cli.runtime.invocation.Invocation` and returns
``(data, meta_extra)`` where ``data`` is the normalized result payload and
``meta_extra`` is any additional envelope metadata (``profile``,
``workspace_id``, ``project_id``, ``pagination``).

Commands without a registered handler resolve to a stable ``not_implemented``
error envelope so an agent gets a deterministic, discoverable response rather
than a crash. Handlers are added per family as each area is implemented.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mammoth_cli import SCHEMA_VERSION, __version__
from mammoth_cli.commands import capability as capability_cmd
from mammoth_cli.commands import folder as folder_cmd
from mammoth_cli.commands import project as project_cmd
from mammoth_cli.commands import schema as schema_cmd
from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.runtime.invocation import Invocation

HandlerResult = tuple[Any, dict[str, Any]]
Handler = Callable[[Invocation], HandlerResult]


def _require_arg(invocation: Invocation, name: str) -> str:
    if not invocation.extra_args:
        raise CliError(
            code="missing_argument",
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return invocation.extra_args[0]


def _version(_: Invocation) -> HandlerResult:
    return {"version": __version__, "schema_version": SCHEMA_VERSION}, {}


def _capability_list(_: Invocation) -> HandlerResult:
    return capability_cmd.capability_entries(), {}


def _capability_get(invocation: Invocation) -> HandlerResult:
    operation_id = _require_arg(invocation, "operation id")
    entry = capability_cmd.get_capability(operation_id)
    if entry is None:
        raise CliError(
            code="capability_not_found",
            message=f"No capability record for operation '{operation_id}'.",
            exit_status=EXIT_USAGE,
            hint="List operations with 'mammoth capability list --output json'.",
        )
    return entry, {}


def _schema_list(_: Invocation) -> HandlerResult:
    return schema_cmd.schema_entries(), {}


def _schema_get(invocation: Invocation) -> HandlerResult:
    command_id = _require_arg(invocation, "command id")
    entry = schema_cmd.get_schema(command_id)
    if entry is None:
        raise CliError(
            code="schema_not_found",
            message=f"No schema record for command '{command_id}'.",
            exit_status=EXIT_USAGE,
            hint="List commands with 'mammoth schema list --output json'.",
        )
    return entry, {}


HANDLERS: dict[str, Handler] = {
    "version": _version,
    "capability.list": _capability_list,
    "capability.get": _capability_get,
    "schema.list": _schema_list,
    "schema.get": _schema_get,
    # project family (read-only)
    "project.list": project_cmd.project_list,
    "project.get": project_cmd.project_get,
    "project.pending-changes": project_cmd.project_pending_changes,
    "project.resource-status": project_cmd.project_resource_status,
    "project.resource-dependencies": project_cmd.project_resource_dependencies,
    "project.publish-credentials": project_cmd.project_publish_credentials,
    # project family (mutations)
    "project.create": project_cmd.project_create,
    "project.update": project_cmd.project_update,
    "project.delete": project_cmd.project_delete,
    "project.bulk-delete": project_cmd.project_bulk_delete,
    "project.bulk-update": project_cmd.project_bulk_update,
    "project.sample-flow": project_cmd.project_sample_flow,
    # folder family
    "folder.list": folder_cmd.folder_list,
    "folder.get": folder_cmd.folder_get,
    "folder.root": folder_cmd.folder_root,
    "folder.create": folder_cmd.folder_create,
    "folder.update": folder_cmd.folder_update,
    "folder.move": folder_cmd.folder_move,
    "folder.trash": folder_cmd.folder_trash,
    "folder.delete": folder_cmd.folder_delete,
    "folder.bulk-delete": folder_cmd.folder_bulk_delete,
}
