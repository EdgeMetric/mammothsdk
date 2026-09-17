# `capability` commands

### `capability.find`

Run: `mammoth capability find`. Exact input fields: `mammoth schema get capability.find --output json --no-input`.

Example: `mammoth capability find 'show projects' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `CapabilityFindResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `capability.get`

Run: `mammoth capability get`. Exact input fields: `mammoth schema get capability.get --output json --no-input`.

Example: `mammoth capability get AddTask --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `CapabilityGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `capability.list`

Run: `mammoth capability list`. Exact input fields: `mammoth schema get capability.list --output json --no-input`.

Example: `mammoth capability list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `CapabilityListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
