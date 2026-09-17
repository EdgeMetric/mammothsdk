# `connector` commands

### `connector.active`

Run: `mammoth connector active`. Exact input fields: `mammoth schema get connector.active --output json --no-input`.

Example: `mammoth connector active --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorActiveResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.ai.chat`

Run: `mammoth connector ai chat`. Exact input fields: `mammoth schema get connector.ai.chat --output json --no-input`.

Example: `mammoth connector ai chat --input '{"body": {"messages": [{"content": "sample", "role": "user"}]}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorAiChatResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.ai.history`

Run: `mammoth connector ai history`. Exact input fields: `mammoth schema get connector.ai.history --output json --no-input`.

Example: `mammoth connector ai history sample --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorAiHistoryResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.ai.session.list`

Run: `mammoth connector ai session list`. Exact input fields: `mammoth schema get connector.ai.session.list --output json --no-input`.

Example: `mammoth connector ai session list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorAiSessionListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.ai.session.messages`

Run: `mammoth connector ai session messages`. Exact input fields: `mammoth schema get connector.ai.session.messages --output json --no-input`.

Example: `mammoth connector ai session messages 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorAiSessionMessagesResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.ai.submit-column-selection`

Run: `mammoth connector ai submit-column-selection`. Exact input fields: `mammoth schema get connector.ai.submit-column-selection --output json --no-input`.

Example: `mammoth connector ai submit-column-selection --input '{"body": {"selected_columns": ["Status"], "session_id": "resource-123"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorAiSubmitColumnSelectionResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.ai.submit-credentials`

Run: `mammoth connector ai submit-credentials`. Exact input fields: `mammoth schema get connector.ai.submit-credentials --output json --no-input`.

Example: `mammoth connector ai submit-credentials --input '{"body": {"credentials": {}, "session_id": "resource-123"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorAiSubmitCredentialsResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.connection.create`

Run: `mammoth connector connection create`. Exact input fields: `mammoth schema get connector.connection.create --output json --no-input`.

Example: `mammoth connector connection create sample --input '{"config": {"sample_key": "Status"}}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ConnectorConnectionCreateResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.connection.delete`

Run: `mammoth connector connection delete`. Exact input fields: `mammoth schema get connector.connection.delete --output json --no-input`.

Example: `mammoth connector connection delete sample sample --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ConnectorConnectionDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.connection.get`

Run: `mammoth connector connection get`. Exact input fields: `mammoth schema get connector.connection.get --output json --no-input`.

Example: `mammoth connector connection get sample sample --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorConnectionGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.connection.list`

Run: `mammoth connector connection list`. Exact input fields: `mammoth schema get connector.connection.list --output json --no-input`.

Example: `mammoth connector connection list sample --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorConnectionListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.connection.update`

Run: `mammoth connector connection update`. Exact input fields: `mammoth schema get connector.connection.update --output json --no-input`.

Example: `mammoth connector connection update sample sample --input '{"credentials": {"sample_key": "Status"}}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ConnectorConnectionUpdateResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.ds-config.create`

Run: `mammoth connector ds-config create`. Exact input fields: `mammoth schema get connector.ds-config.create --output json --no-input`.

Example: `mammoth connector ds-config create sample sample --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ConnectorDsConfigCreateResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.ds-config.delete`

Run: `mammoth connector ds-config delete`. Exact input fields: `mammoth schema get connector.ds-config.delete --output json --no-input`.

Example: `mammoth connector ds-config delete sample sample sample --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ConnectorDsConfigDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.ds-config.delete-all`

Run: `mammoth connector ds-config delete-all`. Exact input fields: `mammoth schema get connector.ds-config.delete-all --output json --no-input`.

Example: `mammoth connector ds-config delete-all sample sample --input '{"config_ids": ["resource-123"]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ConnectorDsConfigDeleteAllResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.ds-config.get`

Run: `mammoth connector ds-config get`. Exact input fields: `mammoth schema get connector.ds-config.get --output json --no-input`.

Example: `mammoth connector ds-config get sample sample sample --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorDsConfigGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.ds-config.list`

Run: `mammoth connector ds-config list`. Exact input fields: `mammoth schema get connector.ds-config.list --output json --no-input`.

Example: `mammoth connector ds-config list sample sample --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorDsConfigListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.ds-config.update`

Run: `mammoth connector ds-config update`. Exact input fields: `mammoth schema get connector.ds-config.update --output json --no-input`.

Example: `mammoth connector ds-config update sample sample sample --input '{"patch": [{"op": "replace", "path": "query", "value": "sample"}]}' --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `ConnectorDsConfigUpdateResult` in the standard JSON envelope; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.get`

Run: `mammoth connector get`. Exact input fields: `mammoth schema get connector.get --output json --no-input`.

Example: `mammoth connector get sample --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.list`

Run: `mammoth connector list`. Exact input fields: `mammoth schema get connector.list --output json --no-input`.

Example: `mammoth connector list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.query.generate`

Run: `mammoth connector query generate`. Exact input fields: `mammoth schema get connector.query.generate --output json --no-input`.

Example: `mammoth connector query generate sample sample --input '{"prompt": "Summarize revenue by region"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorQueryGenerateResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `connector.query.status`

Run: `mammoth connector query status`. Exact input fields: `mammoth schema get connector.query.status --output json --no-input`.

Example: `mammoth connector query status sample sample --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `ConnectorQueryStatusResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
