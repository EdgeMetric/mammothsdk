# `skill` commands

### `skill.install`

Run: `mammoth skill install`. Exact input fields: `mammoth schema get skill.install --output json --no-input`.

Example: `mammoth skill install --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SkillInstallResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `skill.list`

Run: `mammoth skill list`. Exact input fields: `mammoth schema get skill.list --output json --no-input`.

Example: `mammoth skill list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SkillListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `skill.path`

Run: `mammoth skill path`. Exact input fields: `mammoth schema get skill.path --output json --no-input`.

Example: `mammoth skill path --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SkillPathResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `skill.uninstall`

Run: `mammoth skill uninstall`. Exact input fields: `mammoth schema get skill.uninstall --output json --no-input`.

Example: `mammoth skill uninstall --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SkillUninstallResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `skill.update`

Run: `mammoth skill update`. Exact input fields: `mammoth schema get skill.update --output json --no-input`.

Example: `mammoth skill update --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `SkillUpdateResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
