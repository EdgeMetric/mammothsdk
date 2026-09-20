# Typed operations and verification

The installed CLI manifest is the source of truth for local CLI routes. Use
`schema list/find TEXT` to discover those routes; `capability list` is a
separate API-binding inventory and can omit typed/local commands such as view
transforms. `schema get COMMAND_ID` returns the command path, typed positionals/options,
request/result models, accepted input shape, effect/confirmation policy,
wait policy, known restrictions, and recovery/verification metadata. Read the
schema immediately before composing a request because support and fields can
vary by release, profile, or backend.

## Which id is which

| Name | Where it appears | Notes |
|---|---|---|
| `PROJECT_ID` | `--project`, `project_id` input field | the workspace container; required on almost every command |
| `DATASET_ID` | positional; `dataset_id` input field; API `ds_id` | the id returned by an upload or dataset creation; a dataset does not select a view |
| `VIEW_ID` | positional; `dataview_id` in API bodies/responses; `foreign_view` in a join input | the view you transform, export, or preview; get it from `view list DATASET_ID` |
| `foreign_dataset_id` | join input field | the parent dataset of `foreign_view` |
| `JOB_ID` | `job get JOB_ID` | async task/job handle |
| `DASHBOARD_ID` | dashboard commands | dashboard resource id |
| `rule_id` | conditional-format commands | id of one conditional-format rule |
| `task_id` / `sequence` | `view task list` results | pipeline task identifiers |

`schema find`/`schema get`/`schema list` read the installed manifest. They
need no project and no stored credentials. `dataset list`, `folder list`, and
`view list` call the live API and are scoped to one project through
`--project`. `dataset find NAME` and `folder find NAME` search every project
the credential can see (or one, with `--project`); they still need
credentials because they call the live API.

```bash
mammoth capability find "transform"
mammoth capability find "pipeline"
mammoth capability find "export"
mammoth schema find "view.transform"
mammoth schema get view.transform.math
```

## Transforms and pipeline tasks

For common data-preparation intents, search the live catalog rather than
assuming a route is available. Typical discovery queries are:

```bash
mammoth schema find "convert type"
mammoth schema find "duplicate"
mammoth schema find "join"
mammoth schema find "lookup"
mammoth schema find "fill missing"
mammoth schema find "replace"
```

There is no pipeline `union`/`append` transform. `join` and `lookup` are the
typed routes for combining views. Appending rows is a dataset-level
operation: upload into the existing dataset with `file upload --input
'{"append_to_ds_id": DATASET_ID}'`, not a view transform.

Use the exact returned command ID, then read its schema and the current view
schema before composing input. Join only on keys confirmed in both exact view
schemas. Create derived measures through the typed math route after numeric
conversion and verify them from a `view data get` readback. Deduplication is a
semantic operation: define the key/retention rule explicitly; never treat a
successful task submission as proof that duplicates were removed.

For deduplication, discover and use `view.transform.discard-duplicates`; see
recipes/transforms.md for the full procedure.

Prefer a typed `view transform <operation>` command. Its schema is the
discoverable request contract. A job status or pipeline/task definition only
proves the task ran; for any value-changing step the proof is `view data get`
rows — see SKILL.md working rules and
[report-checklist](report-checklist.md). Every transform and draft mutation
carries the exact parent `dataset_id` in `--input`; it never falls back to
project-wide discovery:

```bash
mammoth view transform math VIEW_ID --project PROJECT_ID \
  --input '{"dataset_id":DATASET_ID,"expression":"Unit Price * Quantity","new_column":"Revenue"}' \
 
mammoth view pipeline get VIEW_ID --project PROJECT_ID
```

The low-level `view task add|preview|update` routes expose an opaque
`task_spec` object in the current schema, not a discoverable task union. Prefer
typed transform routes. Use a low-level task route only when an independently
documented task specification is supplied for the target backend; never infer
SDK/backend keys from `schema get` or an illustrative example. Read the
task/list or pipeline/items result back after a successful write. Without that
independent specification, report the route as unsupported/ambiguous and stop
safely.

Typed transforms and `view task add` append at the end of the pipeline and
never reorder or delete an existing step. On a pipeline other people or
agents also edit, make that checkable: read `view task list VIEW_ID`, plan,
then write with `"expected_task_count": N` in the input; the CLI re-reads
the list just before the write and refuses with `pipeline_changed` when the
count moved ([safety](safety.md)). `--dry-run` on the same command shows the
resolved call first.

For a new workflow (a container for automation), discover and then read it
back; workflow creation is not the same as adding a view pipeline task:

```bash
mammoth schema get workflow.create
mammoth workflow create "Revenue report"
mammoth workflow get WORKFLOW_ID
```

Draft mode is server-side batching for view pipeline edits. Enter, inspect
status, submit, and verify pipeline state; discard only with the required
confirmation. A draft submit result is not proof that every intended task was
applied.

## Response shapes

Response shapes are not uniform; never reuse one `jq` path across commands.
`dataset get` returns `data.dataset.{...}`. `dataset list` returns
`data.datasets[]`. `project list` returns `data.projects[]`. Every other
command returns its object directly under `data`. Inspect the first response
before extracting a field.

## Exports

First inspect `view.export.list/get` for existing configuration and the exact
export command schema. Local CSV and dataset exports have different result
shapes from external-effect connectors. External destinations (database,
cloud storage, email, and similar) require `--yes`, commonly return a job, and
must be verified with `job get/wait` and then `view export get/list` or a
destination-side artifact when the schema requires it.

```bash
mammoth schema get view.export.csv
mammoth schema get view.export.postgres
mammoth view export csv VIEW_ID --project PROJECT_ID
mammoth view export list VIEW_ID DATASET_ID --project PROJECT_ID
```

Use `--input` for connector configuration. Keep fields listed as secret by the
schema out of argv, logs, checkpoints, and handoffs; do not claim an export
completed from a submitted job alone. Reconcile a timed-out or uncertain
export before submitting another one.

## Capability boundaries

An operation rejected by `schema get` is not a local CLI route. A capability
inventory record marked `server_unavailable` is a documented API-binding
limitation, but absence from that inventory does not negate a typed route that
`schema get` exposes. A manifest entry proves routing and validation only; it
does not prove tenant permission, backend semantics, production readiness, or
independent postcondition verification. `contract_only_no_disposable_fixture`
means the command lacks that automated test fixture; it is not a runtime
unsupported result. Report the precise unsupported/unauthorized/backend-blocked
condition. Do not substitute local processing, private SDK/HTTP calls, or an
unverified success claim.
