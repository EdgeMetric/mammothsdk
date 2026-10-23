# `history` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `history.list`

Run: `mammoth history list`. Exact input fields: `mammoth schema get history.list`.

Example: `mammoth history list --input '{"undoable_only": true}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `HistoryListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `history.show`

Run: `mammoth history show`. Exact input fields: `mammoth schema get history.show`.

Example: `mammoth history show 97b9ee41d15d`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `HistoryShowResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `history.undo`

Run: `mammoth history undo`. Exact input fields: `mammoth schema get history.undo`.

Example: `mammoth history undo 97b9ee41d15d --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `HistoryUndoResult`; mutation `high_impact`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.
