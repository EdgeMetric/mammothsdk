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
`--output` accepts `table` (default, human), `json`, `yaml`, `ndjson`, `plain`.
Agents should use `json` (or `ndjson` for streams). Machine modes never emit
color or progress.

## Exit codes
| code | meaning |
|---|---|
| 0 | success |
| 1 | API error |
| 2 | usage / input / confirmation failure |
| 4 | authentication failure |
| 5 | not found |
| 6 | conflict |
| 7 | retryable (network/timeout) |
| 130 | interrupted |

Branch on the exit code and the stable `error.code`; never parse the message.
