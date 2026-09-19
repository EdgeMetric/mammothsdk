# `external-key` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `external-key.create`

Run: `mammoth external-key create`. Exact input fields: `mammoth schema get external-key.create`.

Example: `mammoth external-key create --input '{"key_type": "open_ai", "key_name": "Revenue report", "secure_key": "sample"}'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ExternalKeyCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `external-key.delete`

Run: `mammoth external-key delete`. Exact input fields: `mammoth schema get external-key.delete`.

Example: `mammoth external-key delete 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `ExternalKeyDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `external-key.get`

Run: `mammoth external-key get`. Exact input fields: `mammoth schema get external-key.get`.

Example: `mammoth external-key get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ExternalKeyGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `external-key.list`

Run: `mammoth external-key list`. Exact input fields: `mammoth schema get external-key.list`.

Example: `mammoth external-key list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ExternalKeyListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Empty result on this fixture. No owned external_keys present; one house_key (open_ai, in_use) visible read-only, not touched. Minor note: offset=50 returned for an empty list with limit=50…
