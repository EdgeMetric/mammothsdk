# `user` commands

### `user.avatar.delete`

Run: `mammoth user avatar delete`. Exact input fields: `mammoth schema get user.avatar.delete --output json --no-input`.

Example: `mammoth user avatar delete --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `UserAvatarDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `user.avatar.upload`

Run: `mammoth user avatar upload`. Exact input fields: `mammoth schema get user.avatar.upload --output json --no-input`.

Example: `mammoth user avatar upload ./sales.csv --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `UserAvatarUploadResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `user.change-password`

Run: `mammoth user change-password`. Exact input fields: `mammoth schema get user.change-password --output json --no-input`.

Example: `mammoth user change-password --input '{"current_password": "replace-with-secret", "new_password": "replace-with-secret"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `UserChangePasswordResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `user.delete-account`

Run: `mammoth user delete-account`. Exact input fields: `mammoth schema get user.delete-account --output json --no-input`.

Example: `mammoth user delete-account --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `UserDeleteAccountResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `user.get`

Run: `mammoth user get`. Exact input fields: `mammoth schema get user.get --output json --no-input`.

Example: `mammoth user get --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `UserGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `user.preference.get`

Run: `mammoth user preference get`. Exact input fields: `mammoth schema get user.preference.get --output json --no-input`.

Example: `mammoth user preference get --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `UserPreferenceGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `user.preference.update`

Run: `mammoth user preference update`. Exact input fields: `mammoth schema get user.preference.update --output json --no-input`.

Example: `mammoth user preference update --output json --no-input`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B17 VARIADIC_INPUT_UNTYPED]: **prefs is unconstrained; reserved, not registered.

### `user.update`

Run: `mammoth user update`. Exact input fields: `mammoth schema get user.update --output json --no-input`.

Example: `mammoth user update --output json --no-input`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B17 VARIADIC_INPUT_UNTYPED]: **fields is unconstrained; reserved, not registered.
