# `activity` commands

### `activity.export`

Run: `mammoth activity export`. Exact input fields: `mammoth schema get activity.export --output json --no-input`.

Example: `mammoth activity export --output json --no-input`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B19 ACTIVITY_EXPORT_UNTYPED_ASYNC]: format/filters/download response are raw; reserved, not registered.

### `activity.list`

Run: `mammoth activity list`. Exact input fields: `mammoth schema get activity.list --output json --no-input`.

Example: `mammoth activity list --output json --no-input`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B17 VARIADIC_INPUT_UNTYPED]: **filters is unconstrained; reserved, not registered.
