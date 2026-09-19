# `data-app` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `data-app.active-job`

Run: `mammoth data-app active-job`. Exact input fields: `mammoth schema get data-app.active-job`.

Example: `mammoth data-app active-job 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DataAppActiveJobResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `data-app.create`

Run: `mammoth data-app create`. Exact input fields: `mammoth schema get data-app.create`.

Example: `mammoth data-app create --input '{"body": {"automation_id": 1, "dashboard_ids": [1], "name": "Revenue report", "project_id": 1}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DataAppCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `data-app.delete`

Run: `mammoth data-app delete`. Exact input fields: `mammoth schema get data-app.delete`.

Example: `mammoth data-app delete 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DataAppDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `data-app.get`

Run: `mammoth data-app get`. Exact input fields: `mammoth schema get data-app.get`.

Example: `mammoth data-app get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DataAppGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `data-app.job`

Run: `mammoth data-app job`. Exact input fields: `mammoth schema get data-app.job`.

Example: `mammoth data-app job 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DataAppJobResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `data-app.list`

Run: `mammoth data-app list`. Exact input fields: `mammoth schema get data-app.list`.

Example: `mammoth data-app list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DataAppListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: data_apps. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `data-app.pipeline-changes`

Run: `mammoth data-app pipeline-changes`. Exact input fields: `mammoth schema get data-app.pipeline-changes`.

Example: `mammoth data-app pipeline-changes 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DataAppPipelineChangesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `data-app.share`

Run: `mammoth data-app share`. Exact input fields: `mammoth schema get data-app.share`.

Example: `mammoth data-app share 123 --input '{"body": {"params": {"auth": {"type_of_auth": "mammoth"}}}}' --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `DataAppShareResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `data-app.update`

Run: `mammoth data-app update`. Exact input fields: `mammoth schema get data-app.update`.

Example: `mammoth data-app update 123 --input '{"body": {"params": {"name": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DataAppUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `data-app.upload`

Run: `mammoth data-app upload`. Exact input fields: `mammoth schema get data-app.upload`.

Example: `mammoth data-app upload 123 ./sales.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DataAppUploadResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `data-app.user.list`

Run: `mammoth data-app user list`. Exact input fields: `mammoth schema get data-app.user.list`.

Example: `mammoth data-app user list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DataAppUserListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `data-app.user.remove`

Run: `mammoth data-app user remove`. Exact input fields: `mammoth schema get data-app.user.remove`.

Example: `mammoth data-app user remove 123 analyst@example.com`. Illustrative only: append `--yes` after observing an owned target.

Result: `DataAppUserRemoveResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.
