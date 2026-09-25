# `view` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `view.active-user.list`

Run: `mammoth view active-user list`. Exact input fields: `mammoth schema get view.active-user.list`.

Example: `mammoth view active-user list 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewActiveUserListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 exact-parent retained view 46/dataset 29 read succeeded with an empty active-user list. One view and single-page boundary; not Full.

### `view.active-user.mark`

Run: `mammoth view active-user mark`. Exact input fields: `mammoth schema get view.active-user.mark`.

Example: `mammoth view active-user mark 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewActiveUserMarkResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Returned active_users:[{id:5,email:<api user>,...}] confirming our session is now marked active on view 68. Single invocation only.

### `view.ai.generate-data`

Run: `mammoth view ai generate-data`. Exact input fields: `mammoth schema get view.ai.generate-data`.

Example: `mammoth view ai generate-data 123 --input '{"prompt": "Summarize revenue by region"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewAiGenerateDataResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Returned {context_columns:[column_1..4],data:[3 generated row strings],provider:open_ai}. Single invocation only.

### `view.ai.generation-info`

Run: `mammoth view ai generation-info`. Exact input fields: `mammoth schema get view.ai.generation-info`.

Example: `mammoth view ai generation-info 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewAiGenerationInfoResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend: GET /workspaces/4/projects/24/datasets/54/dataviews/76/data/generate -> HTTP 400 5GENR011 NOT_IMPLEMENTED 'Not implemented', request_id:null. Re-check before relying on it.

### `view.ai.profile`

Run: `mammoth view ai profile`. Exact input fields: `mammoth schema get view.ai.profile`.

Example: `mammoth view ai profile 123 --input '{"dataset_id": 456, "action": "insights"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewAiProfileResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: release ProfileGenerationSpec {params:{action}} body accepted; returned real generated insights: {"data":{"insights":{"performance_analysis":{"domain_specific_insights":[...]}}}}. Single…

### `view.bulk-delete`

Run: `mammoth view bulk-delete`. Exact input fields: `mammoth schema get view.bulk-delete`.

Example: `mammoth view bulk-delete 123 --input '{"dataview_ids": [1]}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewBulkDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Created throwaway view 74 (sweep-view-bulkdel) via view create, then bulk-deleted it. Without --yes: confirmation_required. With --yes: job 332 safe_delete_dataviews -> status success. Single invocati…

### `view.checkpoint.create`

Run: `mammoth view checkpoint create`. Exact input fields: `mammoth schema get view.checkpoint.create`.

Example: `mammoth view checkpoint create 123 123 --input '{"body": {"checkpoint_name": "Revenue report", "checkpoint_type": "alert", "pinned_to_end": true}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewCheckpointCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. First attempt without pinned_to_end/task_sequence failed 4GENR007 (schema's own example omits the requirement, doc mismatch). Retried with pinned_to_end:true, created checkpoint id=4. Sing…

### `view.checkpoint.delete`

Run: `mammoth view checkpoint delete`. Exact input fields: `mammoth schema get view.checkpoint.delete`.

Example: `mammoth view checkpoint delete 123 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewCheckpointDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted checkpoint 4 (202 accepted); read-back list is empty. Single invocation only.

### `view.checkpoint.get`

Run: `mammoth view checkpoint get`. Exact input fields: `mammoth schema get view.checkpoint.get`.

Example: `mammoth view checkpoint get 123 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewCheckpointGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Fetched checkpoint 4, matches create. Single invocation only.

### `view.checkpoint.list`

Run: `mammoth view checkpoint list`. Exact input fields: `mammoth schema get view.checkpoint.list`.

Example: `mammoth view checkpoint list 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewCheckpointListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Listed checkpoints, showed id=4. Single invocation only.

### `view.checkpoint.update`

Run: `mammoth view checkpoint update`. Exact input fields: `mammoth schema get view.checkpoint.update`.

Example: `mammoth view checkpoint update 123 123 123 --input '{"body": {"patches": [{"op": "command", "path": "approve", "value": null}]}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewCheckpointUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. First attempt sending a full AddCheckpointSpec body (matching create's shape) failed with invalid_input_field_type; update actually needs body.patches[] (CheckpointPatches/CheckPointPatch…

### `view.conditional-format.create`

Run: `mammoth view conditional-format create`. Exact input fields: `mammoth schema get view.conditional-format.create`.

Example: `mammoth view conditional-format create 123 123 --input '{"rule": {"cf_type": "RULE", "payload": {"FORMAT": {"name": "Flag open orders", "color": "red", "applies_to": "row", "column_ids": "[]"}, "CONDITION": {"OR": [{"column_1": {"CONTAINS": {"VALUE": ["Open"]}}}]}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewConditionalFormatCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.17 — re-verification 2026-09-18 (2.0.16 fixes): exit 0 on release with CLI 2.0.17. HighlightEntry body accepted; response is {rule_id: rule} with COLUMNS_USED resolved. The former generated example ({"rule": {"sample_key": ...}}) was a placeholder; the example hin…

### `view.conditional-format.delete-all`

Run: `mammoth view conditional-format delete-all`. Exact input fields: `mammoth schema get view.conditional-format.delete-all`.

Example: `mammoth view conditional-format delete-all 123 123 --input '{"rule_id": "bca0ff33bd6f8ed1"}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewConditionalFormatDeleteAllResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.17 — re-verification 2026-09-18 (2.0.16 fixes): exit 0 on release with CLI 2.0.17. Fix held: rule_id forwarded; rule created via `view conditional-format create` (HighlightEntry body) was deleted and `conditional-format list` returned [] afterwards. Note: `conditi…

### `view.conditional-format.list`

Run: `mammoth view conditional-format list`. Exact input fields: `mammoth schema get view.conditional-format.list`.

Example: `mammoth view conditional-format list 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewConditionalFormatListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.17 — re-verification 2026-09-18 (2.0.16 fixes): exit 0 on release with CLI 2.0.17. With SDK 0.7.9 the one existing rule is returned as [{rule_id, cf_type, FORMAT, CONDITION, ...}]; with SDK 0.7.8 the same call returned [] (mapping keyed by rule id was discarded).…

### `view.conditional-format.update`

Run: `mammoth view conditional-format update`. Exact input fields: `mammoth schema get view.conditional-format.update`.

Example: `mammoth view conditional-format update 123 123 --input '{"rule": {"sample_key": "Status"}}'`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B09 DATAVIEW_INPUT_UNTYPED]; reserved, not registered.

### `view.create`

Run: `mammoth view create`. Exact input fields: `mammoth schema get view.create`.

Example: `mammoth view create 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19 (CLI 2.0.18): plain create on an owned dataset returned the new view's record (id, dataset_id; earlier releases printed '<unserializable View>'), and discard-duplicates then ran on it. clone_from is not usable on release: the clon…

### `view.data-check.create`

Run: `mammoth view data-check create`. Exact input fields: `mammoth schema get view.data-check.create`.

Example: `mammoth view data-check create 123 123 --input '{"body": {"checks": [{"check_type": "null_percentage", "config": {"column": "Status", "condition": "lt"}}], "name": "Revenue report", "pinned_to_end": true}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDataCheckCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.21 — ergonomics sweep 2026-09-19: exit 0 on release with CLI 2.0.21. Created data_check_id 5. Without pinned_to_end the backend rejects the body with 4GENR007 'Either task_sequence or pinned_to_end must be set' (the shipped example lacked it; corrected in 2.0.22).…

### `view.data-check.delete`

Run: `mammoth view data-check delete`. Exact input fields: `mammoth schema get view.data-check.delete`.

Example: `mammoth view data-check delete 123 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewDataCheckDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted data check 4 (202); read-back get now returns 404 NON_EXISTENT_RESOURCE, confirming deletion. Single invocation only.

### `view.data-check.get`

Run: `mammoth view data-check get`. Exact input fields: `mammoth schema get view.data-check.get`.

Example: `mammoth view data-check get 123 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDataCheckGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.21 — ergonomics sweep 2026-09-19: exit 0 on release with CLI 2.0.21. Read back after each patch: enabled true, then false. Single invocation only.

### `view.data-check.list`

Run: `mammoth view data-check list`. Exact input fields: `mammoth schema get view.data-check.list`.

Example: `mammoth view data-check list 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDataCheckListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.21 — ergonomics sweep 2026-09-19: exit 0 on release with CLI 2.0.21. Listed data check 5 (enabled true, pinned_to_end true). Single invocation only.

### `view.data-check.update`

Run: `mammoth view data-check update`. Exact input fields: `mammoth schema get view.data-check.update`.

Example: `mammoth view data-check update 123 123 123 --input '{"body": {"patches": [{"op": "command", "path": "disable", "value": null}]}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDataCheckUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend_error: PATCH with the schema's documented {op: command, path: enable|disable, value: null} shape returns HTTP 500 empty body (CLI outcome_unknown, exit 7) while the mutatio. Re-check before relying on it.

### `view.data.get`

Run: `mammoth view data get`. Exact input fields: `mammoth schema get view.data.get`.

Example: `mammoth view data get 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDataGetResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.28 — ILG simulation 2026-09-19: exit 0 on release with CLI 2.0.28. Paged reads (limit up to 500) used for every value check; envelope data.data rows keyed by display name. Single invocation only.

### `view.data.query`

Run: `mammoth view data query`. Exact input fields: `mammoth schema get view.data.query`.

Example: `mammoth view data query 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDataQueryResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19 (CLI 2.0.18): condition on the pivoted view compiled to the backend clause shape and answered (exit 0); EQ with a column select and an AND of CONTAINS/NE also verified read-only on a pre-existing view. Before 2.0.18 the spec was f…

### `view.delete`

Run: `mammoth view delete`. Exact input fields: `mammoth schema get view.delete`.

Example: `mammoth view delete 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19: exit 0 on release with CLI 2.0.18. Single invocation only.

### `view.derivative.create`

Run: `mammoth view derivative create`. Exact input fields: `mammoth schema get view.derivative.create`.

Example: `mammoth view derivative create 123 123 --input '{"body": {"param": {"METRIC": {"AS": "total", "EXPRESSION": [{"TYPE": "FUNCTION", "VALUE": {"ARGUMENT": "column_1", "FUNCTION": "SUM"}}]}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDerivativeCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.24 — payload probe 2026-09-19: exit 0 on release with CLI 2.0.24. Created derivative id=6 on view 123 (project 52, dataset 104) with the column INTERNAL name as ARGUMENT; metric_status DONE on read-back. The same call with the display name reproduces the HTTP 500…

### `view.derivative.data`

Run: `mammoth view derivative data`. Exact input fields: `mammoth schema get view.derivative.data`.

Example: `mammoth view derivative data 123 123 123 --input '{"body": {"limit": null}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDerivativeDataResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.24 — payload probe 2026-09-19: exit 0 on release with CLI 2.0.24. STATUS READY, data [{RESULT: 60.0}], metadata total/RESULT/NUMERIC, row_count 1. {"condition": null, "limit": null} (the web app's body) also works; {} is 4GENR007. Example corrected in 2.0.25. Sing…

### `view.derivative.delete`

Run: `mammoth view derivative delete`. Exact input fields: `mammoth schema get view.derivative.delete`.

Example: `mammoth view derivative delete 123 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewDerivativeDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted derivative 5 (202 accepted). Single invocation only.

### `view.derivative.list`

Run: `mammoth view derivative list`. Exact input fields: `mammoth schema get view.derivative.list`.

Example: `mammoth view derivative list 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDerivativeListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 exact-parent retained view 46/dataset 29 read succeeded with an empty derivatives list. One view and single-page boundary; not Full.

### `view.derivative.update`

Run: `mammoth view derivative update`. Exact input fields: `mammoth schema get view.derivative.update`.

Example: `mammoth view derivative update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "param", "value": {"METRIC": {"AS": "sample", "EXPRESSION": [{"TYPE": "FUNCTION", "VALUE": {"ARGUMENT": "sample", "FUNCTION": "SUM"}}]}}}]}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDerivativeUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: 202 Accepted non-object body reported as success. Response: {"data":{"response":null,"status_code":202}}. Single invocation only.

### `view.draft.auto-run`

Run: `mammoth view draft auto-run`. Exact input fields: `mammoth schema get view.draft.auto-run`.

Example: `mammoth view draft auto-run 123 --input '{"enabled": true, "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDraftAutoRunResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.draft.command`

Run: `mammoth view draft command`. Exact input fields: `mammoth schema get view.draft.command`.

Example: `mammoth view draft command 123 --input '{"command": "sample", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDraftCommandResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. command:enter -> {draft_mode:clean}. command:discard without --confirm -> confirmation_target_mismatch exit 2 (correct guardrail). With --yes --confirm 73 -> {draft_mode:clean} again, view 73 left in…

### `view.draft.discard`

Run: `mammoth view draft discard`. Exact input fields: `mammoth schema get view.draft.discard`.

Example: `mammoth view draft discard 123 --input '{"dataset_id": 456}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewDraftDiscardResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.draft.enter`

Run: `mammoth view draft enter`. Exact input fields: `mammoth schema get view.draft.enter`.

Example: `mammoth view draft enter 123 --input '{"dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDraftEnterResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.draft.status`

Run: `mammoth view draft status`. Exact input fields: `mammoth schema get view.draft.status`.

Example: `mammoth view draft status 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDraftStatusResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `view.draft.submit`

Run: `mammoth view draft submit`. Exact input fields: `mammoth schema get view.draft.submit`.

Example: `mammoth view draft submit 123 --input '{"dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewDraftSubmitResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.export.azure-blob`

Run: `mammoth view export azure-blob`. Exact input fields: `mammoth schema get view.export.azure-blob`.

Example: `mammoth view export azure-blob 123 123 --input /private/path/request.json`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportAzureBlobResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.bigquery`

Run: `mammoth view export bigquery`. Exact input fields: `mammoth schema get view.export.bigquery`.

Example: `mammoth view export bigquery 123 123 --input '{"selected_profile": {}, "selected_identity": {}, "table": "exports"}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportBigqueryResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.create`

Run: `mammoth view export create`. Exact input fields: `mammoth schema get view.export.create`.

Example: `mammoth view export create 123 --input '{"export_spec": {"DATAVIEW_ID": 1, "handler_type": "postgres", "trigger_type": "none", "target_properties": {"file": "./sales.csv", "file_type": "./sales.csv", "include_hidden": true, "is_format_set": true, "use_format": true}, "additional_properties": {}, "run_immediately": true}}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportCreateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: ran once on CLI 2.0.27 — cross-project send 2026-09-19: exit 0 on release with CLI 2.0.27. Raw internal_dataset export accepted (job 831 add_action) and created dataset 113 in project 57. Without USER_ID the same spec is 4GENR007 Validation error with no detail (the backend checks th…

### `view.export.csv`

Run: `mammoth view export csv`. Exact input fields: `mammoth schema get view.export.csv`.

Example: `mammoth view export csv 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewExportCsvResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.export.dataset`

Run: `mammoth view export dataset`. Exact input fields: `mammoth schema get view.export.dataset`.

Example: `mammoth view export dataset 123 123 --input '{"dataset_name": "snapshot"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewExportDatasetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.export.delete`

Run: `mammoth view export delete`. Exact input fields: `mammoth schema get view.export.delete`.

Example: `mammoth view export delete 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportDeleteResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Deleted export 2 -> {future_id:null,status:deleted,trigger_id:2}. Single invocation only.

### `view.export.elasticsearch`

Run: `mammoth view export elasticsearch`. Exact input fields: `mammoth schema get view.export.elasticsearch`.

Example: `mammoth view export elasticsearch 123 123 --input /private/path/request.json`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportElasticsearchResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.email`

Run: `mammoth view export email`. Exact input fields: `mammoth schema get view.export.email`.

Example: `mammoth view export email 123 123 --input '{"emails": ["recipient@example.com"]}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportEmailResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.ftp`

Run: `mammoth view export ftp`. Exact input fields: `mammoth schema get view.export.ftp`.

Example: `mammoth view export ftp 123 123 --input /private/path/request.json`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportFtpResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.get`

Run: `mammoth view export get`. Exact input fields: `mammoth schema get view.export.get`.

Example: `mammoth view export get 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewExportGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. export id 2 was created as a fixture via view.export.create using the schema's own postgres runnable_example (run_immediately:false) since the csv_file variant errors (see view.export.create). Returne…

### `view.export.list`

Run: `mammoth view export list`. Exact input fields: `mammoth schema get view.export.list`.

Example: `mammoth view export list 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewExportListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.28 — ILG simulation 2026-09-19: exit 0 on release with CLI 2.0.28. Listed both internal_dataset exports with target_properties (DS_NAME, COLUMN_MAPPING, project fields). Single invocation only.

### `view.export.managed-s3`

Run: `mammoth view export managed-s3`. Exact input fields: `mammoth schema get view.export.managed-s3`.

Example: `mammoth view export managed-s3 123 123 --input '{"file_name": "report.csv"}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportManagedS3Result`; mutation `external_effect`, confirmation `yes_always`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.export.mssql`

Run: `mammoth view export mssql`. Exact input fields: `mammoth schema get view.export.mssql`.

Example: `mammoth view export mssql 123 123 --input /private/path/request.json`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportMssqlResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.mysql`

Run: `mammoth view export mysql`. Exact input fields: `mammoth schema get view.export.mysql`.

Example: `mammoth view export mysql 123 123 --input /private/path/request.json`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportMysqlResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.onedrive`

Run: `mammoth view export onedrive`. Exact input fields: `mammoth schema get view.export.onedrive`.

Example: `mammoth view export onedrive 123 123 --input /private/path/request.json`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportOnedriveResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.postgres`

Run: `mammoth view export postgres`. Exact input fields: `mammoth schema get view.export.postgres`.

Example: `mammoth view export postgres 123 123 --input /private/path/request.json`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportPostgresResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.powerbi`

Run: `mammoth view export powerbi`. Exact input fields: `mammoth schema get view.export.powerbi`.

Example: `mammoth view export powerbi 123 123 --input /private/path/request.json`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportPowerbiResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.publish-db`

Run: `mammoth view export publish-db`. Exact input fields: `mammoth schema get view.export.publish-db`.

Example: `mammoth view export publish-db 123 --input '{"odbc_type": "postgres", "target_properties": {"sample_key": "Status"}}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportPublishDbResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Attempt 1 target_properties:{} -> HTTP 400 4GENR007 extra=[{key:target_properties.table,message:"Field required"}] (clear). Attempt 2 target_properties:{table:sweep_stores} -> {job_id:339}; job get co…

### `view.export.publish-db-update`

Run: `mammoth view export publish-db-update`. Exact input fields: `mammoth schema get view.export.publish-db-update`.

Example: `mammoth view export publish-db-update 123 --input '{"patch": [{"op": "replace", "path": "credentials", "value": {"odbc_type": "postgres"}}]}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportPublishDbUpdateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: CLI defect fixed, untried since — CLI defect fixed in 2.0.16 (example value is the documented {"odbc_type": "postgres"} object (a bare string is rejected)); not re-verified live yet. re-verification 2026-09-18 (2.0.16 fixes) observed not_rerun: Not re-run: needs a live publish-to-database exp…

### `view.export.redshift`

Run: `mammoth view export redshift`. Exact input fields: `mammoth schema get view.export.redshift`.

Example: `mammoth view export redshift 123 123 --input /private/path/request.json`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportRedshiftResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.rest`

Run: `mammoth view export rest`. Exact input fields: `mammoth schema get view.export.rest`.

Example: `mammoth view export rest 123 123 --input '{"base_url": "https://api.example", "endpoint_path": "/records"}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportRestResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.sftp`

Run: `mammoth view export sftp`. Exact input fields: `mammoth schema get view.export.sftp`.

Example: `mammoth view export sftp 123 123 --input '{"host": "sftp.example", "username": "agent"}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportSftpResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.sharepoint`

Run: `mammoth view export sharepoint`. Exact input fields: `mammoth schema get view.export.sharepoint`.

Example: `mammoth view export sharepoint 123 123 --input /private/path/request.json`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportSharepointResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.tableau`

Run: `mammoth view export tableau`. Exact input fields: `mammoth schema get view.export.tableau`.

Example: `mammoth view export tableau 123 123 --input /private/path/request.json`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ViewExportTableauResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `view.export.update`

Run: `mammoth view export update`. Exact input fields: `mammoth schema get view.export.update`.

Example: `mammoth view export update 123 123 --input '{"patches": [{"sample_key": "Status"}]}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewExportUpdateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Attempt 1 path:target_properties -> HTTP 400 4GENR007, clear message: path must be one of run/suspend/restore/discard/params, and value must be the FULL export spec (DATAVIEW_ID,handler_type,trigger_t…

### `view.exportable-config.apply`

Run: `mammoth view exportable-config apply`. Exact input fields: `mammoth schema get view.exportable-config.apply`.

Example: `mammoth view exportable-config apply 123 --input-format json --input '{"config": {"tasks": []}}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ViewExportableConfigApplyResult`; mutation `reversible_pipeline`, confirmation `confirm_target`, wait policy `returns_job`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Re-applied the view's own exportable config verbatim (idempotent no-op); returned dataview_id=106. Single invocation only.

### `view.exportable-config.get`

Run: `mammoth view exportable-config get`. Exact input fields: `mammoth schema get view.exportable-config.get`.

Example: `mammoth view exportable-config get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewExportableConfigGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Fetched full exportable config for view 106 (metadata, display_properties, dependencies, empty tasks/checkpoints/derivatives/data_checks). Single invocation only.

### `view.get`

Run: `mammoth view get`. Exact input fields: `mammoth schema get view.get`.

Example: `mammoth view get 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.21 — ergonomics sweep 2026-09-19: exit 0 on release with CLI 2.0.21. Read back without a dataset id (parent from cache). row_count 6 after the append. Single invocation only.

### `view.list`

Run: `mammoth view list`. Exact input fields: `mammoth schema get view.list`.

Example: `mammoth view list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.21 — ergonomics sweep 2026-09-19: exit 0 on release with CLI 2.0.21. Listed dataview 116 (ds_id 94, row_count 3); the parent cache picked up 116 -> 94 so later view commands took the view id alone. Single invocation only.

### `view.parameter-context`

Run: `mammoth view parameter-context`. Exact input fields: `mammoth schema get view.parameter-context`.

Example: `mammoth view parameter-context 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewParameterContextResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 exact-parent retained view 46/dataset 29 parameter-context read succeeded with empty bindings. One view only; not Full.

### `view.pipeline.edit`

Run: `mammoth view pipeline edit`. Exact input fields: `mammoth schema get view.pipeline.edit`.

Example: `mammoth view pipeline edit 123 --input '{"patches": [{"op": "replace", "path": "auto_run", "value": true}]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPipelineEditResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: documented runnable_example (path auto_run, bool value) ran cleanly and returned the pipeline state object: {"auto_run":true,"draft_mode":"off","execution_state":"idle","state":"ready"}.…

### `view.pipeline.get`

Run: `mammoth view pipeline get`. Exact input fields: `mammoth schema get view.pipeline.get`.

Example: `mammoth view pipeline get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPipelineGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19: exit 0 on release with CLI 2.0.18. Single invocation only.

### `view.pipeline.items`

Run: `mammoth view pipeline items`. Exact input fields: `mammoth schema get view.pipeline.items`.

Example: `mammoth view pipeline items 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPipelineItemsResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.28 — ILG simulation 2026-09-19: exit 0 on release with CLI 2.0.28. fields=__full listed both export steps with sequence/status/execution times; the pre-existing step's timestamps did not move when a second send was appended. Single invocation only.

### `view.pipeline.items-all`

Run: `mammoth view pipeline items-all`. Exact input fields: `mammoth schema get view.pipeline.items-all`.

Example: `mammoth view pipeline items-all 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPipelineItemsAllResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `view.pipeline.rerun`

Run: `mammoth view pipeline rerun`. Exact input fields: `mammoth schema get view.pipeline.rerun`.

Example: `mammoth view pipeline rerun 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPipelineRerunResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Empty result on this fixture. Attempt 1 with only dataset_id (from_sequence omitted, marked optional in schema) -> HTTP 400 4GENR007 extra=[{key:data,message:(quote)data(quote)}] (CLI sends an empty P…

### `view.pipeline.wait`

Run: `mammoth view pipeline wait`. Exact input fields: `mammoth schema get view.pipeline.wait`.

Example: `mammoth view pipeline wait 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPipelineWaitResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `view.preview`

Run: `mammoth view preview`. Exact input fields: `mammoth schema get view.preview`.

Example: `mammoth view preview 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewPreviewResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19: exit 0 on release with CLI 2.0.18. Single invocation only.

### `view.restore`

Run: `mammoth view restore`. Exact input fields: `mammoth schema get view.restore`.

Example: `mammoth view restore 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewRestoreResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. job 349 restore_dataview -> status success (view 72 restored after view.trash). Single invocation only.

### `view.task.add`

Run: `mammoth view task add`. Exact input fields: `mammoth schema get view.task.add`.

Example: `mammoth view task add 123 --input '{"task_spec": {"DATAVIEW_ID": 123, "SEQUENCE_NUMBER": 1, "COPY": [{"SOURCE": "column_1", "AS": {"COLUMN": "Copy of column 1", "TYPE": "TEXT", "INTERNAL_NAME": "column_9"}}], "VERSION": 2}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTaskAddResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 — golden-data check golden-20260919 (CLI 2.0.18): typed transforms bulk-replace, convert-type, discard-duplicates, filter, join, pivot, set-values, text each run once on an owned fixture on release and read back with view data get against a known answer (values…

### `view.task.delete`

Run: `mammoth view task delete`. Exact input fields: `mammoth schema get view.task.delete`.

Example: `mammoth view task delete 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewTaskDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.28 — ILG simulation 2026-09-19: exit 0 on release with CLI 2.0.28. Removed a SQL task that had run on the wrong intermediate shape; view returned to the previous columns and row count. Single invocation only.

### `view.task.get`

Run: `mammoth view task get`. Exact input fields: `mammoth schema get view.task.get`.

Example: `mammoth view task get 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTaskGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI an earlier release — Published PyPI CLI 1.1.11 task get for observed task3 on retained view46/dataset29 succeeded; one retained task does not establish Full support.

### `view.task.list`

Run: `mammoth view task list`. Exact input fields: `mammoth schema get view.task.list`.

Example: `mammoth view task list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTaskListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19: exit 0 on release with CLI 2.0.18. Single invocation only.

### `view.task.preview`

Run: `mammoth view task preview`. Exact input fields: `mammoth schema get view.task.preview`.

Example: `mammoth view task preview 123 --input '{"task_spec": {"DATAVIEW_ID": 123, "SEQUENCE_NUMBER": 1, "COPY": [{"SOURCE": "column_1", "AS": {"COLUMN": "Copy of column 1", "TYPE": "TEXT", "INTERNAL_NAME": "column_9"}}], "VERSION": 2}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTaskPreviewResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Previewed a COPY task using the documented agent_example shape; metadata correctly shows the new column_9. Minor note: data:[] came back empty despite the source view having 3 rows - previ…

### `view.task.update`

Run: `mammoth view task update`. Exact input fields: `mammoth schema get view.task.update`.

Example: `mammoth view task update 123 123 --input '{"task_spec": {"DATAVIEW_ID": 123, "SEQUENCE_NUMBER": 1, "COPY": [{"SOURCE": "column_1", "AS": {"COLUMN": "Copy of column 1", "TYPE": "TEXT", "INTERNAL_NAME": "column_9"}}], "VERSION": 2}, "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTaskUpdateResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: {"patches":[{"op":"replace","path":"params","value":task_spec}]} shape accepted; response: {"data":{"future_id":365,"has_error":false,"status":"processing","type_of_modification":"edit_r…

### `view.trash`

Run: `mammoth view trash`. Exact input fields: `mammoth schema get view.trash`.

Example: `mammoth view trash 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTrashResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. job 348 trash_dataview -> status success. Single invocation only.

### `view.update`

Run: `mammoth view update`. Exact input fields: `mammoth schema get view.update`.

Example: `mammoth view update 123 123 --input '{"patch_data": [{"sample_key": "Status"}]}'`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B09 DATAVIEW_INPUT_UNTYPED]: patch_data is an arbitrary dictionary; reserved, not registered.

### `view.version.apply`

Run: `mammoth view version apply`. Exact input fields: `mammoth schema get view.version.apply`.

Example: `mammoth view version apply 123 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewVersionApplyResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. job 351 apply_pipeline_version -> status success (reapplied the 'add_rule' version that had the convert-type task, restoring task 24's state on view 73). Single invocation only.

### `view.version.delete`

Run: `mammoth view version delete`. Exact input fields: `mammoth schema get view.version.delete`.

Example: `mammoth view version delete 123 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `ViewVersionDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Empty result on this fixture. Deleted pipeline version 41 -> data:{}. Single invocation only.

### `view.version.get`

Run: `mammoth view version get`. Exact input fields: `mammoth schema get view.version.get`.

Example: `mammoth view version get 123 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewVersionGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.5 — retained view 46 / parent dataset 29 returned pipeline version 3 with structured metadata. One observed version and resource scope; no Full claim.

### `view.version.list`

Run: `mammoth view version list`. Exact input fields: `mammoth schema get view.version.list`.

Example: `mammoth view version list 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewVersionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 exact-parent retained view 46/dataset 29 version-list read succeeded with 11 versions on its single-page boundary. One view; not Full.

### `view.version.update`

Run: `mammoth view version update`. Exact input fields: `mammoth schema get view.version.update`.

Example: `mammoth view version update 123 123 123 --input '{"body": {"patches": [{"op": "replace", "path": "name"}]}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewVersionUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Empty result on this fixture. Renamed pipeline version 41 -> data:{} (empty success envelope). Single invocation only.
