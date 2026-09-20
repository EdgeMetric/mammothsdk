# Safe mutation

[Documentation index](llms.txt)

Every command exposes a mutation class and confirmation policy. Check both with
`mammoth schema get COMMAND_ID` before an automated write. The schema also tells
you the required scope, result identity, wait behavior, verification read,
recovery limits, and known backend restrictions.

## Mutation classes

| Class | Meaning |
|---|---|
| `read` | No change. |
| `benign_mutation` | A small, low-risk change. |
| `reversible_pipeline` | A pipeline edit you can undo. |
| `destructive` | Deletes or overwrites data. |
| `external_effect` | Acts outside Mammoth, for example sends a message or writes to an external store. |
| `high_impact` | Workspace- or account-level, hard to reverse. |

## Confirmation policies

| Policy | How to satisfy it |
|---|---|
| `none` | Nothing required. |
| `prompt_or_yes` | Pass `--yes`, or confirm at an interactive terminal. |
| `yes_always` | Pass `--yes` (always, even at a terminal). |
| `confirm_target` | Pass `--yes` and `--confirm TARGET` (exact match). |

Prompts occur only when standard input is a real terminal. Under `--no-input`,
machine output, or a non-terminal, a missing confirmation fails with exit code 2
and a structured `confirmation_required` or
`confirmation_target_mismatch` error. There is no interactive fallback.

```bash
mammoth dataset delete DATASET_ID --project PROJECT_ID --yes \
 
mammoth workspace delete --yes --confirm WORKSPACE_ID \
 
```

## Dry runs and preconditions

`--dry-run` is a global option on every API-backed command. The command is
admitted, its parents resolved and its inputs validated against the live
view exactly as in a real run; the SDK call that the command exists for is
then reported instead of made (`data.dry_run: true`, `data.would_call`). The
gate that stops it also stops any SDK write the command's manifest does not
declare, so a dry run cannot mutate through a side path. Confirmation flags
are not required for a dry run. Local commands (`auth`, `config`, `skill`,
`context`, `upgrade`) send nothing and do not take the option.

Pipeline writes (`view transform *`, `view task add`) accept
`expected_task_count` in the input document. The CLI reads the view's task
list immediately before the write and fails with `pipeline_changed` when the
live count differs from the one given; the recovery command is the read that
settles it. This is the precondition that makes "add only, never disturb an
existing step" checkable on a pipeline other people also edit.

## Scope and display-name safety

Use an explicit profile, workspace, project, and parent dataset/view wherever the
schema accepts them. Retain the returned IDs and verify the relationship before
mutating. A dataset does not imply a usable default view; list views and choose
one explicitly. Column inputs are display names from the exact view schema, not
backend/internal identifiers. Unknown or ambiguous names must fail before a
POST.

## Recovery is part of safety

- A **known job** has an observed job handle. Inspect it with `mammoth job get`
  or wait with `mammoth job wait`; do not submit the mutation again.
- **`outcome_unknown`** means a mutation may have committed but no terminal
  result was confirmed. Re-read the target in the same scope and reconcile
  before replaying a create or delete.
- A retryable read may be retried after honoring `Retry-After`. Exit 7 is not a
  blanket permission to retry a write, and the CLI does not silently replay one.
- A conflict, authorization failure, or job failure requires its documented
  correction. Do not turn it into repeated mutation attempts.

Downloads use a same-directory temporary file and publish atomically only after
the complete content is flushed. On a network fault, disk-full error, or broken
pipe, the old destination remains intact; inspect any reported quarantine path
before deciding what to do next.

An interruption exits 130. It preserves the last observed job/resource handle
when available, but does not prove that a remote operation was cancelled.

## Dependency-aware cleanup

### Deliverable retention classes

Classify resources before creating or deleting them:

- **Temporary:** disposable scratch resources; delete only after readback and explicit cleanup authorization.
- **Intermediate:** child views, batches, tasks, or jobs that verify a result. Retain them until dependents are verified; then, when authorized, clean children before parents.
- **Retained deliverable:** the dataset, view, dashboard, or export artifact requested by the user; preserve it for handoff.
- **Protected:** pre-existing, shared, production, or baseline resources; never delete without authorization naming the exact target.

“Owned” does not mean “delete all.” Cleanup authorization must name the exact
IDs, resource types, parent scope, and dependency order. If a requested
dataset, dashboard, or export is the deliverable, do not remove it as an
incidental cleanup step. The portable handoff can carry these nonsecret roles
and cleanup ownership, but it is not a durable cleanup journal or authority
transfer.

Record every resource created by the task and its parent/dependency IDs. Before
deleting, read the resource and check the dependency graph; never delete an
arbitrary inventory difference. After deletion, verify absence or inspect the
deletion job because an acknowledgement can precede disappearance.

```bash
mammoth dataset get DATASET_ID --project PROJECT_ID
mammoth dataset delete DATASET_ID --project PROJECT_ID --yes \
 
mammoth dataset list --project PROJECT_ID
```

See [troubleshooting](troubleshooting.md) and the [portable handoff](agent-handoff.md)
for recovery and transfer procedures.
