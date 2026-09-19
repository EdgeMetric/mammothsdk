# `template` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `template.create`

Run: `mammoth template create`. Exact input fields: `mammoth schema get template.create`.

Example: `mammoth template create --input '{"body": {"name": "Revenue report"}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `TemplateCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Created template id=1 status=draft (workspace-scoped, no dataset/view source needed since template_data is optional). Single invocation only.

### `template.delete`

Run: `mammoth template delete`. Exact input fields: `mammoth schema get template.delete`.

Example: `mammoth template delete 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `TemplateDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted template 1; read-back list is empty. Single invocation only.

### `template.get`

Run: `mammoth template get`. Exact input fields: `mammoth schema get template.get`.

Example: `mammoth template get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `TemplateGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Fetched template 1, matches create. Single invocation only.

### `template.list`

Run: `mammoth template list`. Exact input fields: `mammoth schema get template.list`.

Example: `mammoth template list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `TemplateListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Empty result on this fixture. Re-check after family 7 cleanup: empty, as expected. Single invocation only.

### `template.update`

Run: `mammoth template update`. Exact input fields: `mammoth schema get template.update`.

Example: `mammoth template update 123 --input '{"body": {"name": "Revenue report"}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `TemplateUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Updated description field. Single invocation only.
