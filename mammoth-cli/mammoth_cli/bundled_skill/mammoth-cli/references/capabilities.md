# What is proven on release

Generated from `docs/release-capability-matrix.json`; do not edit by hand.
455 API operations have a CLI command. 142 were exercised successfully on release, 2 are not supported there, and the rest are untried. Untried is not broken: discover the contract with `mammoth schema get COMMAND_ID --output json --no-input`, run it, and treat the structured error envelope as the answer.

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
| `dashboard` | 104 | 66 | 2 | 36 |
| `view` | 62 | 22 | 0 | 40 |
| `support` | 45 | 0 | 0 | 45 |
| `billing` | 23 | 0 | 0 | 23 |
| `connector` | 22 | 2 | 0 | 20 |
| `workspace` | 19 | 6 | 0 | 13 |
| `project` | 17 | 5 | 0 | 12 |
| `workflow` | 16 | 5 | 0 | 11 |
| `dataset` | 15 | 9 | 0 | 6 |
| `parameter` | 14 | 2 | 0 | 12 |
| `data-app` | 12 | 1 | 0 | 11 |
| `folder` | 8 | 5 | 0 | 3 |
| `snippet` | 8 | 1 | 0 | 7 |
| `automation` | 7 | 1 | 0 | 6 |
| `user` | 7 | 2 | 0 | 5 |
| `webhook` | 7 | 0 | 0 | 7 |
| `addon` | 6 | 0 | 0 | 6 |
| `batch` | 6 | 2 | 0 | 4 |
| `file` | 6 | 3 | 0 | 3 |
| `agent` | 5 | 1 | 0 | 4 |
| `ai` | 5 | 0 | 0 | 5 |
| `annotation` | 5 | 1 | 0 | 4 |
| `client-app` | 5 | 0 | 0 | 5 |
| `notification` | 5 | 1 | 0 | 4 |
| `schedule` | 5 | 0 | 0 | 5 |
| `template` | 5 | 0 | 0 | 5 |
| `browse` | 4 | 2 | 0 | 2 |
| `external-key` | 4 | 0 | 0 | 4 |
| `trash` | 3 | 1 | 0 | 2 |
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

| Command | State | Note |
|---|---|---|
| `ai.sql.generate` | observed blocker | validation_error: HTTP 400 Validation error |
| `ai.suggestion.list` | observed blocker | validation_error: HTTP 400 Validation error |

## `annotation`

Verified: `annotation.list`

## `automation`

Verified: `automation.list`

## `batch`

Verified: `batch.get`, `batch.list`

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

## `dashboard`

Verified: `dashboard.analytics`, `dashboard.cancel-generation`, `dashboard.canvas.get`, `dashboard.canvas.restore`, `dashboard.chat.edit`, `dashboard.chat.history`, `dashboard.context.create`, `dashboard.context.delete`, `dashboard.context.extract`, `dashboard.context.list`, `dashboard.context.update`, `dashboard.create-blank`, `dashboard.delete`, `dashboard.descriptor-data`, `dashboard.duplicate`, `dashboard.exemplar.extract`, `dashboard.get`, `dashboard.get-by-url`, `dashboard.list`, `dashboard.page.plan`, `dashboard.pages.add`, `dashboard.qa.ask`, `dashboard.qa.comment.create`, `dashboard.qa.comment.delete`, `dashboard.qa.feedback`, `dashboard.qa.session.create`, `dashboard.qa.session.delete`, `dashboard.qa.session.fork`, `dashboard.qa.session.get`, `dashboard.qa.session.list`, `dashboard.qa.session.rename`, `dashboard.qa.session.set-visibility`, `dashboard.qa.settings.get`, `dashboard.qa.settings.set`, `dashboard.restore`, `dashboard.rls.assignment.list`, `dashboard.rls.assignment.set`, `dashboard.rls.column.list`, `dashboard.rls.value.list`, `dashboard.signature.create`, `dashboard.signature.delete`, `dashboard.signature.list`, `dashboard.signature.update`, `dashboard.style.custom.create`, `dashboard.style.custom.delete`, `dashboard.style.custom.list`, `dashboard.style.custom.update`, `dashboard.style.extract-brand`, `dashboard.style.preset.list`, `dashboard.style.token.list`, `dashboard.suggestion.list`, `dashboard.swap-data`, `dashboard.tags.delete`, `dashboard.tags.list`, `dashboard.tags.merge`, `dashboard.tags.rename`, `dashboard.tags.set`, `dashboard.template.fit`, `dashboard.template.list`, `dashboard.template.preview`, `dashboard.template.resolve-mapping`, `dashboard.templates.pending`, `dashboard.trash`, `dashboard.update`, `dashboard.v3.generate`, `dashboard.video-state`

| Command | State | Note |
|---|---|---|
| `dashboard.create` | not supported | Not supported on release: backend returns HTTP 409 4DASH012 DASHBOARD_LEGACY_CREATION_RETIRED (legacy dashboard creation retired). Use dashboard.create-blank or dashboard.v3.generate. Dashboard sweep 2026-09-18, CLI 2.0.12. |
| `dashboard.pdf.export` | not supported | Not supported from the CLI on release: backend HTTP 400 4GENR001 requires params.data to be the browser-hydrated DashboardData map and states it cannot rebuild it from stored descriptors (dashboard sweep and Haiku e2e, 2026-09-18). The route works only with a client render pass. |
| `dashboard.pdf-artifact` | observed blocker | blocked_missing_fixture: No real pdf export job_id obtainable (dashboard.pdf.export is itself blocked_missing_fixture) |
| `dashboard.published.canvas` | observed blocker | blocked_missing_fixture: HTTP 404 4DASH001 DASHBOARD_NOT_FOUND via url endpoint: D=52 was never actually published (was_published=false); the only publish mechanism is 'dashboard s |
| `dashboard.source.list` | observed blocker | server_error: HTTP 500 on GET /dashboards/sources; matches documented B04 SERVER_VARIANCE precondition |
| `dashboard.video.export` | observed blocker | validation_error: HTTP 400 4GENR001: 'publish the dashboard before exporting a video' -- clear, actionable message |
| `dashboard.widget-data` | observed blocker | blocked_missing_fixture: HTTP 409 4DASH004 DASHBOARD_WRONG_ENGINE: widget-data is a legacy-engine-only endpoint |
| `dashboard.archive` | CLI defect fixed, untried since | 2.0.14 accepts the non-object 200 body and reports the committed state |
| `dashboard.canvas.save` | CLI defect fixed, untried since | 2.0.14 no longer redacts style_tokens, so the canvas get -> save round-trip is intact |
| `dashboard.data.draft` | CLI defect fixed, untried since | 2.0.14 / SDK 0.7.6 send the WidgetDataSpec params envelope (widget_id) |
| `dashboard.data.published` | CLI defect fixed, untried since | 2.0.14 / SDK 0.7.6 send the WidgetDataSpec params envelope (widget_id) |
| `dashboard.figure-intent` | CLI defect fixed, untried since | SDK 0.7.6 returns an unmatched 2xx body instead of raising ValidationError |
| `dashboard.og-card` | CLI defect fixed, untried since | SDK 0.7.5 returns a described binary body |
| `dashboard.query` | CLI defect fixed, untried since | 2.0.14 example carries a descriptor with kind=scalar |
| `dashboard.style.default.get` | CLI defect fixed, untried since | SDK 0.7.6 returns an unmatched 2xx body instead of raising ValidationError |
| `dashboard.style.derive` | CLI defect fixed, untried since | 2.0.14 no longer redacts styleTokens |
| `dashboard.template.get` | CLI defect fixed, untried since | SDK 0.7.6 returns an unmatched 2xx body instead of raising ValidationError |

## `data-app`

Verified: `data-app.list`

## `dataset`

Verified: `dataset.batch-data`, `dataset.create`, `dataset.data`, `dataset.delete`, `dataset.file-settings.get`, `dataset.file-settings.update`, `dataset.get`, `dataset.list`, `dataset.trash`

## `external-key`

| Command | State | Note |
|---|---|---|
| `external-key.list` | observed blocker | cli_error: not_authenticated although the same session authenticated elsewhere |

## `file`

Verified: `file.get`, `file.list`, `file.upload`

## `folder`

Verified: `folder.create`, `folder.delete`, `folder.get`, `folder.list`, `folder.update`

## `job`

Verified: `job.get`, `job.get-many`

## `notification`

Verified: `notification.list`

## `parameter`

Verified: `parameter.group.list`, `parameter.list`

## `project`

Verified: `project.checkpoint.list`, `project.data-check.list`, `project.list`, `project.pending-changes`, `project.resource-status`

| Command | State | Note |
|---|---|---|
| `project.publish-credentials` | observed blocker | cli_error: requires odbc_type, not discoverable read-only |
| `project.resource-dependencies` | observed blocker | cli_error: required resource_ids has no CLI flag |

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

Verified: `trash.list`

## `user`

Verified: `user.get`, `user.preference.get`

## `view`

Verified: `view.active-user.list`, `view.checkpoint.list`, `view.conditional-format.list`, `view.create`, `view.data-check.list`, `view.data.get`, `view.data.query`, `view.derivative.list`, `view.export.list`, `view.exportable-config.get`, `view.get`, `view.list`, `view.parameter-context`, `view.pipeline.get`, `view.pipeline.items`, `view.preview`, `view.task.add`, `view.task.get`, `view.task.list`, `view.version.get`, `view.version.list`

| Command | State | Note |
|---|---|---|
| `view.ai.generation-info` | observed blocker | validation_error: HTTP 400 with message 'Not implemented' |

## `webhook`

| Command | State | Note |
|---|---|---|
| `webhook.list` | observed blocker | cli_error: api_error with no HTTP status recorded |

## `workflow`

Verified: `workflow.graph`, `workflow.list`, `workflow.workspace-datasets`, `workflow.workspace-exports`, `workflow.workspace-sources`

## `workspace`

Verified: `workspace.app-usage`, `workspace.get`, `workspace.list`, `workspace.segment.list`, `workspace.storage-breakdown`, `workspace.user.list`

Evidence version: CLI mammoth-cli 1.1.11; mammoth-io 0.7.1. Details: `docs/capability-evidence/` in the repository.
