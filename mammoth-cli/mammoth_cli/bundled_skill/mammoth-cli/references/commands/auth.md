# `auth` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `auth.login`

Run: `mammoth auth login`. Exact input fields: `mammoth schema get auth.login`.

Example: `mammoth auth login`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AuthLoginResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `auth.logout`

Run: `mammoth auth logout`. Exact input fields: `mammoth schema get auth.logout`.

Example: `mammoth auth logout`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AuthLogoutResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `auth.status`

Run: `mammoth auth status`. Exact input fields: `mammoth schema get auth.status`.

Example: `mammoth auth status`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AuthStatusResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
