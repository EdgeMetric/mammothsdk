# `config` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `config.get`

Run: `mammoth config get`. Exact input fields: `mammoth schema get config.get`.

Example: `mammoth config get output`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConfigGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `config.list`

Run: `mammoth config list`. Exact input fields: `mammoth schema get config.list`.

Example: `mammoth config list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConfigListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `config.path`

Run: `mammoth config path`. Exact input fields: `mammoth schema get config.path`.

Example: `mammoth config path`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConfigPathResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `config.set`

Run: `mammoth config set`. Exact input fields: `mammoth schema get config.set`.

Example: `mammoth config set output text`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConfigSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
