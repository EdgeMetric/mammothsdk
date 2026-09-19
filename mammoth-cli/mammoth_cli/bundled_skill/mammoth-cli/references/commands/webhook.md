# `webhook` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `webhook.create`

Run: `mammoth webhook create`. Exact input fields: `mammoth schema get webhook.create`.

Example: `mammoth webhook create 'Revenue report'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WebhookCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Created webhook id=1, which auto-created a backing dataset ds_id=86. Single invocation only.

### `webhook.delete`

Run: `mammoth webhook delete`. Exact input fields: `mammoth schema get webhook.delete`.

Example: `mammoth webhook delete 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `WebhookDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted webhook 1; read-back list is empty, confirming deletion. Single invocation only.

### `webhook.get`

Run: `mammoth webhook get`. Exact input fields: `mammoth schema get webhook.get`.

Example: `mammoth webhook get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WebhookGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Fetched webhook 1, fields match create response. Single invocation only.

### `webhook.list`

Run: `mammoth webhook list`. Exact input fields: `mammoth schema get webhook.list`.

Example: `mammoth webhook list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WebhookListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Empty result on this fixture. Re-check after family 2 cleanup: empty, as expected. Single invocation only.

### `webhook.send`

Run: `mammoth webhook send`. Exact input fields: `mammoth schema get webhook.send`.

Example: `mammoth webhook send --input '{"webhook_uri": "https://example.com/data.csv", "data": {"sample_key": "Status"}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WebhookSendResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `webhook.send-get`

Run: `mammoth webhook send-get`. Exact input fields: `mammoth schema get webhook.send-get`.

Example: `mammoth webhook send-get --input '{"webhook_uri": "https://example.com/data.csv"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WebhookSendGetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `webhook.update`

Run: `mammoth webhook update`. Exact input fields: `mammoth schema get webhook.update`.

Example: `mammoth webhook update 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WebhookUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Updated mode replace->combine; response reflects new mode. Single invocation only.
