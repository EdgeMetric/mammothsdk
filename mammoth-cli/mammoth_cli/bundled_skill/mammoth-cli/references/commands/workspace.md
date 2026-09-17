# `workspace` commands

### `workspace.accept-invite`

Run: `mammoth workspace accept-invite`. Exact input fields: `mammoth schema get workspace.accept-invite --output json --no-input`.

Example: `mammoth workspace accept-invite --input '{"token": "replace-with-secret"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceAcceptInviteResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.app-usage`

Run: `mammoth workspace app-usage`. Exact input fields: `mammoth schema get workspace.app-usage --output json --no-input`.

Example: `mammoth workspace app-usage --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceAppUsageResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.check-expression`

Run: `mammoth workspace check-expression`. Exact input fields: `mammoth schema get workspace.check-expression --output json --no-input`.

Example: `mammoth workspace check-expression --input '{"body": {"intent": "Summarize revenue by region"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceCheckExpressionResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.create`

Run: `mammoth workspace create`. Exact input fields: `mammoth schema get workspace.create --output json --no-input`.

Example: `mammoth workspace create --input '{"body": {}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.delete`

Run: `mammoth workspace delete`. Exact input fields: `mammoth schema get workspace.delete --output json --no-input`.

Example: `mammoth workspace delete 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `WorkspaceDeleteResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.get`

Run: `mammoth workspace get`. Exact input fields: `mammoth schema get workspace.get --output json --no-input`.

Example: `mammoth workspace get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.list`

Run: `mammoth workspace list`. Exact input fields: `mammoth schema get workspace.list --output json --no-input`.

Example: `mammoth workspace list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.llm-task`

Run: `mammoth workspace llm-task`. Exact input fields: `mammoth schema get workspace.llm-task --output json --no-input`.

Example: `mammoth workspace llm-task --input '{"task_type": "sample", "params": {"sample_key": "Status"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceLlmTaskResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.reactivate`

Run: `mammoth workspace reactivate`. Exact input fields: `mammoth schema get workspace.reactivate --output json --no-input`.

Example: `mammoth workspace reactivate 123 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `WorkspaceReactivateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.segment.list`

Run: `mammoth workspace segment list`. Exact input fields: `mammoth schema get workspace.segment.list --output json --no-input`.

Example: `mammoth workspace segment list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceSegmentListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.segment.update`

Run: `mammoth workspace segment update`. Exact input fields: `mammoth schema get workspace.segment.update --output json --no-input`.

Example: `mammoth workspace segment update --input '{"patch": [{"sample_key": "Status"}]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceSegmentUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.storage-breakdown`

Run: `mammoth workspace storage-breakdown`. Exact input fields: `mammoth schema get workspace.storage-breakdown --output json --no-input`.

Example: `mammoth workspace storage-breakdown --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceStorageBreakdownResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.update`

Run: `mammoth workspace update`. Exact input fields: `mammoth schema get workspace.update --output json --no-input`.

Example: `mammoth workspace update 123 --input '{"patches": [{"op": "replace", "path": "name", "value": "sample"}]}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `WorkspaceUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.user.add`

Run: `mammoth workspace user add`. Exact input fields: `mammoth schema get workspace.user.add --output json --no-input`.

Example: `mammoth workspace user add --input '{"email_ids": ["analyst@example.com"]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceUserAddResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.user.get`

Run: `mammoth workspace user get`. Exact input fields: `mammoth schema get workspace.user.get --output json --no-input`.

Example: `mammoth workspace user get resource-123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceUserGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.user.list`

Run: `mammoth workspace user list`. Exact input fields: `mammoth schema get workspace.user.list --output json --no-input`.

Example: `mammoth workspace user list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceUserListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.user.remove`

Run: `mammoth workspace user remove`. Exact input fields: `mammoth schema get workspace.user.remove --output json --no-input`.

Example: `mammoth workspace user remove 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `WorkspaceUserRemoveResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.user.remove-batch`

Run: `mammoth workspace user remove-batch`. Exact input fields: `mammoth schema get workspace.user.remove-batch --output json --no-input`.

Example: `mammoth workspace user remove-batch --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `WorkspaceUserRemoveBatchResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.user.update`

Run: `mammoth workspace user update`. Exact input fields: `mammoth schema get workspace.user.update --output json --no-input`.

Example: `mammoth workspace user update resource-123 --input '{"patches": [{"op": "replace", "path": "role", "value": "workspace_member"}]}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `WorkspaceUserUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workspace.user.update-batch`

Run: `mammoth workspace user update-batch`. Exact input fields: `mammoth schema get workspace.user.update-batch --output json --no-input`.

Example: `mammoth workspace user update-batch --input '{"patches": [{"sample_key": "Status"}]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkspaceUserUpdateBatchResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
