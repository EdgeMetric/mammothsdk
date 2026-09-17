# `job` commands

### `job.get`

Run: `mammoth job get`. Exact input fields: `mammoth schema get job.get --output json --no-input`.

Example: `mammoth job get 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `JobGetResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `job.get-many`

Run: `mammoth job get-many`. Exact input fields: `mammoth schema get job.get-many --output json --no-input`.

Example: `mammoth job get-many --input '{"job_ids": [1]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `JobGetManyResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `job.wait`

Run: `mammoth job wait`. Exact input fields: `mammoth schema get job.wait --output json --no-input`.

Example: `mammoth job wait 123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `JobWaitResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `job.wait-many`

Run: `mammoth job wait-many`. Exact input fields: `mammoth schema get job.wait-many --output json --no-input`.

Example: `mammoth job wait-many --input '{"job_ids": [1]}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `JobWaitManyResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `always_wait`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
