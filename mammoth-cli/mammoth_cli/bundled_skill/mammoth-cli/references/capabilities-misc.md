# What is proven on release: administration families

Generated from `docs/release-capability-matrix.json`; do not edit by hand. Companion to [capabilities](capabilities.md), which holds the status meanings, the coverage table and the core families (dashboard, dataset, file, folder, job, project, view). Load this file only for a task in one of the families below.

## `activity`

Ran once: `activity.list`

| Command | State | Note |
|---|---|---|
| `activity.export` | observed blocker | server_error: see sweep report |

## `agent`

Ran once: `agent.session.list`

## `ai`

Ran once: `ai.condition.generate`, `ai.expression.generate`

| Command | State | Note |
|---|---|---|
| `ai.retention.condition` | observed blocker | permission: POST /workspaces/4/projects/24/sql_generation/retention_policy -> HTTP 403 4PERM001 PERMISSION_UNDEFINED, error_object {code:76,message:'Permissions have not been set c |
| `ai.sql.generate` | observed blocker | backend_error: Fix held (dataset_id required and sent as query param -- request reached backend and got a domain-specific conflict, not an empty api_error) |
| `ai.suggestion.list` | observed blocker | backend_error: Fix held: release UnifiedPromptSpec (suggestion_type + params, optional dataset_id/dataview_id) shape accepted and dispatched to a real job (id 381), which failed fo |

## `annotation`

Ran once: `annotation.list`

## `automation`

Ran once: `automation.list`

## `batch`

Ran once: `batch.bulk-delete`, `batch.delete`, `batch.get`, `batch.list`, `batch.update`

| Command | State | Note |
|---|---|---|
| `batch.create` | CLI defect fixed, untried since | 2.0.16 (mapping items carry expected_destination_c_type (TEXT/NUMERIC/DATE) |

## `billing`

Ran once: `billing.stripe.history`, `billing.stripe.payment-method.list`, `billing.stripe.status`, `billing.subscription.get`

| Command | State | Note |
|---|---|---|
| `billing.chargebee-plan` | observed blocker | backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 400 4SUBS014 'Chargebee plan not found for the given workspace' (workspace 4 is n |
| `billing.invoice.get` | observed blocker | blocked_missing_fixture: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: billing invoice list answered HTTP 500, so no invoice id was observed |
| `billing.invoice.list` | observed blocker | backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 500 with empty body on GET /workspaces/4/subscription_v1/invoices |
| `billing.stripe.preview-invoice` | observed blocker | backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 400 4SUBS037 'Failed to perform subscription operation' |
| `billing.stripe.upcoming-invoice` | observed blocker | backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 400 4SUBS074 'Upcoming invoice not found' (no active Stripe subscription on works |
| `billing.stripe.usage` | observed blocker | backend_error: The CLI gates this GET behind --yes --confirm WORKSPACE_ID; with confirmation: HTTP 400 5GENR010 UNKNOWN_ERROR 'Unknown error occurred |

## `browse`

Ran once: `browse.project`, `browse.workspace`

| Command | State | Note |
|---|---|---|
| `browse.folder` | observed blocker | cli_error: rejects folder id 0 although folder.root reports id 0 as the root |
| `browse.root` | observed blocker | server_error: see sweep report |

## `client-app`

| Command | State | Note |
|---|---|---|
| `client-app.list` | observed blocker | forbidden: backend_code=4GENR012 INVALID_TOKEN_FOR_CLIENT_APPS: 'Cannot access this API with API-tokens' on GET /workspaces/4/clientapps |

## `connector`

Ran once: `connector.active`, `connector.list`

| Command | State | Note |
|---|---|---|
| `connector.ai.session.list` | observed blocker | cli_error: backend returned HTTP 200 but the CLI raised api_error (envelope mismatch) |
| `connector.connection.list` | observed blocker | server_error: see sweep report |
| `connector.get` | observed blocker | validation_error: HTTP 400 'Invalid connector key' for a key returned by connector.list |
| `connector.query.generate` | observed blocker | blocked_missing_fixture: No real connector connection exists in workspace 4 (connector.list shows all is_added:false; connector.active returns []), matching the documented capabili |
| `connector.query.status` | observed blocker | blocked_missing_fixture: No real connector connection exists in workspace 4 (connector list shows all is_added:false; connector active returns []) and creating one requires externa |

## `data-app`

Ran once: `data-app.list`

## `external-key`

| Command | State | Note |
|---|---|---|
| `external-key.list` | observed blocker | cli_error: not_authenticated although the same session authenticated elsewhere |

## `notification`

Ran once: `notification.list`

## `parameter`

Ran once: `parameter.group.list`, `parameter.list`

## `report`

Ran once: `report.list`

## `schedule`

| Command | State | Note |
|---|---|---|
| `schedule.get` | observed blocker | blocked_missing_fixture: Not run: id source schedule.list failed with backend_error (5GENR011 NOT_IMPLEMENTED, HTTP 400), so no schedule_id was observed to use |
| `schedule.list` | observed blocker | backend_error: backend_code=5GENR011 NOT_IMPLEMENTED: 'Not implemented' on GET /workspaces/4/projects/3/schedules |

## `snippet`

Ran once: `snippet.list`

## `support`

Ran once: `support.connector-profile.list`, `support.connector.list`, `support.feature-profile.list`, `support.feature.list`, `support.plan.chargebee-list`, `support.plan.list`, `support.plan.self-serve-list`, `support.user.list-all`, `support.workspace.list`

## `template`

| Command | State | Note |
|---|---|---|
| `template.list` | observed blocker | cli_error: backend returned HTTP 200 but the CLI raised api_error (envelope mismatch) |

## `trash`

Ran once: `trash.add`, `trash.list`, `trash.restore`

## `user`

Ran once: `user.get`, `user.preference.get`, `user.preference.update`

## `webhook`

| Command | State | Note |
|---|---|---|
| `webhook.list` | observed blocker | cli_error: api_error with no HTTP status recorded |

## `workflow`

Ran once: `workflow.graph`, `workflow.list`, `workflow.workspace-datasets`, `workflow.workspace-exports`, `workflow.workspace-sources`

## `workspace`

Ran once: `workspace.app-usage`, `workspace.get`, `workspace.list`, `workspace.segment.list`, `workspace.segment.update`, `workspace.storage-breakdown`, `workspace.user.list`

Evidence collected on CLI releases 1.1.5 through 2.0.17; each row's release is recorded in `docs/release-capability-matrix.json` (`evidence_version`). A row that ran on an older release has not been re-run since unless its note says so. Details: `docs/capability-evidence/` in the repository.
