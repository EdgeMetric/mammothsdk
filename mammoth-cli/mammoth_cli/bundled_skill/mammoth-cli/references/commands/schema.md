# `schema` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `schema.find`

Run: `mammoth schema find`. Exact input fields: `mammoth schema get schema.find`.

Example: `mammoth schema find 'view transform'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SchemaFindResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `schema.get`

Run: `mammoth schema get`. Exact input fields: `mammoth schema get schema.get`.

Example: `mammoth schema get view.transform.bulk-replace`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SchemaGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `schema.list`

Run: `mammoth schema list`. Exact input fields: `mammoth schema get schema.list`.

Example: `mammoth schema list view`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SchemaListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
