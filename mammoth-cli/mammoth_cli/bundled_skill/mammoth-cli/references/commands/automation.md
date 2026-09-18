# `automation` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `automation.create`

Run: `mammoth automation create`. Exact input fields: `mammoth schema get automation.create --output json --no-input`.

Example: `mammoth automation create 'Revenue report' --input '{"description": "sample", "tasks": [{"task_type": "run_data_retrieval"}]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `AutomationCreateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.delete`

Run: `mammoth automation delete`. Exact input fields: `mammoth schema get automation.delete --output json --no-input`.

Example: `mammoth automation delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `AutomationDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.get`

Run: `mammoth automation get`. Exact input fields: `mammoth schema get automation.get --output json --no-input`.

Example: `mammoth automation get 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.list`

Run: `mammoth automation list`. Exact input fields: `mammoth schema get automation.list --output json --no-input`.

Example: `mammoth automation list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.10 — Bounded release read with published CLI 1.1.10 returned an empty automation collection; unknown input field produced deterministic unknown_input_field. No Full claim: no automation fixture or lifecycle coverage.

### `automation.restore`

Run: `mammoth automation restore`. Exact input fields: `mammoth schema get automation.restore --output json --no-input`.

Example: `mammoth automation restore 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationRestoreResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.trash`

Run: `mammoth automation trash`. Exact input fields: `mammoth schema get automation.trash --output json --no-input`.

Example: `mammoth automation trash 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationTrashResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.update`

Run: `mammoth automation update`. Exact input fields: `mammoth schema get automation.update --output json --no-input`.

Example: `mammoth automation update 123 --input '{"patch": [{"op": "replace", "path": "details", "value": "sample"}]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `AutomationUpdateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.
