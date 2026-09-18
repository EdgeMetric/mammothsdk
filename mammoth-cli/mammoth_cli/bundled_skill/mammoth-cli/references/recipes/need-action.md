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
mammoth dataset get DATASET_ID --project PROJECT_ID --output json --no-input
mammoth dataset file-settings get DATASET_ID --project PROJECT_ID --output json --no-input
mammoth schema get dataset.file-settings.update --output json --no-input
```

Read the detected `delimiter`, `has_header`, `initial_skip_count`, and
`quotechar` from the `file-settings get` response and send them back
unchanged, adding the one decision the platform is waiting for. For
ambiguous dates that is `date_format` (`"US"` or `"UK"`); decide it from the
task or the data itself (a day value above 12 settles it), and ask the
operator only when neither does.

```bash
mammoth dataset file-settings update DATASET_ID --project PROJECT_ID \
  --input '{"delimiter": ",", "has_header": true, "initial_skip_count": 0, "quotechar": "\"", "date_format": "US"}' \
  --output json --no-input
```

The response is a job (`operation: "understand_csv"`). Poll `dataset get`
until `status` leaves `need_action`; it normally reaches `ready` within a few
seconds, after which `view list` returns the generated view and typed
transforms can proceed. If the status becomes `error`, read `status_info`
and stop; do not retry with guessed settings.
