# `view` commands

### `view.active-user.list`

Run: `mammoth view active-user list`. Exact input fields: `mammoth schema get view.active-user.list --output json --no-input`.

Example: `mammoth view active-user list 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewActiveUserListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.active-user.mark`

Run: `mammoth view active-user mark`. Exact input fields: `mammoth schema get view.active-user.mark --output json --no-input`.

Example: `mammoth view active-user mark 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewActiveUserMarkResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.ai.generate-data`

Run: `mammoth view ai generate-data`. Exact input fields: `mammoth schema get view.ai.generate-data --output json --no-input`.

Example: `mammoth view ai generate-data 123 --input '{"prompt": "Summarize revenue by region"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewAiGenerateDataResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.ai.generation-info`

Run: `mammoth view ai generation-info`. Exact input fields: `mammoth schema get view.ai.generation-info --output json --no-input`.

Example: `mammoth view ai generation-info 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewAiGenerationInfoResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.ai.profile`

Run: `mammoth view ai profile`. Exact input fields: `mammoth schema get view.ai.profile --output json --no-input`.

Example: `mammoth view ai profile 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewAiProfileResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.bulk-delete`

Run: `mammoth view bulk-delete`. Exact input fields: `mammoth schema get view.bulk-delete --output json --no-input`.

Example: `mammoth view bulk-delete 123 --input '{"dataview_ids": [1]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewBulkDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.checkpoint.create`

Run: `mammoth view checkpoint create`. Exact input fields: `mammoth schema get view.checkpoint.create --output json --no-input`.

Example: `mammoth view checkpoint create 123 123 --input '{"body": {"checkpoint_name": "Revenue report", "checkpoint_type": "alert"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewCheckpointCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.checkpoint.delete`

Run: `mammoth view checkpoint delete`. Exact input fields: `mammoth schema get view.checkpoint.delete --output json --no-input`.

Example: `mammoth view checkpoint delete 123 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewCheckpointDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.checkpoint.get`

Run: `mammoth view checkpoint get`. Exact input fields: `mammoth schema get view.checkpoint.get --output json --no-input`.

Example: `mammoth view checkpoint get 123 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewCheckpointGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.checkpoint.list`

Run: `mammoth view checkpoint list`. Exact input fields: `mammoth schema get view.checkpoint.list --output json --no-input`.

Example: `mammoth view checkpoint list 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewCheckpointListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.checkpoint.update`

Run: `mammoth view checkpoint update`. Exact input fields: `mammoth schema get view.checkpoint.update --output json --no-input`.

Example: `mammoth view checkpoint update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "approve"}]}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewCheckpointUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.conditional-format.create`

Run: `mammoth view conditional-format create`. Exact input fields: `mammoth schema get view.conditional-format.create --output json --no-input`.

Example: `mammoth view conditional-format create 123 123 --input '{"rule": {"sample_key": "Status"}}' --output json --no-input`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B09 DATAVIEW_INPUT_UNTYPED]: rule is an arbitrary dictionary; reserved, not registered.

### `view.conditional-format.delete-all`

Run: `mammoth view conditional-format delete-all`. Exact input fields: `mammoth schema get view.conditional-format.delete-all --output json --no-input`.

Example: `mammoth view conditional-format delete-all 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewConditionalFormatDeleteAllResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.conditional-format.list`

Run: `mammoth view conditional-format list`. Exact input fields: `mammoth schema get view.conditional-format.list --output json --no-input`.

Example: `mammoth view conditional-format list 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewConditionalFormatListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.conditional-format.update`

Run: `mammoth view conditional-format update`. Exact input fields: `mammoth schema get view.conditional-format.update --output json --no-input`.

Example: `mammoth view conditional-format update 123 123 --input '{"rule": {"sample_key": "Status"}}' --output json --no-input`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B09 DATAVIEW_INPUT_UNTYPED]; reserved, not registered.

### `view.create`

Run: `mammoth view create`. Exact input fields: `mammoth schema get view.create --output json --no-input`.

Example: `mammoth view create 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.data-check.create`

Run: `mammoth view data-check create`. Exact input fields: `mammoth schema get view.data-check.create --output json --no-input`.

Example: `mammoth view data-check create 123 123 --input '{"body": {"checks": [{"check_type": "null_percentage", "config": {"column": "Status", "condition": "lt"}}], "name": "Revenue report"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDataCheckCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.data-check.delete`

Run: `mammoth view data-check delete`. Exact input fields: `mammoth schema get view.data-check.delete --output json --no-input`.

Example: `mammoth view data-check delete 123 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewDataCheckDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.data-check.get`

Run: `mammoth view data-check get`. Exact input fields: `mammoth schema get view.data-check.get --output json --no-input`.

Example: `mammoth view data-check get 123 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDataCheckGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.data-check.list`

Run: `mammoth view data-check list`. Exact input fields: `mammoth schema get view.data-check.list --output json --no-input`.

Example: `mammoth view data-check list 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDataCheckListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.data-check.update`

Run: `mammoth view data-check update`. Exact input fields: `mammoth schema get view.data-check.update --output json --no-input`.

Example: `mammoth view data-check update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "enable"}]}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDataCheckUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.data.get`

Run: `mammoth view data get`. Exact input fields: `mammoth schema get view.data.get --output json --no-input`.

Example: `mammoth view data get 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDataGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.data.query`

Run: `mammoth view data query`. Exact input fields: `mammoth schema get view.data.query --output json --no-input`.

Example: `mammoth view data query 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDataQueryResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.delete`

Run: `mammoth view delete`. Exact input fields: `mammoth schema get view.delete --output json --no-input`.

Example: `mammoth view delete 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.derivative.create`

Run: `mammoth view derivative create`. Exact input fields: `mammoth schema get view.derivative.create --output json --no-input`.

Example: `mammoth view derivative create 123 123 --input '{"body": {"param": {"METRIC": {"AS": "sample", "EXPRESSION": [{"TYPE": "FUNCTION", "VALUE": {"ARGUMENT": "sample", "FUNCTION": "SUM"}}]}}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDerivativeCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.derivative.data`

Run: `mammoth view derivative data`. Exact input fields: `mammoth schema get view.derivative.data --output json --no-input`.

Example: `mammoth view derivative data 123 123 123 --input '{"body": {"condition": {"FILTER_TYPE": "SHOW"}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDerivativeDataResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.derivative.delete`

Run: `mammoth view derivative delete`. Exact input fields: `mammoth schema get view.derivative.delete --output json --no-input`.

Example: `mammoth view derivative delete 123 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewDerivativeDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.derivative.list`

Run: `mammoth view derivative list`. Exact input fields: `mammoth schema get view.derivative.list --output json --no-input`.

Example: `mammoth view derivative list 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDerivativeListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.derivative.update`

Run: `mammoth view derivative update`. Exact input fields: `mammoth schema get view.derivative.update --output json --no-input`.

Example: `mammoth view derivative update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "param", "value": {"METRIC": {"AS": "sample", "EXPRESSION": [{"TYPE": "FUNCTION", "VALUE": {"ARGUMENT": "sample", "FUNCTION": "SUM"}}]}}}]}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDerivativeUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.draft.auto-run`

Run: `mammoth view draft auto-run`. Exact input fields: `mammoth schema get view.draft.auto-run --output json --no-input`.

Example: `mammoth view draft auto-run 123 --input '{"enabled": true, "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDraftAutoRunResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.draft.command`

Run: `mammoth view draft command`. Exact input fields: `mammoth schema get view.draft.command --output json --no-input`.

Example: `mammoth view draft command 123 --input '{"command": "sample", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDraftCommandResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.draft.discard`

Run: `mammoth view draft discard`. Exact input fields: `mammoth schema get view.draft.discard --output json --no-input`.

Example: `mammoth view draft discard 123 --input '{"dataset_id": 456}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewDraftDiscardResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.draft.enter`

Run: `mammoth view draft enter`. Exact input fields: `mammoth schema get view.draft.enter --output json --no-input`.

Example: `mammoth view draft enter 123 --input '{"dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDraftEnterResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.draft.status`

Run: `mammoth view draft status`. Exact input fields: `mammoth schema get view.draft.status --output json --no-input`.

Example: `mammoth view draft status 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDraftStatusResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.draft.submit`

Run: `mammoth view draft submit`. Exact input fields: `mammoth schema get view.draft.submit --output json --no-input`.

Example: `mammoth view draft submit 123 --input '{"dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewDraftSubmitResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.azure-blob`

Run: `mammoth view export azure-blob`. Exact input fields: `mammoth schema get view.export.azure-blob --output json --no-input`.

Example: `mammoth view export azure-blob 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Sensitive structured input must come from a private file or pipe; never put secrets in literal argv.

Expected success: `ViewExportAzureBlobResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.bigquery`

Run: `mammoth view export bigquery`. Exact input fields: `mammoth schema get view.export.bigquery --output json --no-input`.

Example: `mammoth view export bigquery 123 123 --input '{"selected_profile": {}, "selected_identity": {}, "table": "exports"}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewExportBigqueryResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.create`

Run: `mammoth view export create`. Exact input fields: `mammoth schema get view.export.create --output json --no-input`.

Example: `mammoth view export create 123 --input '{"export_spec": {"DATAVIEW_ID": 1, "handler_type": "postgres", "trigger_type": "none", "target_properties": {"file": "./sales.csv", "file_type": "./sales.csv", "include_hidden": true, "is_format_set": true, "use_format": true}, "additional_properties": {}, "run_immediately": true}}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewExportCreateResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.csv`

Run: `mammoth view export csv`. Exact input fields: `mammoth schema get view.export.csv --output json --no-input`.

Example: `mammoth view export csv 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewExportCsvResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.dataset`

Run: `mammoth view export dataset`. Exact input fields: `mammoth schema get view.export.dataset --output json --no-input`.

Example: `mammoth view export dataset 123 123 --input '{"dataset_name": "snapshot"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewExportDatasetResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.delete`

Run: `mammoth view export delete`. Exact input fields: `mammoth schema get view.export.delete --output json --no-input`.

Example: `mammoth view export delete 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewExportDeleteResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.elasticsearch`

Run: `mammoth view export elasticsearch`. Exact input fields: `mammoth schema get view.export.elasticsearch --output json --no-input`.

Example: `mammoth view export elasticsearch 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Sensitive structured input must come from a private file or pipe; never put secrets in literal argv.

Expected success: `ViewExportElasticsearchResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.email`

Run: `mammoth view export email`. Exact input fields: `mammoth schema get view.export.email --output json --no-input`.

Example: `mammoth view export email 123 123 --input '{"emails": ["recipient@example.com"]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewExportEmailResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.ftp`

Run: `mammoth view export ftp`. Exact input fields: `mammoth schema get view.export.ftp --output json --no-input`.

Example: `mammoth view export ftp 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Sensitive structured input must come from a private file or pipe; never put secrets in literal argv.

Expected success: `ViewExportFtpResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.get`

Run: `mammoth view export get`. Exact input fields: `mammoth schema get view.export.get --output json --no-input`.

Example: `mammoth view export get 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewExportGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.list`

Run: `mammoth view export list`. Exact input fields: `mammoth schema get view.export.list --output json --no-input`.

Example: `mammoth view export list 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewExportListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.managed-s3`

Run: `mammoth view export managed-s3`. Exact input fields: `mammoth schema get view.export.managed-s3 --output json --no-input`.

Example: `mammoth view export managed-s3 123 123 --input '{"file_name": "report.csv"}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewExportManagedS3Result` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.mssql`

Run: `mammoth view export mssql`. Exact input fields: `mammoth schema get view.export.mssql --output json --no-input`.

Example: `mammoth view export mssql 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Sensitive structured input must come from a private file or pipe; never put secrets in literal argv.

Expected success: `ViewExportMssqlResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.mysql`

Run: `mammoth view export mysql`. Exact input fields: `mammoth schema get view.export.mysql --output json --no-input`.

Example: `mammoth view export mysql 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Sensitive structured input must come from a private file or pipe; never put secrets in literal argv.

Expected success: `ViewExportMysqlResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.onedrive`

Run: `mammoth view export onedrive`. Exact input fields: `mammoth schema get view.export.onedrive --output json --no-input`.

Example: `mammoth view export onedrive 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Sensitive structured input must come from a private file or pipe; never put secrets in literal argv.

Expected success: `ViewExportOnedriveResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.postgres`

Run: `mammoth view export postgres`. Exact input fields: `mammoth schema get view.export.postgres --output json --no-input`.

Example: `mammoth view export postgres 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Sensitive structured input must come from a private file or pipe; never put secrets in literal argv.

Expected success: `ViewExportPostgresResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.powerbi`

Run: `mammoth view export powerbi`. Exact input fields: `mammoth schema get view.export.powerbi --output json --no-input`.

Example: `mammoth view export powerbi 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Sensitive structured input must come from a private file or pipe; never put secrets in literal argv.

Expected success: `ViewExportPowerbiResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.publish-db`

Run: `mammoth view export publish-db`. Exact input fields: `mammoth schema get view.export.publish-db --output json --no-input`.

Example: `mammoth view export publish-db 123 --input '{"odbc_type": "postgres", "target_properties": {"sample_key": "Status"}}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewExportPublishDbResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.publish-db-update`

Run: `mammoth view export publish-db-update`. Exact input fields: `mammoth schema get view.export.publish-db-update --output json --no-input`.

Example: `mammoth view export publish-db-update 123 --input '{"patch": [{"sample_key": "Status"}]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewExportPublishDbUpdateResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.redshift`

Run: `mammoth view export redshift`. Exact input fields: `mammoth schema get view.export.redshift --output json --no-input`.

Example: `mammoth view export redshift 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Sensitive structured input must come from a private file or pipe; never put secrets in literal argv.

Expected success: `ViewExportRedshiftResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.rest`

Run: `mammoth view export rest`. Exact input fields: `mammoth schema get view.export.rest --output json --no-input`.

Example: `mammoth view export rest 123 123 --input '{"base_url": "https://api.example", "endpoint_path": "/records"}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewExportRestResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.sftp`

Run: `mammoth view export sftp`. Exact input fields: `mammoth schema get view.export.sftp --output json --no-input`.

Example: `mammoth view export sftp 123 123 --input '{"host": "sftp.example", "username": "agent"}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewExportSftpResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.sharepoint`

Run: `mammoth view export sharepoint`. Exact input fields: `mammoth schema get view.export.sharepoint --output json --no-input`.

Example: `mammoth view export sharepoint 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Sensitive structured input must come from a private file or pipe; never put secrets in literal argv.

Expected success: `ViewExportSharepointResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.tableau`

Run: `mammoth view export tableau`. Exact input fields: `mammoth schema get view.export.tableau --output json --no-input`.

Example: `mammoth view export tableau 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Sensitive structured input must come from a private file or pipe; never put secrets in literal argv.

Expected success: `ViewExportTableauResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.export.update`

Run: `mammoth view export update`. Exact input fields: `mammoth schema get view.export.update --output json --no-input`.

Example: `mammoth view export update 123 123 --input '{"patches": [{"sample_key": "Status"}]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewExportUpdateResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.exportable-config.apply`

Run: `mammoth view exportable-config apply`. Exact input fields: `mammoth schema get view.exportable-config.apply --output json --no-input`.

Example: `mammoth view exportable-config apply 123 --input-format json --input '{"config": {"tasks": []}}' --output json --no-input --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Expected success: `ViewExportableConfigApplyResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `confirm_target`, wait policy `returns_job`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.exportable-config.get`

Run: `mammoth view exportable-config get`. Exact input fields: `mammoth schema get view.exportable-config.get --output json --no-input`.

Example: `mammoth view exportable-config get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewExportableConfigGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.get`

Run: `mammoth view get`. Exact input fields: `mammoth schema get view.get --output json --no-input`.

Example: `mammoth view get 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.list`

Run: `mammoth view list`. Exact input fields: `mammoth schema get view.list --output json --no-input`.

Example: `mammoth view list 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.parameter-context`

Run: `mammoth view parameter-context`. Exact input fields: `mammoth schema get view.parameter-context --output json --no-input`.

Example: `mammoth view parameter-context 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewParameterContextResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.pipeline.edit`

Run: `mammoth view pipeline edit`. Exact input fields: `mammoth schema get view.pipeline.edit --output json --no-input`.

Example: `mammoth view pipeline edit 123 --input '{"patches": [{"sample_key": "Status"}]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewPipelineEditResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.pipeline.get`

Run: `mammoth view pipeline get`. Exact input fields: `mammoth schema get view.pipeline.get --output json --no-input`.

Example: `mammoth view pipeline get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewPipelineGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.pipeline.items`

Run: `mammoth view pipeline items`. Exact input fields: `mammoth schema get view.pipeline.items --output json --no-input`.

Example: `mammoth view pipeline items 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewPipelineItemsResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.pipeline.items-all`

Run: `mammoth view pipeline items-all`. Exact input fields: `mammoth schema get view.pipeline.items-all --output json --no-input`.

Example: `mammoth view pipeline items-all 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewPipelineItemsAllResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.pipeline.rerun`

Run: `mammoth view pipeline rerun`. Exact input fields: `mammoth schema get view.pipeline.rerun --output json --no-input`.

Example: `mammoth view pipeline rerun 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewPipelineRerunResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.pipeline.wait`

Run: `mammoth view pipeline wait`. Exact input fields: `mammoth schema get view.pipeline.wait --output json --no-input`.

Example: `mammoth view pipeline wait 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewPipelineWaitResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.preview`

Run: `mammoth view preview`. Exact input fields: `mammoth schema get view.preview --output json --no-input`.

Example: `mammoth view preview 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewPreviewResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.restore`

Run: `mammoth view restore`. Exact input fields: `mammoth schema get view.restore --output json --no-input`.

Example: `mammoth view restore 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewRestoreResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.task.add`

Run: `mammoth view task add`. Exact input fields: `mammoth schema get view.task.add --output json --no-input`.

Example: `mammoth view task add 123 --input '{"task_spec": {"DATAVIEW_ID": 123, "SEQUENCE_NUMBER": 1, "COPY": {}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTaskAddResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.task.delete`

Run: `mammoth view task delete`. Exact input fields: `mammoth schema get view.task.delete --output json --no-input`.

Example: `mammoth view task delete 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewTaskDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.task.get`

Run: `mammoth view task get`. Exact input fields: `mammoth schema get view.task.get --output json --no-input`.

Example: `mammoth view task get 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTaskGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.task.list`

Run: `mammoth view task list`. Exact input fields: `mammoth schema get view.task.list --output json --no-input`.

Example: `mammoth view task list 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTaskListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.task.preview`

Run: `mammoth view task preview`. Exact input fields: `mammoth schema get view.task.preview --output json --no-input`.

Example: `mammoth view task preview 123 --input '{"task_spec": {"DATAVIEW_ID": 123, "SEQUENCE_NUMBER": 1, "COPY": {}}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTaskPreviewResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.task.update`

Run: `mammoth view task update`. Exact input fields: `mammoth schema get view.task.update --output json --no-input`.

Example: `mammoth view task update 123 123 --input '{"task_spec": {"DATAVIEW_ID": 123, "SEQUENCE_NUMBER": 1, "COPY": {}}, "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTaskUpdateResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.add-column`

Run: `mammoth view transform add-column`. Exact input fields: `mammoth schema get view.transform.add-column --output json --no-input`.

Example: `mammoth view transform add-column 123 --input '{"name": "Revenue report", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformAddColumnResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.add-sql`

Run: `mammoth view transform add-sql`. Exact input fields: `mammoth schema get view.transform.add-sql --output json --no-input`.

Example: `mammoth view transform add-sql 123 --input '{"query": "SELECT region, SUM(revenue) FROM data GROUP BY region", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformAddSqlResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.ai`

Run: `mammoth view transform ai`. Exact input fields: `mammoth schema get view.transform.ai --output json --no-input`.

Example: `mammoth view transform ai 123 --input '{"prompt": "Summarize revenue by region", "context_columns": ["Status"], "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformAiResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.bulk-replace`

Run: `mammoth view transform bulk-replace`. Exact input fields: `mammoth schema get view.transform.bulk-replace --output json --no-input`.

Example: `mammoth view transform bulk-replace 123 --input '{"columns": ["Status"], "mapping": [{"search": ["sample"], "replace": "sample"}], "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformBulkReplaceResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.combine-columns`

Run: `mammoth view transform combine-columns`. Exact input fields: `mammoth schema get view.transform.combine-columns --output json --no-input`.

Example: `mammoth view transform combine-columns 123 --input '{"sources": ["Status"], "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformCombineColumnsResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.convert-type`

Run: `mammoth view transform convert-type`. Exact input fields: `mammoth schema get view.transform.convert-type --output json --no-input`.

Example: `mammoth view transform convert-type 123 --input '{"conversions": [{"column": "Status", "to": "TEXT"}], "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformConvertTypeResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.copy-columns`

Run: `mammoth view transform copy-columns`. Exact input fields: `mammoth schema get view.transform.copy-columns --output json --no-input`.

Example: `mammoth view transform copy-columns 123 --input '{"copies": [{"source": "Status"}], "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformCopyColumnsResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.crosstab`

Run: `mammoth view transform crosstab`. Exact input fields: `mammoth schema get view.transform.crosstab --output json --no-input`.

Example: `mammoth view transform crosstab 123 --input '{"rows": ["sample"], "pivot_column": "Status", "select": {"function": "SUM"}, "dataset_name": "Revenue report", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformCrosstabResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.date-diff`

Run: `mammoth view transform date-diff`. Exact input fields: `mammoth schema get view.transform.date-diff --output json --no-input`.

Example: `mammoth view transform date-diff 123 --input '{"component": "YEAR", "start": "sample", "end": "sample", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformDateDiffResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.delete-columns`

Run: `mammoth view transform delete-columns`. Exact input fields: `mammoth schema get view.transform.delete-columns --output json --no-input`.

Example: `mammoth view transform delete-columns 123 --input '{"columns": ["Status"], "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformDeleteColumnsResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.discard-duplicates`

Run: `mammoth view transform discard-duplicates`. Exact input fields: `mammoth schema get view.transform.discard-duplicates --output json --no-input`.

Example: `mammoth view transform discard-duplicates 123 --input '{"dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformDiscardDuplicatesResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.extract-date`

Run: `mammoth view transform extract-date`. Exact input fields: `mammoth schema get view.transform.extract-date --output json --no-input`.

Example: `mammoth view transform extract-date 123 --input '{"column": "Status", "component": "year", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformExtractDateResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.fill-missing`

Run: `mammoth view transform fill-missing`. Exact input fields: `mammoth schema get view.transform.fill-missing --output json --no-input`.

Example: `mammoth view transform fill-missing 123 --input '{"column": "Status", "direction": "FIRST_VALUE", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformFillMissingResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.filter`

Run: `mammoth view transform filter`. Exact input fields: `mammoth schema get view.transform.filter --output json --no-input`.

Example: `mammoth view transform filter 123 --input '{"condition": {"column": "Status", "operator": "EQ", "value": "Active"}, "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformFilterResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.generate-sql`

Run: `mammoth view transform generate-sql`. Exact input fields: `mammoth schema get view.transform.generate-sql --output json --no-input`.

Example: `mammoth view transform generate-sql 123 --input '{"intent": "Summarize revenue by region", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformGenerateSqlResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.increment-date`

Run: `mammoth view transform increment-date`. Exact input fields: `mammoth schema get view.transform.increment-date --output json --no-input`.

Example: `mammoth view transform increment-date 123 --input '{"column": "Status", "delta": {}, "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformIncrementDateResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.join`

Run: `mammoth view transform join`. Exact input fields: `mammoth schema get view.transform.join --output json --no-input`.

Example: `mammoth view transform join 123 --input '{"foreign_view": 1, "join_type": "INNER", "on": [{"left": "sample", "right": "sample"}], "select": ["sample"], "dataset_id": 456, "foreign_dataset_id": 457}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformJoinResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.json-extract`

Run: `mammoth view transform json-extract`. Exact input fields: `mammoth schema get view.transform.json-extract --output json --no-input`.

Example: `mammoth view transform json-extract 123 --input '{"column": "Status", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformJsonExtractResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.limit-rows`

Run: `mammoth view transform limit-rows`. Exact input fields: `mammoth schema get view.transform.limit-rows --output json --no-input`.

Example: `mammoth view transform limit-rows 123 --input '{"n": 1, "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformLimitRowsResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.lookup`

Run: `mammoth view transform lookup`. Exact input fields: `mammoth schema get view.transform.lookup --output json --no-input`.

Example: `mammoth view transform lookup 123 --input '{"source": "Status", "lookup_view_id": 1, "key": "Status", "value": "sample", "dataset_id": 456, "lookup_dataset_id": 457}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformLookupResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.math`

Run: `mammoth view transform math`. Exact input fields: `mammoth schema get view.transform.math --output json --no-input`.

Example: `mammoth view transform math 123 --input '{"expression": "price * quantity", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformMathResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.pivot`

Run: `mammoth view transform pivot`. Exact input fields: `mammoth schema get view.transform.pivot --output json --no-input`.

Example: `mammoth view transform pivot 123 --input '{"group_by": ["sample"], "aggregations": [{"column": "Status", "function": "SUM"}], "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformPivotResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.replace`

Run: `mammoth view transform replace`. Exact input fields: `mammoth schema get view.transform.replace --output json --no-input`.

Example: `mammoth view transform replace 123 --input '{"columns": ["Status"], "find": "sample", "replace": "sample", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformReplaceResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.set-values`

Run: `mammoth view transform set-values`. Exact input fields: `mammoth schema get view.transform.set-values --output json --no-input`.

Example: `mammoth view transform set-values 123 --input '{"values": [{"value": "sample"}], "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformSetValuesResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.small-large`

Run: `mammoth view transform small-large`. Exact input fields: `mammoth schema get view.transform.small-large --output json --no-input`.

Example: `mammoth view transform small-large 123 --input '{"function": "SMALL", "columns": ["Status"], "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformSmallLargeResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.split`

Run: `mammoth view transform split`. Exact input fields: `mammoth schema get view.transform.split --output json --no-input`.

Example: `mammoth view transform split 123 --input '{"column": "Status", "delimiter": "sample", "new_columns": [{"name": "Revenue report"}], "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformSplitResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.substring`

Run: `mammoth view transform substring`. Exact input fields: `mammoth schema get view.transform.substring --output json --no-input`.

Example: `mammoth view transform substring 123 --input '{"column": "Status", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformSubstringResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.text`

Run: `mammoth view transform text`. Exact input fields: `mammoth schema get view.transform.text --output json --no-input`.

Example: `mammoth view transform text 123 --input '{"columns": ["Status"], "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformTextResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.unnest`

Run: `mammoth view transform unnest`. Exact input fields: `mammoth schema get view.transform.unnest --output json --no-input`.

Example: `mammoth view transform unnest 123 --input '{"columns": ["Status"], "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformUnnestResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.transform.window`

Run: `mammoth view transform window`. Exact input fields: `mammoth schema get view.transform.window --output json --no-input`.

Example: `mammoth view transform window 123 --input '{"function": "ROW_NUMBER", "dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTransformWindowResult` in the standard JSON envelope; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.trash`

Run: `mammoth view trash`. Exact input fields: `mammoth schema get view.trash --output json --no-input`.

Example: `mammoth view trash 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewTrashResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.update`

Run: `mammoth view update`. Exact input fields: `mammoth schema get view.update --output json --no-input`.

Example: `mammoth schema get view.update --output json --no-input`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B09 DATAVIEW_INPUT_UNTYPED]: patch_data is an arbitrary dictionary; reserved, not registered.

### `view.version.apply`

Run: `mammoth view version apply`. Exact input fields: `mammoth schema get view.version.apply --output json --no-input`.

Example: `mammoth view version apply 123 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewVersionApplyResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.version.delete`

Run: `mammoth view version delete`. Exact input fields: `mammoth schema get view.version.delete --output json --no-input`.

Example: `mammoth view version delete 123 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ViewVersionDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.version.get`

Run: `mammoth view version get`. Exact input fields: `mammoth schema get view.version.get --output json --no-input`.

Example: `mammoth view version get 123 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewVersionGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.version.list`

Run: `mammoth view version list`. Exact input fields: `mammoth schema get view.version.list --output json --no-input`.

Example: `mammoth view version list 123 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewVersionListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `view.version.update`

Run: `mammoth view version update`. Exact input fields: `mammoth schema get view.version.update --output json --no-input`.

Example: `mammoth view version update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "name"}]}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ViewVersionUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
