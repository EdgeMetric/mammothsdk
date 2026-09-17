# `trash` commands

### `trash.add`

Run: `mammoth trash add`. Exact input fields: `mammoth schema get trash.add --output json --no-input`.

Example: `mammoth trash add --input '{"items": [{"sample_key": "Status"}]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `TrashAddResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `trash.list`

Run: `mammoth trash list`. Exact input fields: `mammoth schema get trash.list --output json --no-input`.

Example: `mammoth trash list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `TrashListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `trash.restore`

Run: `mammoth trash restore`. Exact input fields: `mammoth schema get trash.restore --output json --no-input`.

Example: `mammoth trash restore --input '{"items": [{"sample_key": "Status"}]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `TrashRestoreResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
