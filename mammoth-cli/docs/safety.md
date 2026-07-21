# Safe mutation

[Documentation index](llms.txt)

Every command carries a reviewed confirmation policy. Discover it with
`mammoth schema get <command.id> --output json --no-input`.

| Policy | How to satisfy it |
|---|---|
| `none` | Nothing required. |
| `prompt_or_yes` | Pass `--yes`, or confirm at an interactive terminal. |
| `yes_always` | Pass `--yes` (always, even at a terminal). |
| `confirm_target` | Pass `--yes` and `--confirm TARGET` (exact match). |

## Noninteractive behavior

Prompts occur only when standard input is a real terminal. Under `--no-input`,
in `json`/`ndjson` output, or in CI, there is no prompt. A missing `--yes` or
`--confirm` fails with exit code `2` and error code `confirmation_required` or
`confirmation_target_mismatch`.

```bash
# normal delete
mammoth dataset delete 2340 --project 180 --output json --no-input --yes

# high-impact: the target must match exactly
mammoth workspace delete 9 --output json --no-input --yes --confirm 9
```

## Other safety rules

- The CLI never retries a mutation without a real server idempotency contract;
  only exit code `7` (retryable) is safe to retry.
- Downloads write to a partial file and rename atomically; an existing target
  needs `--overwrite`.
- An interruption returns exit code `130` and closes sessions and files.
- Secrets never appear on the command line, in logs, or in any envelope.
