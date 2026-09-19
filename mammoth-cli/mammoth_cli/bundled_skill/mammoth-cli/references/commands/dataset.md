# `dataset` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `dataset.batch-data`

Run: `mammoth dataset batch-data`. Exact input fields: `mammoth schema get dataset.batch-data`.

Example: `mammoth dataset batch-data 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DatasetBatchDataResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 batch-data read succeeded for an ID observed from retained dataset 29; bounded 50-row page. One observed-ID chain and page; not Full.

### `dataset.bulk-delete`

Run: `mammoth dataset bulk-delete`. Exact input fields: `mammoth schema get dataset.bulk-delete`.

Example: `mammoth dataset bulk-delete --input '{"dataset_ids": [456, 457]}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `DatasetBulkDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: dataset_ids accepted as required list, no confirm-name issue blocked us, --yes sufficed. Response: {"data":null}. Reconciled: `dataset list --project 23` returned empty datasets array im…

### `dataset.bulk-update`

Run: `mammoth dataset bulk-update`. Exact input fields: `mammoth schema get dataset.bulk-update`.

Example: `mammoth dataset bulk-update --input '{"patch_data": {"sample_key": "Status"}}'`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B07 DATASET_PATCH_UNTYPED]; reserved, not registered.

### `dataset.create`

Run: `mammoth dataset create`. Exact input fields: `mammoth schema get dataset.create`.

Example: `mammoth dataset create --input '{"dataset_spec": {"url": "https://sampledata.mammoth.io/Multi-Store_Retail_Sales.csv"}, "ds_creation_type": "weburl"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DatasetCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 1.1.9 — Bounded owned-fixture create succeeded with pinned CLI 1.1.9 using the documented weburl variant (ds_creation_type=weburl + dataset_spec.url): dataset 16 returned ready with job 39. No Full claim: other creation variants and broader lifecycle/error coverage a…

### `dataset.create-from-pdf`

Run: `mammoth dataset create-from-pdf`. Exact input fields: `mammoth schema get dataset.create-from-pdf`.

Example: `mammoth dataset create-from-pdf 123 --input '{"file_name": "./sales.csv"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DatasetCreateFromPdfResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend: POST /workspaces/4/projects/24/datasets-from-pdf. Re-check before relying on it.

### `dataset.data`

Run: `mammoth dataset data`. Exact input fields: `mammoth schema get dataset.data`.

Example: `mammoth dataset data 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DatasetDataResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 1.1.10 — Bounded retained-resource read with published CLI 1.1.10 and explicit timeout=30,poll_interval=1 returned 100 rows and five headers for dataset 28. No Full claim: retained ETL-owned resource and no option/error/lifecycle matrix beyond this read.

### `dataset.delete`

Run: `mammoth dataset delete`. Exact input fields: `mammoth schema get dataset.delete`.

Example: `mammoth dataset delete 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DatasetDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted dataset 85 (main fixture.csv/view 106) after get-back confirmed id/name. Single invocation only.

### `dataset.file-settings.get`

Run: `mammoth dataset file-settings get`. Exact input fields: `mammoth schema get dataset.file-settings.get`.

Example: `mammoth dataset file-settings get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DatasetFileSettingsGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Read parse info (delimiter, header, ambiguous dates) for dataset 85. Single invocation only.

### `dataset.file-settings.undo`

Run: `mammoth dataset file-settings undo`. Exact input fields: `mammoth schema get dataset.file-settings.undo`.

Example: `mammoth dataset file-settings undo 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DatasetFileSettingsUndoResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: 200 non-object body reported as success. Response: {"data":{"response":null,"status_code":200}}. Preceded by dataset.file-settings.update on dataset 53 to give the undo something to reve…

### `dataset.file-settings.update`

Run: `mammoth dataset file-settings update`. Exact input fields: `mammoth schema get dataset.file-settings.update`.

Example: `mammoth dataset file-settings update 123 --input '{"delimiter": "sample", "has_header": true, "initial_skip_count": 1, "quotechar": "sample"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DatasetFileSettingsUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Confirmed settings for dataset 87; reached status=ready. Single invocation only.

### `dataset.find`

Run: `mammoth dataset find`. Exact input fields: `mammoth schema get dataset.find`.

Example: `mammoth dataset find sales`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DatasetFindResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dataset.get`

Run: `mammoth dataset get`. Exact input fields: `mammoth schema get dataset.get`.

Example: `mammoth dataset get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DatasetGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — golden-data check 2026-09-19: exit 0 on release with CLI 2.0.18. Single invocation only.

### `dataset.list`

Run: `mammoth dataset list`. Exact input fields: `mammoth schema get dataset.list`.

Example: `mammoth dataset list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DatasetListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.28 — ILG simulation 2026-09-19: exit 0 on release with CLI 2.0.28. Listed the datasets the sends created in the target project. Single invocation only.

### `dataset.rename`

Run: `mammoth dataset rename`. Exact input fields: `mammoth schema get dataset.rename`.

Example: `mammoth dataset rename 123 --input '{"name": "Revenue report"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DatasetRenameResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dataset.restore`

Run: `mammoth dataset restore`. Exact input fields: `mammoth schema get dataset.restore`.

Example: `mammoth dataset restore 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DatasetRestoreResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. job 312 restore_datasource -> status success. dataset list --project 21 confirms dataset 49 (name 'stores.csv 2') is back and visible alongside 48. Single invocation only.

### `dataset.trash`

Run: `mammoth dataset trash`. Exact input fields: `mammoth schema get dataset.trash`.

Example: `mammoth dataset trash 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DatasetTrashResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.13 — Haiku e2e 2026-09-18: dataset trash then delete for owned datasets 44-47; final dataset list showed only the baseline ids. Single path only.

### `dataset.update`

Run: `mammoth dataset update`. Exact input fields: `mammoth schema get dataset.update`.

Example: `mammoth dataset update --input '{"patch_data": [{"sample_key": "Status"}]}'`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B07 DATASET_PATCH_UNTYPED]: raw patch operations include rename/refresh/column changes/reattach/deletion; do not dispatch them. Use dataset.rename or dataset.file-settings.update for their typed variants. The pinned SDK has no public binding for the singular UpdateDataset route, so its other OpenAPI patch variants remain unavailable until a typed SDK contract exists.
