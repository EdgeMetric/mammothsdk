# Jobs, draft mode, and bulk replace

## Jobs
A command's `wait_policy` (visible via `mammoth schema get`) determines what
happens with the job, so you do not have to guess:

- `always_wait` and `start_or_wait` commands resolve the job for you and return
  the final result. You do NOT wait manually. A `view transform` success
  envelope still shows the submit record (`"status": "processing"`,
  `future_id`): the pipeline has already finished when it returns, so do not
  poll that `future_id`; verify with `view data get`.
- Only a `returns_job` command normally needs you to wait on the job id
  explicitly:
  ```bash
  mammoth job wait 55123
  mammoth job get 55123
  ```

When a known job times out, exit code 7 includes `recovery_commands` to fetch
or wait that job — inspect it rather than submitting the original mutation.
The `--job-timeout` /
`--pipeline-timeout` options bound the wait.

A transport failure during a mutation without a confirmed job/resource handle
is `outcome_unknown`. Re-read the exact target and scope before replaying it;
the operation may already have committed.

## Draft mode
Batch several pipeline edits, then submit them together:
```bash
mammoth view draft enter 1039 --project 180
mammoth view transform add-column 1039 --project 180 \
  --input '{"name": "flag", "column_type": "TEXT"}'
mammoth view draft status 1039 --project 180
mammoth view draft submit 1039 --project 180
# or discard the batch
mammoth view draft discard 1039 --project 180 --yes
```
Draft state is server-side, so it persists across separate CLI processes.
Do not put a value-changing step you have not yet verified into a draft: a
draft is read back once, after submit, and a uniform result then has every
batched task as a suspect. If you do batch, run `view task list VIEW_ID`
after `draft submit` and read the data back once per task, in order.
(The example above omits `dataset_id`; every real `view transform` and
`view draft` call needs it in `--input`.)

## Bulk replace
Bulk replace is a reversible pipeline mutation; it needs no `--yes`. Preview or
re-run through the pipeline commands rather than simulating a dry run.
