# `batch` commands

### `batch.bulk-delete`

Run: `mammoth batch bulk-delete`. Exact input fields: `mammoth schema get batch.bulk-delete --output json --no-input`.

Example: `mammoth batch bulk-delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `BatchBulkDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `batch.create`

Run: `mammoth batch create`. Exact input fields: `mammoth schema get batch.create --output json --no-input`.

Example: `mammoth batch create 123 123 --input '{"mapping": {"sample_key": "Status"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `BatchCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `batch.create-spec`

Run: `mammoth batch create-spec`. Exact input fields: `mammoth schema get batch.create-spec --output json --no-input`.

Example: `mammoth batch create-spec 123 --input '{"file_id": 94}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `BatchCreateSpecResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `batch.delete`

Run: `mammoth batch delete`. Exact input fields: `mammoth schema get batch.delete --output json --no-input`.

Example: `mammoth batch delete 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `BatchDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `batch.get`

Run: `mammoth batch get`. Exact input fields: `mammoth schema get batch.get --output json --no-input`.

Example: `mammoth batch get 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `BatchGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `batch.list`

Run: `mammoth batch list`. Exact input fields: `mammoth schema get batch.list --output json --no-input`.

Example: `mammoth batch list 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `BatchListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `batch.update`

Run: `mammoth batch update`. Exact input fields: `mammoth schema get batch.update --output json --no-input`.

Example: `mammoth batch update 123 --input '{"patch": [{"sample_key": "Status"}]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `BatchUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
