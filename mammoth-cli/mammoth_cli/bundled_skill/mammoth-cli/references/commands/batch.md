# `batch` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `batch.bulk-delete`

Run: `mammoth batch bulk-delete`. Exact input fields: `mammoth schema get batch.bulk-delete --output json --no-input`.

Example: `mammoth batch bulk-delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `BatchBulkDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Without --yes returned confirmation_required (exit 2) as expected. With --yes returned {job_id:304}. Note: file upload with append_to_ds_id=49 returned dataset_id:50 in its response, but dataset 50 re…

### `batch.create`

Run: `mammoth batch create`. Exact input fields: `mammoth schema get batch.create --output json --no-input`.

Example: `mammoth batch create 123 123 --input '{"mapping": [{"source_c_name": "column_1", "destination_c_name": "column_1", "expected_destination_c_type": "TEXT"}]}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BatchCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`.

Status on release: CLI defect fixed, untried since — CLI defect fixed in 2.0.16 (mapping items carry expected_destination_c_type (TEXT|NUMERIC|DATE); the {src: dst} shortcut stamps a default and the example shows the full item); not re-verified live yet. re-verification 2026-09-18 (2.0.16 fixes) observed not_re…

### `batch.create-spec`

Run: `mammoth batch create-spec`. Exact input fields: `mammoth schema get batch.create-spec --output json --no-input`.

Example: `mammoth batch create-spec 123 --input '{"file_id": 94}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BatchCreateSpecResult`; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`.

Status on release: untried; no live run recorded.

### `batch.delete`

Run: `mammoth batch delete`. Exact input fields: `mammoth schema get batch.delete --output json --no-input`.

Example: `mammoth batch delete 123 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `BatchDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `returns_job`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. First call without --yes correctly returned confirmation_required (exit 2). With --yes returned {job_id:301}. Single invocation only.

### `batch.get`

Run: `mammoth batch get`. Exact input fields: `mammoth schema get batch.get --output json --no-input`.

Example: `mammoth batch get 123 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BatchGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 batch get succeeded for an ID observed from retained dataset 29. One observed-ID chain; not Full.

### `batch.list`

Run: `mammoth batch list`. Exact input fields: `mammoth schema get batch.list --output json --no-input`.

Example: `mammoth batch list 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BatchListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.5 — Partial bounded release evidence: retained 1.1.5 response reports 1 batch with 51 rows; independent public-fixture oracle matches 51 rows; no Full claim.

### `batch.update`

Run: `mammoth batch update`. Exact input fields: `mammoth schema get batch.update --output json --no-input`.

Example: `mammoth batch update 123 --input '{"patch": [{"sample_key": "Status"}]}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `BatchUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 2 on release with CLI 2.0.15. Fix held: SDK-side argument rejection surfaced as invalid_arguments with a clear SDK message instead of an empty api_error: {"error":{"code":"invalid_arguments","message":"Each patch op must have…
