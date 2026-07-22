# Error recovery and cleanup

## Recover from an error
Every error envelope carries `error.recovery_commands`: an ordered list of exact
commands to run next. Prefer them over improvising.

| exit | error.code (examples) | next step |
|---|---|---|
| 4 | not_authenticated, authentication_failed | `mammoth auth login` |
| 5 | resource_not_found | re-list to find the correct id |
| 2 | project_required | `mammoth context project use ID` or `--project` |
| 2 | confirmation_required | re-run with `--yes` (and `--confirm TARGET`) |
| 7 | retryable_error, timeout | wait, then re-run the recovery command |

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
