# Datasets stuck in `need_action` after upload

A freshly uploaded file can land in `status: "need_action"` with
`status_info.need_action` = "We need your input before we process this file".
No views exist yet and transforms cannot start. This is not a UI-only step:
the CLI resolves it. Do not hand it to the operator unless the settings read
below is itself ambiguous.

The usual cause is a CSV whose date column is ambiguous (`01/02/2023` can be
US or UK). `dataset file-settings get` then reports `has_ambiguous_dates: true`
and `date_format: null`.

```bash
mammoth dataset get DATASET_ID --project PROJECT_ID
mammoth dataset file-settings get DATASET_ID --project PROJECT_ID
mammoth schema get dataset.file-settings.update
```

Read the detected `delimiter`, `has_header`, `initial_skip_count`, and
`quotechar` from the `file-settings get` response and send them back
unchanged, adding the one decision the platform is waiting for. For
ambiguous dates that is `date_format` (`"US"` or `"UK"`); decide it from the
task or the data itself (a day value above 12 settles it), and ask the
operator only when neither does.

```bash
mammoth dataset file-settings update DATASET_ID --project PROJECT_ID \
  --input '{"delimiter": ",", "has_header": true, "initial_skip_count": 0, "quotechar": "\"", "date_format": "US"}'
```

The response is a job (`operation: "understand_csv"`). Run
`mammoth job wait JOB_ID` on its `job_id` instead of polling by hand, then
read `dataset get` once (the record is under `data.dataset`, so read
`data.dataset.status`) to confirm the status left `need_action`. It usually
reaches `ready` within seconds; on prague an ISO `YYYY-MM-DD` column was
flagged ambiguous and took about three minutes, so allow up to five minutes
before treating it as stuck.
Then `view list` returns the generated view and typed transforms can
proceed. Every environment can ask, release included: on 2026-09-24 release
flagged an ISO `YYYY-MM-DD` column too and reached `ready` within seconds of
the update. If the status becomes `error`, read `status_info` and stop; do
not retry with guessed settings.

## All-text CSV: ingested, but no view

A CSV whose columns are all text (ids, names, regions, no number or date)
comes back `status: "ready"` with `status_info.ready` = "This file has more
than one plausible way to be read." The rows are ingested (`dataset get`
shows `stats.row_count`), but the platform creates no view. This is not a
parsing question: confirming file settings does not create a view.
`file upload` reports it as `status: "needs_view"` with this `next_command`:

```bash
mammoth view create DATASET_ID --project PROJECT_ID
mammoth view list DATASET_ID --project PROJECT_ID    # the new view, row_count set
```

The new view is ready at once and takes transforms like any other (verified
on release, 2026-09-24). Run `view create` only when `view list DATASET_ID`
is empty, so that a retry does not add a second view.

## A pasted link to a file with "Unstructured rows"

`mammoth project needs-attention --project PROJECT_ID` lists it as a
`needs_input` row with `action: "unstructured_rows"` and the `dataset_id`.
The Monitor panel lists this as **Unstructured rows** ("header and data rows
need mapping"): some lines of an uploaded file did not fit the dataset's
columns and were set aside, so the dataset waits for a person. Turn the pasted
address into ids first; it makes no request:

```bash
mammoth link 'https://app.mammoth.io/workspaces/1/projects/2/data/folders/3?selectedResourceId=4'
```

The folder and `selected_resource_id` in a link are resource ids, not dataset
ids: find the dataset with `mammoth dataset find NAME`. Then read the set-aside
lines and why each one does not fit (the first 100, with `row_count` the total):

```bash
mammoth dataset broken-rows list DATASET_ID --project PROJECT_ID
```

Then fix them, with the user's confirmation. Take a line in after correcting
it so its column count matches, or discard it (discarded lines do not come
back; say so first). `batch_id` and `line_num` come from the list:

```bash
mammoth dataset broken-rows resolve DATASET_ID --project PROJECT_ID \
  --input '{"op": "remove", "batch_id": 7, "rows": [{"line_num": 4, "line": ""}]}'
mammoth job wait JOB_ID
mammoth dataset broken-rows list DATASET_ID --project PROJECT_ID   # row_count 0 = done
```

`op: "add"` takes the corrected `line` of each row in instead. The same step is
**Review & Fix** in the app. Do not tell the user to open the Monitor item's
link.
