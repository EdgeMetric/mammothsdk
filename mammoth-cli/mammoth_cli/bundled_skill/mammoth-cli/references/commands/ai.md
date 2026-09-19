# `ai` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `ai.condition.generate`

Run: `mammoth ai condition generate`. Exact input fields: `mammoth schema get ai.condition.generate`.

Example: `mammoth ai condition generate 123 --input '{"intent": "Summarize revenue by region"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AiConditionGenerateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Generated: lower("region") = 'east' (CD01). First attempt without dataview_id failed with job_failed/CD02 Dataview 4 not found (defaulted to wrong dataview) -- dataview_id must be passed explicitly. S…

### `ai.expression.generate`

Run: `mammoth ai expression generate`. Exact input fields: `mammoth schema get ai.expression.generate`.

Example: `mammoth ai expression generate 123 --input '{"intent": "Summarize revenue by region", "mode": "sample"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AiExpressionGenerateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 2 on release with CLI 2.0.15. Fix held: invalid mode surfaced as invalid_arguments with the SDK message before any request was sent: {"error":{"code":"invalid_arguments","message":"`mode` must be 'math' or 'metric', got 'sampl…

### `ai.retention.condition`

Run: `mammoth ai retention condition`. Exact input fields: `mammoth schema get ai.retention.condition`.

Example: `mammoth ai retention condition 123 --input '{"mode": "generate", "intent": "completed payments older than 90 days"}' --project 456`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AiRetentionConditionResult`; mutation `benign_mutation`, confirmation `none`, wait policy `start_or_wait`.

Status on release: observed blocker — permission: POST /workspaces/4/projects/24/sql_generation/retention_policy -> HTTP 403 4PERM001 PERMISSION_UNDEFINED, error_object {code:76,message:'Permissions have not been set c. Re-check before relying on it.

### `ai.sql.generate`

Run: `mammoth ai sql generate`. Exact input fields: `mammoth schema get ai.sql.generate`.

Example: `mammoth ai sql generate 'Summarize revenue by region' --input '{"dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AiSqlGenerateResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — backend_error: Fix held (dataset_id required and sent as query param -- request reached backend and got a domain-specific conflict, not an empty api_error). Re-check before relying on it.

### `ai.suggestion.list`

Run: `mammoth ai suggestion list`. Exact input fields: `mammoth schema get ai.suggestion.list`.

Example: `mammoth ai suggestion list --input '{"suggestion_type": "generate_task", "params": {"prompt": "Filter rows where Price > 100"}, "dataset_id": 456, "dataview_id": 123}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AiSuggestionListResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — backend_error: Fix held: release UnifiedPromptSpec (suggestion_type + params, optional dataset_id/dataview_id) shape accepted and dispatched to a real job (id 381), which failed fo. Re-check before relying on it.
