# `report` commands

### `report.list`

Run: `mammoth report list`. Exact input fields: `mammoth schema get report.list --output json --no-input`.

Example: `mammoth report list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ReportListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
