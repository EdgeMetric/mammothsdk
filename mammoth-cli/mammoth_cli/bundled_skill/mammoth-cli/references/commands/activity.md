# `activity` commands

### `activity.export`

Run: `mammoth activity export`. Exact input fields: `mammoth schema get activity.export --output json --no-input`.

Example: `mammoth activity export --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ActivityExportResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `activity.list`

Run: `mammoth activity list`. Exact input fields: `mammoth schema get activity.list --output json --no-input`.

Example: `mammoth activity list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ActivityListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
