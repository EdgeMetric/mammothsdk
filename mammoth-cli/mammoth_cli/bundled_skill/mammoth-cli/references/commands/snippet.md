# `snippet` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `snippet.create`

Run: `mammoth snippet create`. Exact input fields: `mammoth schema get snippet.create --output json --no-input`.

Example: `mammoth snippet create 'Revenue report' --input '{"code": "sample", "language": "sample"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `snippet.delete`

Run: `mammoth snippet delete`. Exact input fields: `mammoth schema get snippet.delete --output json --no-input`.

Example: `mammoth snippet delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `SnippetDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `snippet.dependencies`

Run: `mammoth snippet dependencies`. Exact input fields: `mammoth schema get snippet.dependencies --output json --no-input`.

Example: `mammoth snippet dependencies 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetDependenciesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `snippet.duplicate`

Run: `mammoth snippet duplicate`. Exact input fields: `mammoth schema get snippet.duplicate --output json --no-input`.

Example: `mammoth snippet duplicate 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetDuplicateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `snippet.get`

Run: `mammoth snippet get`. Exact input fields: `mammoth schema get snippet.get --output json --no-input`.

Example: `mammoth snippet get 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `snippet.list`

Run: `mammoth snippet list`. Exact input fields: `mammoth schema get snippet.list --output json --no-input`.

Example: `mammoth snippet list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: items, limit, next, offset, total_count. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `snippet.rerun`

Run: `mammoth snippet rerun`. Exact input fields: `mammoth schema get snippet.rerun --output json --no-input`.

Example: `mammoth snippet rerun 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetRerunResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `snippet.update`

Run: `mammoth snippet update`. Exact input fields: `mammoth schema get snippet.update --output json --no-input`.

Example: `mammoth snippet update 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
