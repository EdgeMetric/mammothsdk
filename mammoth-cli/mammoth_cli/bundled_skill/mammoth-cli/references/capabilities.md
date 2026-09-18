# What is proven on release

Generated from `docs/release-capability-matrix.json`; do not edit by hand.
455 API operations have a CLI command. 193 were exercised successfully on release, 2 are not supported there, and the rest are untried. Untried is not broken: discover the contract with `mammoth schema get COMMAND_ID --output json --no-input`, run it, and treat the structured error envelope as the answer.

Status meanings:

- **verified**: one bounded live run on release returned a success envelope (single path; variants and error paths are usually untested).
- **not supported**: the backend refuses the route on release; the note says why and what to use instead.
- **observed blocker**: the last run hit an error; the note quotes it. Re-check before relying on the route, and do not retry the same input.
- **CLI defect fixed, untried since**: the failure was on the CLI side and this release repairs it; nobody has re-run the route yet.
- Commands not listed under a family are untried.

The typed `view transform *` commands all submit through `view.task.add`; its row below carries the transformations proven end to end (filter, fill-missing, join, pivot with an exported summary). A transformation not named there has the same untried status as any other command.

## Coverage by family

| Family | Commands | Verified | Not supported | Untried |
|---|---|---|---|---|
| `dashboard` | 104 | 80 | 2 | 22 |
| `view` | 62 | 43 | 0 | 19 |
| `support` | 45 | 0 | 0 | 45 |
| `billing` | 23 | 0 | 0 | 23 |
| `connector` | 22 | 2 | 0 | 20 |
| `workspace` | 19 | 6 | 0 | 13 |
| `project` | 17 | 11 | 0 | 6 |
| `workflow` | 16 | 5 | 0 | 11 |
| `dataset` | 15 | 10 | 0 | 5 |
| `parameter` | 14 | 2 | 0 | 12 |
| `data-app` | 12 | 1 | 0 | 11 |
| `folder` | 8 | 7 | 0 | 1 |
| `snippet` | 8 | 1 | 0 | 7 |
| `automation` | 7 | 1 | 0 | 6 |
| `user` | 7 | 2 | 0 | 5 |
| `webhook` | 7 | 0 | 0 | 7 |
| `addon` | 6 | 0 | 0 | 6 |
| `batch` | 6 | 4 | 0 | 2 |
| `file` | 6 | 5 | 0 | 1 |
| `agent` | 5 | 1 | 0 | 4 |
| `ai` | 5 | 1 | 0 | 4 |
| `annotation` | 5 | 1 | 0 | 4 |
| `client-app` | 5 | 0 | 0 | 5 |
| `notification` | 5 | 1 | 0 | 4 |
| `schedule` | 5 | 0 | 0 | 5 |
| `template` | 5 | 0 | 0 | 5 |
| `browse` | 4 | 2 | 0 | 2 |
| `external-key` | 4 | 0 | 0 | 4 |
| `trash` | 3 | 3 | 0 | 0 |
| `activity` | 2 | 1 | 0 | 1 |
| `job` | 2 | 2 | 0 | 0 |
| `report` | 1 | 1 | 0 | 0 |

## `activity`

Verified: `activity.list`

| Command | State | Note |
|---|---|---|
| `activity.export` | observed blocker | server_error: see sweep report |

## `agent`

Verified: `agent.session.list`

## `ai`

Verified: `ai.condition.generate`

| Command | State | Note |
|---|---|---|
| `ai.retention.condition` | observed blocker | backend_error: HTTP 403 4PERM001 PERMISSION_UNDEFINED: "Permissions have not been set correctly for this API, please contact Mammoth Help to report this error" on POST /workspaces/ |
| `ai.expression.generate` | CLI defect fixed, untried since | 2.0.15 (SDK-side argument rejections (e.g. mode not math/metric) surface as invalid_arguments with the SDK message instead of an empty api_error) |
| `ai.sql.generate` | CLI defect fixed, untried since | 2.0.15 (dataset_id is required and sent as the query parameter |
| `ai.suggestion.list` | CLI defect fixed, untried since | 2.0.15 (command takes the release UnifiedPromptSpec (suggestion_type + params, optional dataset_id/dataview_id)) |

## `annotation`

Verified: `annotation.list`

## `automation`

Verified: `automation.list`

## `batch`

Verified: `batch.bulk-delete`, `batch.delete`, `batch.get`, `batch.list`

| Command | State | Note |
|---|---|---|
| `batch.create` | CLI defect fixed, untried since | 2.0.15 (mapping is sent as the release list of {source_c_name,destination_c_name} items and body keys match BatchesPostRequest) |
| `batch.update` | CLI defect fixed, untried since | 2.0.15 (SDK-side argument rejections (patch ops must be replace/remove) surface as invalid_arguments with the SDK message instead of an empty api_error) |

## `browse`

Verified: `browse.project`, `browse.workspace`

| Command | State | Note |
|---|---|---|
| `browse.folder` | observed blocker | cli_error: rejects folder id 0 although folder.root reports id 0 as the root |
| `browse.root` | observed blocker | server_error: see sweep report |

## `connector`

Verified: `connector.active`, `connector.list`

| Command | State | Note |
|---|---|---|
| `connector.ai.session.list` | observed blocker | cli_error: backend returned HTTP 200 but the CLI raised api_error (envelope mismatch) |
| `connector.connection.list` | observed blocker | server_error: see sweep report |
| `connector.get` | observed blocker | validation_error: HTTP 400 'Invalid connector key' for a key returned by connector.list |
| `connector.query.status` | observed blocker | blocked_missing_fixture: No real connector connection exists in workspace 4 (connector list shows all is_added:false; connector active returns []) and creating one requires externa |
| `connector.query.generate` | CLI defect fixed, untried since | 2.0.15 (input field is query (release Intent body) instead of prompt) |

## `dashboard`

Verified: `dashboard.action`, `dashboard.analytics`, `dashboard.archive`, `dashboard.cancel-generation`, `dashboard.canvas.get`, `dashboard.canvas.restore`, `dashboard.canvas.save`, `dashboard.chat.edit`, `dashboard.chat.history`, `dashboard.context.create`, `dashboard.context.delete`, `dashboard.context.extract`, `dashboard.context.list`, `dashboard.context.update`, `dashboard.create-blank`, `dashboard.delete`, `dashboard.descriptor-data`, `dashboard.duplicate`, `dashboard.exemplar.extract`, `dashboard.figure-intent`, `dashboard.get`, `dashboard.get-by-url`, `dashboard.job-by-url`, `dashboard.list`, `dashboard.page.plan`, `dashboard.pages.add`, `dashboard.published.canvas`, `dashboard.published.share-page`, `dashboard.qa.ask`, `dashboard.qa.comment.create`, `dashboard.qa.comment.delete`, `dashboard.qa.feedback`, `dashboard.qa.session.create`, `dashboard.qa.session.delete`, `dashboard.qa.session.fork`, `dashboard.qa.session.get`, `dashboard.qa.session.list`, `dashboard.qa.session.rename`, `dashboard.qa.session.set-visibility`, `dashboard.qa.settings.get`, `dashboard.qa.settings.set`, `dashboard.query`, `dashboard.restore`, `dashboard.rls.assignment.list`, `dashboard.rls.assignment.set`, `dashboard.rls.column.list`, `dashboard.rls.value.list`, `dashboard.share`, `dashboard.signature.create`, `dashboard.signature.delete`, `dashboard.signature.list`, `dashboard.signature.update`, `dashboard.style.custom.create`, `dashboard.style.custom.delete`, `dashboard.style.custom.list`, `dashboard.style.custom.update`, `dashboard.style.default.get`, `dashboard.style.default.set`, `dashboard.style.derive`, `dashboard.style.extract-brand`, `dashboard.style.preset.list`, `dashboard.style.token.list`, `dashboard.suggestion.list`, `dashboard.swap-data`, `dashboard.tags.delete`, `dashboard.tags.list`, `dashboard.tags.merge`, `dashboard.tags.rename`, `dashboard.tags.set`, `dashboard.template.apply`, `dashboard.template.fit`, `dashboard.template.get`, `dashboard.template.list`, `dashboard.template.preview`, `dashboard.template.resolve-mapping`, `dashboard.templates.pending`, `dashboard.trash`, `dashboard.update`, `dashboard.v3.generate`, `dashboard.video-state`

| Command | State | Note |
|---|---|---|
| `dashboard.create` | not supported | Not supported on release: backend returns HTTP 409 4DASH012 DASHBOARD_LEGACY_CREATION_RETIRED (legacy dashboard creation retired). Use dashboard.create-blank or dashboard.v3.generate. Dashboard sweep 2026-09-18, CLI 2.0.12. |
| `dashboard.pdf.export` | not supported | Not supported from the CLI on release: backend HTTP 400 4GENR001 requires params.data to be the browser-hydrated DashboardData map and states it cannot rebuild it from stored descriptors (dashboard sweep and Haiku e2e, 2026-09-18). The route works only with a client render pass. |
| `dashboard.data.draft` | observed blocker | blocked_missing_fixture: Dashboard 56 (create-blank/v3 engine) has no widgets in its canvas and getDraftData rejects with backend_code 4DASH004 DASHBOARD_WRONG_ENGINE: "This dashbo |
| `dashboard.data.published` | observed blocker | blocked_missing_fixture: Same as dashboard.data.draft: backend_code 4DASH004 DASHBOARD_WRONG_ENGINE on /dashboards/56/getPublishData |
| `dashboard.published-data-by-url` | observed blocker | blocked_missing_fixture: backend_code 4DASH004 DASHBOARD_WRONG_ENGINE on /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/getPublishData, same class of blocker as widget-data: this v3 dashbo |
| `dashboard.published.pdf-artifact` | observed blocker | blocked_missing_fixture: Same as dashboard.pdf-artifact: no real pdf job available; used job 313 (descriptor-data job) as the only real job id in hand and got backend_code 4DASH001 |
| `dashboard.published.pdf.export` | observed blocker | backend_error: Got backend_code 4PERM002 PERMISSION_ERROR, "User lacks permission to perform given action" on POST /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/pdf (403), envelope: {"err |
| `dashboard.published.video.export` | observed blocker | backend_error: backend_code 4PERM002 PERMISSION_ERROR, "User lacks permission to perform given action" on POST /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/video (403) |
| `dashboard.source.list` | observed blocker | blocker; still broken, not one of the 11 CLI-fixed commands |
| `dashboard.template.create` | observed blocker | backend_error: Both attempts (2/2) returned the same outcome_unknown envelope: {"error":{"code":"outcome_unknown","details":{"endpoint":"/dashboards/v3/templates","method":"POST"," |
| `dashboard.template.delete` | observed blocker | blocked_missing_fixture: dashboard.template.create never produced an owned template (HTTP 500 both attempts, reconciled as not-committed via template list) |
| `dashboard.templates.use` | observed blocker | skipped_out_of_scope: BRIEF instructs running templates.use "on that template" (i.e |
| `dashboard.video.export` | observed blocker | backend_error: After publishing dashboard 56 (dashboard.share public + dashboard.action publish-presentation), the previously-documented "publish the dashboard before exporting a v |
| `dashboard.widget-data` | observed blocker | blocked_missing_fixture: backend_code 4DASH004 DASHBOARD_WRONG_ENGINE, "This dashboard uses a different rendering engine -- use the matching endpoints", on POST /dashboards/56/widg |
| `dashboard.widget-data-by-url` | observed blocker | blocked_missing_fixture: Same backend_code 4DASH004 DASHBOARD_WRONG_ENGINE, on POST /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/widgets/data |
| `dashboard.og-card` | CLI defect fixed, untried since | SDK 0.7.5 returns a described binary body |
| `dashboard.published.data` | CLI defect fixed, untried since | 2.0.15 (published-dashboard jobs are polled through the URL-scoped job route) |

## `data-app`

Verified: `data-app.list`

## `dataset`

Verified: `dataset.batch-data`, `dataset.create`, `dataset.data`, `dataset.delete`, `dataset.file-settings.get`, `dataset.file-settings.update`, `dataset.get`, `dataset.list`, `dataset.restore`, `dataset.trash`

| Command | State | Note |
|---|---|---|
| `dataset.bulk-update` | observed blocker | cli_error: Schema preconditions already flag this as BLOCKED[B07 DATASET_PATCH_UNTYPED]; reserved, not registered -- confirmed live |
| `dataset.create-from-pdf` | observed blocker | backend_error: Attempt 1 (file_name only) -> HTTP 400 4DSET053 MUST_PROVIDE_TABLE_LIST_OR_PREVIEW: "Either 'table_list' or 'is_preview_needed' must be provided." (clear, actionable |
| `dataset.bulk-delete` | CLI defect fixed, untried since | 2.0.15 (dataset_ids is required, confirmation names the ids, and ids are sent as the ids query parameter) |
| `dataset.file-settings.undo` | CLI defect fixed, untried since | 2.0.15 (2xx non-object bodies are reported as success instead of outcome_unknown) |

## `external-key`

| Command | State | Note |
|---|---|---|
| `external-key.list` | observed blocker | cli_error: not_authenticated although the same session authenticated elsewhere |

## `file`

Verified: `file.bulk-delete`, `file.delete`, `file.get`, `file.list`, `file.upload`

| Command | State | Note |
|---|---|---|
| `file.update` | observed blocker | backend_error: CLI accepted the typed patch and submitted job 314 (handle_file on /workspaces/4/projects/21/files/50), then correctly reported timeout after 60s with recovery_comma |

## `folder`

Verified: `folder.bulk-delete`, `folder.create`, `folder.delete`, `folder.get`, `folder.list`, `folder.trash`, `folder.update`

| Command | State | Note |
|---|---|---|
| `folder.move` | CLI defect fixed, untried since | 2.0.15 (SDK now sends {patch:[{op:move,from:[ids],path:destination/root}]}) |

## `job`

Verified: `job.get`, `job.get-many`

## `notification`

Verified: `notification.list`

## `parameter`

Verified: `parameter.group.list`, `parameter.list`

## `project`

Verified: `project.bulk-delete`, `project.checkpoint.list`, `project.create`, `project.data-check.list`, `project.list`, `project.pending-changes`, `project.publish-credentials`, `project.resource-dependencies`, `project.resource-dependencies.update`, `project.resource-status`, `project.sample-flow`

| Command | State | Note |
|---|---|---|
| `project.user.update` | observed blocker | backend_error: HTTP 400 4PROJ010 ROLE_ALREADY_ASSIGNED: "Role already assigned to the user" -- targeted our own user (id 5, already project_admin as project owner) |
| `project.bulk-update` | CLI defect fixed, untried since | 2.0.15 (body must be a ProjectsPatch naming project_id in every value item and the confirmation lists those projects) |
| `project.delete` | CLI defect fixed, untried since | 2.0.15 (2xx non-object bodies such as 202 Accepted are reported as success instead of outcome_unknown) |
| `project.update` | CLI defect fixed, untried since | 2.0.15 (SDK now sends the release ProjectPatch {patches:[{op:replace,path:name/properties,...}]} body) |
| `project.user.add` | CLI defect fixed, untried since | 2.0.15 (SDK now sends {users:[{user_id,role}]} with numeric user ids) |

## `report`

Verified: `report.list`

## `schedule`

| Command | State | Note |
|---|---|---|
| `schedule.list` | observed blocker | validation_error: HTTP 400 with message 'Not implemented' |

## `snippet`

Verified: `snippet.list`

## `template`

| Command | State | Note |
|---|---|---|
| `template.list` | observed blocker | cli_error: backend returned HTTP 200 but the CLI raised api_error (envelope mismatch) |

## `trash`

Verified: `trash.add`, `trash.list`, `trash.restore`

## `user`

Verified: `user.get`, `user.preference.get`

| Command | State | Note |
|---|---|---|
| `user.preference.update` | CLI defect fixed, untried since | 2.0.15 (command takes the release {patch:[...]} list instead of free keyword fields) |

## `view`

Verified: `view.active-user.list`, `view.active-user.mark`, `view.ai.generate-data`, `view.bulk-delete`, `view.checkpoint.create`, `view.checkpoint.list`, `view.conditional-format.list`, `view.conditional-format.update`, `view.create`, `view.data-check.create`, `view.data-check.get`, `view.data-check.list`, `view.data.get`, `view.data.query`, `view.delete`, `view.derivative.create`, `view.derivative.list`, `view.draft.command`, `view.export.delete`, `view.export.get`, `view.export.list`, `view.export.publish-db`, `view.export.update`, `view.exportable-config.get`, `view.get`, `view.list`, `view.parameter-context`, `view.pipeline.get`, `view.pipeline.items`, `view.pipeline.rerun`, `view.preview`, `view.restore`, `view.task.add`, `view.task.delete`, `view.task.get`, `view.task.list`, `view.trash`, `view.version.apply`, `view.version.delete`, `view.version.get`, `view.version.list`, `view.version.update`

| Command | State | Note |
|---|---|---|
| `view.ai.generation-info` | observed blocker | backend_error: HTTP 400 5GENR011 NOT_IMPLEMENTED: "Not implemented" -- matches known capabilities.md observed blocker for this route (backend-side, not CLI) |
| `view.checkpoint.get` | observed blocker | backend_error: HTTP 500 on GET /workspaces/4/projects/21/datasets/48/dataviews/73/pipeline/checkpoints/1 with empty response_body:{}, reproduced twice (2s apart) right after checkp |
| `view.conditional-format.create` | observed blocker | cli_error: Skill doc (view.md) claims this route is 'fail-closed and must not dispatch a request' (BLOCKED B09 DATAVIEW_INPUT_UNTYPED) -- but live it DOES dispatch: HTTP 400 4GENR0 |
| `view.data-check.update` | observed blocker | backend_error: PATCH .../pipeline/data-checks/1 -> HTTP 500, empty response_body, CLI correctly reported outcome_unknown (exit 7) rather than a false success |
| `view.derivative.data` | observed blocker | backend_error: HTTP 500 on POST .../dataviews/73/derivatives/2/data, empty response_body |
| `view.export.create` | observed blocker | cli_error: Both attempts return exit 0 with a job accepted (334, then 335 after adding target_properties.destination:local), but the job itself always fails: job get shows status:e |
| `view.exportable-config.apply` | observed blocker | cli_error: Schema's own runnable_example (config:{tasks:[]}) fails: job_failed, response:{reason:(quote)dependencies(quote)} -- a raw Python KeyError, not a structured validation m |
| `view.task.preview` | observed blocker | cli_error: Schema's own runnable_example (COPY:{}) fails: HTTP 400 5GENR010 UNKNOWN_ERROR "Unknown error occurred |
| `view.ai.profile` | CLI defect fixed, untried since | 2.0.15 (SDK sends the release ProfileGenerationSpec {params:{action}} body (action defaults to insights)) |
| `view.checkpoint.delete` | CLI defect fixed, untried since | 2.0.15 (2xx non-object bodies such as 202 Accepted are reported as success instead of outcome_unknown) |
| `view.checkpoint.update` | CLI defect fixed, untried since | 2.0.15 (example now carries value:null as the backend requires |
| `view.conditional-format.delete-all` | CLI defect fixed, untried since | 2.0.15 (rule_id is required and sent as the query parameter) |
| `view.data-check.delete` | CLI defect fixed, untried since | 2.0.15 (2xx non-object bodies such as 202 Accepted are reported as success instead of outcome_unknown) |
| `view.derivative.delete` | CLI defect fixed, untried since | 2.0.15 (2xx non-object bodies such as 202 Accepted are reported as success instead of outcome_unknown) |
| `view.derivative.update` | CLI defect fixed, untried since | 2.0.15 (2xx non-object bodies such as 202 Accepted are reported as success instead of outcome_unknown) |
| `view.export.publish-db-update` | CLI defect fixed, untried since | 2.0.15 (example now shows the only accepted patch path (credentials -> postgres/bigquery)) |
| `view.pipeline.edit` | CLI defect fixed, untried since | 2.0.15 (example now shows a valid patch (path auto_run with a bool value) |
| `view.task.update` | CLI defect fixed, untried since | 2.0.15 (SDK now sends {patches:[{op:replace,path:params,value:task_spec}]} (or caller-supplied patches)) |

## `webhook`

| Command | State | Note |
|---|---|---|
| `webhook.list` | observed blocker | cli_error: api_error with no HTTP status recorded |

## `workflow`

Verified: `workflow.graph`, `workflow.list`, `workflow.workspace-datasets`, `workflow.workspace-exports`, `workflow.workspace-sources`

## `workspace`

Verified: `workspace.app-usage`, `workspace.get`, `workspace.list`, `workspace.segment.list`, `workspace.storage-breakdown`, `workspace.user.list`

| Command | State | Note |
|---|---|---|
| `workspace.segment.update` | CLI defect fixed, untried since | 2.0.15 (2xx non-object bodies are reported as success instead of outcome_unknown |

Evidence version: CLI mammoth-cli 1.1.11; mammoth-io 0.7.1. Details: `docs/capability-evidence/` in the repository.
