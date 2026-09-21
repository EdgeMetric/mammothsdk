# Safe mutation

Each command carries a reviewed confirmation policy:

| policy | how to satisfy it noninteractively |
|---|---|
| none | nothing required |
| prompt_or_yes | pass `--yes` |
| yes_always | pass `--yes` (always, even at a terminal) |
| confirm_target | pass `--yes` and `--confirm TARGET` (exact match) |

Under `--no-input` (and in `json`/`ndjson` modes) there is no prompt: a missing
`--yes`/`--confirm` fails with exit code 2 and error code
`confirmation_required` or `confirmation_target_mismatch`.

```bash
# normal delete
mammoth folder delete 7 --project 180 --yes

# high-impact: target must equal the resource
mammoth project user remove --project 180 \
  --yes --confirm 180 --input '{"user_ids": ["u_123"]}'

# project delete cascades to every dataset, view, export and dashboard in it
mammoth project delete 180 --yes --confirm 180
```

Discover a command's policy with `mammoth schema get <command.id>`.

## Rehearse before you write

`--dry-run` on any API-backed command does everything but send the request:
input admission, parent resolution, display-name and condition checks, then
it stops at the SDK call and reports it as `data.would_call` (`sdk_symbol`,
resolved `arguments`, `view_id`/`dataset_id`) with `data.dry_run: true`. No
confirmation flag is needed for a dry run; the real run still needs its
`--yes`/`--confirm`. Use it before a mutation on a shared or production
resource, and whenever you are unsure which view or column an input resolves
to.

```bash
mammoth view transform filter 144 --dry-run \
  --input '{"filter_type": "REMOVE", "condition": {"column": "Location", "operator": "EQ", "value": "Total"}}'
# data.would_call.sdk_symbol = ...FilterOpsMixin.filter_rows, view_id 144, dataset_id 122
```

A dry run is a full process with the same reads as the real run. On a
hosted environment budget roughly 2 s per request (about 0.7 s of it TLS
setup from a cold process, the rest server time), so `view task list` →
`--dry-run` → write costs about 30–40 s per pipeline step. That is the
price of the procedure, not a hang; do not shorten `--timeout` below the
default to speed it up.

## Add-only edits to a pipeline someone else may touch

Every `view transform *` and `view task add` accepts `expected_task_count`:
the number of tasks your last `view task list VIEW_ID` returned. The CLI
re-reads the task list right before the write and refuses with
`pipeline_changed` (exit 2, `details.actual_task_count`, `task_ids`) when the
count differs, so a plan made against a stale read cannot land on a pipeline
that changed under you. Read → decide → write with the count, one edit at a
time; on `pipeline_changed`, re-read and re-decide rather than retrying with
the new number blindly.

```bash
mammoth view task list 144            # data.tasks has 3 entries
mammoth view transform filter 144 --input '{"expected_task_count": 3, "filter_type": "REMOVE", "condition": {...}}'
```
Use exact observed resource scope and display names before mutation. A known job
handle should be inspected or waited, not submitted again. `outcome_unknown`
means a mutation may have committed without a terminal response: reconcile the
target before any replay. A retryable read can honor `Retry-After`; exit 7 is
not blanket permission to retry a mutation.
