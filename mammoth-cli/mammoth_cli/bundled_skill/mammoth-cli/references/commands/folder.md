# `folder` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `folder.bulk-delete`

Run: `mammoth folder bulk-delete`. Exact input fields: `mammoth schema get folder.bulk-delete --output json --no-input`.

Example: `mammoth folder bulk-delete --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `FolderBulkDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Without --yes: confirmation_required. With --yes: data:null, exit 0. Verified via folder list --project 21: folders 10 and 11 no longer appear (only 7 and 8 remain, plus 9 already removed by folder.tr…

### `folder.create`

Run: `mammoth folder create`. Exact input fields: `mammoth schema get folder.create --output json --no-input`.

Example: `mammoth folder create 'Revenue report' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FolderCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.5 — Partial bounded release evidence: owned folder resource 10 was created ready and then cleaned; no Full claim.

### `folder.delete`

Run: `mammoth folder delete`. Exact input fields: `mammoth schema get folder.delete --output json --no-input`.

Example: `mammoth folder delete 123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Result: `FolderDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.5 — Partial bounded release evidence: owned folder resource 10 was deleted and final folder list returned empty; no Full claim.

### `folder.find`

Run: `mammoth folder find`. Exact input fields: `mammoth schema get folder.find --output json --no-input`.

Example: `mammoth folder find reports --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FolderFindResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `folder.get`

Run: `mammoth folder get`. Exact input fields: `mammoth schema get folder.get --output json --no-input`.

Example: `mammoth folder get 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FolderGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.12 — Full bounded support in approved release scope: public CLI 1.1.12 verified fields=__full, ready result state, wrong-project/missing-ID error envelopes, disposable create/read/update/delete lifecycle, filtered list option, and final absence readback. Row-level…

### `folder.list`

Run: `mammoth folder list`. Exact input fields: `mammoth schema get folder.list --output json --no-input`.

Example: `mammoth folder list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FolderListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI an earlier release — Partial bounded release evidence: retained 1.1.5 folder list and empty-baseline postcondition; no Full claim.

### `folder.move`

Run: `mammoth folder move`. Exact input fields: `mammoth schema get folder.move --output json --no-input`.

Example: `mammoth folder move --input '{"resource_ids": [8024], "target_folder_resource_id": "root"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FolderMoveResult`; mutation `benign_mutation`, confirmation `none`, wait policy `returns_job`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: SDK-built {patch:[{op:move,from:[ids],path:destination|root}]} body accepted; response: {"data":{"job_id":368,"failure_reason":null,"status_code":null}}. `job get 368` showed status:proc…

### `folder.root`

Run: `mammoth folder root`. Exact input fields: `mammoth schema get folder.root --output json --no-input`.

Example: `mammoth folder root --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FolderRootResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `folder.trash`

Run: `mammoth folder trash`. Exact input fields: `mammoth schema get folder.trash --output json --no-input`.

Example: `mammoth folder trash 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FolderTrashResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. job 320 trash_folder -> status success, response {folder_deleted:true, failed:[], succeeded:[]}. Single invocation only.

### `folder.update`

Run: `mammoth folder update`. Exact input fields: `mammoth schema get folder.update --output json --no-input`.

Example: `mammoth folder update 123 --input '{"name": "Revenue report"}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `FolderUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 typed folder rename succeeded for one owned folder and exact-ID readback confirmed the new name. Owned cleanup list matched baseline; post-delete get returned structured HTTP 400 with authoritative exit 1. One field and f…
