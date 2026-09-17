# `completion` commands

### `completion.install`

Run: `mammoth completion install`. Exact input fields: `mammoth schema get completion.install --output json --no-input`.

Example: `mammoth completion install bash --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `CompletionInstallResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `completion.show`

Run: `mammoth completion show`. Exact input fields: `mammoth schema get completion.show --output json --no-input`.

Example: `mammoth completion show bash --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `CompletionShowResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
