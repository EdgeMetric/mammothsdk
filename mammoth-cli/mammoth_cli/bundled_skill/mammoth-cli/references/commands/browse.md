# `browse` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `browse.folder`

Run: `mammoth browse folder`. Exact input fields: `mammoth schema get browse.folder --output json --no-input`.

Example: `mammoth browse folder 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BrowseFolderResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — cli_error: rejects folder id 0 although folder.root reports id 0 as the root. Re-check before relying on it.

### `browse.project`

Run: `mammoth browse project`. Exact input fields: `mammoth schema get browse.project --output json --no-input`.

Example: `mammoth browse project --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BrowseProjectResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.10 — Bounded release read with pinned CLI 1.1.10: default browse returned documented structured HTTP 500; limit=1 and limit=0 returned valid empty resource pages. No Full claim: backend server variance and no non-empty resource fixture.

### `browse.root`

Run: `mammoth browse root`. Exact input fields: `mammoth schema get browse.root --output json --no-input`.

Example: `mammoth browse root --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BrowseRootResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — server_error: see sweep report. Re-check before relying on it.

### `browse.workspace`

Run: `mammoth browse workspace`. Exact input fields: `mammoth schema get browse.workspace --output json --no-input`.

Example: `mammoth browse workspace --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BrowseWorkspaceResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: limit, next, offset, resources. Single read only; no fixture variants, error envelopes, or write paths assessed.
