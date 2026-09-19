# `view` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `view.active-user.list`

Run: `mammoth view active-user list`. Exact input fields: `mammoth schema get view.active-user.list --output json --no-input`.

Example: `mammoth view active-user list 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewActiveUserListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 exact-parent retained view 46/dataset 29 read succeeded with an empty active-user list. One view and single-page boundary; not Full.

### `view.active-user.mark`

Run: `mammoth view active-user mark`. Exact input fields: `mammoth schema get view.active-user.mark --output json --no-input`.

Example: `mammoth view active-user mark 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewActiveUserMarkResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Returned active_users:[{id:5,email:<api user>,...}] confirming our session is now marked active on view 68. Single invocation only.

### `view.ai.generate-data`

Run: `mammoth view ai generate-data`. Exact input fields: `mammoth schema get view.ai.generate-data --output json --no-input`.

Example: `mammoth view ai generate-data 123 --input '{"prompt": "Summarize revenue by region"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewAiGenerateDataResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Returned {context_columns:[column_1..4],data:[3 generated row strings],provider:open_ai}. Single invocation only.

### `view.ai.generation-info`

Run: `mammoth view ai generation-info`. Exact input fields: `mammoth schema get view.ai.generation-info --output json --no-input`.

Example: `mammoth view ai generation-info 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewAiGenerationInfoResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend: GET /workspaces/4/projects/24/datasets/54/dataviews/76/data/generate -> HTTP 400 5GENR011 NOT_IMPLEMENTED 'Not implemented', request_id:null. Re-check before relying on it.

### `view.ai.profile`

Run: `mammoth view ai profile`. Exact input fields: `mammoth schema get view.ai.profile --output json --no-input`.

Example: `mammoth view ai profile 123 --input '{"dataset_id": 456, "action": "insights"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewAiProfileResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: release ProfileGenerationSpec {params:{action}} body accepted; returned real generated insights: {"data":{"insights":{"performance_analysis":{"domain_specific_insights":[...]}}}}. Single…

### `view.bulk-delete`

Run: `mammoth view bulk-delete`. Exact input fields: `mammoth schema get view.bulk-delete --output json --no-input`.

Example: `mammoth view bulk-delete 123 --input '{"dataview_ids": [1]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewBulkDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Created throwaway view 74 (sweep-view-bulkdel) via view create, then bulk-deleted it. Without --yes: confirmation_required. With --yes: job 332 safe_delete_dataviews -> status success. Single invocati…

### `view.checkpoint.create`

Run: `mammoth view checkpoint create`. Exact input fields: `mammoth schema get view.checkpoint.create --output json --no-input`.

Example: `mammoth view checkpoint create 123 123 --input '{"body": {"checkpoint_name": "Revenue report", "checkpoint_type": "alert", "pinned_to_end": true}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewCheckpointCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. First attempt without pinned_to_end/task_sequence failed 4GENR007 (schema's own example omits the requirement, doc mismatch). Retried with pinned_to_end:true, created checkpoint id=4. Sing…

### `view.checkpoint.delete`

Run: `mammoth view checkpoint delete`. Exact input fields: `mammoth schema get view.checkpoint.delete --output json --no-input`.

Example: `mammoth view checkpoint delete 123 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewCheckpointDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted checkpoint 4 (202 accepted); read-back list is empty. Single invocation only.

### `view.checkpoint.get`

Run: `mammoth view checkpoint get`. Exact input fields: `mammoth schema get view.checkpoint.get --output json --no-input`.

Example: `mammoth view checkpoint get 123 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewCheckpointGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Fetched checkpoint 4, matches create. Single invocation only.

### `view.checkpoint.list`

Run: `mammoth view checkpoint list`. Exact input fields: `mammoth schema get view.checkpoint.list --output json --no-input`.

Example: `mammoth view checkpoint list 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewCheckpointListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Listed checkpoints, showed id=4. Single invocation only.

### `view.checkpoint.update`

Run: `mammoth view checkpoint update`. Exact input fields: `mammoth schema get view.checkpoint.update --output json --no-input`.

Example: `mammoth view checkpoint update 123 123 123 --input '{"body": {"patches": [{"op": "command", "path": "approve", "value": null}]}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewCheckpointUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. First attempt sending a full AddCheckpointSpec body (matching create's shape) failed with invalid_input_field_type; update actually needs body.patches[] (CheckpointPatches/CheckPointPatch…

### `view.conditional-format.create`

Run: `mammoth view conditional-format create`. Exact input fields: `mammoth schema get view.conditional-format.create --output json --no-input`.

Example: `mammoth view conditional-format create 123 123 --input '{"rule": {"cf_type": "RULE", "payload": {"FORMAT": {"name": "Flag open orders", "color": "red", "applies_to": "row", "column_ids": "[]"}, "CONDITION": {"OR": [{"column_1": {"CONTAINS": {"VALUE": ["Open"]}}}]}}}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewConditionalFormatCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.17 — re-verification 2026-09-18 (2.0.16 fixes): exit 0 on release with CLI 2.0.17. HighlightEntry body accepted; response is {rule_id: rule} with COLUMNS_USED resolved. The former generated example ({"rule": {"sample_key": ...}}) was a placeholder; the example hin…

### `view.conditional-format.delete-all`

Run: `mammoth view conditional-format delete-all`. Exact input fields: `mammoth schema get view.conditional-format.delete-all --output json --no-input`.

Example: `mammoth view conditional-format delete-all 123 123 --input '{"rule_id": "bca0ff33bd6f8ed1"}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewConditionalFormatDeleteAllResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.17 — re-verification 2026-09-18 (2.0.16 fixes): exit 0 on release with CLI 2.0.17. Fix held: rule_id forwarded; rule created via `view conditional-format create` (HighlightEntry body) was deleted and `conditional-format list` returned [] afterwards. Note: `conditi…

### `view.conditional-format.list`

Run: `mammoth view conditional-format list`. Exact input fields: `mammoth schema get view.conditional-format.list --output json --no-input`.

Example: `mammoth view conditional-format list 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewConditionalFormatListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.17 — re-verification 2026-09-18 (2.0.16 fixes): exit 0 on release with CLI 2.0.17. With SDK 0.7.9 the one existing rule is returned as [{rule_id, cf_type, FORMAT, CONDITION, ...}]; with SDK 0.7.8 the same call returned [] (mapping keyed by rule id was discarded).…

### `view.conditional-format.update`

Run: `mammoth view conditional-format update`. Exact input fields: `mammoth schema get view.conditional-format.update --output json --no-input`.

Example: `mammoth view conditional-format update 123 123 --input '{"rule": {"sample_key": "Status"}}' --output json --no-input`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B09 DATAVIEW_INPUT_UNTYPED]; reserved, not registered.

### `view.create`

Run: `mammoth view create`. Exact input fields: `mammoth schema get view.create --output json --no-input`.

Example: `mammoth view create 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19 (CLI 2.0.18): plain create on an owned dataset returned the new view's record (id, dataset_id; earlier releases printed '<unserializable View>'), and discard-duplicates then ran on it. clone_from is not usable on release: the clon…

### `view.data-check.create`

Run: `mammoth view data-check create`. Exact input fields: `mammoth schema get view.data-check.create --output json --no-input`.

Example: `mammoth view data-check create 123 123 --input '{"body": {"checks": [{"check_type": "null_percentage", "config": {"column": "Status", "condition": "lt"}}], "name": "Revenue report"}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDataCheckCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. SUSPECTED DEFECT: passing an explicit threshold:5.0 (a float, matching the schema's documented oneOf[number,integer,...] and default) caused invalid_input_field_type on body.checks.0. Omit…

### `view.data-check.delete`

Run: `mammoth view data-check delete`. Exact input fields: `mammoth schema get view.data-check.delete --output json --no-input`.

Example: `mammoth view data-check delete 123 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewDataCheckDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted data check 4 (202); read-back get now returns 404 NON_EXISTENT_RESOURCE, confirming deletion. Single invocation only.

### `view.data-check.get`

Run: `mammoth view data-check get`. Exact input fields: `mammoth schema get view.data-check.get --output json --no-input`.

Example: `mammoth view data-check get 123 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDataCheckGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Fetched data check 4, threshold shows as 0 (the applied default). Single invocation only.

### `view.data-check.list`

Run: `mammoth view data-check list`. Exact input fields: `mammoth schema get view.data-check.list --output json --no-input`.

Example: `mammoth view data-check list 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDataCheckListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 exact-parent retained view 46/dataset 29 read succeeded with an empty data-check list. One view and single-page boundary; not Full.

### `view.data-check.update`

Run: `mammoth view data-check update`. Exact input fields: `mammoth schema get view.data-check.update --output json --no-input`.

Example: `mammoth view data-check update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "enable"}]}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDataCheckUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend_error: SUSPECTED DEFECT: PATCH returned HTTP 500 empty body / CLI code=outcome_unknown, but a follow-up get confirmed the mutation actually applied (enabled:false, updated_. Re-check before relying on it.

### `view.data.get`

Run: `mammoth view data get`. Exact input fields: `mammoth schema get view.data.get --output json --no-input`.

Example: `mammoth view data get 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDataGetResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19 (CLI 2.0.18): read back after every transform in the run (11 reads on release, rows compared by value with the fixture's known answer: amounts, statuses, ids, joined region, pivot totals). Full page only; paging not exercised.

### `view.data.query`

Run: `mammoth view data query`. Exact input fields: `mammoth schema get view.data.query --output json --no-input`.

Example: `mammoth view data query 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDataQueryResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19 (CLI 2.0.18): condition on the pivoted view compiled to the backend clause shape and answered (exit 0); EQ with a column select and an AND of CONTAINS/NE also verified read-only on a pre-existing view. Before 2.0.18 the spec was f…

### `view.delete`

Run: `mammoth view delete`. Exact input fields: `mammoth schema get view.delete --output json --no-input`.

Example: `mammoth view delete 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19: exit 0 on release with CLI 2.0.18. Single invocation only.

### `view.derivative.create`

Run: `mammoth view derivative create`. Exact input fields: `mammoth schema get view.derivative.create --output json --no-input`.

Example: `mammoth view derivative create 123 123 --input '{"body": {"param": {"METRIC": {"AS": "sample", "EXPRESSION": [{"TYPE": "FUNCTION", "VALUE": {"ARGUMENT": "sample", "FUNCTION": "SUM"}}]}}}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDerivativeCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Created a SUM(amount) metric derivative on view 106, id=5 (my own first attempt keyed the param dict by the metric name instead of the required literal 'METRIC' key - that was my error, no…

### `view.derivative.data`

Run: `mammoth view derivative data`. Exact input fields: `mammoth schema get view.derivative.data --output json --no-input`.

Example: `mammoth view derivative data 123 123 123 --input '{"body": {"condition": {"FILTER_TYPE": "SHOW"}}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDerivativeDataResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend_error: SUSPECTED DEFECT: using the CLI's own documented agent_example body verbatim, derivative data fetch returns HTTP 500 empty body / outcome_unknown, reproduced twice (. Re-check before relying on it.

### `view.derivative.delete`

Run: `mammoth view derivative delete`. Exact input fields: `mammoth schema get view.derivative.delete --output json --no-input`.

Example: `mammoth view derivative delete 123 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewDerivativeDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted derivative 5 (202 accepted). Single invocation only.

### `view.derivative.list`

Run: `mammoth view derivative list`. Exact input fields: `mammoth schema get view.derivative.list --output json --no-input`.

Example: `mammoth view derivative list 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDerivativeListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 exact-parent retained view 46/dataset 29 read succeeded with an empty derivatives list. One view and single-page boundary; not Full.

### `view.derivative.update`

Run: `mammoth view derivative update`. Exact input fields: `mammoth schema get view.derivative.update --output json --no-input`.

Example: `mammoth view derivative update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "param", "value": {"METRIC": {"AS": "sample", "EXPRESSION": [{"TYPE": "FUNCTION", "VALUE": {"ARGUMENT": "sample", "FUNCTION": "SUM"}}]}}}]}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDerivativeUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: 202 Accepted non-object body reported as success. Response: {"data":{"response":null,"status_code":202}}. Single invocation only.

### `view.draft.auto-run`

Run: `mammoth view draft auto-run`. Exact input fields: `mammoth schema get view.draft.auto-run --output json --no-input`.

Example: `mammoth view draft auto-run 123 --input '{"enabled": true, "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDraftAutoRunResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.draft.command`

Run: `mammoth view draft command`. Exact input fields: `mammoth schema get view.draft.command --output json --no-input`.

Example: `mammoth view draft command 123 --input '{"command": "sample", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDraftCommandResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. command:enter -> {draft_mode:clean}. command:discard without --confirm -> confirmation_target_mismatch exit 2 (correct guardrail). With --yes --confirm 73 -> {draft_mode:clean} again, view 73 left in…

### `view.draft.discard`

Run: `mammoth view draft discard`. Exact input fields: `mammoth schema get view.draft.discard --output json --no-input`.

Example: `mammoth view draft discard 123 --input '{"dataset_id": 456}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewDraftDiscardResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.draft.enter`

Run: `mammoth view draft enter`. Exact input fields: `mammoth schema get view.draft.enter --output json --no-input`.

Example: `mammoth view draft enter 123 --input '{"dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDraftEnterResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.draft.status`

Run: `mammoth view draft status`. Exact input fields: `mammoth schema get view.draft.status --output json --no-input`.

Example: `mammoth view draft status 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDraftStatusResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `view.draft.submit`

Run: `mammoth view draft submit`. Exact input fields: `mammoth schema get view.draft.submit --output json --no-input`.

Example: `mammoth view draft submit 123 --input '{"dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDraftSubmitResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.export.azure-blob`

Run: `mammoth view export azure-blob`. Exact input fields: `mammoth schema get view.export.azure-blob --output json --no-input`.

Example: `mammoth view export azure-blob 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportAzureBlobResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.bigquery`

Run: `mammoth view export bigquery`. Exact input fields: `mammoth schema get view.export.bigquery --output json --no-input`.

Example: `mammoth view export bigquery 123 123 --input '{"selected_profile": {}, "selected_identity": {}, "table": "exports"}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportBigqueryResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.create`

Run: `mammoth view export create`. Exact input fields: `mammoth schema get view.export.create --output json --no-input`.

Example: `mammoth view export create 123 --input '{"export_spec": {"DATAVIEW_ID": 1, "handler_type": "postgres", "trigger_type": "none", "target_properties": {"file": "./sales.csv", "file_type": "./sales.csv", "include_hidden": true, "is_format_set": true, "use_format": true}, "additional_properties": {}, "run_immediately": true}}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportCreateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: observed blocker — backend: CLI accepts the request (exit 0, job 358 accepted on POST /dataviews/76/actions), but job get 358 -> status:error, response:{"error":{"message":"'destination'"}} (a raw Py. Re-check before relying on it.

### `view.export.csv`

Run: `mammoth view export csv`. Exact input fields: `mammoth schema get view.export.csv --output json --no-input`.

Example: `mammoth view export csv 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewExportCsvResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.export.dataset`

Run: `mammoth view export dataset`. Exact input fields: `mammoth schema get view.export.dataset --output json --no-input`.

Example: `mammoth view export dataset 123 123 --input '{"dataset_name": "snapshot"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewExportDatasetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.export.delete`

Run: `mammoth view export delete`. Exact input fields: `mammoth schema get view.export.delete --output json --no-input`.

Example: `mammoth view export delete 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportDeleteResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Deleted export 2 -> {future_id:null,status:deleted,trigger_id:2}. Single invocation only.

### `view.export.elasticsearch`

Run: `mammoth view export elasticsearch`. Exact input fields: `mammoth schema get view.export.elasticsearch --output json --no-input`.

Example: `mammoth view export elasticsearch 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportElasticsearchResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.email`

Run: `mammoth view export email`. Exact input fields: `mammoth schema get view.export.email --output json --no-input`.

Example: `mammoth view export email 123 123 --input '{"emails": ["recipient@example.com"]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportEmailResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.ftp`

Run: `mammoth view export ftp`. Exact input fields: `mammoth schema get view.export.ftp --output json --no-input`.

Example: `mammoth view export ftp 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportFtpResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.get`

Run: `mammoth view export get`. Exact input fields: `mammoth schema get view.export.get --output json --no-input`.

Example: `mammoth view export get 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewExportGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. export id 2 was created as a fixture via view.export.create using the schema's own postgres runnable_example (run_immediately:false) since the csv_file variant errors (see view.export.create). Returne…

### `view.export.list`

Run: `mammoth view export list`. Exact input fields: `mammoth schema get view.export.list --output json --no-input`.

Example: `mammoth view export list 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewExportListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI an earlier release — Published PyPI CLI 1.1.11 read-only export-list call on retained view46/dataset29 returned a bounded empty page with unexpected offset50; no export was executed and Full support is not claimed.

### `view.export.managed-s3`

Run: `mammoth view export managed-s3`. Exact input fields: `mammoth schema get view.export.managed-s3 --output json --no-input`.

Example: `mammoth view export managed-s3 123 123 --input '{"file_name": "report.csv"}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportManagedS3Result`; mutation `external_effect`, confirmation `yes_always`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.export.mssql`

Run: `mammoth view export mssql`. Exact input fields: `mammoth schema get view.export.mssql --output json --no-input`.

Example: `mammoth view export mssql 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportMssqlResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.mysql`

Run: `mammoth view export mysql`. Exact input fields: `mammoth schema get view.export.mysql --output json --no-input`.

Example: `mammoth view export mysql 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportMysqlResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.onedrive`

Run: `mammoth view export onedrive`. Exact input fields: `mammoth schema get view.export.onedrive --output json --no-input`.

Example: `mammoth view export onedrive 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportOnedriveResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.postgres`

Run: `mammoth view export postgres`. Exact input fields: `mammoth schema get view.export.postgres --output json --no-input`.

Example: `mammoth view export postgres 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportPostgresResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.powerbi`

Run: `mammoth view export powerbi`. Exact input fields: `mammoth schema get view.export.powerbi --output json --no-input`.

Example: `mammoth view export powerbi 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportPowerbiResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.publish-db`

Run: `mammoth view export publish-db`. Exact input fields: `mammoth schema get view.export.publish-db --output json --no-input`.

Example: `mammoth view export publish-db 123 --input '{"odbc_type": "postgres", "target_properties": {"sample_key": "Status"}}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportPublishDbResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Attempt 1 target_properties:{} -> HTTP 400 4GENR007 extra=[{key:target_properties.table,message:"Field required"}] (clear). Attempt 2 target_properties:{table:sweep_stores} -> {job_id:339}; job get co…

### `view.export.publish-db-update`

Run: `mammoth view export publish-db-update`. Exact input fields: `mammoth schema get view.export.publish-db-update --output json --no-input`.

Example: `mammoth view export publish-db-update 123 --input '{"patch": [{"op": "replace", "path": "credentials", "value": {"odbc_type": "postgres"}}]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportPublishDbUpdateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: CLI defect fixed, untried since — CLI defect fixed in 2.0.16 (example value is the documented {"odbc_type": "postgres"} object (a bare string is rejected)); not re-verified live yet. re-verification 2026-09-18 (2.0.16 fixes) observed not_rerun: Not re-run: needs a live publish-to-database exp…

### `view.export.redshift`

Run: `mammoth view export redshift`. Exact input fields: `mammoth schema get view.export.redshift --output json --no-input`.

Example: `mammoth view export redshift 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportRedshiftResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.rest`

Run: `mammoth view export rest`. Exact input fields: `mammoth schema get view.export.rest --output json --no-input`.

Example: `mammoth view export rest 123 123 --input '{"base_url": "https://api.example", "endpoint_path": "/records"}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportRestResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.sftp`

Run: `mammoth view export sftp`. Exact input fields: `mammoth schema get view.export.sftp --output json --no-input`.

Example: `mammoth view export sftp 123 123 --input '{"host": "sftp.example", "username": "agent"}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportSftpResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.sharepoint`

Run: `mammoth view export sharepoint`. Exact input fields: `mammoth schema get view.export.sharepoint --output json --no-input`.

Example: `mammoth view export sharepoint 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportSharepointResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.tableau`

Run: `mammoth view export tableau`. Exact input fields: `mammoth schema get view.export.tableau --output json --no-input`.

Example: `mammoth view export tableau 123 123 --input /private/path/request.json --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportTableauResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.update`

Run: `mammoth view export update`. Exact input fields: `mammoth schema get view.export.update --output json --no-input`.

Example: `mammoth view export update 123 123 --input '{"patches": [{"sample_key": "Status"}]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportUpdateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Attempt 1 path:target_properties -> HTTP 400 4GENR007, clear message: path must be one of run/suspend/restore/discard/params, and value must be the FULL export spec (DATAVIEW_ID,handler_type,trigger_t…

### `view.exportable-config.apply`

Run: `mammoth view exportable-config apply`. Exact input fields: `mammoth schema get view.exportable-config.apply --output json --no-input`.

Example: `mammoth view exportable-config apply 123 --input-format json --input '{"config": {"tasks": []}}' --output json --no-input --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ViewExportableConfigApplyResult`; mutation `reversible_pipeline`, confirmation `confirm_target`, wait policy `returns_job`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Re-applied the view's own exportable config verbatim (idempotent no-op); returned dataview_id=106. Single invocation only.

### `view.exportable-config.get`

Run: `mammoth view exportable-config get`. Exact input fields: `mammoth schema get view.exportable-config.get --output json --no-input`.

Example: `mammoth view exportable-config get 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewExportableConfigGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Fetched full exportable config for view 106 (metadata, display_properties, dependencies, empty tasks/checkpoints/derivatives/data_checks). Single invocation only.

### `view.get`

Run: `mammoth view get`. Exact input fields: `mammoth schema get view.get --output json --no-input`.

Example: `mammoth view get 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 correct-parent read resolves retained view46 under dataset29. The earlier dataset28 403 remains an invalid-parent control, not an authorization boundary; bounded to one view and not Full.

### `view.list`

Run: `mammoth view list`. Exact input fields: `mammoth schema get view.list --output json --no-input`.

Example: `mammoth view list 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Listed 1 dataview: id=106, ds_id=85, status=ready, row_count=3. Note: response includes a 'next' pagination URL (offset=100) despite only 1 total item, possibly a minor pagination defect.…

### `view.parameter-context`

Run: `mammoth view parameter-context`. Exact input fields: `mammoth schema get view.parameter-context --output json --no-input`.

Example: `mammoth view parameter-context 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewParameterContextResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 exact-parent retained view 46/dataset 29 parameter-context read succeeded with empty bindings. One view only; not Full.

### `view.pipeline.edit`

Run: `mammoth view pipeline edit`. Exact input fields: `mammoth schema get view.pipeline.edit --output json --no-input`.

Example: `mammoth view pipeline edit 123 --input '{"patches": [{"op": "replace", "path": "auto_run", "value": true}]}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPipelineEditResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: documented runnable_example (path auto_run, bool value) ran cleanly and returned the pipeline state object: {"auto_run":true,"draft_mode":"off","execution_state":"idle","state":"ready"}.…

### `view.pipeline.get`

Run: `mammoth view pipeline get`. Exact input fields: `mammoth schema get view.pipeline.get --output json --no-input`.

Example: `mammoth view pipeline get 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPipelineGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19: exit 0 on release with CLI 2.0.18. Single invocation only.

### `view.pipeline.items`

Run: `mammoth view pipeline items`. Exact input fields: `mammoth schema get view.pipeline.items --output json --no-input`.

Example: `mammoth view pipeline items 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPipelineItemsResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 pipeline-items read on retained view46/dataset29 returned one bounded item; prior owned-view evidence is retained and no Full claim is made.

### `view.pipeline.items-all`

Run: `mammoth view pipeline items-all`. Exact input fields: `mammoth schema get view.pipeline.items-all --output json --no-input`.

Example: `mammoth view pipeline items-all 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPipelineItemsAllResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `view.pipeline.rerun`

Run: `mammoth view pipeline rerun`. Exact input fields: `mammoth schema get view.pipeline.rerun --output json --no-input`.

Example: `mammoth view pipeline rerun 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPipelineRerunResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Empty result on this fixture. Attempt 1 with only dataset_id (from_sequence omitted, marked optional in schema) -> HTTP 400 4GENR007 extra=[{key:data,message:(quote)data(quote)}] (CLI sends an empty P…

### `view.pipeline.wait`

Run: `mammoth view pipeline wait`. Exact input fields: `mammoth schema get view.pipeline.wait --output json --no-input`.

Example: `mammoth view pipeline wait 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPipelineWaitResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.preview`

Run: `mammoth view preview`. Exact input fields: `mammoth schema get view.preview --output json --no-input`.

Example: `mammoth view preview 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPreviewResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19: exit 0 on release with CLI 2.0.18. Single invocation only.

### `view.restore`

Run: `mammoth view restore`. Exact input fields: `mammoth schema get view.restore --output json --no-input`.

Example: `mammoth view restore 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewRestoreResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. job 349 restore_dataview -> status success (view 72 restored after view.trash). Single invocation only.

### `view.task.add`

Run: `mammoth view task add`. Exact input fields: `mammoth schema get view.task.add --output json --no-input`.

Example: `mammoth view task add 123 --input '{"task_spec": {"DATAVIEW_ID": 123, "SEQUENCE_NUMBER": 1, "COPY": [{"SOURCE": "column_1", "AS": {"COLUMN": "Copy of column 1", "TYPE": "TEXT", "INTERNAL_NAME": "column_9"}}], "VERSION": 2}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTaskAddResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 — golden-data check golden-20260919 (CLI 2.0.18): typed transforms bulk-replace, convert-type, discard-duplicates, filter, join, pivot, set-values, text each run once on an owned fixture on release and read back with view data get against a known answer (values…

### `view.task.delete`

Run: `mammoth view task delete`. Exact input fields: `mammoth schema get view.task.delete --output json --no-input`.

Example: `mammoth view task delete 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewTaskDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Task 24 (created via view transform convert-type) deleted -> {future_id:347,status:processing,type_of_modification:discard_rule}. Verified via view task list 73: tasks:[] afterward. Single invocation…

### `view.task.get`

Run: `mammoth view task get`. Exact input fields: `mammoth schema get view.task.get --output json --no-input`.

Example: `mammoth view task get 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTaskGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI an earlier release — Published PyPI CLI 1.1.11 task get for observed task3 on retained view46/dataset29 succeeded; one retained task does not establish Full support.

### `view.task.list`

Run: `mammoth view task list`. Exact input fields: `mammoth schema get view.task.list --output json --no-input`.

Example: `mammoth view task list 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTaskListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19: exit 0 on release with CLI 2.0.18. Single invocation only.

### `view.task.preview`

Run: `mammoth view task preview`. Exact input fields: `mammoth schema get view.task.preview --output json --no-input`.

Example: `mammoth view task preview 123 --input '{"task_spec": {"DATAVIEW_ID": 123, "SEQUENCE_NUMBER": 1, "COPY": [{"SOURCE": "column_1", "AS": {"COLUMN": "Copy of column 1", "TYPE": "TEXT", "INTERNAL_NAME": "column_9"}}], "VERSION": 2}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTaskPreviewResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Previewed a COPY task using the documented agent_example shape; metadata correctly shows the new column_9. Minor note: data:[] came back empty despite the source view having 3 rows - previ…

### `view.task.update`

Run: `mammoth view task update`. Exact input fields: `mammoth schema get view.task.update --output json --no-input`.

Example: `mammoth view task update 123 123 --input '{"task_spec": {"DATAVIEW_ID": 123, "SEQUENCE_NUMBER": 1, "COPY": [{"SOURCE": "column_1", "AS": {"COLUMN": "Copy of column 1", "TYPE": "TEXT", "INTERNAL_NAME": "column_9"}}], "VERSION": 2}, "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTaskUpdateResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: {"patches":[{"op":"replace","path":"params","value":task_spec}]} shape accepted; response: {"data":{"future_id":365,"has_error":false,"status":"processing","type_of_modification":"edit_r…

### `view.transform.add-column`

Run: `mammoth view transform add-column`. Exact input fields: `mammoth schema get view.transform.add-column --output json --no-input`.

Example: `mammoth view transform add-column 123 --input '{"name": "Revenue report", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformAddColumnResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.add-sql`

Run: `mammoth view transform add-sql`. Exact input fields: `mammoth schema get view.transform.add-sql --output json --no-input`.

Example: `mammoth view transform add-sql 123 --input '{"query": "SELECT region, SUM(revenue) AS revenue FROM \"view:123\" GROUP BY region", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformAddSqlResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.ai`

Run: `mammoth view transform ai`. Exact input fields: `mammoth schema get view.transform.ai --output json --no-input`.

Example: `mammoth view transform ai 123 --input '{"prompt": "Summarize revenue by region", "context_columns": ["Status"], "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformAiResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.bulk-replace`

Run: `mammoth view transform bulk-replace`. Exact input fields: `mammoth schema get view.transform.bulk-replace --output json --no-input`.

Example: `mammoth view transform bulk-replace 123 --input '{"columns": ["Status"], "mapping": [{"search": ["sample"], "replace": "sample"}], "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformBulkReplaceResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.combine-columns`

Run: `mammoth view transform combine-columns`. Exact input fields: `mammoth schema get view.transform.combine-columns --output json --no-input`.

Example: `mammoth view transform combine-columns 123 --input '{"sources": ["Status"], "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformCombineColumnsResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.convert-type`

Run: `mammoth view transform convert-type`. Exact input fields: `mammoth schema get view.transform.convert-type --output json --no-input`.

Example: `mammoth view transform convert-type 123 --input '{"conversions": [{"column": "Status", "to": "TEXT"}], "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformConvertTypeResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.copy-columns`

Run: `mammoth view transform copy-columns`. Exact input fields: `mammoth schema get view.transform.copy-columns --output json --no-input`.

Example: `mammoth view transform copy-columns 123 --input '{"copies": [{"source": "Status"}], "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformCopyColumnsResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.crosstab`

Run: `mammoth view transform crosstab`. Exact input fields: `mammoth schema get view.transform.crosstab --output json --no-input`.

Example: `mammoth view transform crosstab 123 --input '{"rows": ["sample"], "pivot_column": "Status", "select": {"function": "SUM"}, "dataset_name": "Revenue report", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformCrosstabResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.date-diff`

Run: `mammoth view transform date-diff`. Exact input fields: `mammoth schema get view.transform.date-diff --output json --no-input`.

Example: `mammoth view transform date-diff 123 --input '{"component": "YEAR", "start": "sample", "end": "sample", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformDateDiffResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.delete-columns`

Run: `mammoth view transform delete-columns`. Exact input fields: `mammoth schema get view.transform.delete-columns --output json --no-input`.

Example: `mammoth view transform delete-columns 123 --input '{"columns": ["Status"], "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformDeleteColumnsResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.discard-duplicates`

Run: `mammoth view transform discard-duplicates`. Exact input fields: `mammoth schema get view.transform.discard-duplicates --output json --no-input`.

Example: `mammoth view transform discard-duplicates 123 --input '{"dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformDiscardDuplicatesResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.extract-date`

Run: `mammoth view transform extract-date`. Exact input fields: `mammoth schema get view.transform.extract-date --output json --no-input`.

Example: `mammoth view transform extract-date 123 --input '{"column": "Status", "component": "year", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformExtractDateResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.fill-missing`

Run: `mammoth view transform fill-missing`. Exact input fields: `mammoth schema get view.transform.fill-missing --output json --no-input`.

Example: `mammoth view transform fill-missing 123 --input '{"column": "Status", "direction": "FIRST_VALUE", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformFillMissingResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.filter`

Run: `mammoth view transform filter`. Exact input fields: `mammoth schema get view.transform.filter --output json --no-input`.

Example: `mammoth view transform filter 123 --input '{"condition": {"column": "Status", "operator": "EQ", "value": "Active"}, "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformFilterResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.generate-sql`

Run: `mammoth view transform generate-sql`. Exact input fields: `mammoth schema get view.transform.generate-sql --output json --no-input`.

Example: `mammoth view transform generate-sql 123 --input '{"intent": "Summarize revenue by region", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformGenerateSqlResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.increment-date`

Run: `mammoth view transform increment-date`. Exact input fields: `mammoth schema get view.transform.increment-date --output json --no-input`.

Example: `mammoth view transform increment-date 123 --input '{"column": "Status", "delta": {}, "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformIncrementDateResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.join`

Run: `mammoth view transform join`. Exact input fields: `mammoth schema get view.transform.join --output json --no-input`.

Example: `mammoth view transform join 123 --input '{"foreign_view": 1, "join_type": "INNER", "on": [{"left": "sample", "right": "sample"}], "select": ["sample"], "dataset_id": 456, "foreign_dataset_id": 457}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformJoinResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.json-extract`

Run: `mammoth view transform json-extract`. Exact input fields: `mammoth schema get view.transform.json-extract --output json --no-input`.

Example: `mammoth view transform json-extract 123 --input '{"column": "Status", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformJsonExtractResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.limit-rows`

Run: `mammoth view transform limit-rows`. Exact input fields: `mammoth schema get view.transform.limit-rows --output json --no-input`.

Example: `mammoth view transform limit-rows 123 --input '{"n": 1, "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformLimitRowsResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.lookup`

Run: `mammoth view transform lookup`. Exact input fields: `mammoth schema get view.transform.lookup --output json --no-input`.

Example: `mammoth view transform lookup 123 --input '{"source": "Status", "lookup_view_id": 1, "key": "Status", "value": "sample", "dataset_id": 456, "lookup_dataset_id": 457}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformLookupResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.math`

Run: `mammoth view transform math`. Exact input fields: `mammoth schema get view.transform.math --output json --no-input`.

Example: `mammoth view transform math 123 --input '{"expression": "price * quantity", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformMathResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.pivot`

Run: `mammoth view transform pivot`. Exact input fields: `mammoth schema get view.transform.pivot --output json --no-input`.

Example: `mammoth view transform pivot 123 --input '{"group_by": ["sample"], "aggregations": [{"column": "Status", "function": "SUM"}], "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformPivotResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.replace`

Run: `mammoth view transform replace`. Exact input fields: `mammoth schema get view.transform.replace --output json --no-input`.

Example: `mammoth view transform replace 123 --input '{"columns": ["Status"], "find": "sample", "replace": "sample", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformReplaceResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.set-values`

Run: `mammoth view transform set-values`. Exact input fields: `mammoth schema get view.transform.set-values --output json --no-input`.

Example: `mammoth view transform set-values 123 --input '{"values": [{"value": "sample"}], "existing_column": "Status", "condition": {"column": "Status", "operator": "IS_EMPTY"}, "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformSetValuesResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.small-large`

Run: `mammoth view transform small-large`. Exact input fields: `mammoth schema get view.transform.small-large --output json --no-input`.

Example: `mammoth view transform small-large 123 --input '{"function": "SMALL", "columns": ["Status"], "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformSmallLargeResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.split`

Run: `mammoth view transform split`. Exact input fields: `mammoth schema get view.transform.split --output json --no-input`.

Example: `mammoth view transform split 123 --input '{"column": "Status", "delimiter": "sample", "new_columns": [{"name": "Revenue report"}], "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformSplitResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.substring`

Run: `mammoth view transform substring`. Exact input fields: `mammoth schema get view.transform.substring --output json --no-input`.

Example: `mammoth view transform substring 123 --input '{"column": "Status", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformSubstringResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.text`

Run: `mammoth view transform text`. Exact input fields: `mammoth schema get view.transform.text --output json --no-input`.

Example: `mammoth view transform text 123 --input '{"columns": ["Status"], "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformTextResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.unnest`

Run: `mammoth view transform unnest`. Exact input fields: `mammoth schema get view.transform.unnest --output json --no-input`.

Example: `mammoth view transform unnest 123 --input '{"columns": ["Status"], "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformUnnestResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.transform.window`

Run: `mammoth view transform window`. Exact input fields: `mammoth schema get view.transform.window --output json --no-input`.

Example: `mammoth view transform window 123 --input '{"function": "ROW_NUMBER", "dataset_id": 456}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformWindowResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; it submits through `view.task.add`, but this transform was not among those run.

### `view.trash`

Run: `mammoth view trash`. Exact input fields: `mammoth schema get view.trash --output json --no-input`.

Example: `mammoth view trash 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTrashResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. job 348 trash_dataview -> status success. Single invocation only.

### `view.update`

Run: `mammoth view update`. Exact input fields: `mammoth schema get view.update --output json --no-input`.

Example: `mammoth schema get view.update --output json --no-input`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B09 DATAVIEW_INPUT_UNTYPED]: patch_data is an arbitrary dictionary; reserved, not registered.

### `view.version.apply`

Run: `mammoth view version apply`. Exact input fields: `mammoth schema get view.version.apply --output json --no-input`.

Example: `mammoth view version apply 123 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewVersionApplyResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. job 351 apply_pipeline_version -> status success (reapplied the 'add_rule' version that had the convert-type task, restoring task 24's state on view 73). Single invocation only.

### `view.version.delete`

Run: `mammoth view version delete`. Exact input fields: `mammoth schema get view.version.delete --output json --no-input`.

Example: `mammoth view version delete 123 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewVersionDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Empty result on this fixture. Deleted pipeline version 41 -> data:{}. Single invocation only.

### `view.version.get`

Run: `mammoth view version get`. Exact input fields: `mammoth schema get view.version.get --output json --no-input`.

Example: `mammoth view version get 123 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewVersionGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.5 — retained view 46 / parent dataset 29 returned pipeline version 3 with structured metadata. One observed version and resource scope; no Full claim.

### `view.version.list`

Run: `mammoth view version list`. Exact input fields: `mammoth schema get view.version.list --output json --no-input`.

Example: `mammoth view version list 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewVersionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 exact-parent retained view 46/dataset 29 version-list read succeeded with 11 versions on its single-page boundary. One view; not Full.

### `view.version.update`

Run: `mammoth view version update`. Exact input fields: `mammoth schema get view.version.update --output json --no-input`.

Example: `mammoth view version update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "name"}]}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewVersionUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Empty result on this fixture. Renamed pipeline version 41 -> data:{} (empty success envelope). Single invocation only.
