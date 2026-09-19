# What is proven on release

Generated from `docs/release-capability-matrix.json`; do not edit by hand.
The CLI publishes 552 commands. 455 of them bind one of the 528 API operations in the matrix; the remainder are local commands (`schema`, `auth`, `doctor`, `log`, ...) or typed variants that share an operation (every `view transform *` command submits through `view.task.add`). 258 bound commands ran once successfully on release, 2 are not supported there, and the rest are untried. Untried is not broken: discover the contract with `mammoth schema get COMMAND_ID --output json --no-input`, run it, and treat the structured error envelope as the answer.

Status meanings:

- **ran once**: one bounded live run on release returned a success envelope (single path; variants and error paths are usually untested). It is not a guarantee that the route works for other inputs.
- **not supported**: the backend refuses the route on release; the note says why and what to use instead.
- **observed blocker**: the last run hit an error; the note quotes it. Re-check before relying on the route, and do not retry the same input.
- **CLI defect fixed, untried since**: the failure was on the CLI side and this release repairs it; nobody has re-run the route yet.
- Commands not listed under a family are untried.

The typed `view transform *` commands all submit through `view.task.add`; its matrix row names the transformations that ran end to end and were read back (filter, fill-missing, join, pivot, set-values with a condition, text, bulk-replace, convert-type, discard-duplicates). A transformation not named there has the same untried status as any other command.

## Coverage by family

| Family | Commands | Ran once | Not supported | Untried |
|---|---|---|---|---|
| `dashboard` | 104 | 81 | 2 | 21 |
| `view` | 62 | 56 | 0 | 6 |
| `support` | 45 | 9 | 0 | 36 |
| `billing` | 23 | 4 | 0 | 19 |
| `connector` | 22 | 3 | 0 | 19 |
| `workspace` | 19 | 7 | 0 | 12 |
| `project` | 17 | 15 | 0 | 2 |
| `workflow` | 16 | 9 | 0 | 7 |
| `dataset` | 15 | 12 | 0 | 3 |
| `parameter` | 14 | 7 | 0 | 7 |
| `data-app` | 12 | 1 | 0 | 11 |
| `folder` | 8 | 8 | 0 | 0 |
| `snippet` | 8 | 6 | 0 | 2 |
| `automation` | 7 | 3 | 0 | 4 |
| `user` | 7 | 3 | 0 | 4 |
| `webhook` | 7 | 5 | 0 | 2 |
| `addon` | 6 | 0 | 0 | 6 |
| `batch` | 6 | 5 | 0 | 1 |
| `file` | 6 | 5 | 0 | 1 |
| `agent` | 5 | 1 | 0 | 4 |
| `ai` | 5 | 2 | 0 | 3 |
| `annotation` | 5 | 1 | 0 | 4 |
| `client-app` | 5 | 0 | 0 | 5 |
| `notification` | 5 | 1 | 0 | 4 |
| `schedule` | 5 | 0 | 0 | 5 |
| `template` | 5 | 5 | 0 | 0 |
| `browse` | 4 | 1 | 0 | 3 |
| `external-key` | 4 | 1 | 0 | 3 |
| `trash` | 3 | 3 | 0 | 0 |
| `activity` | 2 | 1 | 0 | 1 |
| `job` | 2 | 2 | 0 | 0 |
| `report` | 1 | 1 | 0 | 0 |

Administration families (`workspace`, `user`, `billing`, `support`, `connector`, ...) are in [capabilities-misc](capabilities-misc.md).

## `dashboard`

Ran once: `dashboard.action`, `dashboard.analytics`, `dashboard.archive`, `dashboard.cancel-generation`, `dashboard.canvas.get`, `dashboard.canvas.restore`, `dashboard.canvas.save`, `dashboard.chat.edit`, `dashboard.chat.history`, `dashboard.context.create`, `dashboard.context.delete`, `dashboard.context.extract`, `dashboard.context.list`, `dashboard.context.update`, `dashboard.create-blank`, `dashboard.delete`, `dashboard.descriptor-data`, `dashboard.duplicate`, `dashboard.exemplar.extract`, `dashboard.figure-intent`, `dashboard.get`, `dashboard.get-by-url`, `dashboard.job-by-url`, `dashboard.list`, `dashboard.og-card`, `dashboard.page.plan`, `dashboard.pages.add`, `dashboard.published.canvas`, `dashboard.published.share-page`, `dashboard.qa.ask`, `dashboard.qa.comment.create`, `dashboard.qa.comment.delete`, `dashboard.qa.feedback`, `dashboard.qa.session.create`, `dashboard.qa.session.delete`, `dashboard.qa.session.fork`, `dashboard.qa.session.get`, `dashboard.qa.session.list`, `dashboard.qa.session.rename`, `dashboard.qa.session.set-visibility`, `dashboard.qa.settings.get`, `dashboard.qa.settings.set`, `dashboard.query`, `dashboard.restore`, `dashboard.rls.assignment.list`, `dashboard.rls.assignment.set`, `dashboard.rls.column.list`, `dashboard.rls.value.list`, `dashboard.share`, `dashboard.signature.create`, `dashboard.signature.delete`, `dashboard.signature.list`, `dashboard.signature.update`, `dashboard.style.custom.create`, `dashboard.style.custom.delete`, `dashboard.style.custom.list`, `dashboard.style.custom.update`, `dashboard.style.default.get`, `dashboard.style.default.set`, `dashboard.style.derive`, `dashboard.style.extract-brand`, `dashboard.style.preset.list`, `dashboard.style.token.list`, `dashboard.suggestion.list`, `dashboard.swap-data`, `dashboard.tags.delete`, `dashboard.tags.list`, `dashboard.tags.merge`, `dashboard.tags.rename`, `dashboard.tags.set`, `dashboard.template.apply`, `dashboard.template.fit`, `dashboard.template.get`, `dashboard.template.list`, `dashboard.template.preview`, `dashboard.template.resolve-mapping`, `dashboard.templates.pending`, `dashboard.trash`, `dashboard.update`, `dashboard.v3.generate`, `dashboard.video-state`

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

## `dataset`

Ran once: `dataset.batch-data`, `dataset.bulk-delete`, `dataset.create`, `dataset.data`, `dataset.delete`, `dataset.file-settings.get`, `dataset.file-settings.undo`, `dataset.file-settings.update`, `dataset.get`, `dataset.list`, `dataset.restore`, `dataset.trash`

| Command | State | Note |
|---|---|---|
| `dataset.bulk-update` | observed blocker | skipped_out_of_scope: SUSPECTED DEFECT: schema.get advertises this command's precondition as 'BLOCKED[B07 DATASET_PATCH_UNTYPED]; reserved, not registered' and its only documented |
| `dataset.create-from-pdf` | observed blocker | backend: POST /workspaces/4/projects/24/datasets-from-pdf |

## `file`

Ran once: `file.bulk-delete`, `file.delete`, `file.get`, `file.list`, `file.upload`

| Command | State | Note |
|---|---|---|
| `file.update` | observed blocker | backend_error: CLI accepted the typed patch and submitted job 314 (handle_file on /workspaces/4/projects/21/files/50), then correctly reported timeout after 60s with recovery_comma |

## `folder`

Ran once: `folder.bulk-delete`, `folder.create`, `folder.delete`, `folder.get`, `folder.list`, `folder.move`, `folder.trash`, `folder.update`

## `job`

Ran once: `job.get`, `job.get-many`

## `project`

Ran once: `project.bulk-delete`, `project.bulk-update`, `project.checkpoint.list`, `project.create`, `project.data-check.list`, `project.delete`, `project.list`, `project.pending-changes`, `project.publish-credentials`, `project.resource-dependencies`, `project.resource-dependencies.update`, `project.resource-status`, `project.sample-flow`, `project.update`, `project.user.add`

| Command | State | Note |
|---|---|---|
| `project.user.update` | observed blocker | backend_error: HTTP 400 4PROJ010 ROLE_ALREADY_ASSIGNED: "Role already assigned to the user" -- targeted our own user (id 5, already project_admin as project owner) |

## `view`

Ran once: `view.active-user.list`, `view.active-user.mark`, `view.ai.generate-data`, `view.ai.profile`, `view.bulk-delete`, `view.checkpoint.create`, `view.checkpoint.delete`, `view.checkpoint.get`, `view.checkpoint.list`, `view.checkpoint.update`, `view.conditional-format.create`, `view.conditional-format.delete-all`, `view.conditional-format.list`, `view.conditional-format.update`, `view.create`, `view.data-check.create`, `view.data-check.delete`, `view.data-check.get`, `view.data-check.list`, `view.data.get`, `view.data.query`, `view.delete`, `view.derivative.create`, `view.derivative.delete`, `view.derivative.list`, `view.derivative.update`, `view.draft.command`, `view.export.delete`, `view.export.get`, `view.export.list`, `view.export.publish-db`, `view.export.update`, `view.exportable-config.apply`, `view.exportable-config.get`, `view.get`, `view.list`, `view.parameter-context`, `view.pipeline.edit`, `view.pipeline.get`, `view.pipeline.items`, `view.pipeline.rerun`, `view.preview`, `view.restore`, `view.task.add`, `view.task.delete`, `view.task.get`, `view.task.list`, `view.task.preview`, `view.task.update`, `view.trash`, `view.version.apply`, `view.version.delete`, `view.version.get`, `view.version.list`, `view.version.update`

| Command | State | Note |
|---|---|---|
| `view.ai.generation-info` | observed blocker | backend: GET /workspaces/4/projects/24/datasets/54/dataviews/76/data/generate -> HTTP 400 5GENR011 NOT_IMPLEMENTED 'Not implemented', request_id:null |
| `view.data-check.update` | observed blocker | backend_error: SUSPECTED DEFECT: PATCH returned HTTP 500 empty body / CLI code=outcome_unknown, but a follow-up get confirmed the mutation actually applied (enabled:false, updated_ |
| `view.derivative.data` | observed blocker | backend_error: SUSPECTED DEFECT: using the CLI's own documented agent_example body verbatim, derivative data fetch returns HTTP 500 empty body / outcome_unknown, reproduced twice ( |
| `view.export.create` | observed blocker | backend: CLI accepts the request (exit 0, job 358 accepted on POST /dataviews/76/actions), but job get 358 -> status:error, response:{"error":{"message":"'destination'"}} (a raw Py |
| `view.export.publish-db-update` | CLI defect fixed, untried since | 2.0.16 (example value is the documented {"odbc_type": "postgres"} object (a bare string is rejected)) |

Evidence collected on CLI releases 1.1.5 through 2.0.18; each row's release is recorded in `docs/release-capability-matrix.json` (`evidence_version`). A row that ran on an older release has not been re-run since unless its note says so. Details: `docs/capability-evidence/` in the repository.
