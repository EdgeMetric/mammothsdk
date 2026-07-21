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
from mammoth_cli.commands import annotation as annotation_cmd
from mammoth_cli.commands import batch as batch_cmd
from mammoth_cli.commands import browse as browse_cmd
from mammoth_cli.commands import capability as capability_cmd
from mammoth_cli.commands import dataset as dataset_cmd
from mammoth_cli.commands import file as file_cmd
from mammoth_cli.commands import folder as folder_cmd
from mammoth_cli.commands import job as job_cmd
from mammoth_cli.commands import notification as notification_cmd
from mammoth_cli.commands import project as project_cmd
from mammoth_cli.commands import schema as schema_cmd
from mammoth_cli.commands import trash as trash_cmd
from mammoth_cli.commands import workspace as workspace_cmd
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
    # workspace family
    "workspace.accept-invite": workspace_cmd.workspace_accept_invite,
    "workspace.app-usage": workspace_cmd.workspace_app_usage,
    "workspace.check-expression": workspace_cmd.workspace_check_expression,
    "workspace.create": workspace_cmd.workspace_create,
    "workspace.delete": workspace_cmd.workspace_delete,
    "workspace.get": workspace_cmd.workspace_get,
    "workspace.list": workspace_cmd.workspace_list,
    "workspace.llm-task": workspace_cmd.workspace_llm_task,
    "workspace.reactivate": workspace_cmd.workspace_reactivate,
    "workspace.segment.list": workspace_cmd.workspace_segment_list,
    "workspace.segment.update": workspace_cmd.workspace_segment_update,
    "workspace.storage-breakdown": workspace_cmd.workspace_storage_breakdown,
    "workspace.update": workspace_cmd.workspace_update,
    "workspace.user.add": workspace_cmd.workspace_user_add,
    "workspace.user.get": workspace_cmd.workspace_user_get,
    "workspace.user.list": workspace_cmd.workspace_user_list,
    "workspace.user.remove": workspace_cmd.workspace_user_remove,
    "workspace.user.remove-batch": workspace_cmd.workspace_user_remove_batch,
    "workspace.user.update": workspace_cmd.workspace_user_update,
    "workspace.user.update-batch": workspace_cmd.workspace_user_update_batch,
    # dataset family
    "dataset.list": dataset_cmd.dataset_list,
    "dataset.get": dataset_cmd.dataset_get,
    "dataset.data": dataset_cmd.dataset_data,
    "dataset.file-settings": dataset_cmd.dataset_file_settings,
    "dataset.file-settings.update": dataset_cmd.dataset_file_settings_update,
    "dataset.file-settings.undo": dataset_cmd.dataset_file_settings_undo,
    "dataset.create": dataset_cmd.dataset_create,
    "dataset.create-from-pdf": dataset_cmd.dataset_create_from_pdf,
    "dataset.rename": dataset_cmd.dataset_rename,
    "dataset.trash": dataset_cmd.dataset_trash,
    "dataset.restore": dataset_cmd.dataset_restore,
    "dataset.delete": dataset_cmd.dataset_delete,
    "dataset.bulk-delete": dataset_cmd.dataset_bulk_delete,
    "dataset.bulk-update": dataset_cmd.dataset_bulk_update,
    "dataset.update": dataset_cmd.dataset_update,
    # file family
    "file.list": file_cmd.file_list,
    "file.get": file_cmd.file_get,
    "file.upload": file_cmd.file_upload,
    "file.upload-folder": file_cmd.file_upload_folder,
    "file.update": file_cmd.file_update,
    "file.set-password": file_cmd.file_set_password,
    "file.extract-sheets": file_cmd.file_extract_sheets,
    "file.delete": file_cmd.file_delete,
    "file.bulk-delete": file_cmd.file_bulk_delete,
    # job family
    "job.get": job_cmd.job_get,
    "job.get-many": job_cmd.job_get_many,
    "job.wait": job_cmd.job_wait,
    "job.wait-many": job_cmd.job_wait_many,
    # batch family
    "batch.list": batch_cmd.batch_list,
    "batch.get": batch_cmd.batch_get,
    "batch.create": batch_cmd.batch_create,
    "batch.update": batch_cmd.batch_update,
    "batch.delete": batch_cmd.batch_delete,
    "batch.bulk-delete": batch_cmd.batch_bulk_delete,
    # browse family
    "browse.folder": browse_cmd.browse_folder,
    "browse.project": browse_cmd.browse_project,
    "browse.root": browse_cmd.browse_root,
    "browse.workspace": browse_cmd.browse_workspace,
    # trash family
    "trash.add": trash_cmd.trash_add,
    "trash.list": trash_cmd.trash_list,
    "trash.restore": trash_cmd.trash_restore,
    # notification family
    "notification.list": notification_cmd.notification_list,
    "notification.update": notification_cmd.notification_update,
    "notification.update-batch": notification_cmd.notification_update_batch,
    "notification.delete": notification_cmd.notification_delete,
    "notification.delete-batch": notification_cmd.notification_delete_batch,
    # annotation family
    "annotation.list": annotation_cmd.annotation_list,
    "annotation.create": annotation_cmd.annotation_create,
    "annotation.update": annotation_cmd.annotation_update,
    "annotation.delete": annotation_cmd.annotation_delete,
    "annotation.comment.add": annotation_cmd.annotation_comment_add,
}
