# Workflows: from a template or a description to a scheduled run

A workflow is a project's saved chain of tables, steps and results that Mammoth
runs on its own: on a clock, after another workflow, from a secret link, or on
demand. Build one from a ready-made catalog template, or describe it in words.
Each build adds the steps to a new workflow and waits for the Save that builds
them. Nothing runs on a schedule until you set a trigger.

## "I want to do <template>": from the catalog

1. `mammoth workflow template list` lists the catalog. Pick a `key`, for
   example `bank-reconciliation`. `mammoth schema find "<the job>"` finds it by
   words.
2. `mammoth workflow template fits` reads the project's tables and returns the
   templates they already fit, with the dataset filling each input. Use
   `--input '{"focus": DATASET_ID}'` for one table.
3. `mammoth workflow template get KEY` shows its inputs, roles and settings.
   `workflow template rank KEY` ranks other tables for one input.
4. `mammoth workflow template fit KEY --input '{"inputs": {"main": DATASET_ID}}'`
   proposes the column for every role.
5. `mammoth workflow template preview KEY --input '{"inputs": ..., "matches": ...}'`
   runs it on the first rows and runs its checks. Show the result before
   building.
6. `mammoth workflow template build KEY --input '{"inputs": ..., "matches": ...,
   "destination_name": "Bank reconciliation"}'` builds it and waits for the Save.
   The answer's `workflow.id` is the workflow.

No tables yet? `workflow template samples KEY` imports the template's sample
tables once, so it can be tried first.

## From a description

1. `mammoth workflow describe start --input '{"text": "Match Stripe payouts to
   the bank feed every Monday", "dataset_ids": [812, 815]}'` returns a `draft`.
2. `mammoth workflow describe wait DRAFT` waits for the read-back: its sentence,
   the tables it reads, its steps, its result on your rows, and at most two
   `asks`. When `template_key` is set, the catalog template is the better path.
3. To answer the asks, start again with the same text and
   `"answers": [{"question": ..., "answer": ...}]`.
4. `mammoth workflow describe build --input '{"spec": <read_back.spec>,
   "destination_name": "Payout matches", "schedule": {"frequency": "weekly",
   "by_week_day": ["mo"]}}'` builds it, sets the clock and waits for the Save.

## Run it and keep it running

| Goal | Command |
|---|---|
| Run now, and wait | `workflow run start WORKFLOW_ID --input '{"wait": true}'` |
| What ran, and how it ended | `workflow run list WORKFLOW_ID` |
| On a clock | `workflow schedule set WORKFLOW_ID --input '{"frequency": "daily"}'` |
| After another workflow | `workflow after set WORKFLOW_ID SOURCE_WORKFLOW_ID` |
| From another system | `workflow link create WORKFLOW_ID` (secret shown once), `workflow link remove` |
| Pause, resume, remove a clock | `automation pause / resume / delete AUTOMATION_ID` (the setter returns it) |

`workflow run start` never starts a workflow twice: while a run is in flight,
it answers `already_running: true` with that run's id. Verify each build with
`workflow get WORKFLOW_ID` and each run with `workflow run list`. To undo a
build, run `workflow delete WORKFLOW_ID`, or `workflow save-undo` for its Save.
