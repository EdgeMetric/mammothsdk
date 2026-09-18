# `connector` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `connector.active`

Run: `mammoth connector active`. Exact input fields: `mammoth schema get connector.active --output json --no-input`.

Example: `mammoth connector active --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorActiveResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: l, i, s, t, [, 0, ]. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `connector.ai.chat`

Run: `mammoth connector ai chat`. Exact input fields: `mammoth schema get connector.ai.chat --output json --no-input`.

Example: `mammoth connector ai chat --input '{"body": {"messages": [{"content": "sample", "role": "user"}]}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorAiChatResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ai.history`

Run: `mammoth connector ai history`. Exact input fields: `mammoth schema get connector.ai.history --output json --no-input`.

Example: `mammoth connector ai history sample --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorAiHistoryResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ai.session.list`

Run: `mammoth connector ai session list`. Exact input fields: `mammoth schema get connector.ai.session.list --output json --no-input`.

Example: `mammoth connector ai session list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorAiSessionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — cli_error: backend returned HTTP 200 but the CLI raised api_error (envelope mismatch). Re-check before relying on it.

### `connector.ai.session.messages`

Run: `mammoth connector ai session messages`. Exact input fields: `mammoth schema get connector.ai.session.messages --output json --no-input`.

Example: `mammoth connector ai session messages 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorAiSessionMessagesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ai.submit-column-selection`

Run: `mammoth connector ai submit-column-selection`. Exact input fields: `mammoth schema get connector.ai.submit-column-selection --output json --no-input`.

Example: `mammoth connector ai submit-column-selection --input '{"body": {"selected_columns": ["Status"], "session_id": "resource-123"}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorAiSubmitColumnSelectionResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ai.submit-credentials`

Run: `mammoth connector ai submit-credentials`. Exact input fields: `mammoth schema get connector.ai.submit-credentials --output json --no-input`.

Example: `mammoth connector ai submit-credentials --input '{"body": {"credentials": {}, "session_id": "resource-123"}}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorAiSubmitCredentialsResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.connection.create`

Run: `mammoth connector connection create`. Exact input fields: `mammoth schema get connector.connection.create --output json --no-input`.

Example: `mammoth connector connection create sample --input '{"config": {"sample_key": "Status"}}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorConnectionCreateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.connection.delete`

Run: `mammoth connector connection delete`. Exact input fields: `mammoth schema get connector.connection.delete --output json --no-input`.

Example: `mammoth connector connection delete sample sample --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorConnectionDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.connection.get`

Run: `mammoth connector connection get`. Exact input fields: `mammoth schema get connector.connection.get --output json --no-input`.

Example: `mammoth connector connection get sample sample --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorConnectionGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.connection.list`

Run: `mammoth connector connection list`. Exact input fields: `mammoth schema get connector.connection.list --output json --no-input`.

Example: `mammoth connector connection list sample --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorConnectionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — server_error: see sweep report. Re-check before relying on it.

### `connector.connection.update`

Run: `mammoth connector connection update`. Exact input fields: `mammoth schema get connector.connection.update --output json --no-input`.

Example: `mammoth connector connection update sample sample --input '{"credentials": {"sample_key": "Status"}}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorConnectionUpdateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ds-config.create`

Run: `mammoth connector ds-config create`. Exact input fields: `mammoth schema get connector.ds-config.create --output json --no-input`.

Example: `mammoth connector ds-config create sample sample --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorDsConfigCreateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ds-config.delete`

Run: `mammoth connector ds-config delete`. Exact input fields: `mammoth schema get connector.ds-config.delete --output json --no-input`.

Example: `mammoth connector ds-config delete sample sample sample --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorDsConfigDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ds-config.delete-all`

Run: `mammoth connector ds-config delete-all`. Exact input fields: `mammoth schema get connector.ds-config.delete-all --output json --no-input`.

Example: `mammoth connector ds-config delete-all sample sample --input '{"config_ids": ["resource-123"]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorDsConfigDeleteAllResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ds-config.get`

Run: `mammoth connector ds-config get`. Exact input fields: `mammoth schema get connector.ds-config.get --output json --no-input`.

Example: `mammoth connector ds-config get sample sample sample --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDsConfigGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ds-config.list`

Run: `mammoth connector ds-config list`. Exact input fields: `mammoth schema get connector.ds-config.list --output json --no-input`.

Example: `mammoth connector ds-config list sample sample --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDsConfigListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ds-config.update`

Run: `mammoth connector ds-config update`. Exact input fields: `mammoth schema get connector.ds-config.update --output json --no-input`.

Example: `mammoth connector ds-config update sample sample sample --input '{"patch": [{"op": "replace", "path": "query", "value": "sample"}]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorDsConfigUpdateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.get`

Run: `mammoth connector get`. Exact input fields: `mammoth schema get connector.get --output json --no-input`.

Example: `mammoth connector get sample --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — validation_error: HTTP 400 'Invalid connector key' for a key returned by connector.list. Re-check before relying on it.

### `connector.list`

Run: `mammoth connector list`. Exact input fields: `mammoth schema get connector.list --output json --no-input`.

Example: `mammoth connector list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: l, i, s, t, [, 4, 2, ]. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `connector.query.generate`

Run: `mammoth connector query generate`. Exact input fields: `mammoth schema get connector.query.generate --output json --no-input`.

Example: `mammoth connector query generate sample sample --input '{"query": "Total sales for January"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorQueryGenerateResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — blocked_missing_fixture: No real connector connection exists in workspace 4 (connector.list shows all is_added:false; connector.active returns []), matching the documented capabili. Re-check before relying on it.

### `connector.query.status`

Run: `mammoth connector query status`. Exact input fields: `mammoth schema get connector.query.status --output json --no-input`.

Example: `mammoth connector query status sample sample --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorQueryStatusResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — blocked_missing_fixture: No real connector connection exists in workspace 4 (connector list shows all is_added:false; connector active returns []) and creating one requires externa. Re-check before relying on it.
