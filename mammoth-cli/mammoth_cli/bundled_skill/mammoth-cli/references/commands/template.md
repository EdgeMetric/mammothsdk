# `template` commands

### `template.create`

Run: `mammoth template create`. Exact input fields: `mammoth schema get template.create --output json --no-input`.

Example: `mammoth template create --input '{"body": {"name": "Revenue report"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `TemplateCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `template.delete`

Run: `mammoth template delete`. Exact input fields: `mammoth schema get template.delete --output json --no-input`.

Example: `mammoth template delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `TemplateDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `template.get`

Run: `mammoth template get`. Exact input fields: `mammoth schema get template.get --output json --no-input`.

Example: `mammoth template get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `TemplateGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `template.list`

Run: `mammoth template list`. Exact input fields: `mammoth schema get template.list --output json --no-input`.

Example: `mammoth template list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `TemplateListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `template.update`

Run: `mammoth template update`. Exact input fields: `mammoth schema get template.update --output json --no-input`.

Example: `mammoth template update 123 --input '{"body": {"name": "Revenue report"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `TemplateUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
