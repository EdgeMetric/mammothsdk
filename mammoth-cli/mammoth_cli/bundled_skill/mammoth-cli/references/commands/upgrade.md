# `upgrade` commands

### `upgrade`

Run: `mammoth upgrade`. Exact input fields: `mammoth schema get upgrade --output json --no-input`.

Example: `mammoth upgrade --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `UpgradeResult` in the standard JSON envelope; mutation `external_effect`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
