# `dataset` commands

### `dataset.batch-data`

Run: `mammoth dataset batch-data`. Exact input fields: `mammoth schema get dataset.batch-data --output json --no-input`.

Example: `mammoth dataset batch-data 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DatasetBatchDataResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.bulk-delete`

Run: `mammoth dataset bulk-delete`. Exact input fields: `mammoth schema get dataset.bulk-delete --output json --no-input`.

Example: `mammoth dataset bulk-delete --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DatasetBulkDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.bulk-update`

Run: `mammoth dataset bulk-update`. Exact input fields: `mammoth schema get dataset.bulk-update --output json --no-input`.

Example: `mammoth dataset bulk-update --input '{"patch_data": {"sample_key": "Status"}}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `DatasetBulkUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.create`

Run: `mammoth dataset create`. Exact input fields: `mammoth schema get dataset.create --output json --no-input`.

Example: `mammoth dataset create --input '{"dataset_spec": {"url": "https://sampledata.mammoth.io/Multi-Store_Retail_Sales.csv"}, "ds_creation_type": "weburl"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DatasetCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.create-from-pdf`

Run: `mammoth dataset create-from-pdf`. Exact input fields: `mammoth schema get dataset.create-from-pdf --output json --no-input`.

Example: `mammoth dataset create-from-pdf 123 --input '{"file_name": "./sales.csv"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DatasetCreateFromPdfResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.data`

Run: `mammoth dataset data`. Exact input fields: `mammoth schema get dataset.data --output json --no-input`.

Example: `mammoth dataset data 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DatasetDataResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.delete`

Run: `mammoth dataset delete`. Exact input fields: `mammoth schema get dataset.delete --output json --no-input`.

Example: `mammoth dataset delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DatasetDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.file-settings.get`

Run: `mammoth dataset file-settings get`. Exact input fields: `mammoth schema get dataset.file-settings.get --output json --no-input`.

Example: `mammoth dataset file-settings get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DatasetFileSettingsGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.file-settings.undo`

Run: `mammoth dataset file-settings undo`. Exact input fields: `mammoth schema get dataset.file-settings.undo --output json --no-input`.

Example: `mammoth dataset file-settings undo 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DatasetFileSettingsUndoResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.file-settings.update`

Run: `mammoth dataset file-settings update`. Exact input fields: `mammoth schema get dataset.file-settings.update --output json --no-input`.

Example: `mammoth dataset file-settings update 123 --input '{"delimiter": "sample", "has_header": true, "initial_skip_count": 1, "quotechar": "sample"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DatasetFileSettingsUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.get`

Run: `mammoth dataset get`. Exact input fields: `mammoth schema get dataset.get --output json --no-input`.

Example: `mammoth dataset get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DatasetGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.list`

Run: `mammoth dataset list`. Exact input fields: `mammoth schema get dataset.list --output json --no-input`.

Example: `mammoth dataset list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DatasetListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.rename`

Run: `mammoth dataset rename`. Exact input fields: `mammoth schema get dataset.rename --output json --no-input`.

Example: `mammoth dataset rename 123 --input '{"name": "Revenue report"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DatasetRenameResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.restore`

Run: `mammoth dataset restore`. Exact input fields: `mammoth schema get dataset.restore --output json --no-input`.

Example: `mammoth dataset restore 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DatasetRestoreResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.trash`

Run: `mammoth dataset trash`. Exact input fields: `mammoth schema get dataset.trash --output json --no-input`.

Example: `mammoth dataset trash 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DatasetTrashResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dataset.update`

Run: `mammoth dataset update`. Exact input fields: `mammoth schema get dataset.update --output json --no-input`.

Example: `mammoth dataset update --input '{"patch_data": [{"sample_key": "Status"}]}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `DatasetUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
