# Troubleshooting: exit codes, errors, and recovery

[Documentation index](llms.txt)

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success with the command's documented result. |
| 1 | API, job, or local artifact error. |
| 2 | Usage, input, scope, or confirmation failure. |
| 4 | Authentication or authorization failure. |
| 5 | Resource not found in the requested scope. |
| 6 | Conflict with current remote state. |
| 7 | Retryable read/transport condition, or a timed-out known job; inspect the envelope before acting. |
| 130 | Interrupted; the CLI observed no terminal result. |

Exit status is only the first branch. It does not by itself establish that a
remote write did or did not commit.

## Error envelope

Errors print to stderr as one stable envelope:

```json
{"schema_version": 1, "error": {"code": "...", "message": "...", "hint": "...", "details": {}, "request_id": null, "retryable": false, "authorization_required": false, "recovery_commands": [], "log_ref": {"file": "~/.local/state/mammoth-cli/logs/2026-09-19.jsonl", "run_id": "b6bc6bf6d166"}}}
```

Branch on `error.code`, `details.operation_state`, and `request_id`, not the
human message. `log_ref` names the run log file and the `run_id` of the failed
invocation (see [Run log](#run-log)). `details` is secret-safe and may include `status_code`, HTTP
method, retry delay, phase, job/resource handle, and a quarantined local path.
`recovery_commands` are suggestions for inspection/correction, not permission
to blindly replay a mutation.

Important operation states include:

| State | Meaning | Next action |
|---|---|---|
| `not_started` | The server did not accept the operation. | Correct the reported input/scope and run it once. |
| `running` | A known asynchronous job is still active. | `mammoth job get JOB_ID` or `mammoth job wait JOB_ID`. |
| `succeeded` | A terminal result was observed. | Read back the target and compare acceptance evidence. |
| `failed` | The job or operation reached a terminal failure. | Inspect the failure and correct its cause. |
| `outcome_unknown` | A mutation may have committed, but its terminal result was not observed. | Re-read/reconcile the exact target and scope before any replay. |

## Common cases

| Exit | `error.code` | Next step |
|---|---|---|
| 4 | `not_authenticated`, `authentication_failed` | Run protected `mammoth auth login`, then `mammoth doctor`. |
| 4 | `authorization_required` | Check exact scope and request the required permission. |
| 2 | `login_input_required`, `project_required` | Supply the protected login document or explicit `--project PROJECT_ID`. |
| 2 | `confirmation_required`, `confirmation_target_mismatch` | Inspect the schema, then add `--yes` and the exact target confirmation. |
| 5 | `resource_not_found` | Re-list in the same workspace/project/parent scope. |
| 6 | `conflict` | Read current state and resolve the conflict before acting. |
| 7 | `timeout` with a job handle | Inspect/wait for that known job; do not submit another mutation. |
| 7 | `outcome_unknown` | Reconcile the suspected resource/job first; a retry may duplicate an effect. |
| 7 | `retryable_error` on a read | Honor `Retry-After`, then retry the read within the deadline. |
| 130 | `interrupted` | Use the observed handle/recovery command and checkpoint the state. |

## Run log

Every invocation appends structured JSON lines to a per-day file under the
run-log directory: `$MAMMOTH_LOG_DIR` if set, otherwise the platform state
directory (`~/.local/state/mammoth-cli/logs/YYYY-MM-DD.jsonl` on Linux,
`~/Library/Application Support/mammoth-cli/logs` on macOS,
`%LOCALAPPDATA%\Mammoth\mammoth-cli\logs` on Windows). The directory is
created `0700` and files `0600`; files older than 7 days are removed and a
day file over 20 MB is rotated to `.1.jsonl`.

Each run writes `command.start` (argv with the `--input` document redacted,
profile, project, CLI/SDK versions), one `http` record per API request
(method, path, status, duration, backend request id, outcome), `job.poll`
records under `--debug`, and `command.end` (exit status, error code,
duration). Headers, bodies and credentials are never logged; every record
passes through the same secret redaction as command output.

```bash
mammoth log path                                  # where the files are
mammoth log tail --input '{"errors_only": true, "limit": 20}'
mammoth log tail --input '{"run_id": "b6bc6bf6d166"}'   # one failed invocation
mammoth log tail --input '{"command_id": "view.transform.join", "days": 3}'
mammoth view get 49 28 --debug                    # mirror the records to stderr
```

`mammoth doctor` reports the directory as the `log_directory` check. When
you report a backend fault, quote the `run_id` and the `request_id` from the
matching `http` record.

## Update notice

`meta.update_available` in a success envelope (and one stderr line in human
modes) means a newer `mammoth-cli` is on PyPI; the check runs once a day after
a command, never before it, and `MAMMOTH_NO_UPDATE_CHECK=1` disables it.
`MAMMOTH_AUTO_UPGRADE=1` upgrades in place instead (opt-in; see
[upgrade](upgrade.md)).

## First diagnostic

Run read-only checks with the same profile and explicit project:

```bash
mammoth doctor --profile PROFILE
mammoth auth status --check --profile PROFILE
mammoth context project status --profile PROFILE
```

Capture the exit code, `error.code`, `details`, `request_id` and the
`log_ref.run_id` for support; never include an API secret or credentials file.

## Recovery sequence

For an interrupted or uncertain mutation, preserve the original command and
run a read or job inspection before changing configuration:

```bash
mammoth job get JOB_ID --profile PROFILE
mammoth view get VIEW_ID --project PROJECT_ID
```

If the operation has no known handle, re-list or read the exact scoped target
using the task's checkpoint. Compare IDs, status, schema, and evidence. Only
after reconciliation should the agent choose a new operation. See
[portable handoff](agent-handoff.md) for the checkpoint procedure.

## Every command takes a couple of seconds

Measured from a developer host: the CLI itself now starts in about 0.5 s
(2.0.31 caches the parsed command manifests under the OS cache directory and
builds command groups on demand; set `MAMMOTH_CLI_MANIFEST_CACHE=0` to
bypass the cache). The remainder is one TLS handshake per process (~0.7 s
from Europe to the hosted API) and 1–1.3 s of server time per request, the
same for a trivial `GET /workspaces/{id}/projects` on release and on prague.
Nothing in the CLI shortens that; run independent reads in parallel
processes and keep pipeline writes sequential.
