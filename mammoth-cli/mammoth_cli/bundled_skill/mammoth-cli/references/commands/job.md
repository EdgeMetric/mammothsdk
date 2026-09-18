# `job` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `job.get`

Run: `mammoth job get`. Exact input fields: `mammoth schema get job.get --output json --no-input`.

Example: `mammoth job get 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `JobGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 job.get read of observed job158 returned terminal success and 9 structured suggestions; bounded to one observed job and not Full.

### `job.get-many`

Run: `mammoth job get-many`. Exact input fields: `mammoth schema get job.get-many --output json --no-input`.

Example: `mammoth job get-many --input '{"job_ids": [1]}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `JobGetManyResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 job.get-many read of observed job158 returned terminal success and 9 structured suggestions; bounded to one observed job and not Full.

### `job.wait`

Run: `mammoth job wait`. Exact input fields: `mammoth schema get job.wait --output json --no-input`.

Example: `mammoth job wait 123 --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `JobWaitResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `job.wait-many`

Run: `mammoth job wait-many`. Exact input fields: `mammoth schema get job.wait-many --output json --no-input`.

Example: `mammoth job wait-many --input '{"job_ids": [1]}' --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `JobWaitManyResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.
