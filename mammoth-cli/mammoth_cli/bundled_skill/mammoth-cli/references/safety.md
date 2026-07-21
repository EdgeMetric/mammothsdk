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
mammoth folder delete 7 --project 180 --output json --no-input --yes

# high-impact: target must equal the resource
mammoth project user remove --project 180 --output json --no-input \
  --yes --confirm 180 --input '{"user_ids": ["u_123"]}'
```

Discover a command's policy with `mammoth schema get <command.id> --output json`.
Never retry a mutation blindly; only retry on exit code 7 (retryable).
