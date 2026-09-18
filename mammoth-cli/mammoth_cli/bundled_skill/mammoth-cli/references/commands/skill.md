# `skill` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `skill.install`

Run: `mammoth skill install`. Exact input fields: `mammoth schema get skill.install --output json --no-input`.

Example: `mammoth skill install --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SkillInstallResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `skill.list`

Run: `mammoth skill list`. Exact input fields: `mammoth schema get skill.list --output json --no-input`.

Example: `mammoth skill list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SkillListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `skill.path`

Run: `mammoth skill path`. Exact input fields: `mammoth schema get skill.path --output json --no-input`.

Example: `mammoth skill path --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SkillPathResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `skill.uninstall`

Run: `mammoth skill uninstall`. Exact input fields: `mammoth schema get skill.uninstall --output json --no-input`.

Example: `mammoth skill uninstall --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SkillUninstallResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `skill.update`

Run: `mammoth skill update`. Exact input fields: `mammoth schema get skill.update --output json --no-input`.

Example: `mammoth skill update --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SkillUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
