# Troubleshooting: exit codes, errors, and recovery

[Documentation index](llms.txt)

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success. |
| 1 | API error. |
| 2 | Usage, input, or confirmation failure. |
| 4 | Authentication failure. |
| 5 | Not found. |
| 6 | Conflict. |
| 7 | Retryable (network or timeout). |
| 130 | Interrupted. |

## Error envelope

Errors print to stderr as a stable envelope:

```json
{"schema_version": 1, "error": {"code": "...", "message": "...", "hint": "...", "details": {}, "request_id": null, "retryable": false, "authorization_required": false, "recovery_commands": ["..."]}}
```

Branch on `error.code`, not the message. `recovery_commands` lists exact
next commands to run.

## Common cases

| Exit | `error.code` | Next step |
|---|---|---|
| 4 | `not_authenticated`, `authentication_failed` | `mammoth auth login` |
| 2 | `project_required` | `mammoth context project use ID` or `--project` |
| 2 | `confirmation_required` | re-run with `--yes` (and `--confirm TARGET`) |
| 5 | `resource_not_found` | re-list to find the correct id |
| 7 | `retryable_error`, `timeout` | wait, then re-run the recovery command |

## First diagnostic

```bash
mammoth doctor --output json --no-input
```

It reports the profile, credential presence, resolved endpoint, and whether an
authenticated request succeeds — with no secret in the output.
