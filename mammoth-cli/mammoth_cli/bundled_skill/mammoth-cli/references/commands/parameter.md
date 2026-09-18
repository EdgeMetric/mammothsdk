# `parameter` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `parameter.create`

Run: `mammoth parameter create`. Exact input fields: `mammoth schema get parameter.create --output json --no-input`.

Example: `mammoth parameter create 'Revenue report' --input '{"param_type": "sample", "value": "sample"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ParameterCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `parameter.delete`

Run: `mammoth parameter delete`. Exact input fields: `mammoth schema get parameter.delete --output json --no-input`.

Example: `mammoth parameter delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ParameterDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `parameter.dependencies`

Run: `mammoth parameter dependencies`. Exact input fields: `mammoth schema get parameter.dependencies --output json --no-input`.

Example: `mammoth parameter dependencies 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ParameterDependenciesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `parameter.duplicate`

Run: `mammoth parameter duplicate`. Exact input fields: `mammoth schema get parameter.duplicate --output json --no-input`.

Example: `mammoth parameter duplicate 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ParameterDuplicateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `parameter.get`

Run: `mammoth parameter get`. Exact input fields: `mammoth schema get parameter.get --output json --no-input`.

Example: `mammoth parameter get 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ParameterGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `parameter.group.create`

Run: `mammoth parameter group create`. Exact input fields: `mammoth schema get parameter.group.create --output json --no-input`.

Example: `mammoth parameter group create 'Revenue report' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ParameterGroupCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `parameter.group.delete`

Run: `mammoth parameter group delete`. Exact input fields: `mammoth schema get parameter.group.delete --output json --no-input`.

Example: `mammoth parameter group delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ParameterGroupDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `parameter.group.list`

Run: `mammoth parameter group list`. Exact input fields: `mammoth schema get parameter.group.list --output json --no-input`.

Example: `mammoth parameter group list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ParameterGroupListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: items, limit, next, offset, total_count. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `parameter.group.reorder`

Run: `mammoth parameter group reorder`. Exact input fields: `mammoth schema get parameter.group.reorder --output json --no-input`.

Example: `mammoth parameter group reorder --input '{"order": [1]}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ParameterGroupReorderResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `parameter.group.update`

Run: `mammoth parameter group update`. Exact input fields: `mammoth schema get parameter.group.update --output json --no-input`.

Example: `mammoth parameter group update 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ParameterGroupUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `parameter.list`

Run: `mammoth parameter list`. Exact input fields: `mammoth schema get parameter.list --output json --no-input`.

Example: `mammoth parameter list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ParameterListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: items, limit, next, offset, total_count. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `parameter.rerun`

Run: `mammoth parameter rerun`. Exact input fields: `mammoth schema get parameter.rerun --output json --no-input`.

Example: `mammoth parameter rerun 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ParameterRerunResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `parameter.rerun-all-stale`

Run: `mammoth parameter rerun-all-stale`. Exact input fields: `mammoth schema get parameter.rerun-all-stale --output json --no-input`.

Example: `mammoth parameter rerun-all-stale --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ParameterRerunAllStaleResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `parameter.update`

Run: `mammoth parameter update`. Exact input fields: `mammoth schema get parameter.update --output json --no-input`.

Example: `mammoth parameter update 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ParameterUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
