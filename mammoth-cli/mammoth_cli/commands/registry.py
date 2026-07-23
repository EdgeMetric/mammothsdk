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
from mammoth_cli.commands import activity as activity_cmd
from mammoth_cli.commands import addon as addon_cmd
from mammoth_cli.commands import agent as agent_cmd
from mammoth_cli.commands import ai as ai_cmd
from mammoth_cli.commands import annotation as annotation_cmd
from mammoth_cli.commands import automation as automation_cmd
from mammoth_cli.commands import batch as batch_cmd
from mammoth_cli.commands import billing as billing_cmd
from mammoth_cli.commands import browse as browse_cmd
from mammoth_cli.commands import capability as capability_cmd
from mammoth_cli.commands import client_app as client_app_cmd
from mammoth_cli.commands import completion as completion_cmd
from mammoth_cli.commands import connector as connector_cmd
from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.commands import data_app as data_app_cmd
from mammoth_cli.commands import dataset as dataset_cmd
from mammoth_cli.commands import doctor as doctor_cmd
from mammoth_cli.commands import external_key as external_key_cmd
from mammoth_cli.commands import file as file_cmd
from mammoth_cli.commands import folder as folder_cmd
from mammoth_cli.commands import job as job_cmd
from mammoth_cli.commands import notification as notification_cmd
from mammoth_cli.commands import parameter as parameter_cmd
from mammoth_cli.commands import project as project_cmd
from mammoth_cli.commands import report as report_cmd
from mammoth_cli.commands import schedule as schedule_cmd
from mammoth_cli.commands import schema as schema_cmd
from mammoth_cli.commands import skill as skill_cmd
from mammoth_cli.commands import snippet as snippet_cmd
from mammoth_cli.commands import support as support_cmd
from mammoth_cli.commands import template as template_cmd
from mammoth_cli.commands import trash as trash_cmd
from mammoth_cli.commands import user as user_cmd
from mammoth_cli.commands import view as view_cmd
from mammoth_cli.commands import view_ops as view_ops_cmd
from mammoth_cli.commands import webhook as webhook_cmd
from mammoth_cli.commands import workflow as workflow_cmd
from mammoth_cli.commands import workspace as workspace_cmd
from mammoth_cli.errors.envelope import CODE_MISSING_ARGUMENT, EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.invocation import Invocation

HandlerResult = tuple[Any, dict[str, Any]]
Handler = Callable[[Invocation], HandlerResult]


def _require_arg(invocation: Invocation, name: str) -> str:
    if not invocation.extra_args:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
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
    "doctor": doctor_cmd.doctor,
    "completion.show": completion_cmd.completion_show,
    "completion.install": completion_cmd.completion_install,
    "skill.install": skill_cmd.skill_install,
    "skill.list": skill_cmd.skill_list,
    "skill.path": skill_cmd.skill_path,
    "skill.uninstall": skill_cmd.skill_uninstall,
    "skill.update": skill_cmd.skill_update,
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
    "project.checkpoint.list": project_cmd.project_checkpoint_list,
    "project.data-check.list": project_cmd.project_data_check_list,
    "project.user.add": project_cmd.project_user_add,
    "project.user.remove": project_cmd.project_user_remove,
    "project.user.update": project_cmd.project_user_update,
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
    "dataset.file-settings.get": dataset_cmd.dataset_file_settings,
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
    # schedule family
    "schedule.list": schedule_cmd.schedule_list,
    "schedule.get": schedule_cmd.schedule_get,
    "schedule.create": schedule_cmd.schedule_create,
    "schedule.update": schedule_cmd.schedule_update,
    "schedule.delete": schedule_cmd.schedule_delete,
    # agent family
    "agent.chat": agent_cmd.agent_chat,
    "agent.session.delete": agent_cmd.agent_session_delete,
    "agent.session.list": agent_cmd.agent_session_list,
    "agent.session.messages": agent_cmd.agent_session_messages,
    "agent.session.set-visibility": agent_cmd.agent_session_set_visibility,
    # ai family
    "ai.condition.generate": ai_cmd.ai_condition_generate,
    "ai.expression.generate": ai_cmd.ai_expression_generate,
    "ai.sql.generate": ai_cmd.ai_sql_generate,
    "ai.suggestion.list": ai_cmd.ai_suggestion_list,
    # addon family
    "addon.connector.add": addon_cmd.addon_connector_add,
    "addon.connector.remove": addon_cmd.addon_connector_remove,
    "addon.list": addon_cmd.addon_list,
    "addon.storage.add": addon_cmd.addon_storage_add,
    "addon.storage.remove": addon_cmd.addon_storage_remove,
    "addon.user.add": addon_cmd.addon_user_add,
    "addon.user.remove": addon_cmd.addon_user_remove,
    # external-key family
    "external-key.create": external_key_cmd.external_key_create,
    "external-key.delete": external_key_cmd.external_key_delete,
    "external-key.get": external_key_cmd.external_key_get,
    "external-key.list": external_key_cmd.external_key_list,
    # client-app family
    "client-app.create": client_app_cmd.client_app_create,
    "client-app.delete": client_app_cmd.client_app_delete,
    "client-app.get": client_app_cmd.client_app_get,
    "client-app.list": client_app_cmd.client_app_list,
    "client-app.update": client_app_cmd.client_app_update,
    # report + activity families
    "report.list": report_cmd.report_list,
    "activity.list": activity_cmd.activity_list,
    "activity.export": activity_cmd.activity_export,
    # billing family
    "billing.chargebee-plan": billing_cmd.billing_chargebee_plan,
    "billing.hosted-page": billing_cmd.billing_hosted_page,
    "billing.invoice.charge": billing_cmd.billing_invoice_charge,
    "billing.invoice.get": billing_cmd.billing_invoice_get,
    "billing.invoice.list": billing_cmd.billing_invoice_list,
    "billing.stripe.cancel": billing_cmd.billing_stripe_cancel,
    "billing.stripe.checkout-url": billing_cmd.billing_stripe_checkout_url,
    "billing.stripe.create": billing_cmd.billing_stripe_create,
    "billing.stripe.end-trial": billing_cmd.billing_stripe_end_trial,
    "billing.stripe.get": billing_cmd.billing_stripe_get,
    "billing.stripe.history": billing_cmd.billing_stripe_history,
    "billing.stripe.payment-method.delete": billing_cmd.billing_stripe_payment_method_delete,
    "billing.stripe.payment-method.list": billing_cmd.billing_stripe_payment_method_list,
    "billing.stripe.payment-method.set-default": (
        billing_cmd.billing_stripe_payment_method_set_default
    ),
    "billing.stripe.portal-url": billing_cmd.billing_stripe_portal_url,
    "billing.stripe.preview-invoice": billing_cmd.billing_stripe_preview_invoice,
    "billing.stripe.retry-payment": billing_cmd.billing_stripe_retry_payment,
    "billing.stripe.status": billing_cmd.billing_stripe_status,
    "billing.stripe.sync": billing_cmd.billing_stripe_sync,
    "billing.stripe.upcoming-invoice": billing_cmd.billing_stripe_upcoming_invoice,
    "billing.stripe.usage": billing_cmd.billing_stripe_usage,
    "billing.subscription.get": billing_cmd.billing_subscription_get,
    "billing.subscription.update": billing_cmd.billing_subscription_update,
    # support family
    "support.connector.create": support_cmd.support_connector_create,
    "support.connector.delete": support_cmd.support_connector_delete,
    "support.connector.list": support_cmd.support_connector_list,
    "support.connector.update": support_cmd.support_connector_update,
    "support.connector-profile.add-connector": support_cmd.support_connector_profile_add_connector,
    "support.connector-profile.create": support_cmd.support_connector_profile_create,
    "support.connector-profile.delete": support_cmd.support_connector_profile_delete,
    "support.connector-profile.list": support_cmd.support_connector_profile_list,
    "support.connector-profile.update": support_cmd.support_connector_profile_update,
    "support.feature.create": support_cmd.support_feature_create,
    "support.feature.delete": support_cmd.support_feature_delete,
    "support.feature.list": support_cmd.support_feature_list,
    "support.feature.update": support_cmd.support_feature_update,
    "support.feature-profile.add-feature": support_cmd.support_feature_profile_add_feature,
    "support.feature-profile.create": support_cmd.support_feature_profile_create,
    "support.feature-profile.delete": support_cmd.support_feature_profile_delete,
    "support.feature-profile.list": support_cmd.support_feature_profile_list,
    "support.feature-profile.update": support_cmd.support_feature_profile_update,
    "support.ownership.transfer": support_cmd.support_ownership_transfer,
    "support.plan.archive": support_cmd.support_plan_archive,
    "support.plan.chargebee-list": support_cmd.support_plan_chargebee_list,
    "support.plan.create": support_cmd.support_plan_create,
    "support.plan.delete": support_cmd.support_plan_delete,
    "support.plan.get": support_cmd.support_plan_get,
    "support.plan.list": support_cmd.support_plan_list,
    "support.plan.self-serve-list": support_cmd.support_plan_self_serve_list,
    "support.plan.update": support_cmd.support_plan_update,
    "support.plan.update-storage-tiers": support_cmd.support_plan_update_storage_tiers,
    "support.subscription.create": support_cmd.support_subscription_create,
    "support.subscription.get": support_cmd.support_subscription_get,
    "support.subscription.update": support_cmd.support_subscription_update,
    "support.user.list-all": support_cmd.support_user_list_all,
    "support.user.register": support_cmd.support_user_register,
    "support.user.update": support_cmd.support_user_update,
    "support.workspace.create": support_cmd.support_workspace_create,
    "support.workspace.delete": support_cmd.support_workspace_delete,
    "support.workspace.get": support_cmd.support_workspace_get,
    "support.workspace.list": support_cmd.support_workspace_list,
    "support.workspace.restore-access": support_cmd.support_workspace_restore_access,
    "support.workspace.suspend-access": support_cmd.support_workspace_suspend_access,
    "support.workspace.update": support_cmd.support_workspace_update,
    "support.workspace.user.add": support_cmd.support_workspace_user_add,
    "support.workspace.user.list": support_cmd.support_workspace_user_list,
    "support.workspace.user.remove": support_cmd.support_workspace_user_remove,
    "support.workspace.user.transfer": support_cmd.support_workspace_user_transfer,
    # view family (sub-client backed)
    "view.list": view_cmd.view_list,
    "view.bulk-delete": view_cmd.view_bulk_delete,
    "view.active-user.list": view_cmd.view_active_user_list,
    "view.active-user.mark": view_cmd.view_active_user_mark,
    "view.parameter-context": view_cmd.view_parameter_context,
    "view.preview": view_cmd.view_preview,
    "view.restore": view_cmd.view_restore,
    "view.trash": view_cmd.view_trash,
    "view.update": view_cmd.view_update,
    "view.data.get": view_cmd.view_data_get,
    "view.data.query": view_cmd.view_data_query,
    "view.conditional-format.create": view_cmd.view_conditional_format_create,
    "view.conditional-format.delete-all": view_cmd.view_conditional_format_delete_all,
    "view.conditional-format.list": view_cmd.view_conditional_format_list,
    "view.conditional-format.update": view_cmd.view_conditional_format_update,
    "view.checkpoint.create": view_cmd.view_checkpoint_create,
    "view.checkpoint.delete": view_cmd.view_checkpoint_delete,
    "view.checkpoint.get": view_cmd.view_checkpoint_get,
    "view.checkpoint.list": view_cmd.view_checkpoint_list,
    "view.checkpoint.update": view_cmd.view_checkpoint_update,
    "view.data-check.create": view_cmd.view_data_check_create,
    "view.data-check.delete": view_cmd.view_data_check_delete,
    "view.data-check.get": view_cmd.view_data_check_get,
    "view.data-check.list": view_cmd.view_data_check_list,
    "view.data-check.update": view_cmd.view_data_check_update,
    "view.derivative.create": view_cmd.view_derivative_create,
    "view.derivative.data": view_cmd.view_derivative_data,
    "view.derivative.delete": view_cmd.view_derivative_delete,
    "view.derivative.list": view_cmd.view_derivative_list,
    "view.derivative.update": view_cmd.view_derivative_update,
    "view.version.apply": view_cmd.view_version_apply,
    "view.version.delete": view_cmd.view_version_delete,
    "view.version.get": view_cmd.view_version_get,
    "view.version.list": view_cmd.view_version_list,
    "view.version.update": view_cmd.view_version_update,
    "view.ai.generate-data": view_cmd.view_ai_generate_data,
    "view.ai.generation-info": view_cmd.view_ai_generation_info,
    "view.ai.profile": view_cmd.view_ai_profile,
    "view.draft.command": view_cmd.view_draft_command,
    "view.pipeline.edit": view_cmd.view_pipeline_edit,
    "view.pipeline.get": view_cmd.view_pipeline_get,
    "view.pipeline.items": view_cmd.view_pipeline_items,
    "view.pipeline.rerun": view_cmd.view_pipeline_rerun,
    "view.pipeline.wait": view_cmd.view_pipeline_wait,
    "view.task.add": view_cmd.view_task_add,
    "view.task.delete": view_cmd.view_task_delete,
    "view.task.get": view_cmd.view_task_get,
    "view.task.list": view_cmd.view_task_list,
    "view.task.preview": view_cmd.view_task_preview,
    "view.task.update": view_cmd.view_task_update,
    "view.export.create": view_cmd.view_export_create,
    "view.export.csv": view_cmd.view_export_csv,
    "view.export.delete": view_cmd.view_export_delete,
    "view.export.get": view_cmd.view_export_get,
    "view.export.list": view_cmd.view_export_list,
    "view.export.publish-db": view_cmd.view_export_publish_db,
    "view.export.publish-db-update": view_cmd.view_export_publish_db_update,
    "view.export.update": view_cmd.view_export_update,
    # view family (View-object: create/get/delete, draft, transforms)
    "view.create": view_ops_cmd.view_create,
    "view.get": view_ops_cmd.view_get,
    "view.delete": view_ops_cmd.view_delete,
    "view.draft.enter": view_ops_cmd.view_draft_enter,
    "view.draft.status": view_ops_cmd.view_draft_status,
    "view.draft.submit": view_ops_cmd.view_draft_submit,
    "view.draft.discard": view_ops_cmd.view_draft_discard,
    "view.draft.auto-run": view_ops_cmd.view_draft_auto_run,
    "view.transform.add-column": view_ops_cmd.view_transform_add_column,
    "view.transform.add-sql": view_ops_cmd.view_transform_add_sql,
    "view.transform.ai": view_ops_cmd.view_transform_ai,
    "view.transform.bulk-replace": view_ops_cmd.view_transform_bulk_replace,
    "view.transform.combine-columns": view_ops_cmd.view_transform_combine_columns,
    "view.transform.convert-type": view_ops_cmd.view_transform_convert_type,
    "view.transform.copy-columns": view_ops_cmd.view_transform_copy_columns,
    "view.transform.crosstab": view_ops_cmd.view_transform_crosstab,
    "view.transform.date-diff": view_ops_cmd.view_transform_date_diff,
    "view.transform.delete-columns": view_ops_cmd.view_transform_delete_columns,
    "view.transform.discard-duplicates": view_ops_cmd.view_transform_discard_duplicates,
    "view.transform.extract-date": view_ops_cmd.view_transform_extract_date,
    "view.transform.fill-missing": view_ops_cmd.view_transform_fill_missing,
    "view.transform.filter": view_ops_cmd.view_transform_filter,
    "view.transform.generate-sql": view_ops_cmd.view_transform_generate_sql,
    "view.transform.increment-date": view_ops_cmd.view_transform_increment_date,
    "view.transform.join": view_ops_cmd.view_transform_join,
    "view.transform.json-extract": view_ops_cmd.view_transform_json_extract,
    "view.transform.limit-rows": view_ops_cmd.view_transform_limit_rows,
    "view.transform.lookup": view_ops_cmd.view_transform_lookup,
    "view.transform.math": view_ops_cmd.view_transform_math,
    "view.transform.pivot": view_ops_cmd.view_transform_pivot,
    "view.transform.replace": view_ops_cmd.view_transform_replace,
    "view.transform.set-values": view_ops_cmd.view_transform_set_values,
    "view.transform.small-large": view_ops_cmd.view_transform_small_large,
    "view.transform.split": view_ops_cmd.view_transform_split,
    "view.transform.substring": view_ops_cmd.view_transform_substring,
    "view.transform.text": view_ops_cmd.view_transform_text,
    "view.transform.unnest": view_ops_cmd.view_transform_unnest,
    "view.transform.window": view_ops_cmd.view_transform_window,
}

# Dashboard operations generated from the reviewed OpenAPI inventory share one
# manifest-driven handler. Existing authored handlers remain authoritative.
from mammoth.api.dashboard_generated import GENERATED_METHODS  # noqa: E402

_GENERATED_DASHBOARD_SYMBOLS = {
    f"mammoth.api.dashboards.DashboardsAPI.{method}" for method in GENERATED_METHODS
}
for _record in load_commands():
    if _record.get("sdk_symbol") in _GENERATED_DASHBOARD_SYMBOLS:
        HANDLERS.setdefault(str(_record["command_id"]), dashboard_cmd.generated_dashboard)
