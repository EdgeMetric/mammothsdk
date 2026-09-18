# `folder` commands

### `folder.bulk-delete`

Run: `mammoth folder bulk-delete`. Exact input fields: `mammoth schema get folder.bulk-delete --output json --no-input`.

Example: `mammoth folder bulk-delete --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `FolderBulkDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `folder.create`

Run: `mammoth folder create`. Exact input fields: `mammoth schema get folder.create --output json --no-input`.

Example: `mammoth folder create 'Revenue report' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FolderCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `folder.delete`

Run: `mammoth folder delete`. Exact input fields: `mammoth schema get folder.delete --output json --no-input`.

Example: `mammoth folder delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `FolderDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `folder.find`

Run: `mammoth folder find`. Exact input fields: `mammoth schema get folder.find --output json --no-input`.

Example: `mammoth folder find reports --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FolderFindResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `folder.get`

Run: `mammoth folder get`. Exact input fields: `mammoth schema get folder.get --output json --no-input`.

Example: `mammoth folder get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FolderGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `folder.list`

Run: `mammoth folder list`. Exact input fields: `mammoth schema get folder.list --output json --no-input`.

Example: `mammoth folder list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FolderListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `folder.move`

Run: `mammoth folder move`. Exact input fields: `mammoth schema get folder.move --output json --no-input`.

Example: `mammoth folder move --input '{"resource_ids": [8024], "target_folder_resource_id": "root"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FolderMoveResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `folder.root`

Run: `mammoth folder root`. Exact input fields: `mammoth schema get folder.root --output json --no-input`.

Example: `mammoth folder root --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FolderRootResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `folder.trash`

Run: `mammoth folder trash`. Exact input fields: `mammoth schema get folder.trash --output json --no-input`.

Example: `mammoth folder trash 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FolderTrashResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `folder.update`

Run: `mammoth folder update`. Exact input fields: `mammoth schema get folder.update --output json --no-input`.

Example: `mammoth folder update 123 --input '{"name": "Revenue report"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `FolderUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
