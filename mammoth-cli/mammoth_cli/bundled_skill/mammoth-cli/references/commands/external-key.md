# `external-key` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `external-key.create`

Run: `mammoth external-key create`. Exact input fields: `mammoth schema get external-key.create --output json --no-input`.

Example: `mammoth external-key create --input '{"key_type": "open_ai", "key_name": "Revenue report", "secure_key": "sample"}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ExternalKeyCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `external-key.delete`

Run: `mammoth external-key delete`. Exact input fields: `mammoth schema get external-key.delete --output json --no-input`.

Example: `mammoth external-key delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ExternalKeyDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `external-key.get`

Run: `mammoth external-key get`. Exact input fields: `mammoth schema get external-key.get --output json --no-input`.

Example: `mammoth external-key get 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ExternalKeyGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `external-key.list`

Run: `mammoth external-key list`. Exact input fields: `mammoth schema get external-key.list --output json --no-input`.

Example: `mammoth external-key list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ExternalKeyListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — cli_error: not_authenticated although the same session authenticated elsewhere. Re-check before relying on it.
