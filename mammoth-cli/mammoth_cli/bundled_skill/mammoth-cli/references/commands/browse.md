# `browse` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `browse.folder`

Run: `mammoth browse folder`. Exact input fields: `mammoth schema get browse.folder`.

Example: `mammoth browse folder 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BrowseFolderResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — cli_error: rejects folder id 0 although folder.root reports id 0 as the root. Re-check before relying on it.

### `browse.project`

Run: `mammoth browse project`. Exact input fields: `mammoth schema get browse.project`.

Example: `mammoth browse project`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BrowseProjectResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend_error: GET /workspaces/4/projects/47/browse HTTP 500 empty body. Re-check before relying on it.

### `browse.root`

Run: `mammoth browse root`. Exact input fields: `mammoth schema get browse.root`.

Example: `mammoth browse root`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BrowseRootResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend_error: GET /browse still HTTP 500 empty body on release (same as 2026-09-18/19 sweeps). Re-check before relying on it.

### `browse.workspace`

Run: `mammoth browse workspace`. Exact input fields: `mammoth schema get browse.workspace`.

Example: `mammoth browse workspace`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BrowseWorkspaceResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Works fine and lists workspace resources (read-only; includes pre-existing project 3 datasets, not touched) - contrasts with browse.root/browse.project both 500ing, suggesting a scope-spec…
