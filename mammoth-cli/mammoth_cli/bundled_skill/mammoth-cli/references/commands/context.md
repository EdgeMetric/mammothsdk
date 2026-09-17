# `context` commands

### `context.project.clear`

Run: `mammoth context project clear`. Exact input fields: `mammoth schema get context.project.clear --output json --no-input`.

Example: `mammoth context project clear --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ContextProjectClearResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `context.project.status`

Run: `mammoth context project status`. Exact input fields: `mammoth schema get context.project.status --output json --no-input`.

Example: `mammoth context project status --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ContextProjectStatusResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `context.project.use`

Run: `mammoth context project use`. Exact input fields: `mammoth schema get context.project.use --output json --no-input`.

Example: `mammoth context project use 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ContextProjectUseResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
