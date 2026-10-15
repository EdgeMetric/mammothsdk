# Machine output and exit codes

## Success envelope (stdout)
```json
{"schema_version":1,"data":<result>,"meta":{"command":"project list","profile":"default","workspace_id":4,"project_id":180}}
```

Compact single-line JSON when stdout is not a terminal (pretty when it is;
`MAMMOTH_JSON_PRETTY=1` forces pretty). `meta` carries only the keys that have a
value: `pagination` appears on paged reads, `update_available`
(`{"current", "latest", "command"}`) when a newer CLI is on PyPI (checked once
a day, after a command, never blocking). Run its `command` before starting a
task, not in the middle of one.

## Error envelope (stderr)
```json
{"schema_version": 1, "error": {"code": "resource_not_found", "message": "...", "hint": "...", "details": {}, "request_id": null, "retryable": false, "authorization_required": false, "recovery_commands": ["..."], "log_ref": {"file": ".../logs/2026-09-19.jsonl", "run_id": "b6bc6bf6d166"}}}
```

A mistyped command, option or column carries `details.did_you_mean`: the nearest
commands (unknown command), the nearest option (`--profle`, or `"--project 3633"`
passed as one argument: pass the value separately) or the nearest column (`Day`
for `day`). Use it instead of guessing again.

`log_ref` points at the local run log: `mammoth log tail --input '{"run_id": "RUN_ID"}'` lists every request that invocation made, with HTTP status and backend `request_id`. Quote both when reporting a backend fault.

## `auth status` and token expiry

`data.expires_at` is the OAuth access token's expiry (about one hour ahead), not the login's.
`data.access_token_expires_at` is the same value under a clearer name, `data.refreshes_automatically`
is `true` and `data.expires_at_note` says so; the CLI renews the token itself, and only a failed
refresh (`login_expired`, exit 4) needs a new `mammoth auth login`. `auth status --check` and
`auth login` add `workspace_name` (and `project_name` / `token_project_name` for a project-limited
token); a name is left out when its lookup fails, and the ids are always present.

## Representative result keys

These are compact shapes, not substitutes for `schema get`. IDs and field
names must come from the preceding read/create response.

The following are illustrative envelope shapes. They show keys, not a universal
result schema; dashboard and transform result fields remain schema-driven.

```json
{"schema_version":1,"data":{"id":5,"ds_id":5,"name":"View 1","row_count":51,"status":"ready","metadata":[{"display_name":"store_id","internal_name":"column_1","type":"TEXT"}]},"meta":{"command":"view get","profile":"expanded-live","workspace_id":4}}
{"schema_version":1,"data":{"output_path":"dataview_12_12_export.csv"},"meta":{"command":"view export csv","profile":"expanded-live","workspace_id":4}}
```

For pagination, preserve the returned `meta.pagination` and, on `view data get`,
`view export list` and `view pipeline items`, the `paging` block: `offset` is
0-based (`0` is the first page), and `next_command` / `previous_command` are ready
to run (null at the ends). Request pages only with fields accepted by that
command's schema. For
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
| 1 | API, job, or local artifact error; also a write that did not verify (`status: failed`) |
| 2 | usage / input / confirmation failure |
| 3 | partial: a write whose read-back shows only part of it (`status: partial`) |
| 4 | authentication failure |
| 5 | not found |
| 6 | conflict, or `file_exists` (pass `--overwrite` to replace a local file) |
| 7 | retryable read/transport or timed-out known job; inspect the envelope |
| 130 | interrupted |

Branch on the exit code, stable `error.code`, and `details.operation_state`; never
parse the message. A write still running reports `status: pending` with
`verify.next_command` and exits 0: it was accepted, so wait on it and do not replay it. `outcome_unknown` means a mutation may have committed and
must be reconciled before replay.
