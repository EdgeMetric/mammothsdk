# `config` commands

### `config.get`

Run: `mammoth config get`. Exact input fields: `mammoth schema get config.get --output json --no-input`.

Example: `mammoth config get output --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConfigGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `config.list`

Run: `mammoth config list`. Exact input fields: `mammoth schema get config.list --output json --no-input`.

Example: `mammoth config list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConfigListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `config.path`

Run: `mammoth config path`. Exact input fields: `mammoth schema get config.path --output json --no-input`.

Example: `mammoth config path --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConfigPathResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `config.set`

Run: `mammoth config set`. Exact input fields: `mammoth schema get config.set --output json --no-input`.

Example: `mammoth config set output text --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConfigSetResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
