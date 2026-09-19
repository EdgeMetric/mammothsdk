# `notification` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `notification.delete`

Run: `mammoth notification delete`. Exact input fields: `mammoth schema get notification.delete --output json --no-input`.

Example: `mammoth notification delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `NotificationDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `notification.delete-batch`

Run: `mammoth notification delete-batch`. Exact input fields: `mammoth schema get notification.delete-batch --output json --no-input`.

Example: `mammoth notification delete-batch --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `NotificationDeleteBatchResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `notification.list`

Run: `mammoth notification list`. Exact input fields: `mammoth schema get notification.list --output json --no-input`.

Example: `mammoth notification list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `NotificationListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Empty result on this fixture. No notifications. Single invocation only.

### `notification.update`

Run: `mammoth notification update`. Exact input fields: `mammoth schema get notification.update --output json --no-input`.

Example: `mammoth notification update 123 --input '{"patch": [{"sample_key": "Status"}]}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `NotificationUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `notification.update-batch`

Run: `mammoth notification update-batch`. Exact input fields: `mammoth schema get notification.update-batch --output json --no-input`.

Example: `mammoth notification update-batch --input '{"patch": [{"sample_key": "Status"}]}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `NotificationUpdateBatchResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
