# `client-app` commands

### `client-app.create`

Run: `mammoth client-app create`. Exact input fields: `mammoth schema get client-app.create --output json --no-input`.

Example: `mammoth client-app create 'Revenue report' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `ClientAppCreateResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `client-app.delete`

Run: `mammoth client-app delete`. Exact input fields: `mammoth schema get client-app.delete --output json --no-input`.

Example: `mammoth client-app delete sample --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ClientAppDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `client-app.get`

Run: `mammoth client-app get`. Exact input fields: `mammoth schema get client-app.get --output json --no-input`.

Example: `mammoth client-app get sample --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ClientAppGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `client-app.list`

Run: `mammoth client-app list`. Exact input fields: `mammoth schema get client-app.list --output json --no-input`.

Example: `mammoth client-app list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ClientAppListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `client-app.update`

Run: `mammoth client-app update`. Exact input fields: `mammoth schema get client-app.update --output json --no-input`.

Example: `mammoth client-app update sample --input '{"patch_request": {"patch": [{"op": "replace", "path": "role"}]}}' --output json --no-input`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B21 CLIENT_APP_PATCH_UNCONSTRAINED]: op/path/value are arbitrary strings; reserved, not registered.
