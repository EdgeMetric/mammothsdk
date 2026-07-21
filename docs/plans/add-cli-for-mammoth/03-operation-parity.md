# OpenAPI, SDK, and command parity

## Required pre-code specification artifacts

Before production code changes, create and commit:

1. A pinned copy of the production OpenAPI JSON.
2. A normalized OpenAPI operation inventory.
3. A normalized public SDK method inventory.
4. An operation-disposition manifest.
5. A command-spec manifest.
6. A generated parity report.

Add a deterministic sync script. It must record source URL, fetch time, SHA-256,
OpenAPI version, API version, path count, operation count, and schema count.

The live OpenAPI generator is nondeterministic: repeated fetches changed
examples, a generated project-color default, parameter ordering, and at least
one schema description while paths and operation counts stayed fixed. The sync
script must save the exact raw response and its digest. It must also create a
reviewable contract projection that removes `example` and `examples`, sorts
parameter arrays by location and name, and records every other difference. Do
not automatically discard a changed default or description. A primary reviewer
must classify each projected difference before replacing the pinned snapshot.
Ordinary CI validates the committed snapshot and inventories without fetching
the live document.

Refreshing the snapshot is an explicit maintenance operation. CI must not make
ordinary tests depend on a mutable network document.

Use these exact paths after the sibling CLI package exists:

```text
mammoth-cli/spec/openapi/openapi.json
mammoth-cli/spec/openapi/metadata.json
mammoth-cli/spec/manifests/schema-v1.json
mammoth-cli/spec/manifests/openapi-operations.yaml
mammoth-cli/spec/manifests/sdk-methods.yaml
mammoth-cli/spec/manifests/commands/<top-level-group>.yaml
mammoth-cli/spec/reports/parity.md
mammoth-cli/scripts/sync_openapi.py
mammoth-cli/scripts/inventory_sdk.py
mammoth-cli/scripts/build_parity_report.py
```

The manifest schema version is `1`. Sort OpenAPI records by normalized path and
uppercase method. The stable OpenAPI identity is `METHOD <normalized-path>`;
`operationId` is metadata and may be absent or duplicated. Sort SDK records by
fully qualified public symbol. Sort command files by stable dotted command ID,
for example `view.transform.bulk-replace`.

Allowed dispositions are `command`, `alias`, `protocol_only`, `deprecated`, and
`server_unavailable`. Allowed mutation classes are `read`, `benign_mutation`,
`reversible_pipeline`, `destructive`, `high_impact`, and `external_effect`.
Allowed wait, pagination, and acceptance values are only the named values in
this plan. `schema-v1.json` rejects unknown fields and unresolved markers such
as `TBD`, `TODO`, `unknown`, or an empty required value.

Inventory these SDK members:

- Public methods and properties on exported SDK client, API, resource, view,
  condition, export, and transformation classes.
- Inherited public transformation methods on `mammoth.view.View`.
- Public convenience aliases and deprecated public methods.
- The public import symbol and its implementation origin.

Exclude Pydantic/dataclass utility methods, imported third-party members,
private names, test helpers, and stale MCP wrappers. Record the inventory scope
and generator version in the manifest header.

The primary agent owns every disposition and command decision. Workers can
generate candidate records but cannot approve them. Commit the complete,
reviewed manifests before an SDK or CLI production handler is written.

## OpenAPI operation record

Each of the 376 operations receives this information:

```yaml
operation_id: AddTask
method: POST
path: /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/tasks
tags: [Dataview pipeline Tasks]
summary: Add a task in the pipeline
security: [apiKey, apiSecret]
request_schema: AddTaskRequest
response_schemas: [PipelineModificationResponse, JobResponse]
disposition: command
disposition_reason: User-initiated production operation
sdk_symbol: mammoth.api.pipeline.PipelineAPI.add_task
canonical_command: view task add
reviewed_by: primary
```

## Public SDK record

Each of the 242 audited methods receives:

```yaml
sdk_symbol: mammoth.view.View.bulk_replace
implementation_origin: mammoth._mixins._text_ops.TextOpsMixin.bulk_replace
signature: bulk_replace(columns, mapping, match_case=True, match_words=False, condition=None)
openapi_operation_ids: [AddTask]
canonical_command: view transform bulk-replace
alias_of: null
request_model: BulkReplaceRequest
result_model: PipelineMutationResult
mutation_class: reversible_pipeline
confirmation: none
wait_policy: always_wait
pagination_policy: none
secret_fields: []
unit_tests:
  - UT-VIEW-BULK-REPLACE
contract_tests:
  - CT-VIEW-BULK-REPLACE-HUMAN
  - CT-VIEW-BULK-REPLACE-JSON
  - CT-VIEW-BULK-REPLACE-ERROR
live_test: LT-VIEW-BULK-REPLACE
draft_test: LT-VIEW-BULK-REPLACE-DRAFT
undo_test: LT-VIEW-BULK-REPLACE-UNDO
acceptance_evidence: live_disposable_project
manifest_dependencies: [server_backed_draft_state]
```

## Command specification record

Every canonical command defines:

- Exact command path.
- Positional arguments.
- Global and local options.
- Defaults.
- Environment inputs.
- Typed document schema.
- Flag and document precedence.
- SDK method and conversion.
- Normalized result.
- Pagination policy.
- Wait policy.
- Mutation and confirmation class.
- Draft, preview, and undo behavior.
- Secret fields and approved transports.
- Human example.
- Agent JSON example.
- Unit, subprocess, and live-test IDs.
- Known server or SDK restrictions.

No handler can be implemented without an approved command specification.

Represent each option as a typed record with its exact spelling, positive and
negative boolean spelling, Python type, cardinality, default, required state,
environment source, secret state, and input-document conflict policy. Represent
positionals in order. Reference request and result models by public symbol.
Aliases point to one canonical command ID and cannot form chains or cycles.

Each command selects exactly one acceptance evidence class:

- `live_disposable_project` for safe project-scoped operations.
- `live_dedicated_external_fixture` for controlled external systems.
- `live_read_only` for safe existing-state reads.
- `contract_only_high_impact` for billing, account, ownership, workspace, user,
  email, and external-send operations without disposable fixtures.
- `server_unavailable` only with a reviewed server response.

When the class is not live, set `live_test: null` and require
`live_exemption_reason`, `contract_fixture`, `required_fixture_guard`, and
`reviewed_by`. A permission error is never evidence of `server_unavailable`.

## Production API families missing or incomplete in the current SDK

The OpenAPI audit found important families beyond the existing SDK:

| API family | Required CLI group |
|---|---|
| Agent chat and sessions | `agent` |
| Workflows, blocks, canvas, templates | `workflow`, `template` |
| Annotations and comments | `annotation` |
| Dataview trash, restore, and preview | `view` |
| Derivatives | `view derivative` |
| Pipeline rerun and items | `view pipeline` |
| Pipeline checkpoints | `view checkpoint` |
| Pipeline versions | `view version` |
| Pipeline and project data checks | `view data-check`, `project data-check` |
| Notifications | `notification` |
| Trash and bulk restore | `trash` |
| Parameters and parameter groups | `parameter` |
| Snippets | `snippet` |
| Data apps, uploads, jobs, and sharing | `data-app` |
| AI connector chat sessions | `connector ai` |
| Project dependencies and status | `project` |
| Folder get, update, and trash | `folder` |
| Dataset file settings | `dataset file-settings` |
| Publish credentials | `view export publish` support |
| User avatar and account lifecycle | `user` |
| Subscription and invoices | `billing` |
| Support workspace and user controls | `support` |

The manifest must also classify provider callbacks, privacy webhooks, Stripe
webhooks, OAuth callbacks, health checks, telemetry, unsubscribe links, and
similar protocol endpoints as `protocol_only` when they are not meaningful CLI
actions.

## Existing SDK areas and canonical commands

### Workspace and project

```text
workspace list|get|update|delete|reactivate
workspace user list|get|update
project list|get|create|update|delete|browse
project user add|remove|update
project pending-changes|resource-status|dependencies
```

Workspace deletion and ownership transfer require exact target confirmation.
Project lookup must not stop after the first 100 projects.

### Folder, dataset, and view

```text
folder root|list|get|create|update|move|trash|delete
dataset list|get|create|update|rename|trash|restore|delete
dataset data|file-settings
view list|get|create|update|trash|restore|delete|preview
view data get|query
view active-user list|mark
view conditional-format list|create|update|delete-all
```

Do not expose the current SDK dataset collection `bulk_delete` until the
OpenAPI request contract proves its exact targets. Conditional-format deletion
must say `delete-all` when the endpoint removes every rule.

### Pipeline and transformations

```text
view pipeline get|edit|rerun|wait|items
view task list|get|add|update|delete|preview
view draft status|enter|submit|discard|auto-run
view checkpoint list|get|create|update|delete
view version list|get|apply|update|delete
view data-check list|get|create|update|delete
view transform add-column|delete-columns|copy-columns|combine-columns
view transform convert-type|filter|set-values|math|small-large
view transform text|replace|bulk-replace|split|substring
view transform extract-date|date-diff|increment-date
view transform fill-missing|limit-rows|discard-duplicates|unnest
view transform pivot|window|crosstab|join|lookup|json-extract
view transform ai|generate-sql|add-sql
view ai profile|generate-data|generation-info
ai sql generate
ai suggestion list
connector query generate
```

All task specifications use a typed discriminated union. All condition-bearing
commands use the shared recursive condition model. Draft state must be read
from the server so it works across separate CLI processes.

### Files, jobs, connectors, and webhooks

```text
file list|get|upload|upload-folder|update|set-password|extract-sheets|delete
job get|get-many|wait|wait-many
connector list|get|active
connector connection list|get|create|update|delete
connector ds-config list|get|create|update|delete
webhook list|get|create|update|delete|send|send-get
batch list|get|create|update|delete
```

Folder upload is nonrecursive unless the SDK adds a tested recursive contract.
Connector configurations require typed discriminated models with secret-field
metadata. Webhook ingestion GET operations are mutations and cannot be retried.

### Exports

```text
view export list|get|create|update|delete
view export csv|managed-s3|dataset
view export postgres|mysql|mssql|redshift|bigquery
view export elasticsearch|azure-blob|sharepoint|onedrive
view export tableau|powerbi|ftp|sftp|email|rest|publish-db
```

Create typed destination models and one typed common export-options model.
Remove public `**kwargs: Any` from the CLI boundary. Confirm every OpenAPI export
handler enum member. Record unsupported handlers with server evidence.

External sends require `--yes` when they run immediately. Secrets use stdin,
environment, keyring, or permission-checked files.

### Administration and other resources

```text
dashboard, automation, schedule, client-app, external-key
activity-log, report, addon, user, notification, parameter
snippet, data-app, agent, annotation, workflow, template, trash
billing, support
```

Every group is expanded from its OpenAPI operations in the command manifest.
Do not infer unavailable CRUD verbs.

## Mandatory SDK fixes found by the audit

Resolve these before the affected CLI handlers:

1. Add a public typed dataview-to-dataset resolver.
2. Remove private cross-subclient calls from public view conveniences.
3. Make draft state server-backed and use one typed command vocabulary.
4. Resolve dataset bulk-delete request semantics.
5. Add typed task, pipeline patch, conditional-format, dataset, activity-log,
   profile, connector, batch, and dashboard request models.
6. Add public typed export get, update, delete, and publish methods.
7. Replace export `**kwargs` with typed options and preserve all supplied fields.
8. Add start/wait separation where OpenAPI exposes jobs.
9. Return pagination metadata instead of discarding it.
10. Make CSV downloads atomic and overwrite-safe.
11. Fix empty-list, empty-patch, positive-ID, enum, recurrence, and date checks.
12. Add explicit secret metadata to secret-bearing models.
13. Fix project lookup beyond 100 records.
14. Fix view bulk deletion across datasets and empty input.
15. Correct dashboard password sharing or mark it unavailable with evidence.
16. Reconcile duplicate schedule and view/dataview SDK surfaces through aliases.
17. Correct stale MCP wrappers; never use them as the parity authority.
18. Correct documentation that uses nonexistent upload and export arguments.
19. Fix job wait behavior for empty or missing jobs and normalized status case.
20. Verify each OpenAPI operation path and body, not only endpoint suffixes.
21. Add public `MammothClient.close()`, context-manager support, and lifecycle
   tests so CLI commands can deterministically close the owned HTTP session.

## Transformation-specific validation

The command manifest must encode:

- Exactly one new or existing destination where required.
- Nonempty source lists.
- Function-specific window column requirements.
- Positive row limits and indexes.
- Exclusive substring position and regex modes.
- Nonzero date deltas.
- Nonempty aggregation and mapping specifications.
- Join keys and selected columns.
- Crosstab append/replace confirmation behavior.
- `bulk_replace` defaults: `match_case=true`, `match_words=false`.
- Empty replacement text remains valid.

Do not invent a rename-column pipeline transformation. Column rename, hide,
reorder, sort display state, and number formatting are display operations. Add
typed SDK and CLI commands only when the OpenAPI inventory provides the
production operation.
