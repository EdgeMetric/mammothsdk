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

Branch on `error.code`, not the message. `recovery_commands` lists the exact
next commands to run.

## Common cases

| Exit | `error.code` | Next step |
|---|---|---|
| 4 | `not_authenticated`, `authentication_failed` | Run `mammoth auth login`. |
| 2 | `project_required` | Pass `--project ID`, or run `mammoth context project use ID`. |
| 2 | `confirmation_required` | Re-run with `--yes`. |
| 2 | `confirmation_target_mismatch` | Re-run with `--yes` and a matching `--confirm TARGET`. |
| 5 | `resource_not_found` | Re-list to find the correct id. |
| 7 | `retryable_error`, `timeout` | Wait, then re-run the command. |

Only exit code `7` is safe to retry. The CLI never retries a mutation on its
own. For the confirmation codes, see [Safe mutation](safety.md).

## First diagnostic

`mammoth doctor` is the first diagnostic to run:

```bash
mammoth doctor
```

It reports the profile, credential presence, resolved endpoint, and whether an
authenticated request succeeds — with no secret in the output. To fix an auth
failure, see [Authentication](authentication.md).
