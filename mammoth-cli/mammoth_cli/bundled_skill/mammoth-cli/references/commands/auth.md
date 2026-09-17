# `auth` commands

### `auth.login`

Run: `mammoth auth login`. Exact input fields: `mammoth schema get auth.login --output json --no-input`.

Example: `mammoth auth login --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AuthLoginResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `auth.logout`

Run: `mammoth auth logout`. Exact input fields: `mammoth schema get auth.logout --output json --no-input`.

Example: `mammoth auth logout --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AuthLogoutResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `auth.status`

Run: `mammoth auth status`. Exact input fields: `mammoth schema get auth.status --output json --no-input`.

Example: `mammoth auth status --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AuthStatusResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
