# `connector` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `connector.active`

Run: `mammoth connector active`. Exact input fields: `mammoth schema get connector.active`.

Example: `mammoth connector active`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorActiveResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: l, i, s, t, [, 0, ]. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `connector.ai.chat`

Run: `mammoth connector ai chat`. Exact input fields: `mammoth schema get connector.ai.chat`.

Example: `mammoth connector ai chat --input '{"body": {"messages": [{"content": "Quarterly revenue summary", "role": "user"}]}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorAiChatResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ai.history`

Run: `mammoth connector ai history`. Exact input fields: `mammoth schema get connector.ai.history`.

Example: `mammoth connector ai history prod-warehouse`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorAiHistoryResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ai.session.list`

Run: `mammoth connector ai session list`. Exact input fields: `mammoth schema get connector.ai.session.list`.

Example: `mammoth connector ai session list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorAiSessionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Empty result on this fixture. No AI chat sessions for connectors. Single invocation only.

### `connector.ai.session.messages`

Run: `mammoth connector ai session messages`. Exact input fields: `mammoth schema get connector.ai.session.messages`.

Example: `mammoth connector ai session messages 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorAiSessionMessagesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ai.submit-column-selection`

Run: `mammoth connector ai submit-column-selection`. Exact input fields: `mammoth schema get connector.ai.submit-column-selection`.

Example: `mammoth connector ai submit-column-selection --input '{"body": {"selected_columns": ["Status"], "session_id": "resource-123"}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorAiSubmitColumnSelectionResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ai.submit-credentials`

Run: `mammoth connector ai submit-credentials`. Exact input fields: `mammoth schema get connector.ai.submit-credentials`.

Example: `mammoth connector ai submit-credentials --input '{"body": {"credentials": {}, "session_id": "resource-123"}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorAiSubmitCredentialsResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.connection.create`

Run: `mammoth connector connection create`. Exact input fields: `mammoth schema get connector.connection.create`.

Example: `mammoth connector connection create postgres --input /private/path/request.json --yes`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ConnectorConnectionCreateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.connection.delete`

Run: `mammoth connector connection delete`. Exact input fields: `mammoth schema get connector.connection.delete`.

Example: `mammoth connector connection delete postgres prod-warehouse --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorConnectionDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.connection.get`

Run: `mammoth connector connection get`. Exact input fields: `mammoth schema get connector.connection.get`.

Example: `mammoth connector connection get postgres prod-warehouse`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorConnectionGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.connection.list`

Run: `mammoth connector connection list`. Exact input fields: `mammoth schema get connector.connection.list`.

Example: `mammoth connector connection list postgres`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorConnectionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — server_error: see sweep report. Re-check before relying on it.

### `connector.connection.list-all`

Run: `mammoth connector connection list-all`. Exact input fields: `mammoth schema get connector.connection.list-all`.

Example: `mammoth connector connection list-all`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorConnectionListAllResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.connection.query`

Run: `mammoth connector connection query`. Exact input fields: `mammoth schema get connector.connection.query`.

Example: `mammoth connector connection query postgres prod-warehouse --input '{"query": "SELECT region, SUM(revenue) FROM data GROUP BY region"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorConnectionQueryResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.connection.test`

Run: `mammoth connector connection test`. Exact input fields: `mammoth schema get connector.connection.test`.

Example: `mammoth connector connection test prod-warehouse`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorConnectionTestResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.connection.update`

Run: `mammoth connector connection update`. Exact input fields: `mammoth schema get connector.connection.update`.

Example: `mammoth connector connection update postgres prod-warehouse --input /private/path/request.json --yes`. Illustrative only: append `--yes` after observing an owned target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `ConnectorConnectionUpdateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.browse`

Run: `mammoth connector draft browse`. Exact input fields: `mammoth schema get connector.draft.browse`.

Example: `mammoth connector draft browse 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftBrowseResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.create`

Run: `mammoth connector draft create`. Exact input fields: `mammoth schema get connector.draft.create`.

Example: `mammoth connector draft create --input '{"origin": "connections", "connector_key": "hubspot"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.discard`

Run: `mammoth connector draft discard`. Exact input fields: `mammoth schema get connector.draft.discard`.

Example: `mammoth connector draft discard 123 --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorDraftDiscardResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.fill`

Run: `mammoth connector draft fill`. Exact input fields: `mammoth schema get connector.draft.fill`.

Example: `mammoth connector draft fill 123 --input '{"column": "region", "file_object_id": 77}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftFillResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.get`

Run: `mammoth connector draft get`. Exact input fields: `mammoth schema get connector.draft.get`.

Example: `mammoth connector draft get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.known-sources`

Run: `mammoth connector draft known-sources`. Exact input fields: `mammoth schema get connector.draft.known-sources`.

Example: `mammoth connector draft known-sources`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftKnownSourcesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.list`

Run: `mammoth connector draft list`. Exact input fields: `mammoth schema get connector.draft.list`.

Example: `mammoth connector draft list --input '{"status": "all"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.open`

Run: `mammoth connector draft open`. Exact input fields: `mammoth schema get connector.draft.open`.

Example: `mammoth connector draft open 123 --input '{"ref": "sheet-ref", "name": "Sales 2026"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftOpenResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.read-tables`

Run: `mammoth connector draft read-tables`. Exact input fields: `mammoth schema get connector.draft.read-tables`.

Example: `mammoth connector draft read-tables 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftReadTablesResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.sample`

Run: `mammoth connector draft sample`. Exact input fields: `mammoth schema get connector.draft.sample`.

Example: `mammoth connector draft sample 123 sample.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftSampleResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.save`

Run: `mammoth connector draft save`. Exact input fields: `mammoth schema get connector.draft.save`.

Example: `mammoth connector draft save 123 --input '{"refresh": "daily", "dataset_name": "HubSpot deals"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftSaveResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `connector.draft.source.join-candidates`

Run: `mammoth connector draft source join-candidates`. Exact input fields: `mammoth schema get connector.draft.source.join-candidates`.

Example: `mammoth connector draft source join-candidates 123 resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftSourceJoinCandidatesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.source.list`

Run: `mammoth connector draft source list`. Exact input fields: `mammoth schema get connector.draft.source.list`.

Example: `mammoth connector draft source list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftSourceListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.source.preview`

Run: `mammoth connector draft source preview`. Exact input fields: `mammoth schema get connector.draft.source.preview`.

Example: `mammoth connector draft source preview 123 resource-123 --input '{"limit": 20}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftSourcePreviewResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.draft.update`

Run: `mammoth connector draft update`. Exact input fields: `mammoth schema get connector.draft.update`.

Example: `mammoth connector draft update 123 --input '{"title": "HubSpot deals"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDraftUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ds-config.create`

Run: `mammoth connector ds-config create`. Exact input fields: `mammoth schema get connector.ds-config.create`.

Example: `mammoth connector ds-config create postgres prod-warehouse --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorDsConfigCreateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ds-config.delete`

Run: `mammoth connector ds-config delete`. Exact input fields: `mammoth schema get connector.ds-config.delete`.

Example: `mammoth connector ds-config delete postgres prod-warehouse orders-config --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorDsConfigDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ds-config.delete-all`

Run: `mammoth connector ds-config delete-all`. Exact input fields: `mammoth schema get connector.ds-config.delete-all`.

Example: `mammoth connector ds-config delete-all postgres prod-warehouse --input '{"config_ids": ["resource-123"]}' --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorDsConfigDeleteAllResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ds-config.get`

Run: `mammoth connector ds-config get`. Exact input fields: `mammoth schema get connector.ds-config.get`.

Example: `mammoth connector ds-config get postgres prod-warehouse orders-config`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDsConfigGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ds-config.list`

Run: `mammoth connector ds-config list`. Exact input fields: `mammoth schema get connector.ds-config.list`.

Example: `mammoth connector ds-config list postgres prod-warehouse`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorDsConfigListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.ds-config.update`

Run: `mammoth connector ds-config update`. Exact input fields: `mammoth schema get connector.ds-config.update`.

Example: `mammoth connector ds-config update postgres prod-warehouse orders-config --input '{"patch": [{"op": "replace", "path": "query", "value": "SELECT * FROM orders"}]}' --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `ConnectorDsConfigUpdateResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `connector.get`

Run: `mammoth connector get`. Exact input fields: `mammoth schema get connector.get`.

Example: `mammoth connector get postgres`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend_error: SUSPECTED DEFECT: connector.get rejects the exact name_key values returned by connector.list ('azure_blob', 'bigquery' both tried) with 4CNTR002 INVALID_CONNECTOR_KE. Re-check before relying on it.

### `connector.list`

Run: `mammoth connector list`. Exact input fields: `mammoth schema get connector.list`.

Example: `mammoth connector list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Listed 42 available connectors (name_key, disp_name, api_type, is_added, is_premium). Single invocation only.

### `connector.query.generate`

Run: `mammoth connector query generate`. Exact input fields: `mammoth schema get connector.query.generate`.

Example: `mammoth connector query generate postgres prod-warehouse --input '{"query": "Total sales for January"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorQueryGenerateResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — blocked_missing_fixture: No real connector connection exists in workspace 4 (connector.list shows all is_added:false; connector.active returns []), matching the documented capabili. Re-check before relying on it.

### `connector.query.status`

Run: `mammoth connector query status`. Exact input fields: `mammoth schema get connector.query.status`.

Example: `mammoth connector query status postgres prod-warehouse`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ConnectorQueryStatusResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — blocked_missing_fixture: No real connector connection exists in workspace 4 (connector list shows all is_added:false; connector active returns []) and creating one requires externa. Re-check before relying on it.
