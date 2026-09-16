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
{"schema_version": 1, "error": {"code": "...", "message": "...", "hint": "...", "details": {}, "request_id": null, "retryable": false, "authorization_required": false, "recovery_commands": []}}
```

Branch on `error.code`, `details.operation_state`, and `request_id`, not the
human message. `details` is secret-safe and may include `status_code`, HTTP
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

## First diagnostic

Run read-only checks with the same profile and explicit project:

```bash
mammoth doctor --profile PROFILE --output json --no-input
mammoth auth status --check --profile PROFILE --output json --no-input
mammoth context project status --profile PROFILE --output json --no-input
```

Capture the exit code, `error.code`, `details`, and `request_id` for support;
never include an API secret or credentials file.

## Recovery sequence

For an interrupted or uncertain mutation, preserve the original command and
run a read or job inspection before changing configuration:

```bash
mammoth job get JOB_ID --profile PROFILE --output json --no-input
mammoth view get VIEW_ID --project PROJECT_ID --output json --no-input
```

If the operation has no known handle, re-list or read the exact scoped target
using the task's checkpoint. Compare IDs, status, schema, and evidence. Only
after reconciliation should the agent choose a new operation. See
[portable handoff](agent-handoff.md) for the checkpoint procedure.
