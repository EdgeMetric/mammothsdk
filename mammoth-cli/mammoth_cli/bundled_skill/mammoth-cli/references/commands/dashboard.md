# `dashboard` commands

### `dashboard.action`

Run: `mammoth dashboard action`. Exact input fields: `mammoth schema get dashboard.action --output json --no-input`.

Example: `mammoth dashboard action 123 --input '{"action": "sync"}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DashboardActionResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.analytics`

Run: `mammoth dashboard analytics`. Exact input fields: `mammoth schema get dashboard.analytics --output json --no-input`.

Example: `mammoth dashboard analytics 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardAnalyticsResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.archive`

Run: `mammoth dashboard archive`. Exact input fields: `mammoth schema get dashboard.archive --output json --no-input`.

Example: `mammoth dashboard archive 123 --input '{"archived": true}' --output json --no-input --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `DashboardArchiveResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.assess-pbix`

Run: `mammoth dashboard assess-pbix`. Exact input fields: `mammoth schema get dashboard.assess-pbix --output json --no-input`.

Example: `mammoth dashboard assess-pbix sample.pbix --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `PbixAssessResponse` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.assess-twb`

Run: `mammoth dashboard assess-twb`. Exact input fields: `mammoth schema get dashboard.assess-twb --output json --no-input`.

Example: `mammoth dashboard assess-twb sample.twb --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `TwbAssessResponse` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.cancel-generation`

Run: `mammoth dashboard cancel-generation`. Exact input fields: `mammoth schema get dashboard.cancel-generation --output json --no-input`.

Example: `mammoth dashboard cancel-generation 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardCancelGenerationResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.canvas.get`

Run: `mammoth dashboard canvas get`. Exact input fields: `mammoth schema get dashboard.canvas.get --output json --no-input`.

Example: `mammoth dashboard canvas get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardCanvasGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.canvas.restore`

Run: `mammoth dashboard canvas restore`. Exact input fields: `mammoth schema get dashboard.canvas.restore --output json --no-input`.

Example: `mammoth dashboard canvas restore 123 --input '{"body": {"params": {"target_sequence": 1}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardCanvasRestoreResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.canvas.save`

Run: `mammoth dashboard canvas save`. Exact input fields: `mammoth schema get dashboard.canvas.save --output json --no-input`.

Example: `mammoth dashboard canvas save 123 --input '{"body": {"params": {"canvas": {}}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardCanvasSaveResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.chat.edit`

Run: `mammoth dashboard chat edit`. Exact input fields: `mammoth schema get dashboard.chat.edit --output json --no-input`.

Example: `mammoth dashboard chat edit 123 --input '{"body": {"params": {"prompt": "Summarize revenue by region"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardChatEditResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.chat.history`

Run: `mammoth dashboard chat history`. Exact input fields: `mammoth schema get dashboard.chat.history --output json --no-input`.

Example: `mammoth dashboard chat history 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardChatHistoryResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.context.create`

Run: `mammoth dashboard context create`. Exact input fields: `mammoth schema get dashboard.context.create --output json --no-input`.

Example: `mammoth dashboard context create --input '{"body": {"params": {"name": "Revenue report"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardContextCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.context.delete`

Run: `mammoth dashboard context delete`. Exact input fields: `mammoth schema get dashboard.context.delete --output json --no-input`.

Example: `mammoth dashboard context delete resource-123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DashboardContextDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.context.extract`

Run: `mammoth dashboard context extract`. Exact input fields: `mammoth schema get dashboard.context.extract --output json --no-input`.

Example: `mammoth dashboard context extract --input '{"body": {"params": {"name": "Revenue report"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ContextExtractResponse` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.context.list`

Run: `mammoth dashboard context list`. Exact input fields: `mammoth schema get dashboard.context.list --output json --no-input`.

Example: `mammoth dashboard context list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardContextListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.context.update`

Run: `mammoth dashboard context update`. Exact input fields: `mammoth schema get dashboard.context.update --output json --no-input`.

Example: `mammoth dashboard context update resource-123 --input '{"body": {"params": {"name": "Revenue report"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardContextUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.create`

Run: `mammoth dashboard create`. Exact input fields: `mammoth schema get dashboard.create --output json --no-input`.

Example: `mammoth dashboard create 'Summarize revenue by region' --input '{"source": [1]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.create-blank`

Run: `mammoth dashboard create-blank`. Exact input fields: `mammoth schema get dashboard.create-blank --output json --no-input`.

Example: `mammoth dashboard create-blank --input '{"params": {"dataview_id": 1}}' --output json --no-input --yes`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DashboardCreateBlankResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.data.draft`

Run: `mammoth dashboard data draft`. Exact input fields: `mammoth schema get dashboard.data.draft --output json --no-input`.

Example: `mammoth dashboard data draft 123 --input '{"widget_id": "550e8400-e29b-41d4-a716-446655440000"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardDataDraftResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.data.published`

Run: `mammoth dashboard data published`. Exact input fields: `mammoth schema get dashboard.data.published --output json --no-input`.

Example: `mammoth dashboard data published 123 --input '{"widget_id": "550e8400-e29b-41d4-a716-446655440000"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardDataPublishedResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.delete`

Run: `mammoth dashboard delete`. Exact input fields: `mammoth schema get dashboard.delete --output json --no-input`.

Example: `mammoth dashboard delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DashboardDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.descriptor-data`

Run: `mammoth dashboard descriptor-data`. Exact input fields: `mammoth schema get dashboard.descriptor-data --output json --no-input`.

Example: `mammoth dashboard descriptor-data 123 --input '{"body": {"params": {"descriptor_ids": ["resource-123"]}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardDescriptorDataResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.duplicate`

Run: `mammoth dashboard duplicate`. Exact input fields: `mammoth schema get dashboard.duplicate --output json --no-input`.

Example: `mammoth dashboard duplicate 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardDuplicateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.exemplar.extract`

Run: `mammoth dashboard exemplar extract`. Exact input fields: `mammoth schema get dashboard.exemplar.extract --output json --no-input`.

Example: `mammoth dashboard exemplar extract --input '{"body": {"params": {"name": "Revenue report"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ExemplarExtractResponse` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.figure-intent`

Run: `mammoth dashboard figure-intent`. Exact input fields: `mammoth schema get dashboard.figure-intent --output json --no-input`.

Example: `mammoth dashboard figure-intent 123 --input '{"body": {"params": {"intent": "Summarize revenue by region"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardFigureIntentResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.get`

Run: `mammoth dashboard get`. Exact input fields: `mammoth schema get dashboard.get --output json --no-input`.

Example: `mammoth dashboard get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.get-by-url`

Run: `mammoth dashboard get-by-url`. Exact input fields: `mammoth schema get dashboard.get-by-url --output json --no-input`.

Example: `mammoth dashboard get-by-url https://example.com/data.csv --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardGetByUrlResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.import-workbook`

Run: `mammoth dashboard import-workbook`. Exact input fields: `mammoth schema get dashboard.import-workbook --output json --no-input`.

Example: `mammoth dashboard import-workbook sample.twbx --project 456 --yes --confirm 456 --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `ImportDatasetResponse` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.job-by-url`

Run: `mammoth dashboard job-by-url`. Exact input fields: `mammoth schema get dashboard.job-by-url --output json --no-input`.

Example: `mammoth dashboard job-by-url https://example.com/data.csv 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardJobByUrlResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.list`

Run: `mammoth dashboard list`. Exact input fields: `mammoth schema get dashboard.list --output json --no-input`.

Example: `mammoth dashboard list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.og-card`

Run: `mammoth dashboard og-card`. Exact input fields: `mammoth schema get dashboard.og-card --output json --no-input`.

Example: `mammoth dashboard og-card 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardOgCardResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.page.plan`

Run: `mammoth dashboard page plan`. Exact input fields: `mammoth schema get dashboard.page.plan --output json --no-input`.

Example: `mammoth dashboard page plan 123 --input '{"body": {"params": {"intent": "Summarize revenue by region"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardPagePlanResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.pages.add`

Run: `mammoth dashboard pages add`. Exact input fields: `mammoth schema get dashboard.pages.add --output json --no-input`.

Example: `mammoth dashboard pages add 123 --input '{"body": {"params": {"pages": [{}]}}}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `DashboardPagesAddResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.pdf-artifact`

Run: `mammoth dashboard pdf-artifact`. Exact input fields: `mammoth schema get dashboard.pdf-artifact --output json --no-input`.

Example: `mammoth dashboard pdf-artifact 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardPdfArtifactResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.pdf.export`

Run: `mammoth dashboard pdf export`. Exact input fields: `mammoth schema get dashboard.pdf.export --output json --no-input`.

Example: `mammoth dashboard pdf export 123 --input '{"body": {"params": {"data": {}}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardPdfExportResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.published-data-by-url`

Run: `mammoth dashboard published-data-by-url`. Exact input fields: `mammoth schema get dashboard.published-data-by-url --output json --no-input`.

Example: `mammoth dashboard published-data-by-url https://example.com/data.csv --input '{"body": {"params": {"widget_id": "00000000-0000-4000-8000-000000000001"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardPublishedDataByUrlResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.published.canvas`

Run: `mammoth dashboard published canvas`. Exact input fields: `mammoth schema get dashboard.published.canvas --output json --no-input`.

Example: `mammoth dashboard published canvas https://example.com/data.csv --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardPublishedCanvasResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.published.data`

Run: `mammoth dashboard published data`. Exact input fields: `mammoth schema get dashboard.published.data --output json --no-input`.

Example: `mammoth dashboard published data https://example.com/data.csv --input '{"body": {"params": {"descriptor_ids": ["resource-123"]}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardPublishedDataResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.published.og-card`

Run: `mammoth dashboard published og-card`. Exact input fields: `mammoth schema get dashboard.published.og-card --output json --no-input`.

Example: `mammoth dashboard published og-card https://example.com/data.csv --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardPublishedOgCardResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.published.pdf-artifact`

Run: `mammoth dashboard published pdf-artifact`. Exact input fields: `mammoth schema get dashboard.published.pdf-artifact --output json --no-input`.

Example: `mammoth dashboard published pdf-artifact https://example.com/data.csv 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardPublishedPdfArtifactResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.published.pdf.export`

Run: `mammoth dashboard published pdf export`. Exact input fields: `mammoth schema get dashboard.published.pdf.export --output json --no-input`.

Example: `mammoth dashboard published pdf export https://example.com/data.csv --input '{"body": {"params": {"data": {}}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardPublishedPdfExportResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.published.share-page`

Run: `mammoth dashboard published share-page`. Exact input fields: `mammoth schema get dashboard.published.share-page --output json --no-input`.

Example: `mammoth dashboard published share-page https://example.com/data.csv --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardPublishedSharePageResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.published.video-artifact`

Run: `mammoth dashboard published video-artifact`. Exact input fields: `mammoth schema get dashboard.published.video-artifact --output json --no-input`.

Example: `mammoth dashboard published video-artifact https://example.com/data.csv --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardPublishedVideoArtifactResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.published.video.export`

Run: `mammoth dashboard published video export`. Exact input fields: `mammoth schema get dashboard.published.video.export --output json --no-input`.

Example: `mammoth dashboard published video export https://example.com/data.csv --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardPublishedVideoExportResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.ask`

Run: `mammoth dashboard qa ask`. Exact input fields: `mammoth schema get dashboard.qa.ask --output json --no-input`.

Example: `mammoth dashboard qa ask 123 123 --input '{"body": {"params": {"question": "Summarize revenue by region"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardQaAskResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.comment.create`

Run: `mammoth dashboard qa comment create`. Exact input fields: `mammoth schema get dashboard.qa.comment.create --output json --no-input`.

Example: `mammoth dashboard qa comment create 123 123 --input '{"body": {"params": {"body": "sample"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardQaCommentCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.comment.delete`

Run: `mammoth dashboard qa comment delete`. Exact input fields: `mammoth schema get dashboard.qa.comment.delete --output json --no-input`.

Example: `mammoth dashboard qa comment delete 123 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DashboardQaCommentDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.feedback`

Run: `mammoth dashboard qa feedback`. Exact input fields: `mammoth schema get dashboard.qa.feedback --output json --no-input`.

Example: `mammoth dashboard qa feedback 123 123 123 --input '{"body": {"params": {"rating": "up"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardQaFeedbackResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.session.create`

Run: `mammoth dashboard qa session create`. Exact input fields: `mammoth schema get dashboard.qa.session.create --output json --no-input`.

Example: `mammoth dashboard qa session create 123 --input '{"body": {"params": {"title": "Revenue report"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardQaSessionCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.session.delete`

Run: `mammoth dashboard qa session delete`. Exact input fields: `mammoth schema get dashboard.qa.session.delete --output json --no-input`.

Example: `mammoth dashboard qa session delete 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DashboardQaSessionDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.session.fork`

Run: `mammoth dashboard qa session fork`. Exact input fields: `mammoth schema get dashboard.qa.session.fork --output json --no-input`.

Example: `mammoth dashboard qa session fork 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardQaSessionForkResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.session.get`

Run: `mammoth dashboard qa session get`. Exact input fields: `mammoth schema get dashboard.qa.session.get --output json --no-input`.

Example: `mammoth dashboard qa session get 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardQaSessionGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.session.list`

Run: `mammoth dashboard qa session list`. Exact input fields: `mammoth schema get dashboard.qa.session.list --output json --no-input`.

Example: `mammoth dashboard qa session list 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardQaSessionListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.session.rename`

Run: `mammoth dashboard qa session rename`. Exact input fields: `mammoth schema get dashboard.qa.session.rename --output json --no-input`.

Example: `mammoth dashboard qa session rename 123 123 --input '{"body": {"params": {"title": "Revenue report"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardQaSessionRenameResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.session.set-visibility`

Run: `mammoth dashboard qa session set-visibility`. Exact input fields: `mammoth schema get dashboard.qa.session.set-visibility --output json --no-input`.

Example: `mammoth dashboard qa session set-visibility 123 123 --input '{"body": {"params": {"visibility": "sample"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardQaSessionSetVisibilityResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.settings.get`

Run: `mammoth dashboard qa settings get`. Exact input fields: `mammoth schema get dashboard.qa.settings.get --output json --no-input`.

Example: `mammoth dashboard qa settings get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardQaSettingsGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.qa.settings.set`

Run: `mammoth dashboard qa settings set`. Exact input fields: `mammoth schema get dashboard.qa.settings.set --output json --no-input`.

Example: `mammoth dashboard qa settings set 123 --input '{"body": {"params": {"allow_viewer_qa": true}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardQaSettingsSetResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.query`

Run: `mammoth dashboard query`. Exact input fields: `mammoth schema get dashboard.query --output json --no-input`.

Example: `mammoth dashboard query 123 --input '{"body": {"params": {"descriptor": {"kind": "scalar", "agg": "count"}}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardQueryResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.restore`

Run: `mammoth dashboard restore`. Exact input fields: `mammoth schema get dashboard.restore --output json --no-input`.

Example: `mammoth dashboard restore 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardRestoreResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.rls.assignment.list`

Run: `mammoth dashboard rls assignment list`. Exact input fields: `mammoth schema get dashboard.rls.assignment.list --output json --no-input`.

Example: `mammoth dashboard rls assignment list 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardRlsAssignmentListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.rls.assignment.set`

Run: `mammoth dashboard rls assignment set`. Exact input fields: `mammoth schema get dashboard.rls.assignment.set --output json --no-input`.

Example: `mammoth dashboard rls assignment set 123 --input '{"body": {"params": {"assignments": [{"email": "analyst@example.com"}]}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardRlsAssignmentSetResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.rls.column.list`

Run: `mammoth dashboard rls column list`. Exact input fields: `mammoth schema get dashboard.rls.column.list --output json --no-input`.

Example: `mammoth dashboard rls column list 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardRlsColumnListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.rls.value.list`

Run: `mammoth dashboard rls value list`. Exact input fields: `mammoth schema get dashboard.rls.value.list --output json --no-input`.

Example: `mammoth dashboard rls value list 123 --input '{"column": "Status"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardRlsValueListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.share`

Run: `mammoth dashboard share`. Exact input fields: `mammoth schema get dashboard.share --output json --no-input`.

Example: `mammoth dashboard share 123 --input '{"type_of_auth": "mammoth"}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DashboardShareResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.signature.create`

Run: `mammoth dashboard signature create`. Exact input fields: `mammoth schema get dashboard.signature.create --output json --no-input`.

Example: `mammoth dashboard signature create --input '{"body": {"params": {"name": "Revenue report"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardSignatureCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.signature.delete`

Run: `mammoth dashboard signature delete`. Exact input fields: `mammoth schema get dashboard.signature.delete --output json --no-input`.

Example: `mammoth dashboard signature delete resource-123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DashboardSignatureDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.signature.list`

Run: `mammoth dashboard signature list`. Exact input fields: `mammoth schema get dashboard.signature.list --output json --no-input`.

Example: `mammoth dashboard signature list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardSignatureListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.signature.update`

Run: `mammoth dashboard signature update`. Exact input fields: `mammoth schema get dashboard.signature.update --output json --no-input`.

Example: `mammoth dashboard signature update resource-123 --input '{"body": {"params": {"name": "Revenue report"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardSignatureUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.source.list`

Run: `mammoth dashboard source list`. Exact input fields: `mammoth schema get dashboard.source.list --output json --no-input`.

Example: `mammoth dashboard source list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardSourceListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.style.custom.create`

Run: `mammoth dashboard style custom create`. Exact input fields: `mammoth schema get dashboard.style.custom.create --output json --no-input`.

Example: `mammoth dashboard style custom create --input '{"body": {"params": {"signals": {}}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardStyleCustomCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.style.custom.delete`

Run: `mammoth dashboard style custom delete`. Exact input fields: `mammoth schema get dashboard.style.custom.delete --output json --no-input`.

Example: `mammoth dashboard style custom delete resource-123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DashboardStyleCustomDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.style.custom.list`

Run: `mammoth dashboard style custom list`. Exact input fields: `mammoth schema get dashboard.style.custom.list --output json --no-input`.

Example: `mammoth dashboard style custom list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardStyleCustomListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.style.custom.update`

Run: `mammoth dashboard style custom update`. Exact input fields: `mammoth schema get dashboard.style.custom.update --output json --no-input`.

Example: `mammoth dashboard style custom update resource-123 --input '{"body": {"params": {"signals": {}}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardStyleCustomUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.style.default.get`

Run: `mammoth dashboard style default get`. Exact input fields: `mammoth schema get dashboard.style.default.get --output json --no-input`.

Example: `mammoth dashboard style default get --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardStyleDefaultGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.style.default.set`

Run: `mammoth dashboard style default set`. Exact input fields: `mammoth schema get dashboard.style.default.set --output json --no-input`.

Example: `mammoth dashboard style default set --input '{"body": {"params": {"styleId": "sample"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardStyleDefaultSetResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.style.derive`

Run: `mammoth dashboard style derive`. Exact input fields: `mammoth schema get dashboard.style.derive --output json --no-input`.

Example: `mammoth dashboard style derive --input '{"body": {"params": {"signals": {}}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardStyleDeriveResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.style.extract-brand`

Run: `mammoth dashboard style extract-brand`. Exact input fields: `mammoth schema get dashboard.style.extract-brand --output json --no-input`.

Example: `mammoth dashboard style extract-brand --input '{"body": {"params": {"url": "https://example.com/data.csv"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardStyleExtractBrandResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.style.preset.list`

Run: `mammoth dashboard style preset list`. Exact input fields: `mammoth schema get dashboard.style.preset.list --output json --no-input`.

Example: `mammoth dashboard style preset list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardStylePresetListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.style.token.list`

Run: `mammoth dashboard style token list`. Exact input fields: `mammoth schema get dashboard.style.token.list --output json --no-input`.

Example: `mammoth dashboard style token list resource-123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardStyleTokenListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.suggestion.list`

Run: `mammoth dashboard suggestion list`. Exact input fields: `mammoth schema get dashboard.suggestion.list --output json --no-input`.

Example: `mammoth dashboard suggestion list 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardSuggestionListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.swap-data`

Run: `mammoth dashboard swap-data`. Exact input fields: `mammoth schema get dashboard.swap-data --output json --no-input`.

Example: `mammoth dashboard swap-data 123 --input '{"body": {"params": {"dataview_id": 1}}}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `ObjectJobSchema` in the standard JSON envelope; mutation `benign_mutation`, confirmation `confirm_target`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.tags.delete`

Run: `mammoth dashboard tags delete`. Exact input fields: `mammoth schema get dashboard.tags.delete --output json --no-input`.

Example: `mammoth dashboard tags delete 123 --output json --no-input --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `DashboardTagsDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.tags.list`

Run: `mammoth dashboard tags list`. Exact input fields: `mammoth schema get dashboard.tags.list --output json --no-input`.

Example: `mammoth dashboard tags list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardTagsListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.tags.merge`

Run: `mammoth dashboard tags merge`. Exact input fields: `mammoth schema get dashboard.tags.merge --output json --no-input`.

Example: `mammoth dashboard tags merge 123 --input '{"target_id": 456}' --output json --no-input --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `DashboardTagsMergeResult` in the standard JSON envelope; mutation `destructive`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.tags.rename`

Run: `mammoth dashboard tags rename`. Exact input fields: `mammoth schema get dashboard.tags.rename --output json --no-input`.

Example: `mammoth dashboard tags rename 123 --input '{"name": "Revenue"}' --output json --no-input --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `DashboardTagsRenameResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.tags.set`

Run: `mammoth dashboard tags set`. Exact input fields: `mammoth schema get dashboard.tags.set --output json --no-input`.

Example: `mammoth dashboard tags set 123 --input '{"tags": ["Revenue"]}' --output json --no-input --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `DashboardTagsSetResult` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.template.apply`

Run: `mammoth dashboard template apply`. Exact input fields: `mammoth schema get dashboard.template.apply --output json --no-input`.

Example: `mammoth dashboard template apply --input '{"body": {"params": {"source_dashboard_id": 1, "target_dataview_id": 1}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardTemplateApplyResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.template.create`

Run: `mammoth dashboard template create`. Exact input fields: `mammoth schema get dashboard.template.create --output json --no-input`.

Example: `mammoth dashboard template create --input '{"body": {"params": {"dashboard_id": 1, "title": "Revenue report"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardTemplateCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.template.delete`

Run: `mammoth dashboard template delete`. Exact input fields: `mammoth schema get dashboard.template.delete --output json --no-input`.

Example: `mammoth dashboard template delete resource-123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `DashboardTemplateDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.template.fit`

Run: `mammoth dashboard template fit`. Exact input fields: `mammoth schema get dashboard.template.fit --output json --no-input`.

Example: `mammoth dashboard template fit 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardTemplateFitResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.template.get`

Run: `mammoth dashboard template get`. Exact input fields: `mammoth schema get dashboard.template.get --output json --no-input`.

Example: `mammoth dashboard template get resource-123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardTemplateGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.template.list`

Run: `mammoth dashboard template list`. Exact input fields: `mammoth schema get dashboard.template.list --output json --no-input`.

Example: `mammoth dashboard template list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardTemplateListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.template.preview`

Run: `mammoth dashboard template preview`. Exact input fields: `mammoth schema get dashboard.template.preview --output json --no-input`.

Example: `mammoth dashboard template preview --input '{"body": {"params": {"source_dashboard_id": 1, "target_dataview_id": 1}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardTemplatePreviewResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.template.rename`

Run: `mammoth dashboard template rename`. Exact input fields: `mammoth schema get dashboard.template.rename --output json --no-input`.

Example: `mammoth dashboard template rename resource-123 --input '{"body": {"params": {"title": "Revenue report"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardTemplateRenameResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.template.resolve-mapping`

Run: `mammoth dashboard template resolve-mapping`. Exact input fields: `mammoth schema get dashboard.template.resolve-mapping --output json --no-input`.

Example: `mammoth dashboard template resolve-mapping --input '{"body": {"params": {"source_dashboard_id": 1, "target_dataview_id": 1}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardTemplateResolveMappingResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.templates.pending`

Run: `mammoth dashboard templates pending`. Exact input fields: `mammoth schema get dashboard.templates.pending --output json --no-input`.

Example: `mammoth dashboard templates pending --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `PendingTemplateResponse` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.templates.use`

Run: `mammoth dashboard templates use`. Exact input fields: `mammoth schema get dashboard.templates.use --output json --no-input`.

Example: `mammoth dashboard templates use sample --input '{"body": {"params": {"project_id": 1}}}' --output json --no-input`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `ObjectJobSchema | JobResponse` in the standard JSON envelope; mutation `high_impact`, confirmation `confirm_target`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.trash`

Run: `mammoth dashboard trash`. Exact input fields: `mammoth schema get dashboard.trash --output json --no-input`.

Example: `mammoth dashboard trash 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardTrashResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.update`

Run: `mammoth dashboard update`. Exact input fields: `mammoth schema get dashboard.update --output json --no-input`.

Example: `mammoth dashboard update 123 --input '{"patch": [{"op": "replace", "path": "title", "value": "Renamed dashboard"}]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.v3.generate`

Run: `mammoth dashboard v3 generate`. Exact input fields: `mammoth schema get dashboard.v3.generate --output json --no-input`.

Example: `mammoth dashboard v3 generate --input '{"body": {"params": {"intent": "Summarize revenue by region", "dataview_id": 1}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardV3GenerateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.video-state`

Run: `mammoth dashboard video-state`. Exact input fields: `mammoth schema get dashboard.video-state --output json --no-input`.

Example: `mammoth dashboard video-state 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardVideoStateResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.video.export`

Run: `mammoth dashboard video export`. Exact input fields: `mammoth schema get dashboard.video.export --output json --no-input`.

Example: `mammoth dashboard video export 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardVideoExportResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.widget-data`

Run: `mammoth dashboard widget-data`. Exact input fields: `mammoth schema get dashboard.widget-data --output json --no-input`.

Example: `mammoth dashboard widget-data 123 --input '{"body": {"params": {"widgets": [{"widget_id": "00000000-0000-4000-8000-000000000001"}]}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardWidgetDataResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `dashboard.widget-data-by-url`

Run: `mammoth dashboard widget-data-by-url`. Exact input fields: `mammoth schema get dashboard.widget-data-by-url --output json --no-input`.

Example: `mammoth dashboard widget-data-by-url https://example.com/data.csv --input '{"body": {"params": {"widgets": [{"widget_id": "00000000-0000-4000-8000-000000000001"}]}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `DashboardWidgetDataByUrlResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
