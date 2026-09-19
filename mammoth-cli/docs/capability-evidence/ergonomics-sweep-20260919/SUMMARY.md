# Ergonomics sweep on release (CLI 2.0.21 working tree) — 2026-09-19

Run after the release outage (API tier unreachable ~09:00–11:45Z). Session
defaults only: `MAMMOTH_PROFILE=release`, no `--project`, `--output` or
`--no-input` on any call; the active project came from `project ensure`.

Owned projects: `CLI lean smoke 2021` (44), `2021b` (45), `2021c` (46) for
the lean-flow smoke and `CLI sweep 2021` (47) for the sweep; all four created
and deleted in this run. Fixtures inside them: datasets 91–96, dataviews
113–116, parameter 2, data check 5, dashboard 62, batch job 688. Project 3
and its datasets were read once (`view list 28 --project 3`) to learn the
live dataview record's key names; nothing there was mutated.

## Verdicts

| verdict | count |
|---|---|
| ok | 19 |
| ok_empty | 1 |
| backend_error | 7 |
| **total** | **27** |

## What changed since the 2.0.18 fixture sweep

- `file upload` with `append_to_ds_id` works (row_count 3 → 6); the raw
  ValueError is gone.
- `ai suggestion list` returns a suggestion.
- `batch create` is accepted when the source is a standalone dataset in the
  same project (the 2.0.18 500 used a non-dataset source); the job did not
  finish within the run.
- Still backend-side: `browse root/project` 500, `schedule *`
  NOT_IMPLEMENTED, `dashboard template create` 500, `view derivative create`
  500, `view data-check update` 500-after-applying, `ai sql generate`
  4DTVW029 on a fresh dataset.

## CLI defects found (fixed in 2.0.22)

- `parameter create` example used `param_type: "sample"`; backend accepts
  `NUMERIC|TEXT|DATE` (4PARM008).
- `view data-check create` example lacked `pinned_to_end: true`; backend
  requires `task_sequence` or `pinned_to_end` (4GENR007).
- `view data-check update` example used `op: replace` without a value; the
  schema's shape is `{op: command, path: enable|disable, value: null}`.
- `batch create` had no note that `SOURCE_ID` must be a standalone dataset.
