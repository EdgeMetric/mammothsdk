# Typed operations and verification

The installed CLI manifest is the source of truth. `capability list` tells you
what is exposed for this installation; `schema find TEXT` narrows the catalog;
`schema get COMMAND_ID` returns the command path, typed positionals/options,
request/result models, accepted input shape, effect/confirmation policy,
wait policy, known restrictions, and recovery/verification metadata. Read the
schema immediately before composing a request because support and fields can
vary by release, profile, or backend.

```bash
mammoth capability find "transform pipeline export" --output json --no-input
mammoth schema find "view.transform" --output json --no-input
mammoth schema get view.transform.math --output json --no-input
```

## Transforms and pipeline tasks

Prefer a typed `view transform <operation>` command. Its schema is the
discoverable request contract and its result should be verified with a view
read, preview, pipeline read/items, or the returned job according to
`wait_policy`:

```bash
mammoth view transform math VIEW_ID --project PROJECT_ID \
  --input '{"expression":"Unit Price * Quantity","new_column":"Revenue"}' \
  --output json --no-input
mammoth view pipeline get VIEW_ID --project PROJECT_ID --output json --no-input
```

The low-level `view task add|preview|update` routes expose an opaque
`task_spec` object in the current schema, not a discoverable task union. Prefer
typed transform routes. Use a low-level task route only when an independently
documented task specification is supplied for the target backend; never infer
SDK/backend keys from `schema get` or an illustrative example. Read the
task/list or pipeline/items result back after a successful write. Without that
independent specification, report the route as unsupported/ambiguous and stop
safely.

For a new workflow (a container for automation), discover and then read it
back; workflow creation is not the same as adding a view pipeline task:

```bash
mammoth schema get workflow.create --output json --no-input
mammoth workflow create "Revenue report" --output json --no-input
mammoth workflow get WORKFLOW_ID --output json --no-input
```

Draft mode is server-side batching for view pipeline edits. Enter, inspect
status, submit, and verify pipeline state; discard only with the required
confirmation. A draft submit result is not proof that every intended task was
applied.

## Exports

First inspect `view.export.list/get` for existing configuration and the exact
export command schema. Local CSV and dataset exports have different result
shapes from external-effect connectors. External destinations (database,
cloud storage, email, and similar) require `--yes`, commonly return a job, and
must be verified with `job get/wait` and then `view export get/list` or a
destination-side artifact when the schema requires it.

```bash
mammoth schema get view.export.csv --output json --no-input
mammoth schema get view.export.postgres --output json --no-input
mammoth view export csv VIEW_ID --project PROJECT_ID --output json --no-input
mammoth view export list VIEW_ID DATASET_ID --project PROJECT_ID --output json --no-input
```

Use `--input` for connector configuration. Keep fields listed as secret by the
schema out of argv, logs, checkpoints, and handoffs; do not claim an export
completed from a submitted job alone. Reconcile a timed-out or uncertain
export before submitting another one.

## Capability boundaries

An operation absent from `capability list`, marked `server_unavailable`, or
rejected by `schema get` is a real current capability limitation. A manifest
entry proves routing and validation only; it does not prove tenant permission,
backend semantics, production readiness, or independent postcondition
verification. Report the precise unsupported/unauthorized/backend-blocked
condition. Do not substitute local processing, private SDK/HTTP calls, or an
unverified success claim.
