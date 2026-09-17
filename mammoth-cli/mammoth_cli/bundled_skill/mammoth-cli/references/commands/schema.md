# `schema` commands

### `schema.find`

Run: `mammoth schema find`. Exact input fields: `mammoth schema get schema.find --output json --no-input`.

Example: `mammoth schema find 'view transform' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SchemaFindResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `schema.get`

Run: `mammoth schema get`. Exact input fields: `mammoth schema get schema.get --output json --no-input`.

Example: `mammoth schema get view.transform.bulk-replace --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SchemaGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `schema.list`

Run: `mammoth schema list`. Exact input fields: `mammoth schema get schema.list --output json --no-input`.

Example: `mammoth schema list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SchemaListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
