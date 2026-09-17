# `data-app` commands

### `data-app.active-job`

Run: `mammoth data-app active-job`. Exact input fields: `mammoth schema get data-app.active-job --output json --no-input`.

Example: `mammoth data-app active-job 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DataAppActiveJobResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `data-app.create`

Run: `mammoth data-app create`. Exact input fields: `mammoth schema get data-app.create --output json --no-input`.

Example: `mammoth data-app create --input '{"body": {"automation_id": 1, "dashboard_ids": [1], "name": "Revenue report", "project_id": 1}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DataAppCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `data-app.delete`

Run: `mammoth data-app delete`. Exact input fields: `mammoth schema get data-app.delete --output json --no-input`.

Example: `mammoth data-app delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DataAppDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `data-app.get`

Run: `mammoth data-app get`. Exact input fields: `mammoth schema get data-app.get --output json --no-input`.

Example: `mammoth data-app get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DataAppGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `data-app.job`

Run: `mammoth data-app job`. Exact input fields: `mammoth schema get data-app.job --output json --no-input`.

Example: `mammoth data-app job 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DataAppJobResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `data-app.list`

Run: `mammoth data-app list`. Exact input fields: `mammoth schema get data-app.list --output json --no-input`.

Example: `mammoth data-app list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DataAppListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `data-app.pipeline-changes`

Run: `mammoth data-app pipeline-changes`. Exact input fields: `mammoth schema get data-app.pipeline-changes --output json --no-input`.

Example: `mammoth data-app pipeline-changes 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DataAppPipelineChangesResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `data-app.share`

Run: `mammoth data-app share`. Exact input fields: `mammoth schema get data-app.share --output json --no-input`.

Example: `mammoth data-app share 123 --input '{"body": {"params": {"auth": {"type_of_auth": "mammoth"}}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DataAppShareResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `data-app.update`

Run: `mammoth data-app update`. Exact input fields: `mammoth schema get data-app.update --output json --no-input`.

Example: `mammoth data-app update 123 --input '{"body": {"params": {"name": "Revenue report"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DataAppUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `data-app.upload`

Run: `mammoth data-app upload`. Exact input fields: `mammoth schema get data-app.upload --output json --no-input`.

Example: `mammoth data-app upload 123 ./sales.csv --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DataAppUploadResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `data-app.user.list`

Run: `mammoth data-app user list`. Exact input fields: `mammoth schema get data-app.user.list --output json --no-input`.

Example: `mammoth data-app user list 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DataAppUserListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `data-app.user.remove`

Run: `mammoth data-app user remove`. Exact input fields: `mammoth schema get data-app.user.remove --output json --no-input`.

Example: `mammoth data-app user remove 123 analyst@example.com --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DataAppUserRemoveResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
