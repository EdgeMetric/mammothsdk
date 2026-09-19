# `schedule` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `schedule.create`

Run: `mammoth schedule create`. Exact input fields: `mammoth schema get schedule.create --output json --no-input`.

Example: `mammoth schedule create --input '{"spec": {"rrule": {"frequency": "minutely", "start": "2026-01-01T00:00:00Z"}}}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ScheduleCreateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: observed blocker — backend_error: SUSPECTED CLI/BACKEND DEFECT: second create attempt (with work_items bound to dataset 85) returned HTTP 500 with empty response body, surfaced by CLI as code=outcome. Re-check before relying on it.

### `schedule.delete`

Run: `mammoth schedule delete`. Exact input fields: `mammoth schema get schedule.delete --output json --no-input`.

Example: `mammoth schedule delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ScheduleDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `schedule.get`

Run: `mammoth schedule get`. Exact input fields: `mammoth schema get schedule.get --output json --no-input`.

Example: `mammoth schedule get 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ScheduleGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — blocked_missing_fixture: Not run: id source schedule.list failed with backend_error (5GENR011 NOT_IMPLEMENTED, HTTP 400), so no schedule_id was observed to use. Re-check before relying on it.

### `schedule.list`

Run: `mammoth schedule list`. Exact input fields: `mammoth schema get schedule.list --output json --no-input`.

Example: `mammoth schedule list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ScheduleListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend_error: Re-confirms 5GENR011 NOT_IMPLEMENTED from family 3. Re-check before relying on it.

### `schedule.update`

Run: `mammoth schedule update`. Exact input fields: `mammoth schema get schedule.update --output json --no-input`.

Example: `mammoth schedule update 123 --input '{"patch": [{"op": "replace", "path": "rrule", "value": {"rrule": {"frequency": "minutely", "start": "2026-01-01T00:00:00Z"}, "work_items": [{"name": "pull_cloud_data", "execution_params": {"schedule_type": "moment", "first_pull_at": "now", "on_refresh_action": "replace"}, "args": [1]}]}}]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ScheduleUpdateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.
