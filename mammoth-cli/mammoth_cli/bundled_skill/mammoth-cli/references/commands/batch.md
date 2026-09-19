# `batch` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `batch.bulk-delete`

Run: `mammoth batch bulk-delete`. Exact input fields: `mammoth schema get batch.bulk-delete`.

Example: `mammoth batch bulk-delete 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `BatchBulkDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Without --yes returned confirmation_required (exit 2) as expected. With --yes returned {job_id:304}. Note: file upload with append_to_ds_id=49 returned dataset_id:50 in its response, but dataset 50 re…

### `batch.create`

Run: `mammoth batch create`. Exact input fields: `mammoth schema get batch.create`.

Example: `mammoth batch create 123 123 --input '{"mapping": [{"source_c_name": "column_1", "destination_c_name": "column_1", "expected_destination_c_type": "TEXT"}]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BatchCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`.

Status on release: ran once on CLI 2.0.21 — ergonomics sweep 2026-09-19: exit 0 on release with CLI 2.0.21. Accepted as job 688 (validate_append) when SOURCE_ID is a standalone dataset (96) in the same project; using the append child dataset 95 as source is 4BATC010 INVALID_SOURCE_DATASET. Job 688 was…

### `batch.create-spec`

Run: `mammoth batch create-spec`. Exact input fields: `mammoth schema get batch.create-spec`.

Example: `mammoth batch create-spec 123 --input '{"file_id": 94}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BatchCreateSpecResult`; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `batch.delete`

Run: `mammoth batch delete`. Exact input fields: `mammoth schema get batch.delete`.

Example: `mammoth batch delete 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `BatchDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `returns_job`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Deleted batch 90 (async job_id=612); read-back batch.list confirms 0 active batches. Single invocation only.

### `batch.get`

Run: `mammoth batch get`. Exact input fields: `mammoth schema get batch.get`.

Example: `mammoth batch get 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BatchGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Fetched batch 90 detail, matches list. Single invocation only.

### `batch.list`

Run: `mammoth batch list`. Exact input fields: `mammoth schema get batch.list`.

Example: `mammoth batch list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BatchListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.21 — ergonomics sweep 2026-09-19: exit 0 on release with CLI 2.0.21. active_batches 2: file batch 99 (3 rows) and combine_ds batch 101 from the append (3 rows). Single invocation only.

### `batch.update`

Run: `mammoth batch update`. Exact input fields: `mammoth schema get batch.update`.

Example: `mammoth batch update 123 --input '{"patch": [{"sample_key": "Status"}]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BatchUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 2 on release with CLI 2.0.15. Fix held: SDK-side argument rejection surfaced as invalid_arguments with a clear SDK message instead of an empty api_error: {"error":{"code":"invalid_arguments","message":"Each patch op must have…
