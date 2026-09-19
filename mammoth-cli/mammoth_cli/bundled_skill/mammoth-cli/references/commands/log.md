# `log` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `log.path`

Run: `mammoth log path`. Exact input fields: `mammoth schema get log.path`.

Example: `mammoth log path`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `LogPathResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `log.tail`

Run: `mammoth log tail`. Exact input fields: `mammoth schema get log.tail`.

Example: `mammoth log tail --input '{"errors_only": true, "limit": 20}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `LogTailResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
