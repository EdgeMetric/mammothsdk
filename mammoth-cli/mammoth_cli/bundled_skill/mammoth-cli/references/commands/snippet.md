# `snippet` commands

### `snippet.create`

Run: `mammoth snippet create`. Exact input fields: `mammoth schema get snippet.create --output json --no-input`.

Example: `mammoth snippet create 'Revenue report' --input '{"code": "sample", "language": "sample"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SnippetCreateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `snippet.delete`

Run: `mammoth snippet delete`. Exact input fields: `mammoth schema get snippet.delete --output json --no-input`.

Example: `mammoth snippet delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `SnippetDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `snippet.dependencies`

Run: `mammoth snippet dependencies`. Exact input fields: `mammoth schema get snippet.dependencies --output json --no-input`.

Example: `mammoth snippet dependencies 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SnippetDependenciesResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `snippet.duplicate`

Run: `mammoth snippet duplicate`. Exact input fields: `mammoth schema get snippet.duplicate --output json --no-input`.

Example: `mammoth snippet duplicate 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SnippetDuplicateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `snippet.get`

Run: `mammoth snippet get`. Exact input fields: `mammoth schema get snippet.get --output json --no-input`.

Example: `mammoth snippet get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SnippetGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `snippet.list`

Run: `mammoth snippet list`. Exact input fields: `mammoth schema get snippet.list --output json --no-input`.

Example: `mammoth snippet list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SnippetListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `snippet.rerun`

Run: `mammoth snippet rerun`. Exact input fields: `mammoth schema get snippet.rerun --output json --no-input`.

Example: `mammoth snippet rerun 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SnippetRerunResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `snippet.update`

Run: `mammoth snippet update`. Exact input fields: `mammoth schema get snippet.update --output json --no-input`.

Example: `mammoth snippet update 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SnippetUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
