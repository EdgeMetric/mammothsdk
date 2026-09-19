# `context` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `context.project.clear`

Run: `mammoth context project clear`. Exact input fields: `mammoth schema get context.project.clear`.

Example: `mammoth context project clear`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ContextProjectClearResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `context.project.status`

Run: `mammoth context project status`. Exact input fields: `mammoth schema get context.project.status`.

Example: `mammoth context project status`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ContextProjectStatusResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `context.project.use`

Run: `mammoth context project use`. Exact input fields: `mammoth schema get context.project.use`.

Example: `mammoth context project use 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ContextProjectUseResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
