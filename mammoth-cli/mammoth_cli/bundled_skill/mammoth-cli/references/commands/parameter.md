# `parameter` commands

### `parameter.create`

Run: `mammoth parameter create`. Exact input fields: `mammoth schema get parameter.create --output json --no-input`.

Example: `mammoth parameter create 'Revenue report' --input '{"param_type": "sample", "value": "sample"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ParameterCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.delete`

Run: `mammoth parameter delete`. Exact input fields: `mammoth schema get parameter.delete --output json --no-input`.

Example: `mammoth parameter delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ParameterDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.dependencies`

Run: `mammoth parameter dependencies`. Exact input fields: `mammoth schema get parameter.dependencies --output json --no-input`.

Example: `mammoth parameter dependencies 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ParameterDependenciesResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.duplicate`

Run: `mammoth parameter duplicate`. Exact input fields: `mammoth schema get parameter.duplicate --output json --no-input`.

Example: `mammoth parameter duplicate 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ParameterDuplicateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.get`

Run: `mammoth parameter get`. Exact input fields: `mammoth schema get parameter.get --output json --no-input`.

Example: `mammoth parameter get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ParameterGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.group.create`

Run: `mammoth parameter group create`. Exact input fields: `mammoth schema get parameter.group.create --output json --no-input`.

Example: `mammoth parameter group create 'Revenue report' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ParameterGroupCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.group.delete`

Run: `mammoth parameter group delete`. Exact input fields: `mammoth schema get parameter.group.delete --output json --no-input`.

Example: `mammoth parameter group delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ParameterGroupDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.group.list`

Run: `mammoth parameter group list`. Exact input fields: `mammoth schema get parameter.group.list --output json --no-input`.

Example: `mammoth parameter group list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ParameterGroupListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.group.reorder`

Run: `mammoth parameter group reorder`. Exact input fields: `mammoth schema get parameter.group.reorder --output json --no-input`.

Example: `mammoth parameter group reorder --input '{"order": [1]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ParameterGroupReorderResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.group.update`

Run: `mammoth parameter group update`. Exact input fields: `mammoth schema get parameter.group.update --output json --no-input`.

Example: `mammoth parameter group update 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ParameterGroupUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.list`

Run: `mammoth parameter list`. Exact input fields: `mammoth schema get parameter.list --output json --no-input`.

Example: `mammoth parameter list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ParameterListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.rerun`

Run: `mammoth parameter rerun`. Exact input fields: `mammoth schema get parameter.rerun --output json --no-input`.

Example: `mammoth parameter rerun 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ParameterRerunResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.rerun-all-stale`

Run: `mammoth parameter rerun-all-stale`. Exact input fields: `mammoth schema get parameter.rerun-all-stale --output json --no-input`.

Example: `mammoth parameter rerun-all-stale --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ParameterRerunAllStaleResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `parameter.update`

Run: `mammoth parameter update`. Exact input fields: `mammoth schema get parameter.update --output json --no-input`.

Example: `mammoth parameter update 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ParameterUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
