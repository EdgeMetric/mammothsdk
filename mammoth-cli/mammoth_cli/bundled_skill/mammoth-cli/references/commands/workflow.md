# `workflow` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `workflow.after.loops`

Run: `mammoth workflow after loops`. Exact input fields: `mammoth schema get workflow.after.loops`.

Example: `mammoth workflow after loops 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowAfterLoopsResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.after.set`

Run: `mammoth workflow after set`. Exact input fields: `mammoth schema get workflow.after.set`.

Example: `mammoth workflow after set 123 456`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowAfterSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.archive`

Run: `mammoth workflow archive`. Exact input fields: `mammoth schema get workflow.archive`.

Example: `mammoth workflow archive 123 --input '{"archived": true}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowArchiveResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.attach-dataset`

Run: `mammoth workflow attach-dataset`. Exact input fields: `mammoth schema get workflow.attach-dataset`.

Example: `mammoth workflow attach-dataset 123 456`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowAttachDatasetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.before-after`

Run: `mammoth workflow before-after`. Exact input fields: `mammoth schema get workflow.before-after`.

Example: `mammoth workflow before-after 123 --input '{"keys": ["Status"]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowBeforeAfterResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.block.add`

Run: `mammoth workflow block add`. Exact input fields: `mammoth schema get workflow.block.add`.

Example: `mammoth workflow block add 123 --input '{"block_type": "source"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowBlockAddResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.block.auth`

Run: `mammoth workflow block auth`. Exact input fields: `mammoth schema get workflow.block.auth`.

Example: `mammoth workflow block auth 123 456 --input '{"auth_data": {"name": "Status"}}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `WorkflowBlockAuthResult`; mutation `benign_mutation`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.block.config`

Run: `mammoth workflow block config`. Exact input fields: `mammoth schema get workflow.block.config`.

Example: `mammoth workflow block config 123 456`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowBlockConfigResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.block.type`

Run: `mammoth workflow block type`. Exact input fields: `mammoth schema get workflow.block.type`.

Example: `mammoth workflow block type 123 456 --input '{"connection_type": "postgres"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowBlockTypeResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.canvas`

Run: `mammoth workflow canvas`. Exact input fields: `mammoth schema get workflow.canvas`.

Example: `mammoth workflow canvas 12 --input '{"canvas_state": {"proposed_changes": [{"op": "add_view", "dataset_id": 415, "name": "Urgent tickets", "ref": "urgent"}, {"op": "add_step", "view_ref": "urgent", "transform": "filter", "params": {"condition": {"column": "Priority", "operator": "EQ", "value": "Urgent"}}, "label": "Keep urgent tickets"}, {"op": "send_to_new_dataset", "dataset_id": 415, "view_ref": "urgent", "name": "Urgent tickets by team"}]}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowCanvasResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.cleanup`

Run: `mammoth workflow cleanup`. Exact input fields: `mammoth schema get workflow.cleanup`.

Example: `mammoth workflow cleanup --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `WorkflowCleanupResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.create`

Run: `mammoth workflow create`. Exact input fields: `mammoth schema get workflow.create`.

Example: `mammoth workflow create 'Revenue report'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Created workflow id=1 seeded from dataset 85. Single invocation only.

### `workflow.delete`

Run: `mammoth workflow delete`. Exact input fields: `mammoth schema get workflow.delete`.

Example: `mammoth workflow delete 123 --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `WorkflowDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted workflow 1; read-back get now returns 404 WORKFLOW_NOT_FOUND, confirming deletion. Single invocation only.

### `workflow.describe.build`

Run: `mammoth workflow describe build`. Exact input fields: `mammoth schema get workflow.describe.build`.

Example: `mammoth workflow describe build --input '{"spec": {"name": "Status"}, "destination_name": "Revenue report"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowDescribeBuildResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.describe.check`

Run: `mammoth workflow describe check`. Exact input fields: `mammoth schema get workflow.describe.check`.

Example: `mammoth workflow describe check --input '{"spec": {"name": "Status"}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowDescribeCheckResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.describe.fed-by`

Run: `mammoth workflow describe fed-by`. Exact input fields: `mammoth schema get workflow.describe.fed-by`.

Example: `mammoth workflow describe fed-by 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowDescribeFedByResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.describe.get`

Run: `mammoth workflow describe get`. Exact input fields: `mammoth schema get workflow.describe.get`.

Example: `mammoth workflow describe get d-3f2a`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowDescribeGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.describe.sample`

Run: `mammoth workflow describe sample`. Exact input fields: `mammoth schema get workflow.describe.sample`.

Example: `mammoth workflow describe sample --input '{"file": "./sales.csv"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowDescribeSampleResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.describe.start`

Run: `mammoth workflow describe start`. Exact input fields: `mammoth schema get workflow.describe.start`.

Example: `mammoth workflow describe start --input '{"text": "Quarterly revenue summary"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowDescribeStartResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.describe.wait`

Run: `mammoth workflow describe wait`. Exact input fields: `mammoth schema get workflow.describe.wait`.

Example: `mammoth workflow describe wait d-3f2a`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowDescribeWaitResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.duplicate`

Run: `mammoth workflow duplicate`. Exact input fields: `mammoth schema get workflow.duplicate`.

Example: `mammoth workflow duplicate 123 --input '{"name": "Revenue report", "dataset_ids": [1]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowDuplicateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

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

### `workflow.held.check`

Run: `mammoth workflow held check`. Exact input fields: `mammoth schema get workflow.held.check`.

Example: `mammoth workflow held check 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowHeldCheckResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.link.create`

Run: `mammoth workflow link create`. Exact input fields: `mammoth schema get workflow.link.create`.

Example: `mammoth workflow link create 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowLinkCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.link.remove`

Run: `mammoth workflow link remove`. Exact input fields: `mammoth schema get workflow.link.remove`.

Example: `mammoth workflow link remove 123 --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `WorkflowLinkRemoveResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.list`

Run: `mammoth workflow list`. Exact input fields: `mammoth schema get workflow.list`.

Example: `mammoth workflow list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Empty result on this fixture. Empty after family 5 cleanup, as expected. Single invocation only.

### `workflow.page.start`

Run: `mammoth workflow page start`. Exact input fields: `mammoth schema get workflow.page.start`.

Example: `mammoth workflow page start stripe-payout-reconciliation`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowPageStartResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.repeat-counts`

Run: `mammoth workflow repeat-counts`. Exact input fields: `mammoth schema get workflow.repeat-counts`.

Example: `mammoth workflow repeat-counts`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowRepeatCountsResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.resolve-held`

Run: `mammoth workflow resolve-held`. Exact input fields: `mammoth schema get workflow.resolve-held`.

Example: `mammoth workflow resolve-held 123 Status --input '{"built": true}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowResolveHeldResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.run.list`

Run: `mammoth workflow run list`. Exact input fields: `mammoth schema get workflow.run.list`.

Example: `mammoth workflow run list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowRunListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.run.start`

Run: `mammoth workflow run start`. Exact input fields: `mammoth schema get workflow.run.start`.

Example: `mammoth workflow run start 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowRunStartResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.run.wait`

Run: `mammoth workflow run wait`. Exact input fields: `mammoth schema get workflow.run.wait`.

Example: `mammoth workflow run wait 123 resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowRunWaitResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.save`

Run: `mammoth workflow save`. Exact input fields: `mammoth schema get workflow.save`.

Example: `mammoth workflow save 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowSaveResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.save-cancel-step`

Run: `mammoth workflow save-cancel-step`. Exact input fields: `mammoth schema get workflow.save-cancel-step`.

Example: `mammoth workflow save-cancel-step 123 resource-123 456`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowSaveCancelStepResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.save-undo`

Run: `mammoth workflow save-undo`. Exact input fields: `mammoth schema get workflow.save-undo`.

Example: `mammoth workflow save-undo 123 resource-123 --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `WorkflowSaveUndoResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `workflow.schedule.set`

Run: `mammoth workflow schedule set`. Exact input fields: `mammoth schema get workflow.schedule.set`.

Example: `mammoth workflow schedule set 123 --input '{"frequency": "weekly", "by_week_day": ["mo"]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowScheduleSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.sentence.dismiss-ask`

Run: `mammoth workflow sentence dismiss-ask`. Exact input fields: `mammoth schema get workflow.sentence.dismiss-ask`.

Example: `mammoth workflow sentence dismiss-ask 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowSentenceDismissAskResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.sentence.read`

Run: `mammoth workflow sentence read`. Exact input fields: `mammoth schema get workflow.sentence.read`.

Example: `mammoth workflow sentence read 123 --input '{"text": "Quarterly revenue summary"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowSentenceReadResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.step-lines`

Run: `mammoth workflow step-lines`. Exact input fields: `mammoth schema get workflow.step-lines`.

Example: `mammoth workflow step-lines 123 --input '{"view_ids": [1]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowStepLinesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.swap.apply`

Run: `mammoth workflow swap apply`. Exact input fields: `mammoth schema get workflow.swap.apply`.

Example: `mammoth workflow swap apply 123 456 789`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowSwapApplyResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.swap.cancel`

Run: `mammoth workflow swap cancel`. Exact input fields: `mammoth schema get workflow.swap.cancel`.

Example: `mammoth workflow swap cancel 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowSwapCancelResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.swap.fit`

Run: `mammoth workflow swap fit`. Exact input fields: `mammoth schema get workflow.swap.fit`.

Example: `mammoth workflow swap fit 123 456 --input '{"dataset_ids": [1]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowSwapFitResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.swap.undo`

Run: `mammoth workflow swap undo`. Exact input fields: `mammoth schema get workflow.swap.undo`.

Example: `mammoth workflow swap undo 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowSwapUndoResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.template.build`

Run: `mammoth workflow template build`. Exact input fields: `mammoth schema get workflow.template.build`.

Example: `mammoth workflow template build bank-reconciliation --input '{"inputs": {"main": 101}, "matches": {"main": {"amount": {"column": "Amount"}}}, "destination_name": "Bank reconciliation"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowTemplateBuildResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.template.fit`

Run: `mammoth workflow template fit`. Exact input fields: `mammoth schema get workflow.template.fit`.

Example: `mammoth workflow template fit bank-reconciliation --input '{"inputs": {"main": 101}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowTemplateFitResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.template.fits`

Run: `mammoth workflow template fits`. Exact input fields: `mammoth schema get workflow.template.fits`.

Example: `mammoth workflow template fits`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowTemplateFitsResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.template.get`

Run: `mammoth workflow template get`. Exact input fields: `mammoth schema get workflow.template.get`.

Example: `mammoth workflow template get bank-reconciliation`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowTemplateGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.template.list`

Run: `mammoth workflow template list`. Exact input fields: `mammoth schema get workflow.template.list`.

Example: `mammoth workflow template list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowTemplateListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.template.preview`

Run: `mammoth workflow template preview`. Exact input fields: `mammoth schema get workflow.template.preview`.

Example: `mammoth workflow template preview bank-reconciliation --input '{"inputs": {"main": 101}, "matches": {"main": {"amount": {"column": "Amount"}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowTemplatePreviewResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.template.rank`

Run: `mammoth workflow template rank`. Exact input fields: `mammoth schema get workflow.template.rank`.

Example: `mammoth workflow template rank bank-reconciliation --input '{"input_key": "main", "dataset_ids": [101, 102]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowTemplateRankResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.template.sample-result`

Run: `mammoth workflow template sample-result`. Exact input fields: `mammoth schema get workflow.template.sample-result`.

Example: `mammoth workflow template sample-result bank-reconciliation`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowTemplateSampleResultResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.template.samples`

Run: `mammoth workflow template samples`. Exact input fields: `mammoth schema get workflow.template.samples`.

Example: `mammoth workflow template samples bank-reconciliation`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowTemplateSamplesResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `workflow.update`

Run: `mammoth workflow update`. Exact input fields: `mammoth schema get workflow.update`.

Example: `mammoth workflow update 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Updated notes field; response reflects change and bumped updated_at. Single invocation only.

### `workflow.values`

Run: `mammoth workflow values`. Exact input fields: `mammoth schema get workflow.values`.

Example: `mammoth workflow values 123 456 --input '{"column": "Status", "text": "Quarterly revenue summary"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WorkflowValuesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

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
