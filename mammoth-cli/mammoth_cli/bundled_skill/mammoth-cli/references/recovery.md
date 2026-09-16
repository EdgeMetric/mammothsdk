# Error recovery and cleanup

## Recover from an error
Every error envelope may carry `error.recovery_commands`: exact inspection or
correction commands. Read `error.code` and `details.operation_state` first;
these commands are not blanket permission to replay a mutation.

| exit | error.code (examples) | next step |
|---|---|---|
| 4 | not_authenticated, authentication_failed | `mammoth auth login` |
| 5 | resource_not_found | re-list to find the correct id |
| 2 | project_required | `mammoth context project use ID` or `--project` |
| 2 | confirmation_required | re-run with `--yes` (and `--confirm TARGET`) |
| 6 | conflict | inspect current remote state and resolve it |
| 7 | `timeout` with a known job | inspect or wait that job; do not replay the mutation |
| 7 | `outcome_unknown` | reconcile exact target/scope before any replay |
| 7 | `retryable_error` on a read | honor `Retry-After`, then retry the read |
| 130 | interrupted | preserve the handle, inspect it, and checkpoint the state |

## Cleanup discipline
In a shared project, delete only the resources you created, and never touch
pre-existing ones. Track ids you create and remove them when done:
```bash
mammoth dataset delete "$DS" --project 180 --output json --no-input --yes
mammoth folder delete "$F" --project 180 --output json --no-input --yes
```

## Discovery when stuck
```bash
mammoth capability get GetProjectCheckpoints --output json --no-input
mammoth schema get view.transform.pivot --output json --no-input
mammoth doctor --output json --no-input
```
