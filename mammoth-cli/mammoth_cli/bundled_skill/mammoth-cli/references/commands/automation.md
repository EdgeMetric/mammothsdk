# `automation` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `automation.create`

Run: `mammoth automation create`. Exact input fields: `mammoth schema get automation.create`.

Example: `mammoth automation create 'Revenue report' --input '{"description": "sample", "tasks": [{"task_type": "run_data_retrieval"}]}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `AutomationCreateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Created automation id=1 after two failed attempts: agent_example's run_data_retrieval needs cloud-source dataset ids (4AUTO006), and send_an_alert needed attachments.dataview_ids (undocume…

### `automation.delete`

Run: `mammoth automation delete`. Exact input fields: `mammoth schema get automation.delete`.

Example: `mammoth automation delete 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `AutomationDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Delete returned 200/data:{} despite get/list never having shown the resource; cannot independently confirm deletion given get/list breakage for this id. Single invocation only.

### `automation.get`

Run: `mammoth automation get`. Exact input fields: `mammoth schema get automation.get`.

Example: `mammoth automation get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend_error: SUSPECTED DEFECT: automation.get on the id just returned by automation.create (id=1) returns HTTP 500 empty body every time (3 retries, several seconds apart), not e. Re-check before relying on it.

### `automation.list`

Run: `mammoth automation list`. Exact input fields: `mammoth schema get automation.list`.

Example: `mammoth automation list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.21 — ergonomics sweep 2026-09-19: exit 0 on release with CLI 2.0.21. Empty result on this fixture. Empty list in a fresh project. Single invocation only.

### `automation.restore`

Run: `mammoth automation restore`. Exact input fields: `mammoth schema get automation.restore`.

Example: `mammoth automation restore 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationRestoreResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.trash`

Run: `mammoth automation trash`. Exact input fields: `mammoth schema get automation.trash`.

Example: `mammoth automation trash 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationTrashResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.update`

Run: `mammoth automation update`. Exact input fields: `mammoth schema get automation.update`.

Example: `mammoth automation update 123 --input '{"patch": [{"op": "replace", "path": "details", "value": "sample"}]}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `AutomationUpdateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: observed blocker — cli_error: CLI rejected 'name' field; error message says accepted field is 'patch' (nested patch object), not documented in agent_example. Re-check before relying on it.
