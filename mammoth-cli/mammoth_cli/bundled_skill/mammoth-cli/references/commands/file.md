# `file` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `file.bulk-delete`

Run: `mammoth file bulk-delete`. Exact input fields: `mammoth schema get file.bulk-delete`.

Example: `mammoth file bulk-delete --input '{"file_ids": [1]}'`. Illustrative only: append `--yes` after observing an owned target.

Result: `FileBulkDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Without --yes returned confirmation_required as expected. With --yes: data:null, exit 0. Single invocation only.

### `file.delete`

Run: `mammoth file delete`. Exact input fields: `mammoth schema get file.delete`.

Example: `mammoth file delete 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `FileDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Response data:null but exit 0; verified via file list --project 21 that file 50 (sample.pdf) is gone (only 47,48 remain). Single invocation only.

### `file.extract-sheets`

Run: `mammoth file extract-sheets`. Exact input fields: `mammoth schema get file.extract-sheets`.

Example: `mammoth file extract-sheets 123 --input '{"sheets": ["sample"]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FileExtractSheetsResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `file.get`

Run: `mammoth file get`. Exact input fields: `mammoth schema get file.get`.

Example: `mammoth file get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FileGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 file get succeeded for an ID observed from the scoped file list. One observed-ID chain; not Full.

### `file.list`

Run: `mammoth file list`. Exact input fields: `mammoth schema get file.list`.

Example: `mammoth file list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FileListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI an earlier release — Bounded release read in project 3 succeeded; empty file list observed. No Full claim: no non-empty fixture.

### `file.set-password`

Run: `mammoth file set-password`. Exact input fields: `mammoth schema get file.set-password`.

Example: `mammoth file set-password 123 --input /private/path/request.json`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `FileSetPasswordResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `file.update`

Run: `mammoth file update`. Exact input fields: `mammoth schema get file.update`.

Example: `mammoth file update 123 --input '{"patch_request": {"patch": [{"op": "replace", "path": "extract_sheets", "value": "sample"}]}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FileUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — backend_error: CLI accepted the typed patch and submitted job 314 (handle_file on /workspaces/4/projects/21/files/50), then correctly reported timeout after 60s with recovery_comma. Re-check before relying on it.

### `file.upload`

Run: `mammoth file upload`. Exact input fields: `mammoth schema get file.upload`.

Example: `mammoth file upload ./sales.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FileUploadResult`; mutation `benign_mutation`, confirmation `none`, wait policy `start_or_wait`.

Status on release: ran once on CLI 2.0.21 — ergonomics sweep 2026-09-19: exit 0 on release with CLI 2.0.21. Uploaded smoke.csv -> dataset 94 ready; dataview 116 (3 rows). Second call with --input {"append_to_ds_id": 94} returned dataset 95 ready and view 116 row_count went 3 -> 6: append path works (th…

### `file.upload-folder`

Run: `mammoth file upload-folder`. Exact input fields: `mammoth schema get file.upload-folder`.

Example: `mammoth file upload-folder ./sales.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FileUploadFolderResult`; mutation `benign_mutation`, confirmation `none`, wait policy `start_or_wait`.

Status on release: untried; no live run recorded.
