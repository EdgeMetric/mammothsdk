# `snippet` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `snippet.create`

Run: `mammoth snippet create`. Exact input fields: `mammoth schema get snippet.create`.

Example: `mammoth snippet create 'Revenue report' --input '{"code": "sample", "language": "sample"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. First attempt with hyphenated name 'sweep-218 snippet' failed 4SNPT006 (name must be letters/digits/underscore); retried with sweep_218_snippet, created id=1 scope=project. Single invocati…

### `snippet.delete`

Run: `mammoth snippet delete`. Exact input fields: `mammoth schema get snippet.delete`.

Example: `mammoth snippet delete 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `SnippetDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted snippet 1; read-back list shows total_count=0. Single invocation only.

### `snippet.dependencies`

Run: `mammoth snippet dependencies`. Exact input fields: `mammoth schema get snippet.dependencies`.

Example: `mammoth snippet dependencies 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetDependenciesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Empty result on this fixture. No dependencies for unused snippet, as expected. Single invocation only.

### `snippet.duplicate`

Run: `mammoth snippet duplicate`. Exact input fields: `mammoth schema get snippet.duplicate`.

Example: `mammoth snippet duplicate 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetDuplicateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `snippet.get`

Run: `mammoth snippet get`. Exact input fields: `mammoth schema get snippet.get`.

Example: `mammoth snippet get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Fetched snippet 1 with dependencies/history fields added. Minor note: meta.project_id is null on this response (and on dependencies/update/delete) while list/create show 41 - inconsistent…

### `snippet.list`

Run: `mammoth snippet list`. Exact input fields: `mammoth schema get snippet.list`.

Example: `mammoth snippet list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Empty result on this fixture. Empty after family 6 cleanup, as expected. Single invocation only.

### `snippet.rerun`

Run: `mammoth snippet rerun`. Exact input fields: `mammoth schema get snippet.rerun`.

Example: `mammoth snippet rerun 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetRerunResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `snippet.update`

Run: `mammoth snippet update`. Exact input fields: `mammoth schema get snippet.update`.

Example: `mammoth snippet update 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `SnippetUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Updated description; response reflects change. Single invocation only.
