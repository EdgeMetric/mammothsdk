# Safe mutation

[Documentation index](llms.txt)

Every command exposes a mutation class and confirmation policy. Check both with
`mammoth schema get <command.id>` before an automated write. This gives a run
the same preflight information as the generated command reference.

## Mutation classes

The class states what a command does to your data or account.

| Class | Meaning |
|---|---|
| `read` | No change. |
| `benign_mutation` | A small, low-risk change. |
| `reversible_pipeline` | A pipeline edit you can undo. |
| `destructive` | Deletes or overwrites data. |
| `external_effect` | Acts outside Mammoth, for example sends a message or writes to an external store. |
| `high_impact` | Workspace- or account-level, hard to reverse. |

## Confirmation policies

The policy states what you must pass before a command runs.

| Policy | How to satisfy it |
|---|---|
| `none` | Nothing required. |
| `prompt_or_yes` | Pass `--yes`, or confirm at an interactive terminal. |
| `yes_always` | Pass `--yes` (always, even at a terminal). |
| `confirm_target` | Pass `--yes` and `--confirm TARGET` (exact match). |

## Behavior without a terminal

Prompts occur only when standard input is a real terminal. Under `--no-input`,
in `json`/`ndjson` output, or in CI, there is no prompt. A missing `--yes` or
`--confirm` fails with exit code `2` and error code `confirmation_required` or
`confirmation_target_mismatch`.

```bash
# normal delete
mammoth dataset delete 2340 --project 180 --yes

# high-impact: --confirm must match the workspace id exactly
mammoth workspace delete --yes --confirm 9
```

## Other safety rules

- The CLI never retries a mutation without a real server idempotency contract;
  only exit code `7` (retryable) is safe to retry.
- Downloads write to a partial file and rename atomically; an existing target
  needs `--overwrite`.
- An interruption returns exit code `130` and closes sessions and files.
- Secrets never appear on the command line, in logs, or in any envelope.

## A safe cleanup pattern

Use IDs returned by the run, list or preview the target if the run may have
been interrupted, and then delete explicitly. Do not use broad name matching in
cleanup scripts.

```bash
mammoth dataset list --project 180 --output json --no-input
mammoth dataset delete DATASET_ID --project 180 --yes --output json --no-input
```
