# `client-app` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `client-app.create`

Run: `mammoth client-app create`. Exact input fields: `mammoth schema get client-app.create --output json --no-input`.

Example: `mammoth client-app create 'Revenue report' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ClientAppCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `client-app.delete`

Run: `mammoth client-app delete`. Exact input fields: `mammoth schema get client-app.delete --output json --no-input`.

Example: `mammoth client-app delete sample --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ClientAppDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `client-app.get`

Run: `mammoth client-app get`. Exact input fields: `mammoth schema get client-app.get --output json --no-input`.

Example: `mammoth client-app get sample --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ClientAppGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `client-app.list`

Run: `mammoth client-app list`. Exact input fields: `mammoth schema get client-app.list --output json --no-input`.

Example: `mammoth client-app list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ClientAppListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — forbidden: backend_code=4GENR012 INVALID_TOKEN_FOR_CLIENT_APPS: 'Cannot access this API with API-tokens' on GET /workspaces/4/clientapps. Re-check before relying on it.

### `client-app.update`

Run: `mammoth client-app update`. Exact input fields: `mammoth schema get client-app.update --output json --no-input`.

Example: `mammoth client-app update sample --input '{"patch_request": {"patch": [{"op": "replace", "path": "role"}]}}' --output json --no-input`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B21 CLIENT_APP_PATCH_UNCONSTRAINED]: op/path/value are arbitrary strings; reserved, not registered.
