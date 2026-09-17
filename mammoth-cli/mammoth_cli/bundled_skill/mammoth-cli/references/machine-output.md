# Machine output and exit codes

## Success envelope (stdout)
```json
{"schema_version": 1, "data": <result>, "meta": {"command": "project list", "profile": "default", "workspace_id": 4, "project_id": 180, "pagination": null}}
```

## Error envelope (stderr)
```json
{"schema_version": 1, "error": {"code": "resource_not_found", "message": "...", "hint": "...", "details": {}, "request_id": null, "retryable": false, "authorization_required": false, "recovery_commands": ["..."]}}
```

## Representative result keys

These are compact shapes, not substitutes for `schema get`. IDs and field
names must come from the preceding read/create response.

The following are abbreviated from retained CLI 1.1.5 evidence, with values
reduced only for brevity. They show envelope keys, not a universal result
schema. Dashboard and transform result fields remain schema-driven.

```json
{"schema_version":1,"data":{"id":5,"ds_id":5,"name":"View 1","row_count":51,"status":"ready","metadata":[{"display_name":"store_id","internal_name":"column_1","type":"TEXT"}]},"meta":{"command":"view get","pagination":null,"profile":"expanded-live","project_id":null,"workspace_id":4}}
{"schema_version":1,"data":{"output_path":"dataview_12_12_export.csv"},"meta":{"command":"view export csv","pagination":null,"profile":"expanded-live","project_id":null,"workspace_id":4}}
```

Sources: `docs/live-evidence-20260917/transform-next/view-get.json` and
`docs/live-evidence-20260917/export-next/export-csv.json` (CLI 1.1.5).

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
