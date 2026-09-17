# `file` commands

### `file.bulk-delete`

Run: `mammoth file bulk-delete`. Exact input fields: `mammoth schema get file.bulk-delete --output json --no-input`.

Example: `mammoth file bulk-delete --input '{"file_ids": [1]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `FileBulkDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `file.delete`

Run: `mammoth file delete`. Exact input fields: `mammoth schema get file.delete --output json --no-input`.

Example: `mammoth file delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `FileDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `file.extract-sheets`

Run: `mammoth file extract-sheets`. Exact input fields: `mammoth schema get file.extract-sheets --output json --no-input`.

Example: `mammoth file extract-sheets 123 --input '{"sheets": ["sample"]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FileExtractSheetsResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `file.get`

Run: `mammoth file get`. Exact input fields: `mammoth schema get file.get --output json --no-input`.

Example: `mammoth file get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FileGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `file.list`

Run: `mammoth file list`. Exact input fields: `mammoth schema get file.list --output json --no-input`.

Example: `mammoth file list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FileListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `file.set-password`

Run: `mammoth file set-password`. Exact input fields: `mammoth schema get file.set-password --output json --no-input`.

Example: `mammoth file set-password 123 --input '{"password": "replace-with-secret"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `FileSetPasswordResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `file.update`

Run: `mammoth file update`. Exact input fields: `mammoth schema get file.update --output json --no-input`.

Example: `mammoth file update 123 --input '{"patch_request": {"patch": [{"op": "replace", "path": "extract_sheets", "value": "sample"}]}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FileUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `file.upload`

Run: `mammoth file upload`. Exact input fields: `mammoth schema get file.upload --output json --no-input`.

Example: `mammoth file upload ./sales.csv --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FileUploadResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `start_or_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `file.upload-folder`

Run: `mammoth file upload-folder`. Exact input fields: `mammoth schema get file.upload-folder --output json --no-input`.

Example: `mammoth file upload-folder ./sales.csv --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FileUploadFolderResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `start_or_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
