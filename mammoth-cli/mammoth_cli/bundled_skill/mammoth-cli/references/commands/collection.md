# `collection` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `collection.active-job`

Run: `mammoth collection active-job`. Exact input fields: `mammoth schema get collection.active-job`.

Example: `mammoth collection active-job 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CollectionActiveJobResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.activity`

Run: `mammoth collection activity`. Exact input fields: `mammoth schema get collection.activity`.

Example: `mammoth collection activity 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CollectionActivityResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.create`

Run: `mammoth collection create`. Exact input fields: `mammoth schema get collection.create`.

Example: `mammoth collection create --input '{"name": "Revenue report"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CollectionCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.dashboards.add`

Run: `mammoth collection dashboards add`. Exact input fields: `mammoth schema get collection.dashboards.add`.

Example: `mammoth collection dashboards add 123 --input '{"dashboard_ids": [1]}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `CollectionDashboardsAddResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.dashboards.remove`

Run: `mammoth collection dashboards remove`. Exact input fields: `mammoth schema get collection.dashboards.remove`.

Example: `mammoth collection dashboards remove 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `CollectionDashboardsRemoveResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.delete`

Run: `mammoth collection delete`. Exact input fields: `mammoth schema get collection.delete`.

Example: `mammoth collection delete 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `CollectionDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.files.upload`

Run: `mammoth collection files upload`. Exact input fields: `mammoth schema get collection.files.upload`.

Example: `mammoth collection files upload 123 --input '{"files": ["./sales.csv"]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CollectionFilesUploadResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.for-dashboard`

Run: `mammoth collection for-dashboard`. Exact input fields: `mammoth schema get collection.for-dashboard`.

Example: `mammoth collection for-dashboard 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CollectionForDashboardResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.get`

Run: `mammoth collection get`. Exact input fields: `mammoth schema get collection.get`.

Example: `mammoth collection get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CollectionGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.get-by-url`

Run: `mammoth collection get-by-url`. Exact input fields: `mammoth schema get collection.get-by-url`.

Example: `mammoth collection get-by-url https://example.com/data.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CollectionGetByUrlResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.job`

Run: `mammoth collection job`. Exact input fields: `mammoth schema get collection.job`.

Example: `mammoth collection job 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CollectionJobResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.list`

Run: `mammoth collection list`. Exact input fields: `mammoth schema get collection.list`.

Example: `mammoth collection list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CollectionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.members.remove`

Run: `mammoth collection members remove`. Exact input fields: `mammoth schema get collection.members.remove`.

Example: `mammoth collection members remove 123 --input '{"email": "analyst@example.com"}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `CollectionMembersRemoveResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.pipeline-changes`

Run: `mammoth collection pipeline-changes`. Exact input fields: `mammoth schema get collection.pipeline-changes`.

Example: `mammoth collection pipeline-changes 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CollectionPipelineChangesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.share`

Run: `mammoth collection share`. Exact input fields: `mammoth schema get collection.share`.

Example: `mammoth collection share 123 --input '{"emails": ["analyst@example.com"]}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `CollectionShareResult`; mutation `external_effect`, confirmation `yes_always`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `collection.update`

Run: `mammoth collection update`. Exact input fields: `mammoth schema get collection.update`.

Example: `mammoth collection update 123 --input '{"name": "Q3 pack"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `CollectionUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
