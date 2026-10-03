# Typed operations and verification

The installed CLI manifest is the source of truth for local CLI routes. Use
`schema list/find TEXT` to discover those routes. `capability list` is a
separate API-binding inventory and can omit typed/local commands such as view
transforms. `schema get COMMAND_ID` returns the full contract of one command:

- command path and typed positionals/options;
- request/result models and the accepted input shape;
- effect/confirmation policy and wait policy;
- known restrictions and recovery/verification metadata.

Read the schema immediately before composing a request. Support and fields can
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
`view list` call the live API, and `--project` scopes them to one
project. `dataset find NAME` and `folder find NAME` search every project
the credential can see (or one, with `--project`); they still need
credentials because they call the live API. To find a dataset by name, run
`dataset find NAME` (no project needed), or
`dataset list --input '{"name": "NAME"}'` inside one project: a
case-insensitive substring match over every page, returned as short rows
(id, name, rows, cols) with `matched`. Do not page `dataset list` by hand;
`limit` is at most 100. To find the dataset that holds given columns, pass
`dataset find --input '{"columns": ["Order ID", "Region"]}'` (the name is then
optional). To find the dataset that holds a value you were given (a campaign,
a region, a product) when its name does not say, run `dataset search TERM`: it
returns the project's datasets whose name, column names or sampled column
values contain TERM, each with the matched column and value. `dataset find`
and `browse` search match names only. A `browse` search hit carries `dataset_id` or `view_id`: use those,
never the tree `id`.

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

Use the command ID exactly as the search returns it. Read its schema and the current view
schema before composing input. Join only on keys confirmed in both exact view
schemas. After numeric conversion, create derived measures through the typed
math route. Verify them from a `view data get` readback. Deduplication is a
semantic operation: define the key/retention rule explicitly. A successful
task submission does not prove that the task removed duplicates.

For deduplication, discover and use `view.transform.discard-duplicates`; see
recipes/transforms.md for the full procedure.

Prefer a typed `view transform <operation>` command. Its schema is the
discoverable request contract. A job status or pipeline/task definition only
proves that the task ran. For a value-changing step, the proof is the
`view data get` rows; see SKILL.md and [report-checklist](report-checklist.md).
A transform needs the view's parent dataset. The CLI remembers it from any
earlier read of the view (`view list DATASET_ID`, `view get VIEW_ID`); pass
`dataset_id` in `--input` only when the command asks for it. It never falls
back to project-wide discovery:

```bash
mammoth view transform math VIEW_ID --project PROJECT_ID \
  --input '{"expression":"Unit Price * Quantity","new_column":"Revenue"}'
mammoth view pipeline get VIEW_ID --project PROJECT_ID
```

The low-level `view task add|preview|update` routes expose an opaque
`task_spec` object in the current schema, not a discoverable task union. Prefer
typed transform routes. Use a low-level task route only with an independently
documented task specification for the target backend. Never infer SDK/backend
keys from `schema get` or an illustrative example. Read the
task/list or pipeline/items result back after a successful write. Without that
independent specification, report the route as unsupported/ambiguous and stop
safely.

Typed transforms and `view task add` append at the end of the pipeline and
never reorder or delete an existing step. Other people or agents may also
edit the pipeline. To guard against that, read `view task list VIEW_ID`,
plan, then write with `"expected_task_count": N` in the input. The CLI
re-reads the list just before the write. It refuses with `pipeline_changed`
when the count moved ([safety](safety.md)). `--dry-run` on the same command shows the
resolved call first.

A workflow is a container for automation. Creating one is not the same as
adding a view pipeline task. Discover its schema, create it, and read it back:

```bash
mammoth schema get workflow.create
mammoth workflow create "Revenue report"
mammoth workflow get WORKFLOW_ID
```

`WORKFLOW_ID` is the workflow's record id (URL id `w12` is record 12). An
unnamed workflow (long base64 URL id) has no record: list the workflows and
root datasets with `workflow graph`, then name it with `workflow create
NAME --input '{"seed_datasource_id": ROOT_DATASET_ID}'`, which returns its
record id. `workflow cleanup` deletes the project's orphaned skeleton
("ghost") workflows (destructive; needs `--yes`).

To only *suggest* a workflow's shape for the user to review, use `workflow
canvas WORKFLOW_ID --input '{"canvas_state": {"proposed_changes": [...]}}'`.
Nothing is built until the user presses Save on the Workflows canvas; tell
them the changes are waiting there. Changes are `add_view`, `rename_view`,
`trash_view`, `rename_dataset`, `trash_dataset`, `send_to_new_dataset`,
`send_to_dataset`, `join` and `export` (fields per op: `schema get
workflow.canvas`). A later change in the same call can point at an earlier
one: give the earlier change a `ref`, then use `view_ref`, `dataset_ref` or
`target_dataset_ref` instead of an id. It cannot add filters, calculations or
other tasks; if the request needs those, build it with `view` commands.

Draft mode is server-side batching for view pipeline edits. Enter, inspect
status, submit, and verify pipeline state; discard only with the required
confirmation. A draft submit result is not proof that every intended task was
applied.

## Reading data and history without changing the pipeline

- A trend, distribution or top-values answer: `view data explore VIEW_ID
  COLUMN` (read-only; `level` sets the date bucket). `{"cumulative": true}`
  adds a running total per bucket, whatever `sort` or `limit` shows. Figures
  from `explore` and `view data aggregate` are rounded for display (2
  decimals; 4 below 1); `view data compare` keeps full precision.
- "Who changed X": `activity list` (a change list of time, user, action and a
  `path` naming the dataset and view). Filter with `resource_id` in the log's
  typed form, `dataview_<id>` or `datasource_<id>` (a bare number matches
  nothing and is refused), plus `start_time`, `end_time`, `user_ids`; page
  with `limit` and `offset`.
- `view export dataset` that returns `status: pending` was accepted and is
  still being written. Do not export again (that makes a second dataset); run
  its `next` command (`dataset find NAME`) to get the new dataset id.

## Response shapes

Response shapes are not uniform; never reuse one `jq` path across commands.
`dataset get` returns `data.dataset.{...}`. `dataset list` returns
`data.datasets[]`. `project list` returns `data.projects[]`. Every other
command returns its object directly under `data`. Inspect the first response
before extracting a field.

`project list` shows only the projects the user is a member of, the same as the
Mammoth UI. A workspace owner or admin can read other projects but not open
them, so never report them as access denied. Pass `include_non_members: true`
only when the user asks about projects they are not in; each row then carries
`member`.

## Conditional formatting

One `view conditional-format create` rule covers many columns: pass
`--input '{"columns": ["Q1", "Q2"], "operator": "<", "value": 55, "color": "red"}'`
(display names; `applies_to` is `columns` by default, or `row` to colour the
whole row). Never create one rule per column. A raw `rule` body still works.

## Exports

First inspect `view.export.list/get` for existing configuration and the exact
export command schema. Local CSV and dataset exports have different result
shapes from external-effect connectors. External destinations (database,
cloud storage, email, and similar) require `--yes` and commonly return a job.
Verify them with `job get/wait`, then with `view export get/list` or a
destination-side artifact when the schema requires it.

```bash
mammoth schema get view.export.csv
mammoth schema get view.export.postgres
mammoth view export csv VIEW_ID --project PROJECT_ID
mammoth view export list VIEW_ID DATASET_ID --project PROJECT_ID
```

Use `--input` for connector configuration. Keep the schema's secret fields out
of argv, logs, checkpoints, and handoffs. A submitted job alone does not prove
that an export completed. Reconcile a timed-out or uncertain
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
