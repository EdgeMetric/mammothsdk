# Machine output and exit codes

## Success envelope (stdout)
```json
{"schema_version": 1, "data": <result>, "meta": {"command": "project list", "profile": "default", "workspace_id": 4, "project_id": 180, "pagination": null}}
```

## Error envelope (stderr)
```json
{"schema_version": 1, "error": {"code": "resource_not_found", "message": "...", "hint": "...", "details": {}, "request_id": null, "retryable": false, "authorization_required": false, "recovery_commands": ["..."]}}
```

## Output modes
`--output` accepts `auto`, `table`, `json`, `yaml`, `ndjson`, `plain`. Agents
should use `json` (or `ndjson` for documented streams). `json` emits one
complete object; `ndjson` emits one complete envelope per line. Machine modes
never emit color or progress.

## Exit codes
| code | meaning |
|---|---|
| 0 | success |
| 1 | API, job, or local artifact error |
| 2 | usage / input / confirmation failure |
| 4 | authentication failure |
| 5 | not found |
| 6 | conflict |
| 7 | retryable read/transport or timed-out known job; inspect the envelope |
| 130 | interrupted |

Branch on the exit code, stable `error.code`, and `details.operation_state`; never
parse the message. `outcome_unknown` means a mutation may have committed and
must be reconciled before replay.
