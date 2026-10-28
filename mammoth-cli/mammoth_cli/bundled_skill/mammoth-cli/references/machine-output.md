# Machine output and exit codes

## Success envelope (stdout)
```json
{"schema_version":1,"data":<result>,"meta":{"command":"project list","profile":"default","workspace_id":4,"project_id":180,"exit":0}}
```

Compact single-line JSON when stdout is not a terminal (pretty when it is;
`MAMMOTH_JSON_PRETTY=1` forces pretty). `meta` carries only the keys that have a
value: `exit` is the exit status (0, or 1 or 3 for a write whose read-back failed
or was partial); `run_id` names this invocation (the same id as `log_ref.run_id`, for
`mammoth log tail` and `mammoth history show`); `stderr` (embedded calls only) holds up to 500 characters a library
wrote to stderr during the call, and `elapsed_ms` (embedded calls only) its wall time;
`pagination` appears on paged reads, `update_available`
(`{"current", "latest", "command"}`) when a newer CLI is on PyPI (checked once
a day, after a command, never blocking). Run its `command` before starting a
task, not in the middle of one. `next_commands` appears after a main-flow
command that succeeded (`file upload`, `view create`, a `view transform`,
`dashboard v3 generate`, `dashboard figure add`, ...): one to three commands
filled in with this result's ids, usually the read-back. Run them as they are
when they fit the task; a write that did not verify has none.

## Error envelope (stdout, non-zero exit)
```json
{"schema_version": 1, "error": {"code": "resource_not_found", "message": "...", "hint": "...", "details": {}, "request_id": null, "retryable": false, "authorization_required": false, "recovery_commands": ["..."], "exit": 1, "log_ref": {"file": ".../logs/2026-09-19.jsonl", "run_id": "b6bc6bf6d166"}}}
```

With `-o json`, `-o ndjson` or `-o yaml` (also via `MAMMOTH_OUTPUT`, or `auto` on a pipe) the error
envelope is the one document on stdout, exactly where a success envelope would be, and the exit
status stays non-zero: read stdout, parse it, branch on `error` and the exit code. This covers
usage errors, refusals, unexpected exceptions and Ctrl-C. stderr carries only what a person reads
(the `Next:` line, hints, progress, `--debug` tracebacks); never depend on it. Only if stdout is
unwritable (a closed pipe) does the envelope fall back to stderr. Table, plain and csv output keep
the short `error [code]: message` text on stderr.

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
token); a name is left out when its lookup fails, and the ids are always present. A sign-in limited
to several projects adds `project_ids` to `auth login` and `token_projects` to `auth status --check`.

## Resource ids in results

One id key per resource, at the top level of `data`: `<resource>_id`. Every create-type command
(`create`, `create-*`, `duplicate`, `copy`) names the resource it made that way: `dataset create`
gives `dataset_id`, `project create` `project_id`, `connector connection create` `connection_id`
(the value `identity_key` / `connection_key` holds, which is the CONNECTION_KEY other commands
take), `dashboard create-blank` `dashboard_id`. A write that made a dataset, view or dashboard
(`file upload`, `view export dataset`, `dashboard v3 generate`, ...) also gives that
`<kind>_id`, and `job wait` / `job get` lift the `dataset_id`, `view_id` or `dashboard_id` their
`response` or `result` holds, so a script never reads `response.dataset_id`. The older keys
(`id`, `identity_key`, nested `response`) stay for compatibility; save `data.<resource>_id`, never
the whole reply. A result that carries no id (a job still running) has no such key: wait on its
`job_id`, then read the id from `job wait`.

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
`--output` accepts `auto`, `table`, `json`, `yaml`, `ndjson`, `plain` (`text`
is the same as `plain`), `csv`. Agents should use `json` (or `ndjson` for
documented streams). To read a skill file, `mammoth skill show -o plain`
(`--input '{"file": "references/..."}'` for another file) prints the markdown
as it is, not one escaped JSON string. `json` emits one
complete object; `ndjson` emits one complete envelope per line. Machine modes
never emit color or progress.

## Many commands, one process: `mammoth run`

`mammoth run [FILE|-]` reads JSON Lines (one object per line, blank lines skipped) and runs each
line in this one process: one credential load, one client and connection pool, warm caches.

| key | type | meaning |
|---|---|---|
| `cmd` | string, required | the command path as in `meta.command`, for example `"view task list"` |
| `args` | list | the positionals in order (strings or numbers). A flag the command itself declares (`"--full"`) is allowed here; global flags are not |
| `input` | object | the `--input` document |
| `flags` | object | global flags by long name without dashes: `{"project": 3633, "yes": true, "confirm": "42", "dry-run": true}`. Booleans take `true`/`false`, the others a string or number. `output`, `input`, `input-format`, `no-input`, `no-progress` and `color` are set by `run` and refused |
| `id` | string or number | echoed on that line's envelope |

Output is JSON Lines on stdout, one envelope per line: the envelope the single command prints
(`data` and `meta`, or `error`) plus `line` (the physical line number), `cmd`, `exit` and the
echoed `id`. The last line is the summary, which has no `line`: `data` holds `lines`, `ok`, `failed`,
`skipped`, `stopped_at`, `failed_lines`, `continue`, `dry_run` and `exit`.

- The run stops at the first failed line and exits with that line's status; the lines after it
  are `skipped`. `--continue` (before or after FILE) runs every line and exits with the first
  failure's status. Ctrl-C ends the whole run either way: the lines after it are `skipped` and the
  exit is 130. FILE defaults to stdin, so `mammoth run --continue < steps.jsonl` works.
- Only `\n` ends a line (a raw U+2028 inside a JSON string stays in it), a UTF-8 BOM is accepted,
  and `line` counts physical lines, blank ones included.
- A line is a command like any other. A mutating line without its own `"yes": true` (and
  `"confirm"` where the command needs the target) fails that line with `confirmation_required`;
  `run` has no global `--yes` or `--confirm` and refuses them.
- `--dry-run`, `--profile`, `--project`, `--session` and the timeout flags given to `run` apply to
  every line; a line's `flags` override all of them except `--dry-run`.
- A bad line (invalid JSON, a duplicate or unknown key, a flag in `args`, a reserved flag) is an
  `invalid_run_line` error for that line, exit 2. `run`, `auth login` and `auth logout` cannot be
  lines, however `cmd` and `args` spell them (`run_command_refused`).
- stdout carries only the envelopes (errors included); progress and diagnostics stay on stderr.
- Steps: a line with `"name": "up"` keeps its envelope, and a later line reads it in `args`,
  `input` or `flags` as `"{{steps.up.data.dataset.id}}"` (a whole-string reference keeps its type;
  paths take `[0]` indexes). `"when"` skips a line when false (`{"eq": [A, B]}`, `{"in": [A, LIST]}`,
  `{"not": C}`, `{"all": [...]}`, `{"any": [...]}`, `{"present": REF}`), printing `skipped: true`.
  `"for_each": "{{steps.ls.data.items}}"` runs a line once per item with `{{item}}` and `{{index}}`,
  one envelope per item (`item` = its index). `$keys`, `$first`, `$without` and `$default` build
  values. A reference that does not resolve fails the line with `unresolved_reference` (exit 2);
  under `--dry-run` the line is planned instead (`data.planned`, `data.waits_on`). JSON only: no code runs.

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
