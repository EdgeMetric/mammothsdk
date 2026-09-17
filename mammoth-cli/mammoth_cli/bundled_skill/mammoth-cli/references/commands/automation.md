# `automation` commands

### `automation.create`

Run: `mammoth automation create`. Exact input fields: `mammoth schema get automation.create --output json --no-input`.

Example: `mammoth automation create 'Revenue report' --input '{"description": "sample", "tasks": [{"task_type": "run_data_retrieval"}]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `AutomationCreateResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `automation.delete`

Run: `mammoth automation delete`. Exact input fields: `mammoth schema get automation.delete --output json --no-input`.

Example: `mammoth automation delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `AutomationDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `automation.get`

Run: `mammoth automation get`. Exact input fields: `mammoth schema get automation.get --output json --no-input`.

Example: `mammoth automation get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AutomationGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `automation.list`

Run: `mammoth automation list`. Exact input fields: `mammoth schema get automation.list --output json --no-input`.

Example: `mammoth automation list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AutomationListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `automation.restore`

Run: `mammoth automation restore`. Exact input fields: `mammoth schema get automation.restore --output json --no-input`.

Example: `mammoth automation restore 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AutomationRestoreResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `automation.trash`

Run: `mammoth automation trash`. Exact input fields: `mammoth schema get automation.trash --output json --no-input`.

Example: `mammoth automation trash 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AutomationTrashResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `automation.update`

Run: `mammoth automation update`. Exact input fields: `mammoth schema get automation.update --output json --no-input`.

Example: `mammoth automation update 123 --input '{"patch": [{"op": "replace", "path": "details", "value": "sample"}]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `AutomationUpdateResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
