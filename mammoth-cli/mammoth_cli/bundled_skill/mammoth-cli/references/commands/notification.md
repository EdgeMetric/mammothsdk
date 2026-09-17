# `notification` commands

### `notification.delete`

Run: `mammoth notification delete`. Exact input fields: `mammoth schema get notification.delete --output json --no-input`.

Example: `mammoth notification delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `NotificationDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `notification.delete-batch`

Run: `mammoth notification delete-batch`. Exact input fields: `mammoth schema get notification.delete-batch --output json --no-input`.

Example: `mammoth notification delete-batch --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `NotificationDeleteBatchResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `notification.list`

Run: `mammoth notification list`. Exact input fields: `mammoth schema get notification.list --output json --no-input`.

Example: `mammoth notification list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `NotificationListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `notification.update`

Run: `mammoth notification update`. Exact input fields: `mammoth schema get notification.update --output json --no-input`.

Example: `mammoth notification update 123 --input '{"patch": [{"sample_key": "Status"}]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `NotificationUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `notification.update-batch`

Run: `mammoth notification update-batch`. Exact input fields: `mammoth schema get notification.update-batch --output json --no-input`.

Example: `mammoth notification update-batch --input '{"patch": [{"sample_key": "Status"}]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `NotificationUpdateBatchResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
