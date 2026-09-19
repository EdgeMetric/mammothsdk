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

Ran once: `ai.condition.generate`, `ai.expression.generate`, `ai.suggestion.list`

| Command | State | Note |
|---|---|---|
| `ai.retention.condition` | observed blocker | permission: POST /workspaces/4/projects/24/sql_generation/retention_policy -> HTTP 403 4PERM001 PERMISSION_UNDEFINED, error_object {code:76,message:'Permissions have not been set c |
| `ai.sql.generate` | observed blocker | backend_error: 4DTVW029 conflict: 'Cannot run AI generation for this rule: the input table from the previous rule is not available' on a fresh dataset with no prior rule |

## `annotation`

Ran once: `annotation.list`

## `automation`

Ran once: `automation.create`, `automation.delete`, `automation.list`

| Command | State | Note |
|---|---|---|
| `automation.get` | observed blocker | backend_error: SUSPECTED DEFECT: automation.get on the id just returned by automation.create (id=1) returns HTTP 500 empty body every time (3 retries, several seconds apart), not e |
| `automation.update` | observed blocker | cli_error: CLI rejected 'name' field; error message says accepted field is 'patch' (nested patch object), not documented in agent_example |

## `batch`

Ran once: `batch.bulk-delete`, `batch.create`, `batch.delete`, `batch.get`, `batch.list`, `batch.update`

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

Ran once: `browse.workspace`

| Command | State | Note |
|---|---|---|
| `browse.folder` | observed blocker | cli_error: rejects folder id 0 although folder.root reports id 0 as the root |
| `browse.project` | observed blocker | backend_error: GET /workspaces/4/projects/47/browse HTTP 500 empty body |
| `browse.root` | observed blocker | backend_error: GET /browse still HTTP 500 empty body on release (same as 2026-09-18/19 sweeps) |

## `client-app`

| Command | State | Note |
|---|---|---|
| `client-app.list` | observed blocker | forbidden: backend_code=4GENR012 INVALID_TOKEN_FOR_CLIENT_APPS: 'Cannot access this API with API-tokens' on GET /workspaces/4/clientapps |

## `connector`

Ran once: `connector.active`, `connector.ai.session.list`, `connector.list`

| Command | State | Note |
|---|---|---|
| `connector.connection.list` | observed blocker | server_error: see sweep report |
| `connector.get` | observed blocker | backend_error: SUSPECTED DEFECT: connector.get rejects the exact name_key values returned by connector.list ('azure_blob', 'bigquery' both tried) with 4CNTR002 INVALID_CONNECTOR_KE |
| `connector.query.generate` | observed blocker | blocked_missing_fixture: No real connector connection exists in workspace 4 (connector.list shows all is_added:false; connector.active returns []), matching the documented capabili |
| `connector.query.status` | observed blocker | blocked_missing_fixture: No real connector connection exists in workspace 4 (connector list shows all is_added:false; connector active returns []) and creating one requires externa |

## `data-app`

Ran once: `data-app.list`

## `external-key`

Ran once: `external-key.list`

## `notification`

Ran once: `notification.list`

## `parameter`

Ran once: `parameter.create`, `parameter.delete`, `parameter.dependencies`, `parameter.get`, `parameter.group.list`, `parameter.list`, `parameter.update`

## `report`

Ran once: `report.list`

## `schedule`

| Command | State | Note |
|---|---|---|
| `schedule.create` | observed blocker | backend_error: SUSPECTED CLI/BACKEND DEFECT: second create attempt (with work_items bound to dataset 85) returned HTTP 500 with empty response body, surfaced by CLI as code=outcome |
| `schedule.get` | observed blocker | blocked_missing_fixture: Not run: id source schedule.list failed with backend_error (5GENR011 NOT_IMPLEMENTED, HTTP 400), so no schedule_id was observed to use |
| `schedule.list` | observed blocker | backend_error: 5GENR011 NOT_IMPLEMENTED on GET /workspaces/4/projects/47/schedules; schedules remain unimplemented on release |

## `snippet`

Ran once: `snippet.create`, `snippet.delete`, `snippet.dependencies`, `snippet.get`, `snippet.list`, `snippet.update`

## `support`

Ran once: `support.connector-profile.list`, `support.connector.list`, `support.feature-profile.list`, `support.feature.list`, `support.plan.chargebee-list`, `support.plan.list`, `support.plan.self-serve-list`, `support.user.list-all`, `support.workspace.list`

## `template`

Ran once: `template.create`, `template.delete`, `template.get`, `template.list`, `template.update`

## `trash`

Ran once: `trash.add`, `trash.list`, `trash.restore`

## `user`

Ran once: `user.get`, `user.preference.get`, `user.preference.update`

## `webhook`

Ran once: `webhook.create`, `webhook.delete`, `webhook.get`, `webhook.list`, `webhook.update`

## `workflow`

Ran once: `workflow.create`, `workflow.delete`, `workflow.get`, `workflow.graph`, `workflow.list`, `workflow.update`, `workflow.workspace-datasets`, `workflow.workspace-exports`, `workflow.workspace-sources`

## `workspace`

Ran once: `workspace.app-usage`, `workspace.get`, `workspace.list`, `workspace.segment.list`, `workspace.segment.update`, `workspace.storage-breakdown`, `workspace.user.list`

Evidence collected on CLI releases 1.1.5 through 2.0.21; each row's release is recorded in `docs/release-capability-matrix.json` (`evidence_version`). A row that ran on an older release has not been re-run since unless its note says so. Details: `docs/capability-evidence/` in the repository.
