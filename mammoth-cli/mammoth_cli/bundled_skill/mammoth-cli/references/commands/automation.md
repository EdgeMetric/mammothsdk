# `automation` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `automation.capabilities`

Run: `mammoth automation capabilities`. Exact input fields: `mammoth schema get automation.capabilities`.

Example: `mammoth automation capabilities`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationCapabilitiesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.create`

Run: `mammoth automation create`. Exact input fields: `mammoth schema get automation.create`.

Example: `mammoth automation create 'Revenue report' --input '{"description": "Quarterly revenue summary", "tasks": [{"task_type": "run_data_retrieval", "details": {"ds_details": [{"ds_id": 42}]}}]}' --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `AutomationCreateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on CLI 2.0.18. Created automation id=1 after two failed attempts: run_data_retrieval needs cloud-source dataset ids (4AUTO006); send_an_alert needs attachments.dataview_ids, sent as CSV. Single invocation only.

### `automation.delete`

Run: `mammoth automation delete`. Exact input fields: `mammoth schema get automation.delete`.

Example: `mammoth automation delete 123 --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `AutomationDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Delete returned 200/data:{} despite get/list never having shown the resource; cannot independently confirm deletion given get/list breakage for this id. Single invocation only.

### `automation.folders`

Run: `mammoth automation folders`. Exact input fields: `mammoth schema get automation.folders`.

Example: `mammoth automation folders`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationFoldersResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.get`

Run: `mammoth automation get`. Exact input fields: `mammoth schema get automation.get`.

Example: `mammoth automation get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend_error: SUSPECTED DEFECT: automation.get on the id that automation.create returned (id=1) returns HTTP 500 empty body every time (3 retries, several seconds apart), not even. Re-check before relying on it.

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

### `automation.route.order`

Run: `mammoth automation route order`. Exact input fields: `mammoth schema get automation.route.order`.

Example: `mammoth automation route order 123 --input '{"automation_ids": [12, 11]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationRouteOrderResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.route.preview`

Run: `mammoth automation route preview`. Exact input fields: `mammoth schema get automation.route.preview`.

Example: `mammoth automation route preview 123 --input '{"names": ["sales_2026-10.csv"]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationRoutePreviewResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.run-file.add-anyway`

Run: `mammoth automation run-file add-anyway`. Exact input fields: `mammoth schema get automation.run-file.add-anyway`.

Example: `mammoth automation run-file add-anyway 123 --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `AutomationRunFileAddAnywayResult`; mutation `benign_mutation`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.runs`

Run: `mammoth automation runs`. Exact input fields: `mammoth schema get automation.runs`.

Example: `mammoth automation runs 123 --input '{"limit": 10}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationRunsResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.trash`

Run: `mammoth automation trash`. Exact input fields: `mammoth schema get automation.trash`.

Example: `mammoth automation trash 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AutomationTrashResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `automation.update`

Run: `mammoth automation update`. Exact input fields: `mammoth schema get automation.update`.

Example: `mammoth automation update 123 --input '{"patch": [{"op": "replace", "path": "details", "value": {"name": "Daily revenue export"}}]}' --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `AutomationUpdateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: CLI defect fixed, untried since — CLI defect fixed in mammoth-io 0.7.19 / mammoth-cli 2.0.46: AutomationsAPI.update sent path=status value='resume' to the backend verbatim; the backend's wire vocabulary for that path is 'suspend'/'restore' (apiv2/apiv2/automations/schema.py AutomationStatusVa…
