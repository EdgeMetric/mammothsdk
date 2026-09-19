# Machine output and exit codes

## Success envelope (stdout)
```json
{"schema_version": 1, "data": <result>, "meta": {"command": "project list", "profile": "default", "workspace_id": 4, "project_id": 180, "pagination": null, "update_available": null}}
```

`meta.update_available` is `null` or `{"current", "latest", "command"}` when a
newer CLI is on PyPI (checked once a day, after a command, never blocking).
Run its `command` before starting a task, not in the middle of one.

## Error envelope (stderr)
```json
{"schema_version": 1, "error": {"code": "resource_not_found", "message": "...", "hint": "...", "details": {}, "request_id": null, "retryable": false, "authorization_required": false, "recovery_commands": ["..."], "log_ref": {"file": ".../logs/2026-09-19.jsonl", "run_id": "b6bc6bf6d166"}}}
```

`log_ref` points at the local run log: `mammoth log tail --input '{"run_id": "RUN_ID"}' --output json --no-input` lists every request that invocation made, with HTTP status and backend `request_id`. Quote both when reporting a backend fault.

## Representative result keys

These are compact shapes, not substitutes for `schema get`. IDs and field
names must come from the preceding read/create response.

The following are illustrative envelope shapes. They show keys, not a universal
result schema; dashboard and transform result fields remain schema-driven.

```json
{"schema_version":1,"data":{"id":5,"ds_id":5,"name":"View 1","row_count":51,"status":"ready","metadata":[{"display_name":"store_id","internal_name":"column_1","type":"TEXT"}]},"meta":{"command":"view get","pagination":null,"profile":"expanded-live","project_id":null,"workspace_id":4}}
{"schema_version":1,"data":{"output_path":"dataview_12_12_export.csv"},"meta":{"command":"view export csv","pagination":null,"profile":"expanded-live","project_id":null,"workspace_id":4}}
```

For pagination, preserve the returned `meta.pagination`/`data.next` cursor and
request the next page only with fields accepted by that command's schema. For
auth, `auth status` reports profile/endpoint/workspace state but never a
secret. A rejected mutation remains the error envelope above; use its recovery
command or a read-back, rather than treating a model/result type as success.

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
