# `addon` commands

### `addon.connector.add`

Run: `mammoth addon connector add`. Exact input fields: `mammoth schema get addon.connector.add --output json --no-input`.

Example: `mammoth addon connector add --input '{"connector_id": 42}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `AddonConnectorAddResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `addon.connector.remove`

Run: `mammoth addon connector remove`. Exact input fields: `mammoth schema get addon.connector.remove --output json --no-input`.

Example: `mammoth addon connector remove --input '{"connector_id": 42}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `AddonConnectorRemoveResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `addon.list`

Run: `mammoth addon list`. Exact input fields: `mammoth schema get addon.list --output json --no-input`.

Example: `mammoth addon list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AddonListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `addon.storage.add`

Run: `mammoth addon storage add`. Exact input fields: `mammoth schema get addon.storage.add --output json --no-input`.

Example: `mammoth addon storage add --input '{"additional_storage_gb": 1}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `AddonStorageAddResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `addon.storage.remove`

Run: `mammoth addon storage remove`. Exact input fields: `mammoth schema get addon.storage.remove --output json --no-input`.

Example: `mammoth addon storage remove --input '{"removal_storage_gb": 1}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `AddonStorageRemoveResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `addon.user.add`

Run: `mammoth addon user add`. Exact input fields: `mammoth schema get addon.user.add --output json --no-input`.

Example: `mammoth addon user add --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `AddonUserAddResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `addon.user.remove`

Run: `mammoth addon user remove`. Exact input fields: `mammoth schema get addon.user.remove --output json --no-input`.

Example: `mammoth addon user remove --input '{"user_count": 1}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `AddonUserRemoveResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
