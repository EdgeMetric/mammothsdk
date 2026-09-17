# `schedule` commands

### `schedule.create`

Run: `mammoth schedule create`. Exact input fields: `mammoth schema get schedule.create --output json --no-input`.

Example: `mammoth schedule create --input '{"spec": {"rrule": {"frequency": "minutely", "start": "2026-01-01T00:00:00Z"}}}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ScheduleCreateResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `schedule.delete`

Run: `mammoth schedule delete`. Exact input fields: `mammoth schema get schedule.delete --output json --no-input`.

Example: `mammoth schedule delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ScheduleDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `schedule.get`

Run: `mammoth schedule get`. Exact input fields: `mammoth schema get schedule.get --output json --no-input`.

Example: `mammoth schedule get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ScheduleGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `schedule.list`

Run: `mammoth schedule list`. Exact input fields: `mammoth schema get schedule.list --output json --no-input`.

Example: `mammoth schedule list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ScheduleListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `schedule.update`

Run: `mammoth schedule update`. Exact input fields: `mammoth schema get schedule.update --output json --no-input`.

Example: `mammoth schedule update 123 --input '{"patch": [{"op": "replace", "path": "rrule", "value": {"rrule": {"frequency": "minutely", "start": "2026-01-01T00:00:00Z"}, "work_items": [{"name": "pull_cloud_data", "execution_params": {"schedule_type": "moment", "first_pull_at": "now", "on_refresh_action": "replace"}, "args": [1]}]}}]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ScheduleUpdateResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
