# `ai` commands

### `ai.condition.generate`

Run: `mammoth ai condition generate`. Exact input fields: `mammoth schema get ai.condition.generate --output json --no-input`.

Example: `mammoth ai condition generate 123 --input '{"intent": "Summarize revenue by region"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AiConditionGenerateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `ai.expression.generate`

Run: `mammoth ai expression generate`. Exact input fields: `mammoth schema get ai.expression.generate --output json --no-input`.

Example: `mammoth ai expression generate 123 --input '{"intent": "Summarize revenue by region", "mode": "sample"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AiExpressionGenerateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `ai.retention.condition`

Run: `mammoth ai retention condition`. Exact input fields: `mammoth schema get ai.retention.condition --output json --no-input`.

Example: `mammoth ai retention condition 123 --input '{"mode": "generate", "intent": "completed payments older than 90 days"}' --output json --no-input --project 456`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AiRetentionConditionResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `start_or_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `ai.sql.generate`

Run: `mammoth ai sql generate`. Exact input fields: `mammoth schema get ai.sql.generate --output json --no-input`.

Example: `mammoth ai sql generate 'Summarize revenue by region' --input '{"dataset_id": 456}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AiSqlGenerateResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `ai.suggestion.list`

Run: `mammoth ai suggestion list`. Exact input fields: `mammoth schema get ai.suggestion.list --output json --no-input`.

Example: `mammoth ai suggestion list --input '{"suggestion_type": "generate_task", "params": {"prompt": "Filter rows where Price > 100"}, "dataset_id": 456, "dataview_id": 123}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AiSuggestionListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
