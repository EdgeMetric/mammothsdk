# `external-key` commands

### `external-key.create`

Run: `mammoth external-key create`. Exact input fields: `mammoth schema get external-key.create --output json --no-input`.

Example: `mammoth external-key create --input '{"key_type": "open_ai", "key_name": "Revenue report", "secure_key": "sample"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `ExternalKeyCreateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `external-key.delete`

Run: `mammoth external-key delete`. Exact input fields: `mammoth schema get external-key.delete --output json --no-input`.

Example: `mammoth external-key delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ExternalKeyDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `external-key.get`

Run: `mammoth external-key get`. Exact input fields: `mammoth schema get external-key.get --output json --no-input`.

Example: `mammoth external-key get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ExternalKeyGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `external-key.list`

Run: `mammoth external-key list`. Exact input fields: `mammoth schema get external-key.list --output json --no-input`.

Example: `mammoth external-key list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ExternalKeyListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
