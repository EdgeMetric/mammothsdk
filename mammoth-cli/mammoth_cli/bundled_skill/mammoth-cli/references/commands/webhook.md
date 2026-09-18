# `webhook` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `webhook.create`

Run: `mammoth webhook create`. Exact input fields: `mammoth schema get webhook.create --output json --no-input`.

Example: `mammoth webhook create 'Revenue report' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WebhookCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `webhook.delete`

Run: `mammoth webhook delete`. Exact input fields: `mammoth schema get webhook.delete --output json --no-input`.

Example: `mammoth webhook delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `WebhookDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `webhook.get`

Run: `mammoth webhook get`. Exact input fields: `mammoth schema get webhook.get --output json --no-input`.

Example: `mammoth webhook get 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WebhookGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `webhook.list`

Run: `mammoth webhook list`. Exact input fields: `mammoth schema get webhook.list --output json --no-input`.

Example: `mammoth webhook list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WebhookListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — cli_error: api_error with no HTTP status recorded. Re-check before relying on it.

### `webhook.send`

Run: `mammoth webhook send`. Exact input fields: `mammoth schema get webhook.send --output json --no-input`.

Example: `mammoth webhook send --input '{"webhook_uri": "https://example.com/data.csv", "data": {"sample_key": "Status"}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WebhookSendResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `webhook.send-get`

Run: `mammoth webhook send-get`. Exact input fields: `mammoth schema get webhook.send-get --output json --no-input`.

Example: `mammoth webhook send-get --input '{"webhook_uri": "https://example.com/data.csv"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WebhookSendGetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `webhook.update`

Run: `mammoth webhook update`. Exact input fields: `mammoth schema get webhook.update --output json --no-input`.

Example: `mammoth webhook update 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `WebhookUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
