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
from mammoth_cli.commands import automation as automation_cmd
from mammoth_cli.commands import batch as batch_cmd
from mammoth_cli.commands import browse as browse_cmd
from mammoth_cli.commands import capability as capability_cmd
from mammoth_cli.commands import connector as connector_cmd
from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.commands import data_app as data_app_cmd
from mammoth_cli.commands import dataset as dataset_cmd
from mammoth_cli.commands import file as file_cmd
from mammoth_cli.commands import folder as folder_cmd
from mammoth_cli.commands import job as job_cmd
from mammoth_cli.commands import notification as notification_cmd
from mammoth_cli.commands import parameter as parameter_cmd
from mammoth_cli.commands import project as project_cmd
from mammoth_cli.commands import schema as schema_cmd
from mammoth_cli.commands import snippet as snippet_cmd
from mammoth_cli.commands import template as template_cmd
from mammoth_cli.commands import trash as trash_cmd
from mammoth_cli.commands import user as user_cmd
from mammoth_cli.commands import webhook as webhook_cmd
from mammoth_cli.commands import workflow as workflow_cmd
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
    # connector family
    "connector.active": connector_cmd.connector_active,
    "connector.ai.chat": connector_cmd.connector_ai_chat,
    "connector.ai.history": connector_cmd.connector_ai_history,
    "connector.ai.session.list": connector_cmd.connector_ai_session_list,
    "connector.ai.session.messages": connector_cmd.connector_ai_session_messages,
    "connector.ai.submit-column-selection": connector_cmd.connector_ai_submit_column_selection,
    "connector.ai.submit-credentials": connector_cmd.connector_ai_submit_credentials,
    "connector.connection.create": connector_cmd.connector_connection_create,
    "connector.connection.delete": connector_cmd.connector_connection_delete,
    "connector.connection.get": connector_cmd.connector_connection_get,
    "connector.connection.list": connector_cmd.connector_connection_list,
    "connector.connection.update": connector_cmd.connector_connection_update,
    "connector.ds-config.create": connector_cmd.connector_ds_config_create,
    "connector.ds-config.delete": connector_cmd.connector_ds_config_delete,
    "connector.ds-config.delete-all": connector_cmd.connector_ds_config_delete_all,
    "connector.ds-config.get": connector_cmd.connector_ds_config_get,
    "connector.ds-config.list": connector_cmd.connector_ds_config_list,
    "connector.ds-config.update": connector_cmd.connector_ds_config_update,
    "connector.get": connector_cmd.connector_get,
    "connector.list": connector_cmd.connector_list,
    "connector.query.generate": connector_cmd.connector_query_generate,
    "connector.query.status": connector_cmd.connector_query_status,
    # dashboard family
    "dashboard.action": dashboard_cmd.dashboard_action,
    "dashboard.analytics": dashboard_cmd.dashboard_analytics,
    "dashboard.cancel-generation": dashboard_cmd.dashboard_cancel_generation,
    "dashboard.create": dashboard_cmd.dashboard_create,
    "dashboard.data.draft": dashboard_cmd.dashboard_data_draft,
    "dashboard.data.published": dashboard_cmd.dashboard_data_published,
    "dashboard.delete": dashboard_cmd.dashboard_delete,
    "dashboard.get": dashboard_cmd.dashboard_get,
    "dashboard.get-by-url": dashboard_cmd.dashboard_get_by_url,
    "dashboard.job-by-url": dashboard_cmd.dashboard_job_by_url,
    "dashboard.list": dashboard_cmd.dashboard_list,
    "dashboard.published-data-by-url": dashboard_cmd.dashboard_published_data_by_url,
    "dashboard.restore": dashboard_cmd.dashboard_restore,
    "dashboard.share": dashboard_cmd.dashboard_share,
    "dashboard.source.list": dashboard_cmd.dashboard_source_list,
    "dashboard.trash": dashboard_cmd.dashboard_trash,
    "dashboard.update": dashboard_cmd.dashboard_update,
    "dashboard.widget-data": dashboard_cmd.dashboard_widget_data,
    "dashboard.widget-data-by-url": dashboard_cmd.dashboard_widget_data_by_url,
    # workflow family
    "workflow.block.add": workflow_cmd.workflow_block_add,
    "workflow.block.auth": workflow_cmd.workflow_block_auth,
    "workflow.block.config": workflow_cmd.workflow_block_config,
    "workflow.block.type": workflow_cmd.workflow_block_type,
    "workflow.canvas": workflow_cmd.workflow_canvas,
    "workflow.cleanup": workflow_cmd.workflow_cleanup,
    "workflow.create": workflow_cmd.workflow_create,
    "workflow.delete": workflow_cmd.workflow_delete,
    "workflow.from-template": workflow_cmd.workflow_from_template,
    "workflow.get": workflow_cmd.workflow_get,
    "workflow.graph": workflow_cmd.workflow_graph,
    "workflow.list": workflow_cmd.workflow_list,
    "workflow.update": workflow_cmd.workflow_update,
    "workflow.workspace-datasets": workflow_cmd.workflow_workspace_datasets,
    "workflow.workspace-exports": workflow_cmd.workflow_workspace_exports,
    "workflow.workspace-sources": workflow_cmd.workflow_workspace_sources,
    # parameter family
    "parameter.create": parameter_cmd.parameter_create,
    "parameter.delete": parameter_cmd.parameter_delete,
    "parameter.dependencies": parameter_cmd.parameter_dependencies,
    "parameter.duplicate": parameter_cmd.parameter_duplicate,
    "parameter.get": parameter_cmd.parameter_get,
    "parameter.group.create": parameter_cmd.parameter_group_create,
    "parameter.group.delete": parameter_cmd.parameter_group_delete,
    "parameter.group.list": parameter_cmd.parameter_group_list,
    "parameter.group.reorder": parameter_cmd.parameter_group_reorder,
    "parameter.group.update": parameter_cmd.parameter_group_update,
    "parameter.list": parameter_cmd.parameter_list,
    "parameter.rerun": parameter_cmd.parameter_rerun,
    "parameter.rerun-all-stale": parameter_cmd.parameter_rerun_all_stale,
    "parameter.update": parameter_cmd.parameter_update,
    # data-app family
    "data-app.active-job": data_app_cmd.data_app_active_job,
    "data-app.create": data_app_cmd.data_app_create,
    "data-app.delete": data_app_cmd.data_app_delete,
    "data-app.get": data_app_cmd.data_app_get,
    "data-app.job": data_app_cmd.data_app_job,
    "data-app.list": data_app_cmd.data_app_list,
    "data-app.pipeline-changes": data_app_cmd.data_app_pipeline_changes,
    "data-app.share": data_app_cmd.data_app_share,
    "data-app.update": data_app_cmd.data_app_update,
    "data-app.upload": data_app_cmd.data_app_upload,
    "data-app.user.list": data_app_cmd.data_app_user_list,
    "data-app.user.remove": data_app_cmd.data_app_user_remove,
    # snippet family
    "snippet.create": snippet_cmd.snippet_create,
    "snippet.delete": snippet_cmd.snippet_delete,
    "snippet.dependencies": snippet_cmd.snippet_dependencies,
    "snippet.duplicate": snippet_cmd.snippet_duplicate,
    "snippet.get": snippet_cmd.snippet_get,
    "snippet.list": snippet_cmd.snippet_list,
    "snippet.rerun": snippet_cmd.snippet_rerun,
    "snippet.update": snippet_cmd.snippet_update,
    # user family
    "user.avatar.delete": user_cmd.user_avatar_delete,
    "user.avatar.upload": user_cmd.user_avatar_upload,
    "user.change-password": user_cmd.user_change_password,
    "user.delete-account": user_cmd.user_delete_account,
    "user.get": user_cmd.user_get,
    "user.preference.get": user_cmd.user_preference_get,
    "user.preference.update": user_cmd.user_preference_update,
    "user.update": user_cmd.user_update,
    # automation family
    "automation.list": automation_cmd.automation_list,
    "automation.get": automation_cmd.automation_get,
    "automation.trash": automation_cmd.automation_trash,
    "automation.restore": automation_cmd.automation_restore,
    "automation.delete": automation_cmd.automation_delete,
    "automation.create": automation_cmd.automation_create,
    "automation.update": automation_cmd.automation_update,
    # webhook family
    "webhook.create": webhook_cmd.webhook_create,
    "webhook.delete": webhook_cmd.webhook_delete,
    "webhook.get": webhook_cmd.webhook_get,
    "webhook.list": webhook_cmd.webhook_list,
    "webhook.send": webhook_cmd.webhook_send,
    "webhook.send-get": webhook_cmd.webhook_send_get,
    "webhook.update": webhook_cmd.webhook_update,
    # template family
    "template.create": template_cmd.template_create,
    "template.delete": template_cmd.template_delete,
    "template.get": template_cmd.template_get,
    "template.list": template_cmd.template_list,
    "template.update": template_cmd.template_update,
}
