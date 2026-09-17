# `annotation` commands

### `annotation.comment.add`

Run: `mammoth annotation comment add`. Exact input fields: `mammoth schema get annotation.comment.add --output json --no-input`.

Example: `mammoth annotation comment add 123 --input '{"body": "sample"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AnnotationCommentAddResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `annotation.create`

Run: `mammoth annotation create`. Exact input fields: `mammoth schema get annotation.create --output json --no-input`.

Example: `mammoth annotation create --input '{"target_type": "sample", "target_id": 1, "body": "sample"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AnnotationCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `annotation.delete`

Run: `mammoth annotation delete`. Exact input fields: `mammoth schema get annotation.delete --output json --no-input`.

Example: `mammoth annotation delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `AnnotationDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `annotation.list`

Run: `mammoth annotation list`. Exact input fields: `mammoth schema get annotation.list --output json --no-input`.

Example: `mammoth annotation list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AnnotationListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `annotation.update`

Run: `mammoth annotation update`. Exact input fields: `mammoth schema get annotation.update --output json --no-input`.

Example: `mammoth annotation update 123 --input '{"status": "sample"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AnnotationUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
