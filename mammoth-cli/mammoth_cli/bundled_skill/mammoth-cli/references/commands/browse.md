# `browse` commands

### `browse.folder`

Run: `mammoth browse folder`. Exact input fields: `mammoth schema get browse.folder --output json --no-input`.

Example: `mammoth browse folder 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `BrowseFolderResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `browse.project`

Run: `mammoth browse project`. Exact input fields: `mammoth schema get browse.project --output json --no-input`.

Example: `mammoth browse project --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `BrowseProjectResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `browse.root`

Run: `mammoth browse root`. Exact input fields: `mammoth schema get browse.root --output json --no-input`.

Example: `mammoth browse root --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `BrowseRootResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `browse.workspace`

Run: `mammoth browse workspace`. Exact input fields: `mammoth schema get browse.workspace --output json --no-input`.

Example: `mammoth browse workspace --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `BrowseWorkspaceResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
