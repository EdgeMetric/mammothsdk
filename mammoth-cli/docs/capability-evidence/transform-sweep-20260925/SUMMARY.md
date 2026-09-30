# Live sweep of every `view transform` command (2026-09-25)

CLI 2.0.40 (source), SDK 0.7.18 (source), release workspace 4, throwaway
project `cli-transform-sweep-27700` (deleted afterwards). Fixture:
`fixture.csv` (7 synthetic rows: text, numbers, ISO dates, a pipe list, a
JSON object, blanks, one duplicate row) and the two-file eval data
(`evals/two-files-dashboard/data`) for lookup and join.

Each of the 32 commands ran once and was read back with `view data get`
(or `view get` for types and display properties) against a known answer.
`results.jsonl` holds the input, the observed values and notes.

Result: 32 of 32 work. Four findings, fixed in 2.0.40 / SDK 0.7.18:

- `convert-type` to the type a column already has put the pipeline in
  `ref_error`; every read failed until the task was removed. Uploads type
  numbers and ISO dates on their own. The CLI now skips those entries.
- The `pipeline_reference_error` recovery command lacked the dataset, so it
  fell back to project discovery (`/browse`, 502 during a release outage).
  It now carries `--input '{"dataset_id": N}'`.
- `fill-missing` directions were documented the wrong way round:
  `FIRST_VALUE` takes the previous row's value (forward fill), `LAST_VALUE`
  the next row's (back-fill). Docs fixed in the SDK and the skill.
- `generate-sql` writes and validates a query but adds no task. The CLI
  result now says `applied: false` and gives the `add-sql` command.

Not covered: condition variants, every enum value, error paths, large
views. `increment-date` shows a new DATE column as `31-Jan-2026`.
