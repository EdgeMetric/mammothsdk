# `project` commands

### `project.bulk-delete`

Run: `mammoth project bulk-delete`. Exact input fields: `mammoth schema get project.bulk-delete --output json --no-input`.

Example: `mammoth project bulk-delete --input '{"project_ids": [1]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ProjectBulkDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.bulk-update`

Run: `mammoth project bulk-update`. Exact input fields: `mammoth schema get project.bulk-update --output json --no-input`.

Example: `mammoth project bulk-update --input '{"patch_data": {"patches": [{"op": "add", "path": "role", "value": [{"project_id": 456, "user_roles": [{"user_id": 123, "role": "project_analyst"}]}]}]}}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `ProjectBulkUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.checkpoint.list`

Run: `mammoth project checkpoint list`. Exact input fields: `mammoth schema get project.checkpoint.list --output json --no-input`.

Example: `mammoth project checkpoint list 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ProjectCheckpointListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.create`

Run: `mammoth project create`. Exact input fields: `mammoth schema get project.create --output json --no-input`.

Example: `mammoth project create 'Revenue report' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ProjectCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.data-check.list`

Run: `mammoth project data-check list`. Exact input fields: `mammoth schema get project.data-check.list --output json --no-input`.

Example: `mammoth project data-check list 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ProjectDataCheckListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.delete`

Run: `mammoth project delete`. Exact input fields: `mammoth schema get project.delete --output json --no-input`.

Example: `mammoth project delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ProjectDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.get`

Run: `mammoth project get`. Exact input fields: `mammoth schema get project.get --output json --no-input`.

Example: `mammoth project get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ProjectGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.list`

Run: `mammoth project list`. Exact input fields: `mammoth schema get project.list --output json --no-input`.

Example: `mammoth project list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ProjectListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.pending-changes`

Run: `mammoth project pending-changes`. Exact input fields: `mammoth schema get project.pending-changes --output json --no-input`.

Example: `mammoth project pending-changes 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ProjectPendingChangesResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.publish-credentials`

Run: `mammoth project publish-credentials`. Exact input fields: `mammoth schema get project.publish-credentials --output json --no-input`.

Example: `mammoth project publish-credentials 123 --input '{"odbc_type": "postgres"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ProjectPublishCredentialsResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.resource-dependencies`

Run: `mammoth project resource-dependencies`. Exact input fields: `mammoth schema get project.resource-dependencies --output json --no-input`.

Example: `mammoth project resource-dependencies 123 --input '{"resource_ids": [456]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ProjectResourceDependenciesResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.resource-dependencies.update`

Run: `mammoth project resource-dependencies update`. Exact input fields: `mammoth schema get project.resource-dependencies.update --output json --no-input`.

Example: `mammoth project resource-dependencies update 123 --input '{"patches": [{"op": "replace", "path": "data_sync", "value": {"context_type": "dataview", "context_id": 1}}]}' --output json --no-input --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `ProjectResourceDependenciesUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.resource-status`

Run: `mammoth project resource-status`. Exact input fields: `mammoth schema get project.resource-status --output json --no-input`.

Example: `mammoth project resource-status 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ProjectResourceStatusResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.sample-flow`

Run: `mammoth project sample-flow`. Exact input fields: `mammoth schema get project.sample-flow --output json --no-input`.

Example: `mammoth project sample-flow 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ProjectSampleFlowResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.update`

Run: `mammoth project update`. Exact input fields: `mammoth schema get project.update --output json --no-input`.

Example: `mammoth project update 123 --input '{"name": "Renamed project"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ProjectUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.user.add`

Run: `mammoth project user add`. Exact input fields: `mammoth schema get project.user.add --output json --no-input`.

Example: `mammoth project user add 123 --input '{"user_ids": [123], "role": "project_analyst"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `ProjectUserAddResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.user.remove`

Run: `mammoth project user remove`. Exact input fields: `mammoth schema get project.user.remove --output json --no-input`.

Example: `mammoth project user remove 123 --input '{"user_ids": ["resource-123"]}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `ProjectUserRemoveResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `project.user.update`

Run: `mammoth project user update`. Exact input fields: `mammoth schema get project.user.update --output json --no-input`.

Example: `mammoth project user update 123 --input '{"role": "project_admin", "user_id": 123}' --output json --no-input --yes`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ProjectUserUpdateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
