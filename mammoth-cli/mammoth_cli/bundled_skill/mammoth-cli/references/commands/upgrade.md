# `upgrade` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `upgrade`

Run: `mammoth upgrade`. Exact input fields: `mammoth schema get upgrade`.

Example: `mammoth upgrade`. Illustrative only: append `--yes` after observing an owned target.

Result: `UpgradeResult`; mutation `external_effect`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.
