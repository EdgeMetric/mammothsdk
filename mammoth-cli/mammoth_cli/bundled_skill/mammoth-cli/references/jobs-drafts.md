# Jobs, draft mode, and bulk replace

## Jobs
Async operations return a job. Wait, then inspect:
```bash
mammoth job wait 55123 --output json --no-input
mammoth job get 55123 --output json --no-input
```
A timeout returns exit code 7 with `recovery_commands` that re-wait or fetch the
job. The `--job-timeout` / `--pipeline-timeout` options bound the wait.

## Draft mode
Batch several pipeline edits, then submit them together:
```bash
mammoth view draft enter 1039 --project 180 --output json --no-input
mammoth view transform add-column 1039 --project 180 --output json --no-input \
  --input '{"name": "flag", "column_type": "TEXT"}'
mammoth view draft status 1039 --project 180 --output json --no-input
mammoth view draft submit 1039 --project 180 --output json --no-input
# or discard the batch
mammoth view draft discard 1039 --project 180 --output json --no-input --yes
```
Draft state is server-side, so it persists across separate CLI processes.

## Bulk replace
Bulk replace is a reversible pipeline mutation; it needs no `--yes`. Preview or
re-run through the pipeline commands rather than simulating a dry run.
