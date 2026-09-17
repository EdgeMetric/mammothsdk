---
name: mammoth-cli
description: "Operate Mammoth Analytics with the published CLI: authenticate, discover contracts, manage projects/data/views/pipelines/dashboards, and verify safe mutations."
---

# Mammoth CLI

Use deterministic JSON: `mammoth … --output json --no-input`. Discover before
mutating: `mammoth schema get COMMAND_ID` gives exact fields; inspect the JSON
success/error envelope and `recovery_commands`, never guess an alias or replay
an `outcome_unknown` mutation. Read back results and delete only IDs returned
by this task.

Resolve project/dataset/view parents from reads and pass the observed scope.
For columns and expressions use exact view-schema **display names**, never
backend aliases. A timeout or unknown mutation outcome requires reconciliation
of the specific target before any retry.

Start cold tasks with [task-start](references/task-start.md). For credentials,
scope, machine output, structured input, confirmations, jobs and recovery use
[auth](references/auth.md), [machine output](references/machine-output.md),
[input](references/input.md), [safety](references/safety.md),
[jobs/drafts](references/jobs-drafts.md), and [recovery](references/recovery.md).
In an evaluated worker, use a controller-provided auth broker; do not mount or
read a credential profile.

Before creating or cleaning resources, classify them with [retention and
cleanup](references/retention.md). Preserve requested datasets, views,
dashboards, and export artifacts; cleanup requires explicit exact-ID
authorization and never means delete-all-owned-resources.

For data work—including transforms, blend/task/pipeline drafts, dashboards and
exports—read [operations](references/operations.md). For every published CLI
command, load only the relevant domain from the generated
[command catalog](references/command-index.md): it provides the command path,
schema ID, compact example, expected result type, mutation/confirmation/wait
policy, and error/recovery pointer. The catalog covers local CLI manifest
commands; `capability list` is an API-binding inventory, not a complete list
of typed/local CLI routes. Use the catalog plus `schema list/find/get` to
discover CLI support, then use capability metadata only for its API-binding
and evidence boundary.

For focused end-to-end patterns—uploads and URL imports, resource navigation,
typed transforms, dashboards, exports, and owned cleanup—read the
[recipes index](references/recipes/index.md).

For a safe cross-agent continuation, read the nonsecret [handoff
format](references/handoff.md). It records scope, observed IDs, jobs, unknown
outcomes, and cleanup ownership; it never transfers credentials or authority.
