# `capability` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `capability.find`

Run: `mammoth capability find`. Exact input fields: `mammoth schema get capability.find`.

Example: `mammoth capability find 'show projects'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CapabilityFindResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `capability.get`

Run: `mammoth capability get`. Exact input fields: `mammoth schema get capability.get`.

Example: `mammoth capability get AddTask`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CapabilityGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `capability.list`

Run: `mammoth capability list`. Exact input fields: `mammoth schema get capability.list`.

Example: `mammoth capability list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CapabilityListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
