# `webhook` commands

### `webhook.create`

Run: `mammoth webhook create`. Exact input fields: `mammoth schema get webhook.create --output json --no-input`.

Example: `mammoth webhook create 'Revenue report' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WebhookCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `webhook.delete`

Run: `mammoth webhook delete`. Exact input fields: `mammoth schema get webhook.delete --output json --no-input`.

Example: `mammoth webhook delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `WebhookDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `webhook.get`

Run: `mammoth webhook get`. Exact input fields: `mammoth schema get webhook.get --output json --no-input`.

Example: `mammoth webhook get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WebhookGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `webhook.list`

Run: `mammoth webhook list`. Exact input fields: `mammoth schema get webhook.list --output json --no-input`.

Example: `mammoth webhook list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WebhookListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `webhook.send`

Run: `mammoth webhook send`. Exact input fields: `mammoth schema get webhook.send --output json --no-input`.

Example: `mammoth webhook send --input '{"webhook_uri": "https://example.com/data.csv", "data": {"sample_key": "Status"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WebhookSendResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `webhook.send-get`

Run: `mammoth webhook send-get`. Exact input fields: `mammoth schema get webhook.send-get --output json --no-input`.

Example: `mammoth webhook send-get --input '{"webhook_uri": "https://example.com/data.csv"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WebhookSendGetResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `webhook.update`

Run: `mammoth webhook update`. Exact input fields: `mammoth schema get webhook.update --output json --no-input`.

Example: `mammoth webhook update 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WebhookUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
