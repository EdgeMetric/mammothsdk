# `workflow` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `workflow.block.add`

Run: `mammoth workflow block add`. Exact input fields: `mammoth schema get workflow.block.add`.

Example: `mammoth workflow block add 123 --input '{"block_type": "sample"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowBlockAddResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.block.auth`

Run: `mammoth workflow block auth`. Exact input fields: `mammoth schema get workflow.block.auth`.

Example: `mammoth workflow block auth 123 123 --input '{"auth_data": {"sample_key": "Status"}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowBlockAuthResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.block.config`

Run: `mammoth workflow block config`. Exact input fields: `mammoth schema get workflow.block.config`.

Example: `mammoth workflow block config 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowBlockConfigResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.block.type`

Run: `mammoth workflow block type`. Exact input fields: `mammoth schema get workflow.block.type`.

Example: `mammoth workflow block type 123 123 --input '{"connection_type": "sample"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowBlockTypeResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.canvas`

Run: `mammoth workflow canvas`. Exact input fields: `mammoth schema get workflow.canvas`.

Example: `mammoth workflow canvas 123 --input '{"canvas_state": {"sample_key": "Status"}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowCanvasResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.cleanup`

Run: `mammoth workflow cleanup`. Exact input fields: `mammoth schema get workflow.cleanup`.

Example: `mammoth workflow cleanup`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowCleanupResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.create`

Run: `mammoth workflow create`. Exact input fields: `mammoth schema get workflow.create`.

Example: `mammoth workflow create 'Revenue report'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Created workflow id=1 seeded from dataset 85. Single invocation only.

### `workflow.delete`

Run: `mammoth workflow delete`. Exact input fields: `mammoth schema get workflow.delete`.

Example: `mammoth workflow delete 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `WorkflowDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted workflow 1; read-back get now returns 404 WORKFLOW_NOT_FOUND, confirming deletion. Single invocation only.

### `workflow.from-template`

Run: `mammoth workflow from-template`. Exact input fields: `mammoth schema get workflow.from-template`.

Example: `mammoth workflow from-template 123 --input '{"workflow_name": "Revenue report"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowFromTemplateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.get`

Run: `mammoth workflow get`. Exact input fields: `mammoth schema get workflow.get`.

Example: `mammoth workflow get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Read back workflow 1, fields match create response. Single invocation only.

### `workflow.graph`

Run: `mammoth workflow graph`. Exact input fields: `mammoth schema get workflow.graph`.

Example: `mammoth workflow graph`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowGraphResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: cli_navigation, datasets, dataviews, skeleton_workflows, workflows. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `workflow.list`

Run: `mammoth workflow list`. Exact input fields: `mammoth schema get workflow.list`.

Example: `mammoth workflow list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Empty result on this fixture. Empty after family 5 cleanup, as expected. Single invocation only.

### `workflow.update`

Run: `mammoth workflow update`. Exact input fields: `mammoth schema get workflow.update`.

Example: `mammoth workflow update 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Updated notes field; response reflects change and bumped updated_at. Single invocation only.

### `workflow.workspace-datasets`

Run: `mammoth workflow workspace-datasets`. Exact input fields: `mammoth schema get workflow.workspace-datasets`.

Example: `mammoth workflow workspace-datasets`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowWorkspaceDatasetsResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: l, i, s, t, [, 6, ]. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `workflow.workspace-exports`

Run: `mammoth workflow workspace-exports`. Exact input fields: `mammoth schema get workflow.workspace-exports`.

Example: `mammoth workflow workspace-exports`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowWorkspaceExportsResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: l, i, s, t, [, 0, ]. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `workflow.workspace-sources`

Run: `mammoth workflow workspace-sources`. Exact input fields: `mammoth schema get workflow.workspace-sources`.

Example: `mammoth workflow workspace-sources`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowWorkspaceSourcesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: l, i, s, t, [, 0, ]. Single read only; no fixture variants, error envelopes, or write paths assessed.
