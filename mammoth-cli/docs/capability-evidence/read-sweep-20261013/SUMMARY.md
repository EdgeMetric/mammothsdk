# Read-only capability sweep, 2026-10-13

CLI 2.2.77 (mammoth-cli from origin/main 20c5eb14f7), SDK from the same tree, installed into a throwaway venv.

Every `read` command in `mammoth schema list` (293 of 747) was run once per environment through the real CLI
(`--output json --no-input --timeout 60`), by `harness/read_sweep.py`. Fixtures are bound by positional name from
list commands (`read_extra.py` re-runs the few that need a hand-built input). Only response shapes are stored, not data.

- `koyal` (profile `koyal`, workspace 2, project 25654): the dev box. Its token is limited to project 25654.
- `prod` (profile `default`, workspace 304, project 4404): strictly read-only (list/get/schema/data reads).
- Not run: the 4 LLM generate commands (cost) and the local credential/config families (auth, config, context, completion, upgrade, skill, log, doctor).
- The 2026-09-18 sweep ran on the release box (workspace 4); fixtures differ, so a verdict change between sweeps is a signal, not proof of a regression.

| verdict | koyal | prod |
|---|---|---|
| authorization_error | 1 | 3 |
| blocked_missing_fixture | 137 | 111 |
| cli_error | 3 | 16 |
| not_found | 5 | 5 |
| not_run | 17 | 17 |
| ok | 78 | 94 |
| ok_empty | 44 | 42 |
| server_error | 2 | 1 |
| validation_error | 6 | 4 |
| **total** | 293 | 293 |

## Commands in the 2026-09-18 read sweep (171): old vs new

| command | old (release 09-18) | new koyal | new prod |
|---|---|---|---|
| `dataset.list` | ok | ok | ok |
| `project.list` | ok | ok | ok |
| `project.get` | ok | ok | ok |
| `folder.root` | ok | ok | ok |
| `folder.list` | ok | ok_empty | ok_empty |
| `file.list` | ok | ok | ok_empty |
| `dashboard.list` | ok | ok | ok |
| `webhook.list` | cli_error | ok_empty | ok_empty |
| `workspace.list` | ok | ok | ok |
| `workspace.user.list` | ok | ok | ok |
| `workspace.segment.list` | ok | ok | ok |
| `report.list` | ok | ok_empty | ok |
| `trash.list` | ok | ok_empty | ok_empty |
| `notification.list` | ok | ok_empty | ok |
| `parameter.list` | ok | ok_empty | ok_empty |
| `parameter.group.list` | ok | ok_empty | ok_empty |
| `connector.list` | ok | ok | ok |
| `connector.active` | ok_empty | ok | ok |
| `client-app.list` | authorization_error | ok_empty | ok |
| `external-key.list` | cli_error | ok | ok |
| `addon.list` | not_supported | cli_error | cli_error |
| `automation.list` | ok_empty | ok | ok |
| `annotation.list` | ok_empty | ok_empty | ok_empty |
| `agent.session.list` | ok | authorization_error | ok |
| `dashboard.tags.list` | ok | ok | ok |
| `dashboard.signature.list` | ok | ok_empty | ok_empty |
| `dashboard.source.list` | server_error | ok | cli_error |
| `dashboard.style.preset.list` | ok | ok | ok |
| `dashboard.style.custom.list` | ok | ok_empty | ok_empty |
| `dashboard.context.list` | ok | ok_empty | ok_empty |
| `dashboard.template.list` | ok | ok | ok |
| `skill.list` | ok | not_run | not_run |
| `skill.path` | ok | not_run | not_run |
| `schema.list` | ok | ok | ok |
| `config.list` | fence_denied | not_run | not_run |
| `config.path` | fence_denied | not_run | not_run |
| `capability.list` | ok | ok | ok |
| `doctor` | ok | not_run | not_run |
| `version` | ok | ok | ok |
| `user.get` | ok | ok | ok |
| `user.preference.get` | ok | ok | ok |
| `workspace.get` | ok | ok | ok |
| `workspace.app-usage` | ok | ok | ok |
| `workspace.storage-breakdown` | ok | ok | ok |
| `job.get-many` | cli_error | blocked_missing_fixture | blocked_missing_fixture |
| `job.wait-many` | cli_error | blocked_missing_fixture | blocked_missing_fixture |
| `browse.root` | server_error | ok | ok |
| `browse.workspace` | ok | ok | ok |
| `browse.project` | server_error | ok | ok |
| `context.project.status` | fence_denied | not_run | not_run |
| `data-app.list` | ok | not_found | not_found |
| `completion.show` | fence_denied | not_run | not_run |
| `schema.find` | ok | blocked_missing_fixture | blocked_missing_fixture |
| `capability.find` | ok | blocked_missing_fixture | blocked_missing_fixture |
| `ai.suggestion.list` | validation_error | cli_error | cli_error |
| `schedule.list` | validation_error | cli_error | cli_error |
| `snippet.list` | ok | ok_empty | ok_empty |
| `workflow.list` | ok_empty | ok_empty | ok_empty |
| `workflow.graph` | ok | ok | ok |
| `workflow.workspace-datasets` | ok | ok | ok |
| `workflow.workspace-exports` | ok_empty | ok_empty | ok_empty |
| `workflow.workspace-sources` | ok_empty | ok | ok |
| `template.list` | cli_error | ok_empty | ok_empty |
| `dashboard.style.default.get` | cli_error | ok | ok |
| `ai.sql.generate` | validation_error | not_run | not_run |
| `auth.status` | fence_denied | not_run | not_run |
| `activity.list` | ok | ok | ok |
| `capability.get` | ok | blocked_missing_fixture | blocked_missing_fixture |
| `schema.get` | ok | blocked_missing_fixture | blocked_missing_fixture |
| `batch.list` | ok | ok | ok |
| `view.list` | ok | ok | ok |
| `project.checkpoint.list` | ok | ok_empty | ok_empty |
| `project.data-check.list` | ok | ok_empty | ok_empty |
| `project.pending-changes` | ok | ok | ok |
| `project.publish-credentials` | cli_error | blocked_missing_fixture | blocked_missing_fixture |
| `project.resource-status` | ok | ok | ok |
| `dataset.get` | ok | ok | ok |
| `dataset.data` | ok | ok | ok |
| `dataset.file-settings.get` | ok | server_error | server_error |
| `workspace.user.get` | not_supported | ok | ok |
| `activity.export` | server_error | ok | ok |
| `project.resource-dependencies` | cli_error | blocked_missing_fixture | blocked_missing_fixture |
| `browse.folder` | cli_error | blocked_missing_fixture | blocked_missing_fixture |
| `view.get` | ok | ok | ok |
| `view.data.get` | ok | ok | ok |
| `view.data.query` | ok | ok | ok |
| `view.derivative.list` | ok | ok_empty | ok_empty |
| `view.checkpoint.list` | ok | ok_empty | ok_empty |
| `view.conditional-format.list` | cli_error | ok_empty | ok_empty |
| `view.data-check.list` | ok | ok_empty | ok_empty |
| `view.exportable-config.get` | ok | ok | ok |
| `view.parameter-context` | ok | ok_empty | ok_empty |
| `view.pipeline.get` | ok | ok | ok |
| `view.pipeline.items` | ok | ok_empty | ok_empty |
| `view.pipeline.items-all` | cli_error | ok_empty | ok_empty |
| `view.pipeline.wait` | ok | ok | ok |
| `view.preview` | ok | ok | ok |
| `view.task.list` | ok | ok_empty | ok_empty |
| `view.version.list` | ok | ok_empty | ok_empty |
| `view.active-user.list` | ok | ok_empty | ok_empty |
| `view.ai.generation-info` | validation_error | validation_error | validation_error |
| `view.draft.status` | ok | ok | ok |
| `view.export.list` | ok | ok_empty | ok_empty |
| `dashboard.get` | ok | blocked_missing_fixture | ok |
| `dashboard.analytics` | ok | blocked_missing_fixture | ok |
| `dashboard.canvas.get` | ok | blocked_missing_fixture | cli_error |
| `dashboard.chat.history` | ok | blocked_missing_fixture | cli_error |
| `dashboard.data.draft` | cli_error | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.data.published` | cli_error | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.get-by-url` | ok | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.og-card` | cli_error | blocked_missing_fixture | cli_error |
| `dashboard.published.canvas` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.published.og-card` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.published.share-page` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.published.video-artifact` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.qa.session.list` | ok | blocked_missing_fixture | cli_error |
| `dashboard.qa.settings.get` | ok | blocked_missing_fixture | cli_error |
| `dashboard.rls.assignment.list` | ok | blocked_missing_fixture | ok_empty |
| `dashboard.rls.column.list` | ok | blocked_missing_fixture | ok_empty |
| `dashboard.suggestion.list` | ok | ok | ok |
| `dashboard.template.fit` | ok | ok_empty | ok |
| `dashboard.template.get` | cli_error | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.video-state` | ok | blocked_missing_fixture | cli_error |
| `dashboard.rls.value.list` | cli_error | blocked_missing_fixture | blocked_missing_fixture |
| `connector.get` | validation_error | ok | ok |
| `dashboard.style.token.list` | ok | blocked_missing_fixture | blocked_missing_fixture |
| `view.task.get` | ok | blocked_missing_fixture | blocked_missing_fixture |
| `view.version.get` | ok | blocked_missing_fixture | blocked_missing_fixture |
| `view.task.preview` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `connector.connection.list` | server_error | ok_empty | ok_empty |
| `connector.ai.session.list` | cli_error | ok_empty | ok |
| `dataset.batch-data` | ok | blocked_missing_fixture | blocked_missing_fixture |
| `job.get` | ok | blocked_missing_fixture | blocked_missing_fixture |
| `job.wait` | ok | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.job-by-url` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.pdf-artifact` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `batch.get` | ok | blocked_missing_fixture | blocked_missing_fixture |
| `agent.session.messages` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `automation.get` | blocked_missing_fixture | ok | ok |
| `client-app.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `connector.ai.history` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `connector.ai.session.messages` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `connector.connection.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `connector.ds-config.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `connector.ds-config.list` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `connector.query.generate` | blocked_missing_fixture | not_run | not_run |
| `connector.query.status` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.assess-pbix` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.assess-twb` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `dashboard.qa.session.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `data-app.active-job` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `data-app.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `data-app.job` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `data-app.pipeline-changes` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `data-app.user.list` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `external-key.get` | blocked_missing_fixture | blocked_missing_fixture | ok |
| `file.get` | blocked_missing_fixture | ok | blocked_missing_fixture |
| `folder.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `parameter.dependencies` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `parameter.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `schedule.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `snippet.dependencies` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `snippet.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `template.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `view.checkpoint.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `view.data-check.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `view.export.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `webhook.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `workflow.get` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |
| `config.get` | fence_denied | not_run | not_run |
| `dashboard.published.pdf-artifact` | blocked_missing_fixture | blocked_missing_fixture | blocked_missing_fixture |

## Regressions candidates (old ok, now not ok on prod, not a fixture gap)

- `skill.list`: ok -> koyal not_run, prod not_run (None, None, )
- `skill.path`: ok -> koyal not_run, prod not_run (None, None, )
- `doctor`: ok -> koyal not_run, prod not_run (None, None, )
- `data-app.list`: ok -> koyal not_found, prod not_found (resource_not_found, 404, The requested Mammoth resource does not exist.)
- `dataset.file-settings.get`: ok -> koyal server_error, prod server_error (api_error, 500, Mammoth returned an API error.)
- `dashboard.canvas.get`: ok -> koyal blocked_missing_fixture, prod cli_error (conflict, 409, This dashboard uses a different rendering engine — use the matching endpoints [4DASH004])
- `dashboard.chat.history`: ok -> koyal blocked_missing_fixture, prod cli_error (conflict, 409, This dashboard uses a different rendering engine — use the matching endpoints [4DASH004])
- `dashboard.qa.session.list`: ok -> koyal blocked_missing_fixture, prod cli_error (conflict, 409, This dashboard uses a different rendering engine — use the matching endpoints [4DASH004])
- `dashboard.qa.settings.get`: ok -> koyal blocked_missing_fixture, prod cli_error (conflict, 409, This dashboard uses a different rendering engine — use the matching endpoints [4DASH004])
- `dashboard.video-state`: ok -> koyal blocked_missing_fixture, prod cli_error (conflict, 409, This dashboard uses a different rendering engine — use the matching endpoints [4DASH004])

## Old defects that now pass on prod

- `webhook.list` (was cli_error)
- `client-app.list` (was authorization_error)
- `external-key.list` (was cli_error)
- `browse.root` (was server_error)
- `browse.project` (was server_error)
- `template.list` (was cli_error)
- `dashboard.style.default.get` (was cli_error)
- `workspace.user.get` (was not_supported)
- `activity.export` (was server_error)
- `view.conditional-format.list` (was cli_error)
- `view.pipeline.items-all` (was cli_error)
- `connector.get` (was validation_error)
- `connector.connection.list` (was server_error)
- `connector.ai.session.list` (was cli_error)

## Not ok on prod now, grouped

### cli_error
- `addon.list` (koyal: cli_error): not_available  'addon list' is not available: the server no longer offers it.
- `ai.suggestion.list` (koyal: cli_error): missing_field  This command requires the 'suggestion_type' input field.
- `dashboard.canvas.get` (koyal: blocked_missing_fixture): conflict 409 This dashboard uses a different rendering engine — use the matching endpoints [4DASH004]
- `dashboard.chat.history` (koyal: blocked_missing_fixture): conflict 409 This dashboard uses a different rendering engine — use the matching endpoints [4DASH004]
- `dashboard.columns` (koyal: blocked_missing_fixture): conflict 409 This dashboard uses a different rendering engine — use the matching endpoints [4DASH004]
- `dashboard.context.review` (koyal: blocked_missing_fixture): conflict 409 This dashboard uses a different rendering engine — use the matching endpoints [4DASH004]
- `dashboard.filter.list` (koyal: blocked_missing_fixture): conflict 409 This dashboard uses a different rendering engine — use the matching endpoints [4DASH004]
- `dashboard.og-card` (koyal: blocked_missing_fixture): conflict 409 This dashboard uses a different rendering engine — use the matching endpoints [4DASH004]
- `dashboard.own-data.preview` (koyal: blocked_missing_fixture): conflict 409 This dashboard uses a different rendering engine — use the matching endpoints [4DASH004]
- `dashboard.own-data.status` (koyal: blocked_missing_fixture): conflict 409 This dashboard uses a different rendering engine — use the matching endpoints [4DASH004]
- `dashboard.qa.insights` (koyal: blocked_missing_fixture): conflict 409 This dashboard uses a different rendering engine — use the matching endpoints [4DASH004]
- `dashboard.qa.session.list` (koyal: blocked_missing_fixture): conflict 409 This dashboard uses a different rendering engine — use the matching endpoints [4DASH004]
- `dashboard.qa.settings.get` (koyal: blocked_missing_fixture): conflict 409 This dashboard uses a different rendering engine — use the matching endpoints [4DASH004]
- `dashboard.source.list` (koyal: ok): retryable_error  Mammoth is temporarily unavailable or the request timed out.
- `dashboard.video-state` (koyal: blocked_missing_fixture): conflict 409 This dashboard uses a different rendering engine — use the matching endpoints [4DASH004]
- `schedule.list` (koyal: cli_error): not_available  'schedule list' is not available: the server no longer offers it.
### validation_error
- `billing.stripe.get` (koyal: validation_error): api_error 400 No subscription found for this workspace [4SUBS038]
- `billing.stripe.preview-invoice` (koyal: validation_error): api_error 400 Failed to perform subscription operation [4SUBS037]
- `billing.stripe.upcoming-invoice` (koyal: validation_error): api_error 400 Upcoming invoice not found [4SUBS074]
- `view.ai.generation-info` (koyal: validation_error): api_error 400 Please select an API key to use for AI generation. [4GENR019]
### server_error
- `dataset.file-settings.get` (koyal: server_error): api_error 500 Mammoth returned an API error.
### not_found
- `agent.list` (koyal: not_found): resource_not_found 404 The requested Mammoth resource does not exist.
- `agent.roles` (koyal: not_found): resource_not_found 404 The requested Mammoth resource does not exist.
- `data-app.list` (koyal: not_found): resource_not_found 404 The requested Mammoth resource does not exist.
- `dataset.column-stats` (koyal: not_found): resource_not_found 404 The requested Mammoth resource does not exist.
- `dataset.definition.list` (koyal: not_found): resource_not_found 404 The requested Mammoth resource does not exist.
### authorization_error
- `support.subscription.get` (koyal: ok): authorization_required 401 No access to workspace 1730 (this sign-in is for workspace 304).
- `support.workspace.get` (koyal: ok): authorization_required 401 No access to workspace 1730 (this sign-in is for workspace 304).
- `support.workspace.user.list` (koyal: ok): authorization_required 401 No access to workspace 1730 (this sign-in is for workspace 304).
