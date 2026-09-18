# `completion` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `completion.install`

Run: `mammoth completion install`. Exact input fields: `mammoth schema get completion.install --output json --no-input`.

Example: `mammoth completion install bash --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CompletionInstallResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `completion.show`

Run: `mammoth completion show`. Exact input fields: `mammoth schema get completion.show --output json --no-input`.

Example: `mammoth completion show bash --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CompletionShowResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
