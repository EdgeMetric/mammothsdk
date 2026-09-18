# What is proven on release

Generated from `docs/release-capability-matrix.json`; do not edit by hand.
455 API operations have a CLI command. 225 were exercised successfully on release, 2 are not supported there, and the rest are untried. Untried is not broken: discover the contract with `mammoth schema get COMMAND_ID --output json --no-input`, run it, and treat the structured error envelope as the answer.

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
| `dashboard` | 104 | 81 | 2 | 21 |
| `view` | 62 | 50 | 0 | 12 |
| `support` | 45 | 9 | 0 | 36 |
| `billing` | 23 | 4 | 0 | 19 |
| `connector` | 22 | 2 | 0 | 20 |
| `workspace` | 19 | 7 | 0 | 12 |
| `project` | 17 | 15 | 0 | 2 |
| `workflow` | 16 | 5 | 0 | 11 |
| `dataset` | 15 | 12 | 0 | 3 |
| `parameter` | 14 | 2 | 0 | 12 |
| `data-app` | 12 | 1 | 0 | 11 |
| `folder` | 8 | 8 | 0 | 0 |
| `snippet` | 8 | 1 | 0 | 7 |
| `automation` | 7 | 1 | 0 | 6 |
| `user` | 7 | 3 | 0 | 4 |
| `webhook` | 7 | 0 | 0 | 7 |
| `addon` | 6 | 0 | 0 | 6 |
| `batch` | 6 | 5 | 0 | 1 |
| `file` | 6 | 5 | 0 | 1 |
| `agent` | 5 | 1 | 0 | 4 |
| `ai` | 5 | 2 | 0 | 3 |
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

Verified: `ai.condition.generate`, `ai.expression.generate`

| Command | State | Note |
|---|---|---|
| `ai.retention.condition` | observed blocker | permission: POST /workspaces/4/projects/24/sql_generation/retention_policy -> HTTP 403 4PERM001 PERMISSION_UNDEFINED, error_object {code:76,message:'Permissions have not been set c |
| `ai.sql.generate` | observed blocker | backend_error: Fix held (dataset_id required and sent as query param -- request reached backend and got a domain-specific conflict, not an empty api_error) |
| `ai.suggestion.list` | observed blocker | backend_error: Fix held: release UnifiedPromptSpec (suggestion_type + params, optional dataset_id/dataview_id) shape accepted and dispatched to a real job (id 381), which failed fo |

## `annotation`

Verified: `annotation.list`

## `automation`

Verified: `automation.list`

## `batch`

Verified: `batch.bulk-delete`, `batch.delete`, `batch.get`, `batch.list`, `batch.update`

| Command | State | Note |
|---|---|---|
| `batch.create` | CLI defect fixed, untried since | 2.0.16 (mapping items carry expected_destination_c_type (TEXT/NUMERIC/DATE) |

## `billing`

Verified: `billing.stripe.history`, `billing.stripe.payment-method.list`, `billing.stripe.status`, `billing.subscription.get`

| Command | State | Note |
|---|---|---|
| `billing.chargebee-plan` | observed blocker | backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 400 4SUBS014 'Chargebee plan not found for the given workspace' (workspace 4 is n |
| `billing.invoice.get` | observed blocker | blocked_missing_fixture: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: billing invoice list answered HTTP 500, so no invoice id was observed |
| `billing.invoice.list` | observed blocker | backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 500 with empty body on GET /workspaces/4/subscription_v1/invoices |
| `billing.stripe.preview-invoice` | observed blocker | backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 400 4SUBS037 'Failed to perform subscription operation' |
| `billing.stripe.upcoming-invoice` | observed blocker | backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 400 4SUBS074 'Upcoming invoice not found' (no active Stripe subscription on works |
| `billing.stripe.usage` | observed blocker | backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 400 5GENR010 UNKNOWN_ERROR 'Unknown error occurred |

## `browse`

Verified: `browse.project`, `browse.workspace`

| Command | State | Note |
|---|---|---|
| `browse.folder` | observed blocker | cli_error: rejects folder id 0 although folder.root reports id 0 as the root |
| `browse.root` | observed blocker | server_error: see sweep report |

## `client-app`

| Command | State | Note |
|---|---|---|
| `client-app.list` | observed blocker | forbidden: backend_code=4GENR012 INVALID_TOKEN_FOR_CLIENT_APPS: 'Cannot access this API with API-tokens' on GET /workspaces/4/clientapps |

## `connector`

Verified: `connector.active`, `connector.list`

| Command | State | Note |
|---|---|---|
| `connector.ai.session.list` | observed blocker | cli_error: backend returned HTTP 200 but the CLI raised api_error (envelope mismatch) |
| `connector.connection.list` | observed blocker | server_error: see sweep report |
| `connector.get` | observed blocker | validation_error: HTTP 400 'Invalid connector key' for a key returned by connector.list |
| `connector.query.generate` | observed blocker | blocked_missing_fixture: No real connector connection exists in workspace 4 (connector.list shows all is_added:false; connector.active returns []), matching the documented capabili |
| `connector.query.status` | observed blocker | blocked_missing_fixture: No real connector connection exists in workspace 4 (connector list shows all is_added:false; connector active returns []) and creating one requires externa |

## `dashboard`

Verified: `dashboard.action`, `dashboard.analytics`, `dashboard.archive`, `dashboard.cancel-generation`, `dashboard.canvas.get`, `dashboard.canvas.restore`, `dashboard.canvas.save`, `dashboard.chat.edit`, `dashboard.chat.history`, `dashboard.context.create`, `dashboard.context.delete`, `dashboard.context.extract`, `dashboard.context.list`, `dashboard.context.update`, `dashboard.create-blank`, `dashboard.delete`, `dashboard.descriptor-data`, `dashboard.duplicate`, `dashboard.exemplar.extract`, `dashboard.figure-intent`, `dashboard.get`, `dashboard.get-by-url`, `dashboard.job-by-url`, `dashboard.list`, `dashboard.og-card`, `dashboard.page.plan`, `dashboard.pages.add`, `dashboard.published.canvas`, `dashboard.published.share-page`, `dashboard.qa.ask`, `dashboard.qa.comment.create`, `dashboard.qa.comment.delete`, `dashboard.qa.feedback`, `dashboard.qa.session.create`, `dashboard.qa.session.delete`, `dashboard.qa.session.fork`, `dashboard.qa.session.get`, `dashboard.qa.session.list`, `dashboard.qa.session.rename`, `dashboard.qa.session.set-visibility`, `dashboard.qa.settings.get`, `dashboard.qa.settings.set`, `dashboard.query`, `dashboard.restore`, `dashboard.rls.assignment.list`, `dashboard.rls.assignment.set`, `dashboard.rls.column.list`, `dashboard.rls.value.list`, `dashboard.share`, `dashboard.signature.create`, `dashboard.signature.delete`, `dashboard.signature.list`, `dashboard.signature.update`, `dashboard.style.custom.create`, `dashboard.style.custom.delete`, `dashboard.style.custom.list`, `dashboard.style.custom.update`, `dashboard.style.default.get`, `dashboard.style.default.set`, `dashboard.style.derive`, `dashboard.style.extract-brand`, `dashboard.style.preset.list`, `dashboard.style.token.list`, `dashboard.suggestion.list`, `dashboard.swap-data`, `dashboard.tags.delete`, `dashboard.tags.list`, `dashboard.tags.merge`, `dashboard.tags.rename`, `dashboard.tags.set`, `dashboard.template.apply`, `dashboard.template.fit`, `dashboard.template.get`, `dashboard.template.list`, `dashboard.template.preview`, `dashboard.template.resolve-mapping`, `dashboard.templates.pending`, `dashboard.trash`, `dashboard.update`, `dashboard.v3.generate`, `dashboard.video-state`

| Command | State | Note |
|---|---|---|
| `dashboard.create` | not supported | Not supported on release: backend returns HTTP 409 4DASH012 DASHBOARD_LEGACY_CREATION_RETIRED (legacy dashboard creation retired). Use dashboard.create-blank or dashboard.v3.generate. Dashboard sweep 2026-09-18, CLI 2.0.12. |
| `dashboard.pdf.export` | not supported | Not supported from the CLI on release: backend HTTP 400 4GENR001 requires params.data to be the browser-hydrated DashboardData map and states it cannot rebuild it from stored descriptors (dashboard sweep and Haiku e2e, 2026-09-18). The route works only with a client render pass. |
| `dashboard.data.draft` | observed blocker | blocked_missing_fixture: Dashboard 56 (create-blank/v3 engine) has no widgets in its canvas and getDraftData rejects with backend_code 4DASH004 DASHBOARD_WRONG_ENGINE: "This dashbo |
| `dashboard.data.published` | observed blocker | blocked_missing_fixture: Same as dashboard.data.draft: backend_code 4DASH004 DASHBOARD_WRONG_ENGINE on /dashboards/56/getPublishData |
| `dashboard.published-data-by-url` | observed blocker | blocked_missing_fixture: backend_code 4DASH004 DASHBOARD_WRONG_ENGINE on /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/getPublishData, same class of blocker as widget-data: this v3 dashbo |
| `dashboard.published.data` | observed blocker | blocked_missing_fixture: Could not publish dashboard 59 to reach a live published state: `dashboard action 59 {action:publish-presentation}` failed twice with HTTP 500 outcome_unkn |
| `dashboard.published.pdf-artifact` | observed blocker | blocked_missing_fixture: Same as dashboard.pdf-artifact: no real pdf job available; used job 313 (descriptor-data job) as the only real job id in hand and got backend_code 4DASH001 |
| `dashboard.published.pdf.export` | observed blocker | backend_error: Got backend_code 4PERM002 PERMISSION_ERROR, "User lacks permission to perform given action" on POST /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/pdf (403), envelope: {"err |
| `dashboard.published.video.export` | observed blocker | backend_error: backend_code 4PERM002 PERMISSION_ERROR, "User lacks permission to perform given action" on POST /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/video (403) |
| `dashboard.source.list` | observed blocker | blocker; still broken, not one of the 11 CLI-fixed commands |
| `dashboard.template.create` | observed blocker | backend: POST /dashboards/v3/templates -> HTTP 500, empty response_body, request_id:null, code:outcome_unknown |
| `dashboard.template.delete` | observed blocker | blocked_missing_fixture: dashboard.template.create never produced an owned template (HTTP 500 both attempts, reconciled as not-committed via template list) |
| `dashboard.templates.use` | observed blocker | skipped_out_of_scope: BRIEF instructs running templates.use "on that template" (i.e |
| `dashboard.video.export` | observed blocker | backend_error: After publishing dashboard 56 (dashboard.share public + dashboard.action publish-presentation), the previously-documented "publish the dashboard before exporting a v |
| `dashboard.widget-data` | observed blocker | blocked_missing_fixture: backend_code 4DASH004 DASHBOARD_WRONG_ENGINE, "This dashboard uses a different rendering engine -- use the matching endpoints", on POST /dashboards/56/widg |
| `dashboard.widget-data-by-url` | observed blocker | blocked_missing_fixture: Same backend_code 4DASH004 DASHBOARD_WRONG_ENGINE, on POST /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/widgets/data |

## `data-app`

Verified: `data-app.list`

## `dataset`

Verified: `dataset.batch-data`, `dataset.bulk-delete`, `dataset.create`, `dataset.data`, `dataset.delete`, `dataset.file-settings.get`, `dataset.file-settings.undo`, `dataset.file-settings.update`, `dataset.get`, `dataset.list`, `dataset.restore`, `dataset.trash`

| Command | State | Note |
|---|---|---|
| `dataset.bulk-update` | observed blocker | cli_error: Schema preconditions already flag this as BLOCKED[B07 DATASET_PATCH_UNTYPED]; reserved, not registered -- confirmed live |
| `dataset.create-from-pdf` | observed blocker | backend: POST /workspaces/4/projects/24/datasets-from-pdf |

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

Verified: `folder.bulk-delete`, `folder.create`, `folder.delete`, `folder.get`, `folder.list`, `folder.move`, `folder.trash`, `folder.update`

## `job`

Verified: `job.get`, `job.get-many`

## `notification`

Verified: `notification.list`

## `parameter`

Verified: `parameter.group.list`, `parameter.list`

## `project`

Verified: `project.bulk-delete`, `project.bulk-update`, `project.checkpoint.list`, `project.create`, `project.data-check.list`, `project.delete`, `project.list`, `project.pending-changes`, `project.publish-credentials`, `project.resource-dependencies`, `project.resource-dependencies.update`, `project.resource-status`, `project.sample-flow`, `project.update`, `project.user.add`

| Command | State | Note |
|---|---|---|
| `project.user.update` | observed blocker | backend_error: HTTP 400 4PROJ010 ROLE_ALREADY_ASSIGNED: "Role already assigned to the user" -- targeted our own user (id 5, already project_admin as project owner) |

## `report`

Verified: `report.list`

## `schedule`

| Command | State | Note |
|---|---|---|
| `schedule.get` | observed blocker | blocked_missing_fixture: Not run: id source schedule.list failed with backend_error (5GENR011 NOT_IMPLEMENTED, HTTP 400), so no schedule_id was observed to use |
| `schedule.list` | observed blocker | backend_error: backend_code=5GENR011 NOT_IMPLEMENTED: 'Not implemented' on GET /workspaces/4/projects/3/schedules |

## `snippet`

Verified: `snippet.list`

## `support`

Verified: `support.connector-profile.list`, `support.connector.list`, `support.feature-profile.list`, `support.feature.list`, `support.plan.chargebee-list`, `support.plan.list`, `support.plan.self-serve-list`, `support.user.list-all`, `support.workspace.list`

## `template`

| Command | State | Note |
|---|---|---|
| `template.list` | observed blocker | cli_error: backend returned HTTP 200 but the CLI raised api_error (envelope mismatch) |

## `trash`

Verified: `trash.add`, `trash.list`, `trash.restore`

## `user`

Verified: `user.get`, `user.preference.get`, `user.preference.update`

## `view`

Verified: `view.active-user.list`, `view.active-user.mark`, `view.ai.generate-data`, `view.ai.profile`, `view.bulk-delete`, `view.checkpoint.create`, `view.checkpoint.delete`, `view.checkpoint.list`, `view.conditional-format.list`, `view.conditional-format.update`, `view.create`, `view.data-check.create`, `view.data-check.delete`, `view.data-check.get`, `view.data-check.list`, `view.data.get`, `view.data.query`, `view.delete`, `view.derivative.create`, `view.derivative.delete`, `view.derivative.list`, `view.derivative.update`, `view.draft.command`, `view.export.delete`, `view.export.get`, `view.export.list`, `view.export.publish-db`, `view.export.update`, `view.exportable-config.get`, `view.get`, `view.list`, `view.parameter-context`, `view.pipeline.edit`, `view.pipeline.get`, `view.pipeline.items`, `view.pipeline.rerun`, `view.preview`, `view.restore`, `view.task.add`, `view.task.delete`, `view.task.get`, `view.task.list`, `view.task.update`, `view.trash`, `view.version.apply`, `view.version.delete`, `view.version.get`, `view.version.list`, `view.version.update`

| Command | State | Note |
|---|---|---|
| `view.ai.generation-info` | observed blocker | backend: GET /workspaces/4/projects/24/datasets/54/dataviews/76/data/generate -> HTTP 400 5GENR011 NOT_IMPLEMENTED 'Not implemented', request_id:null |
| `view.checkpoint.get` | observed blocker | backend: GET /workspaces/4/projects/24/datasets/54/dataviews/76/pipeline/checkpoints/2 -> HTTP 500, empty response_body:{}, request_id:null, backend code: none surfaced (generic ap |
| `view.checkpoint.update` | observed blocker | backend_error: CLI-side fix (payload now carries value:null as required) held: the correctly-shaped request was dispatched and the backend returned HTTP 500 (not a CLI-side crash): |
| `view.conditional-format.create` | observed blocker | cli_error: Skill doc (view.md) claims this route is 'fail-closed and must not dispatch a request' (BLOCKED B09 DATAVIEW_INPUT_UNTYPED) -- but live it DOES dispatch: HTTP 400 4GENR0 |
| `view.data-check.update` | observed blocker | backend: PATCH .../pipeline/data-checks/3 -> HTTP 500, empty response_body, request_id:null, code:outcome_unknown |
| `view.derivative.data` | observed blocker | backend: POST .../derivatives/4/data -> HTTP 500, empty response_body, request_id:null, code:outcome_unknown |
| `view.export.create` | observed blocker | backend: CLI accepts the request (exit 0, job 358 accepted on POST /dataviews/76/actions), but job get 358 -> status:error, response:{"error":{"message":"'destination'"}} (a raw Py |
| `view.exportable-config.apply` | observed blocker | cli_error: Schema's own runnable_example (config:{tasks:[]}) fails: job_failed, response:{reason:(quote)dependencies(quote)} -- a raw Python KeyError, not a structured validation m |
| `view.conditional-format.delete-all` | CLI defect fixed, untried since | 2.0.16 (the handler now forwards rule_id from --input (2.0.15 accepted the field but dropped it before the SDK call)) |
| `view.export.publish-db-update` | CLI defect fixed, untried since | 2.0.16 (example value is the documented {"odbc_type": "postgres"} object (a bare string is rejected)) |
| `view.task.preview` | CLI defect fixed, untried since | 2.0.16 (example now uses the backend COPY param-template shape: list of {SOURCE, AS{COLUMN,TYPE,INTERNAL_NAME}}, VERSION 2 |

## `webhook`

| Command | State | Note |
|---|---|---|
| `webhook.list` | observed blocker | cli_error: api_error with no HTTP status recorded |

## `workflow`

Verified: `workflow.graph`, `workflow.list`, `workflow.workspace-datasets`, `workflow.workspace-exports`, `workflow.workspace-sources`

## `workspace`

Verified: `workspace.app-usage`, `workspace.get`, `workspace.list`, `workspace.segment.list`, `workspace.segment.update`, `workspace.storage-breakdown`, `workspace.user.list`

Evidence version: CLI mammoth-cli 1.1.11; mammoth-io 0.7.1. Details: `docs/capability-evidence/` in the repository.
