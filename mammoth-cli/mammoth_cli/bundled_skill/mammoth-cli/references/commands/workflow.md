# `workflow` commands

### `workflow.block.add`

Run: `mammoth workflow block add`. Exact input fields: `mammoth schema get workflow.block.add --output json --no-input`.

Example: `mammoth workflow block add 123 --input '{"block_type": "sample"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowBlockAddResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.block.auth`

Run: `mammoth workflow block auth`. Exact input fields: `mammoth schema get workflow.block.auth --output json --no-input`.

Example: `mammoth workflow block auth 123 123 --input '{"auth_data": {"sample_key": "Status"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowBlockAuthResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.block.config`

Run: `mammoth workflow block config`. Exact input fields: `mammoth schema get workflow.block.config --output json --no-input`.

Example: `mammoth workflow block config 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowBlockConfigResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.block.type`

Run: `mammoth workflow block type`. Exact input fields: `mammoth schema get workflow.block.type --output json --no-input`.

Example: `mammoth workflow block type 123 123 --input '{"connection_type": "sample"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowBlockTypeResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.canvas`

Run: `mammoth workflow canvas`. Exact input fields: `mammoth schema get workflow.canvas --output json --no-input`.

Example: `mammoth workflow canvas 123 --input '{"canvas_state": {"sample_key": "Status"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowCanvasResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.cleanup`

Run: `mammoth workflow cleanup`. Exact input fields: `mammoth schema get workflow.cleanup --output json --no-input`.

Example: `mammoth workflow cleanup --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowCleanupResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.create`

Run: `mammoth workflow create`. Exact input fields: `mammoth schema get workflow.create --output json --no-input`.

Example: `mammoth workflow create 'Revenue report' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.delete`

Run: `mammoth workflow delete`. Exact input fields: `mammoth schema get workflow.delete --output json --no-input`.

Example: `mammoth workflow delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `WorkflowDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.from-template`

Run: `mammoth workflow from-template`. Exact input fields: `mammoth schema get workflow.from-template --output json --no-input`.

Example: `mammoth workflow from-template 123 --input '{"workflow_name": "Revenue report"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowFromTemplateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.get`

Run: `mammoth workflow get`. Exact input fields: `mammoth schema get workflow.get --output json --no-input`.

Example: `mammoth workflow get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.graph`

Run: `mammoth workflow graph`. Exact input fields: `mammoth schema get workflow.graph --output json --no-input`.

Example: `mammoth workflow graph --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowGraphResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.list`

Run: `mammoth workflow list`. Exact input fields: `mammoth schema get workflow.list --output json --no-input`.

Example: `mammoth workflow list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.update`

Run: `mammoth workflow update`. Exact input fields: `mammoth schema get workflow.update --output json --no-input`.

Example: `mammoth workflow update 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.workspace-datasets`

Run: `mammoth workflow workspace-datasets`. Exact input fields: `mammoth schema get workflow.workspace-datasets --output json --no-input`.

Example: `mammoth workflow workspace-datasets --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowWorkspaceDatasetsResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.workspace-exports`

Run: `mammoth workflow workspace-exports`. Exact input fields: `mammoth schema get workflow.workspace-exports --output json --no-input`.

Example: `mammoth workflow workspace-exports --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowWorkspaceExportsResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `workflow.workspace-sources`

Run: `mammoth workflow workspace-sources`. Exact input fields: `mammoth schema get workflow.workspace-sources --output json --no-input`.

Example: `mammoth workflow workspace-sources --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `WorkflowWorkspaceSourcesResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
