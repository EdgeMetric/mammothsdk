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

import re
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from mammoth_cli import SCHEMA_VERSION, __version__
from mammoth_cli.commands._lazy import LazyTable
from mammoth_cli.errors.envelope import CODE_MISSING_ARGUMENT, EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime import runlog

if TYPE_CHECKING:
    from mammoth_cli.runtime.invocation import Invocation

HandlerResult = tuple[Any, dict[str, Any]]
type Handler = Callable[[Invocation], HandlerResult]


def _require_arg(invocation: Invocation, name: str) -> str:
    bound = invocation.bound_input()
    value = bound.get(name)
    if value is None and invocation.extra_args:
        value = invocation.extra_args[0]
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return str(value)


def _version(_: Invocation) -> HandlerResult:
    return {"version": __version__, "schema_version": SCHEMA_VERSION}, {}


def _capability_list(_: Invocation) -> HandlerResult:
    from mammoth_cli.commands import capability as capability_cmd

    return capability_cmd.capability_entries(), {}


def _capability_get(invocation: Invocation) -> HandlerResult:
    from mammoth_cli.commands import capability as capability_cmd

    operation_id = _require_arg(invocation, "operation id")
    entry = capability_cmd.get_capability(operation_id)
    if entry is None:
        raise CliError(
            code="capability_not_found",
            message=f"No capability record for operation '{operation_id}'.",
            exit_status=EXIT_USAGE,
            hint="List operations with 'mammoth capability list'.",
        )
    return entry, {}


def _capability_find(invocation: Invocation) -> HandlerResult:
    from mammoth_cli.commands import capability as capability_cmd

    query = _require_arg(invocation, "search query")
    if not query.strip():
        raise CliError(
            code="empty_search_query",
            message="The capability search query must contain at least one word.",
            exit_status=EXIT_USAGE,
            hint="For the complete inventory, use 'mammoth capability list'.",
        )
    return capability_cmd.find_capabilities(query), {}


def _schema_list(invocation: Invocation) -> HandlerResult:
    """Command index by family; ``schema list FAMILY`` for one family; ``full`` for every record."""
    from mammoth_cli.commands import schema as schema_cmd

    bound = invocation.bound_input()
    if bound.get("full"):
        return schema_cmd.schema_entries(), {}
    family = bound.get("family")
    if family is None and invocation.extra_args:
        family = invocation.extra_args[0]
    return schema_cmd.schema_index(str(family) if family else None), {}


#: Same ceiling as ``schema find``: more ids than this in one ``schema get`` is
#: a pasted list, not a lookup.
_MAX_GET_IDS = 12


def _resolve_schema(command_id: str, rest: list[str]) -> tuple[str, dict[str, Any] | None]:
    """Look up one schema, also accepting the command as typed.

    ``view transform math`` (quoted or not) and ``mammoth view transform math``
    both mean ``view.transform.math``. Returns the id that resolved, and the
    entry (``None`` when nothing matched).
    """
    from mammoth_cli.commands import schema as schema_cmd

    entry = schema_cmd.get_schema(command_id)
    if entry is not None:
        return command_id, entry
    if rest and rest[0] == command_id:
        rest = rest[1:]
    words = [*command_id.split(), *rest]
    if words and words[0] == "mammoth":
        words = words[1:]
    dotted = ".".join(words)
    if dotted and dotted != command_id:
        entry = schema_cmd.get_schema(dotted)
        if entry is not None:
            return dotted, entry
    return command_id, None


def _schema_not_found(command_id: str) -> CliError:
    return CliError(
        code="schema_not_found",
        message=f"No schema record for command '{command_id}'.",
        exit_status=EXIT_USAGE,
        hint="Use the dotted id (view.transform.math); 'mammoth schema find WORDS' searches.",
    )


def _schema_get_many(ids: list[str], full: bool) -> dict[str, Any]:
    """One result for several ids: the schemas found, and one error per id not found."""
    from mammoth_cli.commands import schema as schema_cmd

    if len(ids) > _MAX_GET_IDS:
        raise CliError(
            code="too_many_ids",
            message=f"schema get accepts at most {_MAX_GET_IDS} ids per call; got {len(ids)}.",
            exit_status=EXIT_USAGE,
            hint="Split the ids across more than one 'schema get' call.",
        )
    schemas: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for command_id in ids:
        _, entry = _resolve_schema(command_id, [])
        if entry is None:
            error = _schema_not_found(command_id)
            errors.append({"command_id": command_id, "code": error.code, "message": error.message})
        else:
            schemas.append(entry if full else schema_cmd.brief_schema(entry))
    return {"requested": len(ids), "schemas": schemas, "errors": errors}


def _schema_get(invocation: Invocation) -> HandlerResult:
    from mammoth_cli.commands import schema as schema_cmd

    command_id = _require_arg(invocation, "command id")
    full = bool(invocation.bound_input().get("full"))
    # 'schema get A,B,C' (or 'A;B;C'): several ids in one call, like the
    # ';'-separated goals of 'schema find'. Command ids never contain either.
    ids = list(
        dict.fromkeys(part.strip() for part in re.split(r"[,;]", command_id) if part.strip())
    )
    if len(ids) > 1:
        return _schema_get_many(ids, full), {}
    rest = [str(arg) for arg in invocation.extra_args or []]
    command_id, entry = _resolve_schema(ids[0] if ids else command_id, rest)
    if entry is None:
        raise _schema_not_found(command_id)
    return (entry if full else schema_cmd.brief_schema(entry)), {}


#: Above this many ';'-separated goals in one 'schema find' call, an agent is
#: almost certainly pasting something else (a whole plan, a sentence with
#: semicolons) rather than a real goal list; reject with a clear message
#: instead of silently running dozens of searches.
_MAX_FIND_GOALS = 12

_EMPTY_QUERY_ERROR = CliError(
    code="empty_search_query",
    message="The schema search query must contain at least one word.",
    exit_status=EXIT_USAGE,
    hint="For the complete inventory, use 'mammoth schema list'.",
)


def _cap_inline_detail(result: dict[str, Any], keep: int) -> None:
    """Strip inline ``accepted_fields``/``agent_example`` past the top `keep`."""
    for key in ("matches", "suggestions"):
        for entry in (result.get(key) or [])[keep:]:
            entry.pop("accepted_fields", None)
            entry.pop("agent_example", None)


def _schema_find(invocation: Invocation) -> HandlerResult:
    from mammoth_cli.commands import schema as schema_cmd

    query = _require_arg(invocation, "search query")
    if not query.strip():
        raise _EMPTY_QUERY_ERROR
    if ";" not in query:
        return schema_cmd.find_schemas(query), {}
    # Several goals in one call ("join customers onto orders; remove
    # duplicate rows; build a dashboard"): run the existing single-goal
    # search per goal instead of round-tripping once per goal.
    goals = [goal.strip() for goal in query.split(";") if goal.strip()]
    if not goals:
        raise _EMPTY_QUERY_ERROR
    if len(goals) > _MAX_FIND_GOALS:
        raise CliError(
            code="too_many_goals",
            message=(
                f"schema find accepts at most {_MAX_FIND_GOALS} ';'-separated goals per "
                f"call; got {len(goals)}."
            ),
            exit_status=EXIT_USAGE,
            hint="Split the goals across more than one 'schema find' call.",
        )
    results = [schema_cmd.find_schemas(goal) for goal in goals]
    if len(results) > 1:
        # Cap inline accepted_fields/agent_example to the top match per goal
        # so a multi-goal envelope stays small even when every goal has
        # several candidates.
        for result in results:
            _cap_inline_detail(result, 1)
    return {
        "goals": [{"goal": goal, **result} for goal, result in zip(goals, results, strict=True)]
    }, {}


def _log_path(_: Invocation) -> HandlerResult:
    """Show the run-log directory, today's file, and the days kept."""
    return runlog.log_path(), {}


def _log_tail(invocation: Invocation) -> HandlerResult:
    """Read recent run-log records; filter with 'errors_only', 'command_id', 'run_id', 'days'."""
    document = invocation.bound_input()
    records = runlog.read_records(
        days=int(document.get("days", 1)),
        limit=int(document.get("limit", 50)),
        errors_only=bool(document.get("errors_only", False)),
        command_id=document.get("command_id"),
        run_id=document.get("run_id"),
    )
    return {"records": records, "count": len(records)}, {}


_TARGETS: dict[str, str] = {
    "version": "mammoth_cli.commands.registry:_version",
    "log.path": "mammoth_cli.commands.registry:_log_path",
    "log.tail": "mammoth_cli.commands.registry:_log_tail",
    "doctor": "mammoth_cli.commands.doctor:doctor",
    "calc": "mammoth_cli.commands.calc:calc",
    "link": "mammoth_cli.commands.link:link",
    "resolve": "mammoth_cli.commands.resolve:resolve",
    "completion.show": "mammoth_cli.commands.completion:completion_show",
    "completion.install": "mammoth_cli.commands.completion:completion_install",
    "skill.agents-md.install": "mammoth_cli.commands.skill:skill_agents_md_install",
    "skill.install": "mammoth_cli.commands.skill:skill_install",
    "skill.list": "mammoth_cli.commands.skill:skill_list",
    "skill.path": "mammoth_cli.commands.skill:skill_path",
    "skill.show": "mammoth_cli.commands.skill:skill_show",
    "skill.uninstall": "mammoth_cli.commands.skill:skill_uninstall",
    "skill.update": "mammoth_cli.commands.skill:skill_update",
    "capability.list": "mammoth_cli.commands.registry:_capability_list",
    "capability.get": "mammoth_cli.commands.registry:_capability_get",
    "capability.find": "mammoth_cli.commands.registry:_capability_find",
    "schema.list": "mammoth_cli.commands.registry:_schema_list",
    "schema.get": "mammoth_cli.commands.registry:_schema_get",
    "schema.find": "mammoth_cli.commands.registry:_schema_find",
    "project.list": "mammoth_cli.commands.project:project_list",
    "project.get": "mammoth_cli.commands.project:project_get",
    "project.check": "mammoth_cli.commands.project:project_check",
    "project.needs-attention": "mammoth_cli.commands.project:project_needs_attention",
    "project.pending-changes": "mammoth_cli.commands.project:project_pending_changes",
    "project.memory.list": "mammoth_cli.commands.project:project_memory_list",
    "project.memory.add": "mammoth_cli.commands.project:project_memory_add",
    "project.memory.remove": "mammoth_cli.commands.project:project_memory_remove",
    "project.resource-status": "mammoth_cli.commands.project:project_resource_status",
    "project.resource-dependencies": "mammoth_cli.commands.project:project_resource_dependencies",
    "project.resource-dependencies.update": (
        "mammoth_cli.commands.project:project_resource_dependencies_update"
    ),
    "project.publish-credentials": "mammoth_cli.commands.project:project_publish_credentials",
    "project.create": "mammoth_cli.commands.project:project_create",
    "project.copy": "mammoth_cli.commands.project:project_copy",
    "project.ensure": "mammoth_cli.commands.project:project_ensure",
    "project.update": "mammoth_cli.commands.project:project_update",
    "project.delete": "mammoth_cli.commands.project:project_delete",
    "project.bulk-delete": "mammoth_cli.commands.project:project_bulk_delete",
    "project.bulk-update": "mammoth_cli.commands.project:project_bulk_update",
    "project.sample-flow": "mammoth_cli.commands.project:project_sample_flow",
    "project.checkpoint.list": "mammoth_cli.commands.project:project_checkpoint_list",
    "project.data-check.list": "mammoth_cli.commands.project:project_data_check_list",
    "project.user.add": "mammoth_cli.commands.project:project_user_add",
    "project.user.remove": "mammoth_cli.commands.project:project_user_remove",
    "project.user.update": "mammoth_cli.commands.project:project_user_update",
    "folder.find": "mammoth_cli.commands.folder:folder_find",
    "folder.list": "mammoth_cli.commands.folder:folder_list",
    "folder.get": "mammoth_cli.commands.folder:folder_get",
    "folder.root": "mammoth_cli.commands.folder:folder_root",
    "folder.create": "mammoth_cli.commands.folder:folder_create",
    "folder.update": "mammoth_cli.commands.folder:folder_update",
    "folder.move": "mammoth_cli.commands.folder:folder_move",
    "folder.trash": "mammoth_cli.commands.folder:folder_trash",
    "folder.delete": "mammoth_cli.commands.folder:folder_delete",
    "folder.bulk-delete": "mammoth_cli.commands.folder:folder_bulk_delete",
    "workspace.accept-invite": "mammoth_cli.commands.workspace:workspace_accept_invite",
    "workspace.app-usage": "mammoth_cli.commands.workspace:workspace_app_usage",
    "workspace.check-expression": "mammoth_cli.commands.workspace:workspace_check_expression",
    "workspace.create": "mammoth_cli.commands.workspace:workspace_create",
    "workspace.delete": "mammoth_cli.commands.workspace:workspace_delete",
    "workspace.get": "mammoth_cli.commands.workspace:workspace_get",
    "workspace.home": "mammoth_cli.commands.workspace:workspace_home",
    "workspace.list": "mammoth_cli.commands.workspace:workspace_list",
    "workspace.invite.delete": "mammoth_cli.commands.workspace:workspace_invite_delete",
    "workspace.invite.list": "mammoth_cli.commands.workspace:workspace_invite_list",
    "workspace.invite.resend": "mammoth_cli.commands.workspace:workspace_invite_resend",
    "workspace.invite.revoke": "mammoth_cli.commands.workspace:workspace_invite_revoke",
    "workspace.invite.update-role": "mammoth_cli.commands.workspace:workspace_invite_update_role",
    "workspace.llm-task": "mammoth_cli.commands.workspace:workspace_llm_task",
    "workspace.reactivate": "mammoth_cli.commands.workspace:workspace_reactivate",
    "workspace.segment.list": "mammoth_cli.commands.workspace:workspace_segment_list",
    "workspace.segment.update": "mammoth_cli.commands.workspace:workspace_segment_update",
    "workspace.storage-breakdown": "mammoth_cli.commands.workspace:workspace_storage_breakdown",
    "workspace.update": "mammoth_cli.commands.workspace:workspace_update",
    "workspace.user.add": "mammoth_cli.commands.workspace:workspace_user_add",
    "workspace.user.get": "mammoth_cli.commands.workspace:workspace_user_get",
    "workspace.user.list": "mammoth_cli.commands.workspace:workspace_user_list",
    "workspace.user.remove": "mammoth_cli.commands.workspace:workspace_user_remove",
    "workspace.user.remove-batch": "mammoth_cli.commands.workspace:workspace_user_remove_batch",
    "workspace.user.update": "mammoth_cli.commands.workspace:workspace_user_update",
    "workspace.user.update-batch": "mammoth_cli.commands.workspace:workspace_user_update_batch",
    "dataset.find": "mammoth_cli.commands.dataset:dataset_find",
    "dataset.list": "mammoth_cli.commands.dataset:dataset_list",
    "dataset.search": "mammoth_cli.commands.dataset:dataset_search",
    "dataset.get": "mammoth_cli.commands.dataset:dataset_get",
    "dataset.batch-data": "mammoth_cli.commands.dataset:dataset_batch_data",
    "dataset.data": "mammoth_cli.commands.dataset:dataset_data",
    "dataset.file-settings.get": "mammoth_cli.commands.dataset:dataset_file_settings",
    "dataset.file-settings.update": "mammoth_cli.commands.dataset:dataset_file_settings_update",
    "dataset.file-settings.undo": "mammoth_cli.commands.dataset:dataset_file_settings_undo",
    "dataset.broken-rows.list": "mammoth_cli.commands.dataset:dataset_broken_rows",
    "dataset.broken-rows.resolve": "mammoth_cli.commands.dataset:dataset_broken_rows_resolve",
    "dataset.interpretation.preview": "mammoth_cli.commands.dataset:dataset_interpretation",
    "dataset.interpretation.confirm": "mammoth_cli.commands.dataset:dataset_interpretation",
    "dataset.create": "mammoth_cli.commands.dataset:dataset_create",
    "dataset.create-from-pdf": "mammoth_cli.commands.dataset:dataset_create_from_pdf",
    "dataset.rename": "mammoth_cli.commands.dataset:dataset_rename",
    "dataset.trash": "mammoth_cli.commands.dataset:dataset_trash",
    "dataset.restore": "mammoth_cli.commands.dataset:dataset_restore",
    "dataset.delete": "mammoth_cli.commands.dataset:dataset_delete",
    "dataset.bulk-delete": "mammoth_cli.commands.dataset:dataset_bulk_delete",
    "dataset.bulk-update": "mammoth_cli.commands.dataset:dataset_bulk_update",
    "dataset.update": "mammoth_cli.commands.dataset:dataset_update",
    "file.list": "mammoth_cli.commands.file:file_list",
    "file.get": "mammoth_cli.commands.file:file_get",
    "file.upload": "mammoth_cli.commands.file:file_upload",
    "file.upload-folder": "mammoth_cli.commands.file:file_upload_folder",
    "file.update": "mammoth_cli.commands.file:file_update",
    "file.set-password": "mammoth_cli.commands.file:file_set_password",
    "file.extract-sheets": "mammoth_cli.commands.file:file_extract_sheets",
    "file.delete": "mammoth_cli.commands.file:file_delete",
    "file.bulk-delete": "mammoth_cli.commands.file:file_bulk_delete",
    "job.get": "mammoth_cli.commands.job:job_get",
    "job.get-many": "mammoth_cli.commands.job:job_get_many",
    "job.wait": "mammoth_cli.commands.job:job_wait",
    "job.wait-many": "mammoth_cli.commands.job:job_wait_many",
    "batch.list": "mammoth_cli.commands.batch:batch_list",
    "batch.get": "mammoth_cli.commands.batch:batch_get",
    "batch.create": "mammoth_cli.commands.batch:batch_create",
    "batch.create-spec": "mammoth_cli.commands.batch:batch_create_spec",
    "batch.update": "mammoth_cli.commands.batch:batch_update",
    "batch.delete": "mammoth_cli.commands.batch:batch_delete",
    "batch.bulk-delete": "mammoth_cli.commands.batch:batch_bulk_delete",
    "browse.folder": "mammoth_cli.commands.browse:browse_folder",
    "browse.ancestors": "mammoth_cli.commands.browse:browse_ancestors",
    "browse.resource": "mammoth_cli.commands.browse:browse_resource",
    "browse.resources": "mammoth_cli.commands.browse:browse_resources",
    "browse.resources.bulk": "mammoth_cli.commands.browse:browse_resources_bulk",
    "browse.search": "mammoth_cli.commands.browse:browse_search",
    "browse.project": "mammoth_cli.commands.browse:browse_project",
    "browse.root": "mammoth_cli.commands.browse:browse_root",
    "browse.workspace": "mammoth_cli.commands.browse:browse_workspace",
    "trash.add": "mammoth_cli.commands.trash:trash_add",
    "trash.list": "mammoth_cli.commands.trash:trash_list",
    "trash.restore": "mammoth_cli.commands.trash:trash_restore",
    "notification.list": "mammoth_cli.commands.notification:notification_list",
    "notification.update": "mammoth_cli.commands.notification:notification_update",
    "notification.update-batch": "mammoth_cli.commands.notification:notification_update_batch",
    "notification.delete": "mammoth_cli.commands.notification:notification_delete",
    "notification.delete-batch": "mammoth_cli.commands.notification:notification_delete_batch",
    "annotation.list": "mammoth_cli.commands.annotation:annotation_list",
    "annotation.create": "mammoth_cli.commands.annotation:annotation_create",
    "annotation.update": "mammoth_cli.commands.annotation:annotation_update",
    "annotation.delete": "mammoth_cli.commands.annotation:annotation_delete",
    "annotation.comment.add": "mammoth_cli.commands.annotation:annotation_comment_add",
    "connector.active": "mammoth_cli.commands.connector:connector_active",
    "connector.ai.chat": "mammoth_cli.commands.connector:connector_ai_chat",
    "connector.ai.history": "mammoth_cli.commands.connector:connector_ai_history",
    "connector.ai.session.list": "mammoth_cli.commands.connector:connector_ai_session_list",
    "connector.ai.session.messages": "mammoth_cli.commands.connector:connector_ai_session_messages",
    "connector.ai.submit-column-selection": (
        "mammoth_cli.commands.connector:connector_ai_submit_column_selection"
    ),
    "connector.ai.submit-credentials": (
        "mammoth_cli.commands.connector:connector_ai_submit_credentials"
    ),
    "connector.connection.create": "mammoth_cli.commands.connector:connector_connection_create",
    "connector.connection.delete": "mammoth_cli.commands.connector:connector_connection_delete",
    "connector.connection.get": "mammoth_cli.commands.connector:connector_connection_get",
    "connector.connection.list": "mammoth_cli.commands.connector:connector_connection_list",
    "connector.connection.update": "mammoth_cli.commands.connector:connector_connection_update",
    "connector.ds-config.create": "mammoth_cli.commands.connector:connector_ds_config_create",
    "connector.ds-config.delete": "mammoth_cli.commands.connector:connector_ds_config_delete",
    "connector.ds-config.delete-all": (
        "mammoth_cli.commands.connector:connector_ds_config_delete_all"
    ),
    "connector.ds-config.get": "mammoth_cli.commands.connector:connector_ds_config_get",
    "connector.ds-config.list": "mammoth_cli.commands.connector:connector_ds_config_list",
    "connector.ds-config.update": "mammoth_cli.commands.connector:connector_ds_config_update",
    "connector.get": "mammoth_cli.commands.connector:connector_get",
    "connector.list": "mammoth_cli.commands.connector:connector_list",
    "connector.query.generate": "mammoth_cli.commands.connector:connector_query_generate",
    "connector.query.status": "mammoth_cli.commands.connector:connector_query_status",
    "dashboard.action": "mammoth_cli.commands.dashboard:dashboard_action",
    "dashboard.archive": "mammoth_cli.commands.dashboard:dashboard_archive",
    "dashboard.analytics": "mammoth_cli.commands.dashboard:dashboard_analytics",
    "dashboard.cancel-generation": "mammoth_cli.commands.dashboard:dashboard_cancel_generation",
    "dashboard.create-blank": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.data.draft": "mammoth_cli.commands.dashboard:dashboard_data_draft",
    "dashboard.data.published": "mammoth_cli.commands.dashboard:dashboard_data_published",
    "dashboard.delete": "mammoth_cli.commands.dashboard:dashboard_delete",
    "dashboard.get": "mammoth_cli.commands.dashboard:dashboard_get",
    "dashboard.filter.add": "mammoth_cli.commands.dashboard:dashboard_filter_add",
    "dashboard.filter.list": "mammoth_cli.commands.dashboard:dashboard_filter_list",
    "dashboard.filter.remove": "mammoth_cli.commands.dashboard:dashboard_filter_remove",
    "dashboard.get-by-url": "mammoth_cli.commands.dashboard:dashboard_get_by_url",
    "dashboard.job-by-url": "mammoth_cli.commands.dashboard:dashboard_job_by_url",
    "dashboard.list": "mammoth_cli.commands.dashboard:dashboard_list",
    "dashboard.tags.list": "mammoth_cli.commands.dashboard:dashboard_tags_list",
    "dashboard.tags.rename": "mammoth_cli.commands.dashboard:dashboard_tags_rename",
    "dashboard.tags.set": "mammoth_cli.commands.dashboard:dashboard_tags_set",
    "dashboard.tags.delete": "mammoth_cli.commands.dashboard:dashboard_tags_delete",
    "dashboard.tags.merge": "mammoth_cli.commands.dashboard:dashboard_tags_merge",
    "dashboard.published-data-by-url": (
        "mammoth_cli.commands.dashboard:dashboard_published_data_by_url"
    ),
    "dashboard.restore": "mammoth_cli.commands.dashboard:dashboard_restore",
    "dashboard.figure.add": "mammoth_cli.commands.dashboard:dashboard_figure_add",
    "dashboard.share": "mammoth_cli.commands.dashboard:dashboard_share",
    "dashboard.source.list": "mammoth_cli.commands.dashboard:dashboard_source_list",
    "dashboard.trash": "mammoth_cli.commands.dashboard:dashboard_trash",
    "dashboard.update": "mammoth_cli.commands.dashboard:dashboard_update",
    "dashboard.widget-data": "mammoth_cli.commands.dashboard:dashboard_widget_data",
    "dashboard.widget-data-by-url": "mammoth_cli.commands.dashboard:dashboard_widget_data_by_url",
    "dashboard.pages.add": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.context.extract": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.exemplar.extract": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.swap-data": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.swap-fit": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.audience.get": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.audience.summary": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.audience.digest.get": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.audience.digest.set": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.columns": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.context.review": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.context.apply": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.qa.insights": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.templates.pending": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.templates.use": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.duplicate": "mammoth_cli.commands.dashboard:dashboard_duplicate",
    "dashboard.pbix-intent": "mammoth_cli.commands.dashboard:dashboard_attachment_read",
    "dashboard.pbix-assess": "mammoth_cli.commands.dashboard:dashboard_attachment_read",
    "dashboard.assess-twb": "mammoth_cli.commands.dashboard:dashboard_assess_twb",
    "dashboard.assess-pbix": "mammoth_cli.commands.dashboard:dashboard_assess_pbix",
    "dashboard.import-workbook": "mammoth_cli.commands.dashboard:dashboard_import_workbook",
    "dashboard.bi-preflight": "mammoth_cli.commands.dashboard:dashboard_bi_preflight",
    "dashboard.bi-export": "mammoth_cli.commands.dashboard:dashboard_bi_export",
    "dashboard.embed.config.get": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.embed.config.set": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.embed.key.rotate": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.embed.usage.get": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.embed.usage.summary": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.format-preview": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.template.thumbnail.get": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.template.thumbnail.set": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.template.thumbnail.clear": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.gallery.list": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.gallery.get": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.embed.origin.revoke": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.embed.preview-token.create": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.embed.secret.rotate": "mammoth_cli.commands.dashboard:generated_dashboard",
    "dashboard.embed.lifetime.set": "mammoth_cli.commands.dashboard:generated_dashboard",
    # Collections have no handler of their own: the manifest-driven dashboard handler binds the
    # input to the SDK signature, applies the manifest's confirmation and calls the symbol.
    "collection.list": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.get": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.get-by-url": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.create": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.update": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.delete": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.dashboards.add": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.dashboards.remove": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.share": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.members.remove": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.for-dashboard": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.activity": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.pipeline-changes": "mammoth_cli.commands.dashboard:generated_dashboard",
    "collection.files.upload": "mammoth_cli.commands.dashboard:generated_dashboard",
    "workflow.block.add": "mammoth_cli.commands.workflow:workflow_block_add",
    "workflow.block.auth": "mammoth_cli.commands.workflow:workflow_block_auth",
    "workflow.block.config": "mammoth_cli.commands.workflow:workflow_block_config",
    "workflow.block.type": "mammoth_cli.commands.workflow:workflow_block_type",
    "workflow.canvas": "mammoth_cli.commands.workflow:workflow_canvas",
    "workflow.cleanup": "mammoth_cli.commands.workflow:workflow_cleanup",
    "workflow.create": "mammoth_cli.commands.workflow:workflow_create",
    "workflow.delete": "mammoth_cli.commands.workflow:workflow_delete",
    "workflow.from-template": "mammoth_cli.commands.workflow:workflow_from_template",
    "workflow.get": "mammoth_cli.commands.workflow:workflow_get",
    "workflow.graph": "mammoth_cli.commands.workflow:workflow_graph",
    "workflow.list": "mammoth_cli.commands.workflow:workflow_list",
    "workflow.update": "mammoth_cli.commands.workflow:workflow_update",
    "workflow.workspace-datasets": "mammoth_cli.commands.workflow:workflow_workspace_datasets",
    "workflow.workspace-exports": "mammoth_cli.commands.workflow:workflow_workspace_exports",
    "workflow.workspace-sources": "mammoth_cli.commands.workflow:workflow_workspace_sources",
    "parameter.create": "mammoth_cli.commands.parameter:parameter_create",
    "parameter.delete": "mammoth_cli.commands.parameter:parameter_delete",
    "parameter.dependencies": "mammoth_cli.commands.parameter:parameter_dependencies",
    "parameter.duplicate": "mammoth_cli.commands.parameter:parameter_duplicate",
    "parameter.get": "mammoth_cli.commands.parameter:parameter_get",
    "parameter.group.create": "mammoth_cli.commands.parameter:parameter_group_create",
    "parameter.group.delete": "mammoth_cli.commands.parameter:parameter_group_delete",
    "parameter.group.list": "mammoth_cli.commands.parameter:parameter_group_list",
    "parameter.group.reorder": "mammoth_cli.commands.parameter:parameter_group_reorder",
    "parameter.group.update": "mammoth_cli.commands.parameter:parameter_group_update",
    "parameter.list": "mammoth_cli.commands.parameter:parameter_list",
    "parameter.rerun": "mammoth_cli.commands.parameter:parameter_rerun",
    "parameter.rerun-all-stale": "mammoth_cli.commands.parameter:parameter_rerun_all_stale",
    "parameter.update": "mammoth_cli.commands.parameter:parameter_update",
    "data-app.active-job": "mammoth_cli.commands.data_app:data_app_active_job",
    "data-app.create": "mammoth_cli.commands.data_app:data_app_create",
    "data-app.delete": "mammoth_cli.commands.data_app:data_app_delete",
    "data-app.get": "mammoth_cli.commands.data_app:data_app_get",
    "data-app.job": "mammoth_cli.commands.data_app:data_app_job",
    "data-app.list": "mammoth_cli.commands.data_app:data_app_list",
    "data-app.pipeline-changes": "mammoth_cli.commands.data_app:data_app_pipeline_changes",
    "data-app.share": "mammoth_cli.commands.data_app:data_app_share",
    "data-app.update": "mammoth_cli.commands.data_app:data_app_update",
    "data-app.upload": "mammoth_cli.commands.data_app:data_app_upload",
    "data-app.user.list": "mammoth_cli.commands.data_app:data_app_user_list",
    "data-app.user.remove": "mammoth_cli.commands.data_app:data_app_user_remove",
    "snippet.create": "mammoth_cli.commands.snippet:snippet_create",
    "snippet.delete": "mammoth_cli.commands.snippet:snippet_delete",
    "snippet.dependencies": "mammoth_cli.commands.snippet:snippet_dependencies",
    "snippet.duplicate": "mammoth_cli.commands.snippet:snippet_duplicate",
    "snippet.get": "mammoth_cli.commands.snippet:snippet_get",
    "snippet.list": "mammoth_cli.commands.snippet:snippet_list",
    "snippet.rerun": "mammoth_cli.commands.snippet:snippet_rerun",
    "snippet.update": "mammoth_cli.commands.snippet:snippet_update",
    "user.avatar.delete": "mammoth_cli.commands.user:user_avatar_delete",
    "user.avatar.upload": "mammoth_cli.commands.user:user_avatar_upload",
    "user.change-password": "mammoth_cli.commands.user:user_change_password",
    "user.delete-account": "mammoth_cli.commands.user:user_delete_account",
    "user.get": "mammoth_cli.commands.user:user_get",
    "user.preference.get": "mammoth_cli.commands.user:user_preference_get",
    "user.preference.update": "mammoth_cli.commands.user:user_preference_update",
    "user.update": "mammoth_cli.commands.user:user_update",
    "automation.list": "mammoth_cli.commands.automation:automation_list",
    "automation.capabilities": "mammoth_cli.commands.automation:automation_capabilities",
    "automation.get": "mammoth_cli.commands.automation:automation_get",
    "automation.trash": "mammoth_cli.commands.automation:automation_trash",
    "automation.restore": "mammoth_cli.commands.automation:automation_restore",
    "automation.delete": "mammoth_cli.commands.automation:automation_delete",
    "automation.create": "mammoth_cli.commands.automation:automation_create",
    "automation.update": "mammoth_cli.commands.automation:automation_update",
    "webhook.create": "mammoth_cli.commands.webhook:webhook_create",
    "webhook.delete": "mammoth_cli.commands.webhook:webhook_delete",
    "webhook.get": "mammoth_cli.commands.webhook:webhook_get",
    "webhook.list": "mammoth_cli.commands.webhook:webhook_list",
    "webhook.send": "mammoth_cli.commands.webhook:webhook_send",
    "webhook.send-get": "mammoth_cli.commands.webhook:webhook_send_get",
    "webhook.update": "mammoth_cli.commands.webhook:webhook_update",
    "template.create": "mammoth_cli.commands.template:template_create",
    "template.delete": "mammoth_cli.commands.template:template_delete",
    "template.get": "mammoth_cli.commands.template:template_get",
    "template.list": "mammoth_cli.commands.template:template_list",
    "template.update": "mammoth_cli.commands.template:template_update",
    "schedule.list": "mammoth_cli.commands.schedule:schedule_list",
    "schedule.get": "mammoth_cli.commands.schedule:schedule_get",
    "schedule.create": "mammoth_cli.commands.schedule:schedule_create",
    "schedule.update": "mammoth_cli.commands.schedule:schedule_update",
    "schedule.delete": "mammoth_cli.commands.schedule:schedule_delete",
    "agent.access.set": "mammoth_cli.commands.agent:agent_access_set",
    "agent.charter.get": "mammoth_cli.commands.agent:agent_charter_get",
    "agent.charter.restore": "mammoth_cli.commands.agent:agent_charter_restore",
    "agent.charter.set": "mammoth_cli.commands.agent:agent_charter_set",
    "agent.charter.versions": "mammoth_cli.commands.agent:agent_charter_versions",
    "agent.create": "mammoth_cli.commands.agent:agent_create",
    "agent.delete": "mammoth_cli.commands.agent:agent_delete",
    "agent.disable": "mammoth_cli.commands.agent:agent_disable",
    "agent.feedback.list": "mammoth_cli.commands.agent:agent_feedback_list",
    "agent.get": "mammoth_cli.commands.agent:agent_get",
    "agent.goldens.add": "mammoth_cli.commands.agent:agent_goldens_add",
    "agent.goldens.list": "mammoth_cli.commands.agent:agent_goldens_list",
    "agent.goldens.remove": "mammoth_cli.commands.agent:agent_goldens_remove",
    "agent.goldens.run": "mammoth_cli.commands.agent:agent_goldens_run",
    "agent.goldens.status": "mammoth_cli.commands.agent:agent_goldens_status",
    "agent.list": "mammoth_cli.commands.agent:agent_list",
    "agent.memory.add": "mammoth_cli.commands.agent:agent_memory_add",
    "agent.memory.list": "mammoth_cli.commands.agent:agent_memory_list",
    "agent.memory.remove": "mammoth_cli.commands.agent:agent_memory_remove",
    "agent.projects.clear": "mammoth_cli.commands.agent:agent_projects_clear",
    "agent.projects.set": "mammoth_cli.commands.agent:agent_projects_set",
    "agent.publish": "mammoth_cli.commands.agent:agent_publish",
    "agent.roles": "mammoth_cli.commands.agent:agent_roles",
    "agent.scratch.clear": "mammoth_cli.commands.agent:agent_scratch_clear",
    "agent.scratch.get": "mammoth_cli.commands.agent:agent_scratch_get",
    "agent.scratch.list": "mammoth_cli.commands.agent:agent_scratch_list",
    "agent.scratch.set": "mammoth_cli.commands.agent:agent_scratch_set",
    "agent.team.set": "mammoth_cli.commands.agent:agent_team_set",
    "agent.update": "mammoth_cli.commands.agent:agent_update",
    "agent.action.delete": "mammoth_cli.commands.agent:agent_action_delete",
    "agent.action.list": "mammoth_cli.commands.agent:agent_action_list",
    "agent.chat": "mammoth_cli.commands.agent:agent_chat",
    "agent.run.extend": "mammoth_cli.commands.agent:agent_run_extend",
    "agent.run.list": "mammoth_cli.commands.agent:agent_run_list",
    "agent.run.pause": "mammoth_cli.commands.agent:agent_run_pause",
    "agent.run.resume": "mammoth_cli.commands.agent:agent_run_resume",
    "agent.run.status": "mammoth_cli.commands.agent:agent_run_status",
    "agent.run.stop": "mammoth_cli.commands.agent:agent_run_stop",
    "agent.run.units.set": "mammoth_cli.commands.agent:agent_run_units_set",
    "agent.run.units.list": "mammoth_cli.commands.agent:agent_run_units_list",
    "agent.run.instance.list": "mammoth_cli.commands.agent:agent_run_instance_list",
    "agent.run.instance.messages": "mammoth_cli.commands.agent:agent_run_instance_messages",
    "agent.run.instance.transcript": "mammoth_cli.commands.agent:agent_run_instance_transcript",
    "agent.run.retry": "mammoth_cli.commands.agent:agent_run_retry",
    "agent.turn.cancel": "mammoth_cli.commands.agent:agent_turn_cancel",
    "agent.message.set-request-kind": "mammoth_cli.commands.agent:agent_message_set_request_kind",
    "agent.plan.edit-proposal": "mammoth_cli.commands.agent:agent_plan_edit_proposal",
    "agent.session.delete": "mammoth_cli.commands.agent:agent_session_delete",
    "agent.session.list": "mammoth_cli.commands.agent:agent_session_list",
    "agent.session.messages": "mammoth_cli.commands.agent:agent_session_messages",
    "agent.session.set-visibility": "mammoth_cli.commands.agent:agent_session_set_visibility",
    "ai.condition.generate": "mammoth_cli.commands.ai:ai_condition_generate",
    "ai.expression.generate": "mammoth_cli.commands.ai:ai_expression_generate",
    "ai.sql.generate": "mammoth_cli.commands.ai:ai_sql_generate",
    "ai.retention.condition": "mammoth_cli.commands.ai:ai_retention_condition",
    "ai.suggestion.list": "mammoth_cli.commands.ai:ai_suggestion_list",
    "addon.connector.add": "mammoth_cli.commands.addon:addon_connector_add",
    "addon.connector.remove": "mammoth_cli.commands.addon:addon_connector_remove",
    "addon.list": "mammoth_cli.commands.addon:addon_list",
    "addon.storage.add": "mammoth_cli.commands.addon:addon_storage_add",
    "addon.storage.remove": "mammoth_cli.commands.addon:addon_storage_remove",
    "addon.user.add": "mammoth_cli.commands.addon:addon_user_add",
    "addon.user.remove": "mammoth_cli.commands.addon:addon_user_remove",
    "external-key.create": "mammoth_cli.commands.external_key:external_key_create",
    "external-key.delete": "mammoth_cli.commands.external_key:external_key_delete",
    "external-key.get": "mammoth_cli.commands.external_key:external_key_get",
    "external-key.list": "mammoth_cli.commands.external_key:external_key_list",
    "client-app.create": "mammoth_cli.commands.client_app:client_app_create",
    "client-app.delete": "mammoth_cli.commands.client_app:client_app_delete",
    "client-app.get": "mammoth_cli.commands.client_app:client_app_get",
    "client-app.list": "mammoth_cli.commands.client_app:client_app_list",
    "client-app.update": "mammoth_cli.commands.client_app:client_app_update",
    "token.create": "mammoth_cli.commands.client_app:client_app_create",
    "token.list": "mammoth_cli.commands.client_app:client_app_list",
    "token.revoke": "mammoth_cli.commands.client_app:client_app_delete",
    "report.list": "mammoth_cli.commands.report:report_list",
    "activity.list": "mammoth_cli.commands.activity:activity_list",
    "activity.export": "mammoth_cli.commands.activity:activity_export",
    "billing.chargebee-plan": "mammoth_cli.commands.billing:billing_chargebee_plan",
    "billing.hosted-page": "mammoth_cli.commands.billing:billing_hosted_page",
    "billing.invoice.charge": "mammoth_cli.commands.billing:billing_invoice_charge",
    "billing.invoice.list": "mammoth_cli.commands.billing:billing_invoice_list",
    "billing.stripe.cancel": "mammoth_cli.commands.billing:billing_stripe_cancel",
    "billing.stripe.checkout-url": "mammoth_cli.commands.billing:billing_stripe_checkout_url",
    "billing.stripe.create": "mammoth_cli.commands.billing:billing_stripe_create",
    "billing.stripe.end-trial": "mammoth_cli.commands.billing:billing_stripe_end_trial",
    "billing.stripe.get": "mammoth_cli.commands.billing:billing_stripe_get",
    "billing.stripe.history": "mammoth_cli.commands.billing:billing_stripe_history",
    "billing.stripe.payment-method.delete": (
        "mammoth_cli.commands.billing:billing_stripe_payment_method_delete"
    ),
    "billing.stripe.payment-method.list": (
        "mammoth_cli.commands.billing:billing_stripe_payment_method_list"
    ),
    "billing.stripe.payment-method.set-default": (
        "mammoth_cli.commands.billing:billing_stripe_payment_method_set_default"
    ),
    "billing.stripe.portal-url": "mammoth_cli.commands.billing:billing_stripe_portal_url",
    "billing.stripe.preview-invoice": "mammoth_cli.commands.billing:billing_stripe_preview_invoice",
    "billing.stripe.recheck-limits": "mammoth_cli.commands.billing:billing_stripe_recheck_limits",
    "billing.stripe.resume": "mammoth_cli.commands.billing:billing_stripe_resume",
    "billing.stripe.retry-payment": "mammoth_cli.commands.billing:billing_stripe_retry_payment",
    "billing.stripe.status": "mammoth_cli.commands.billing:billing_stripe_status",
    "billing.stripe.storage.set": "mammoth_cli.commands.billing:billing_stripe_storage_set",
    "billing.stripe.sync": "mammoth_cli.commands.billing:billing_stripe_sync",
    "billing.stripe.upcoming-invoice": (
        "mammoth_cli.commands.billing:billing_stripe_upcoming_invoice"
    ),
    "billing.stripe.usage": "mammoth_cli.commands.billing:billing_stripe_usage",
    "billing.subscription.get": "mammoth_cli.commands.billing:billing_subscription_get",
    "billing.subscription.update": "mammoth_cli.commands.billing:billing_subscription_update",
    "support.connector.create": "mammoth_cli.commands.support:support_connector_create",
    "support.connector.delete": "mammoth_cli.commands.support:support_connector_delete",
    "support.connector.list": "mammoth_cli.commands.support:support_connector_list",
    "support.connector.update": "mammoth_cli.commands.support:support_connector_update",
    "support.connector-profile.add-connector": (
        "mammoth_cli.commands.support:support_connector_profile_add_connector"
    ),
    "support.connector-profile.create": (
        "mammoth_cli.commands.support:support_connector_profile_create"
    ),
    "support.connector-profile.delete": (
        "mammoth_cli.commands.support:support_connector_profile_delete"
    ),
    "support.connector-profile.list": "mammoth_cli.commands.support:support_connector_profile_list",
    "support.connector-profile.update": (
        "mammoth_cli.commands.support:support_connector_profile_update"
    ),
    "support.feature.create": "mammoth_cli.commands.support:support_feature_create",
    "support.feature.delete": "mammoth_cli.commands.support:support_feature_delete",
    "support.feature.list": "mammoth_cli.commands.support:support_feature_list",
    "support.feature.update": "mammoth_cli.commands.support:support_feature_update",
    "support.feature-profile.add-feature": (
        "mammoth_cli.commands.support:support_feature_profile_add_feature"
    ),
    "support.feature-profile.create": "mammoth_cli.commands.support:support_feature_profile_create",
    "support.feature-profile.delete": "mammoth_cli.commands.support:support_feature_profile_delete",
    "support.feature-profile.list": "mammoth_cli.commands.support:support_feature_profile_list",
    "support.feature-profile.update": "mammoth_cli.commands.support:support_feature_profile_update",
    "support.ownership.transfer": "mammoth_cli.commands.support:support_ownership_transfer",
    "support.plan.archive": "mammoth_cli.commands.support:support_plan_archive",
    "support.plan.unarchive": "mammoth_cli.commands.support:support_plan_unarchive",
    "support.plan.storage-option.list": (
        "mammoth_cli.commands.support:support_plan_storage_option_list"
    ),
    "support.plan.storage-option.create": (
        "mammoth_cli.commands.support:support_plan_storage_option_create"
    ),
    "support.plan.storage-option.update": (
        "mammoth_cli.commands.support:support_plan_storage_option_update"
    ),
    "support.plan.storage-option.archive": (
        "mammoth_cli.commands.support:support_plan_storage_option_archive"
    ),
    "support.template.list": "mammoth_cli.commands.support:support_template_list",
    "support.template.edit": "mammoth_cli.commands.support:support_template_edit",
    "support.template.data-preview": "mammoth_cli.commands.support:support_template_data_preview",
    "support.template.canvas": "mammoth_cli.commands.support:support_template_canvas",
    "support.template.publish": "mammoth_cli.commands.support:support_template_publish",
    "support.template.unpublish": "mammoth_cli.commands.support:support_template_unpublish",
    "support.template.retire": "mammoth_cli.commands.support:support_template_retire",
    "support.template.inspect": "mammoth_cli.commands.support:support_template_inspect",
    "support.template.import": "mammoth_cli.commands.support:support_template_import",
    "support.template.thumbnail.set": "mammoth_cli.commands.support:support_template_thumbnail_set",
    "support.template.thumbnail.clear": (
        "mammoth_cli.commands.support:support_template_thumbnail_clear"
    ),
    "support.template.discard": "mammoth_cli.commands.support:support_template_discard",
    "support.template.snapshots": "mammoth_cli.commands.support:support_template_snapshots",
    "support.template.audit": "mammoth_cli.commands.support:support_template_audit",
    "support.template.export": "mammoth_cli.commands.support:support_template_export",
    "support.template.export-dashboard": (
        "mammoth_cli.commands.support:support_template_export_dashboard"
    ),
    "support.plan.chargebee-list": "mammoth_cli.commands.support:support_plan_chargebee_list",
    "support.plan.create": "mammoth_cli.commands.support:support_plan_create",
    "support.plan.delete": "mammoth_cli.commands.support:support_plan_delete",
    "support.plan.get": "mammoth_cli.commands.support:support_plan_get",
    "support.plan.list": "mammoth_cli.commands.support:support_plan_list",
    "support.plan.self-serve-list": "mammoth_cli.commands.support:support_plan_self_serve_list",
    "support.plan.update": "mammoth_cli.commands.support:support_plan_update",
    "support.plan.update-storage-tiers": (
        "mammoth_cli.commands.support:support_plan_update_storage_tiers"
    ),
    "support.subscription.create": "mammoth_cli.commands.support:support_subscription_create",
    "support.subscription.get": "mammoth_cli.commands.support:support_subscription_get",
    "support.subscription.update": "mammoth_cli.commands.support:support_subscription_update",
    "support.user.list-all": "mammoth_cli.commands.support:support_user_list_all",
    "support.user.register": "mammoth_cli.commands.support:support_user_register",
    "support.user.update": "mammoth_cli.commands.support:support_user_update",
    "support.workspace.create": "mammoth_cli.commands.support:support_workspace_create",
    "support.workspace.delete": "mammoth_cli.commands.support:support_workspace_delete",
    "support.workspace.get": "mammoth_cli.commands.support:support_workspace_get",
    "support.workspace.list": "mammoth_cli.commands.support:support_workspace_list",
    "support.workspace.restore-access": (
        "mammoth_cli.commands.support:support_workspace_restore_access"
    ),
    "support.workspace.suspend-access": (
        "mammoth_cli.commands.support:support_workspace_suspend_access"
    ),
    "support.workspace.update": "mammoth_cli.commands.support:support_workspace_update",
    "support.workspace.user.add": "mammoth_cli.commands.support:support_workspace_user_add",
    "support.workspace.user.list": "mammoth_cli.commands.support:support_workspace_user_list",
    "support.workspace.user.remove": "mammoth_cli.commands.support:support_workspace_user_remove",
    "support.workspace.user.transfer": (
        "mammoth_cli.commands.support:support_workspace_user_transfer"
    ),
    "view.list": "mammoth_cli.commands.view:view_list",
    "view.bulk-delete": "mammoth_cli.commands.view:view_bulk_delete",
    "view.active-user.list": "mammoth_cli.commands.view:view_active_user_list",
    "view.active-user.mark": "mammoth_cli.commands.view:view_active_user_mark",
    "view.parameter-context": "mammoth_cli.commands.view:view_parameter_context",
    "view.preview": "mammoth_cli.commands.view:view_preview",
    "view.restore": "mammoth_cli.commands.view:view_restore",
    "view.trash": "mammoth_cli.commands.view:view_trash",
    "view.impact": "mammoth_cli.commands.view:view_impact",
    "view.analyze": "mammoth_cli.commands.view:view_analyze",
    "view.optimize": "mammoth_cli.commands.view:view_optimize",
    "view.compare": "mammoth_cli.commands.view:view_compare",
    "view.update": "mammoth_cli.commands.view:view_update",
    "view.explore-panel.get": "mammoth_cli.commands.view:view_explore_panel_get",
    "view.explore-panel.set": "mammoth_cli.commands.view:view_explore_panel_set",
    "view.explore-panel.edit": "mammoth_cli.commands.view_explore:view_explore_panel_edit",
    "view.explore-panel.add-to-dashboard": (
        "mammoth_cli.commands.view_explore:view_explore_panel_add_to_dashboard"
    ),
    "view.data.get": "mammoth_cli.commands.view:view_data_get",
    "view.data.query": "mammoth_cli.commands.view:view_data_query",
    "view.data.aggregate": "mammoth_cli.commands.view:view_data_aggregate_rounded",
    "view.data.compare": "mammoth_cli.commands.view:view_data_compare",
    "view.data.explore": "mammoth_cli.commands.view:view_data_explore",
    "view.data.profile": "mammoth_cli.commands.view_profile:view_data_profile",
    "view.exportable-config.get": "mammoth_cli.commands.view:view_exportable_config_get",
    "view.exportable-config.apply": "mammoth_cli.commands.view:view_exportable_config_apply",
    "view.conditional-format.create": "mammoth_cli.commands.view:view_conditional_format_create",
    "view.conditional-format.delete-all": (
        "mammoth_cli.commands.view:view_conditional_format_delete_all"
    ),
    "view.conditional-format.list": "mammoth_cli.commands.view:view_conditional_format_list",
    "view.conditional-format.update": "mammoth_cli.commands.view:view_conditional_format_update",
    "view.checkpoint.create": "mammoth_cli.commands.view:view_checkpoint_create",
    "view.checkpoint.delete": "mammoth_cli.commands.view:view_checkpoint_delete",
    "view.checkpoint.get": "mammoth_cli.commands.view:view_checkpoint_get",
    "view.checkpoint.list": "mammoth_cli.commands.view:view_checkpoint_list",
    "view.checkpoint.update": "mammoth_cli.commands.view:view_checkpoint_update",
    "view.data-check.create": "mammoth_cli.commands.view:view_data_check_create",
    "view.data-check.delete": "mammoth_cli.commands.view:view_data_check_delete",
    "view.data-check.get": "mammoth_cli.commands.view:view_data_check_get",
    "view.data-check.list": "mammoth_cli.commands.view:view_data_check_list",
    "view.data-check.update": "mammoth_cli.commands.view:view_data_check_update",
    "view.derivative.create": "mammoth_cli.commands.view:view_derivative_create",
    "view.derivative.data": "mammoth_cli.commands.view:view_derivative_data",
    "view.derivative.delete": "mammoth_cli.commands.view:view_derivative_delete",
    "view.derivative.list": "mammoth_cli.commands.view:view_derivative_list",
    "view.derivative.update": "mammoth_cli.commands.view:view_derivative_update",
    "view.version.apply": "mammoth_cli.commands.view:view_version_apply",
    "view.version.delete": "mammoth_cli.commands.view:view_version_delete",
    "view.version.get": "mammoth_cli.commands.view:view_version_get",
    "view.version.list": "mammoth_cli.commands.view:view_version_list",
    "view.version.update": "mammoth_cli.commands.view:view_version_update",
    "view.ai.generate-data": "mammoth_cli.commands.view:view_ai_generate_data",
    "view.ai.generation-info": "mammoth_cli.commands.view:view_ai_generation_info",
    "view.ai.profile": "mammoth_cli.commands.view:view_ai_profile",
    "view.draft.command": "mammoth_cli.commands.view:view_draft_command",
    "view.pipeline.edit": "mammoth_cli.commands.view:view_pipeline_edit",
    "view.pipeline.get": "mammoth_cli.commands.view:view_pipeline_get",
    "view.pipeline.items": "mammoth_cli.commands.view:view_pipeline_items",
    "view.pipeline.items-all": "mammoth_cli.commands.view:view_pipeline_items_all",
    "view.pipeline.rerun": "mammoth_cli.commands.view:view_pipeline_rerun",
    "view.pipeline.wait": "mammoth_cli.commands.view:view_pipeline_wait",
    "view.task.add": "mammoth_cli.commands.view:view_task_add",
    "view.task.delete": "mammoth_cli.commands.view:view_task_delete",
    "view.task.get": "mammoth_cli.commands.view:view_task_get",
    "view.task.list": "mammoth_cli.commands.view:view_task_list",
    "view.task.preview": "mammoth_cli.commands.view:view_task_preview",
    "view.task.update": "mammoth_cli.commands.view:view_task_update",
    "view.export.create": "mammoth_cli.commands.view:view_export_create",
    "view.export.csv": "mammoth_cli.commands.view:view_export_csv",
    "view.export.delete": "mammoth_cli.commands.view:view_export_delete",
    "view.export.get": "mammoth_cli.commands.view:view_export_get",
    "view.export.list": "mammoth_cli.commands.view:view_export_list",
    "view.export.publish-db": "mammoth_cli.commands.view:view_export_publish_db",
    "view.export.publish-db-update": "mammoth_cli.commands.view:view_export_publish_db_update",
    "view.export.update": "mammoth_cli.commands.view:view_export_update",
    "view.export.dataset": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.managed-s3": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.live-link": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.azure-blob": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.bigquery": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.elasticsearch": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.email": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.ftp": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.mssql": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.mysql": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.onedrive": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.postgres": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.powerbi": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.redshift": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.rest": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.sftp": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.sharepoint": "mammoth_cli.commands.view:view_export_specialized",
    "view.export.tableau": "mammoth_cli.commands.view:view_export_specialized",
    "view.create": "mammoth_cli.commands.view_ops:view_create",
    "view.variants.create": "mammoth_cli.commands.view_ops:view_variants_create",
    "view.get": "mammoth_cli.commands.view_ops:view_get",
    "view.delete": "mammoth_cli.commands.view_ops:view_delete",
    "view.draft.enter": "mammoth_cli.commands.view_ops:view_draft_enter",
    "view.draft.status": "mammoth_cli.commands.view_ops:view_draft_status",
    "view.draft.submit": "mammoth_cli.commands.view_ops:view_draft_submit",
    "view.draft.discard": "mammoth_cli.commands.view_ops:view_draft_discard",
    "view.draft.auto-run": "mammoth_cli.commands.view_ops:view_draft_auto_run",
    "view.transform.add-column": "mammoth_cli.commands.view_ops:view_transform_add_column",
    "view.transform.add-sql": "mammoth_cli.commands.view_ops:view_transform_add_sql",
    "view.transform.ai": "mammoth_cli.commands.view_ops:view_transform_ai",
    "view.transform.bulk-replace": "mammoth_cli.commands.view_ops:view_transform_bulk_replace",
    "view.transform.combine-columns": (
        "mammoth_cli.commands.view_ops:view_transform_combine_columns"
    ),
    "view.transform.convert-type": "mammoth_cli.commands.view_ops:view_transform_convert_type",
    "view.transform.copy-columns": "mammoth_cli.commands.view_ops:view_transform_copy_columns",
    "view.transform.crosstab": "mammoth_cli.commands.view_ops:view_transform_crosstab",
    "view.transform.date-diff": "mammoth_cli.commands.view_ops:view_transform_date_diff",
    "view.transform.delete-columns": "mammoth_cli.commands.view_ops:view_transform_delete_columns",
    "view.transform.discard-duplicates": (
        "mammoth_cli.commands.view_ops:view_transform_discard_duplicates"
    ),
    "view.transform.extract-date": "mammoth_cli.commands.view_ops:view_transform_extract_date",
    "view.transform.fill-missing": "mammoth_cli.commands.view_ops:view_transform_fill_missing",
    "view.transform.filter": "mammoth_cli.commands.view_ops:view_transform_filter",
    "view.transform.generate-sql": "mammoth_cli.commands.view_ops:view_transform_generate_sql",
    "view.transform.increment-date": "mammoth_cli.commands.view_ops:view_transform_increment_date",
    "view.transform.join": "mammoth_cli.commands.view_ops:view_transform_join",
    "view.transform.json-extract": "mammoth_cli.commands.view_ops:view_transform_json_extract",
    "view.transform.limit-rows": "mammoth_cli.commands.view_ops:view_transform_limit_rows",
    "view.transform.lookup": "mammoth_cli.commands.view_ops:view_transform_lookup",
    "view.transform.math": "mammoth_cli.commands.view_ops:view_transform_math",
    "view.transform.pivot": "mammoth_cli.commands.view_ops:view_transform_pivot",
    "view.transform.rename-columns": "mammoth_cli.commands.view_ops:view_transform_rename_columns",
    "view.transform.replace": "mammoth_cli.commands.view_ops:view_transform_replace",
    "view.transform.set-values": "mammoth_cli.commands.view_ops:view_transform_set_values",
    "view.transform.small-large": "mammoth_cli.commands.view_ops:view_transform_small_large",
    "view.transform.sort": "mammoth_cli.commands.view_ops:view_transform_sort",
    "view.transform.split": "mammoth_cli.commands.view_ops:view_transform_split",
    "view.transform.substring": "mammoth_cli.commands.view_ops:view_transform_substring",
    "view.transform.first-name": "mammoth_cli.commands.view_ops:view_transform_first_name",
    "view.transform.update-column": "mammoth_cli.commands.view_ops:view_transform_update_column",
    "view.transform.text": "mammoth_cli.commands.view_ops:view_transform_text",
    "view.transform.unnest": "mammoth_cli.commands.view_ops:view_transform_unnest",
    "view.transform.window": "mammoth_cli.commands.view_ops:view_transform_window",
}

# Dashboard operations generated from the reviewed OpenAPI inventory share one
# manifest-driven handler. Existing authored handlers remain authoritative, so
# only the dashboard commands that have none are added. Matching on the SDK
# symbol prefix (rather than importing the generated method list) keeps the
# generated dashboard models off the startup import path.
_DASHBOARD_SDK_PREFIX = "mammoth.api.dashboards.DashboardsAPI."
for _record in load_commands():
    if str(_record.get("sdk_symbol", "")).startswith(_DASHBOARD_SDK_PREFIX):
        _TARGETS.setdefault(
            str(_record["command_id"]), "mammoth_cli.commands.dashboard:generated_dashboard"
        )

#: Command id -> handler, imported from its command module on first use.
HANDLERS: Mapping[str, Handler] = LazyTable(_TARGETS)
