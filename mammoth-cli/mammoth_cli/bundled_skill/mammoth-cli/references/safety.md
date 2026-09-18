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

# project delete cascades to every dataset, view, export and dashboard in it
mammoth project delete 180 --output json --no-input --yes --confirm 180
```

Discover a command's policy with `mammoth schema get <command.id> --output json`.
Use exact observed resource scope and display names before mutation. A known job
handle should be inspected or waited, not submitted again. `outcome_unknown`
means a mutation may have committed without a terminal response: reconcile the
target before any replay. A retryable read can honor `Retry-After`; exit 7 is
not blanket permission to retry a mutation.
