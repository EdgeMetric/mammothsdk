# Typed transformations and drafts

```bash
mammoth schema find "convert type" --output json --no-input
mammoth schema find "duplicate" --output json --no-input
mammoth schema find "fill missing" --output json --no-input
mammoth schema find "join" --output json --no-input
mammoth schema get view.transform.join --output json --no-input
mammoth view transform OPERATION VIEW_ID --project PROJECT_ID --input INPUT_JSON --output json --no-input
```

Prefer typed operations such as convert-type, fill-missing, replace, join,
lookup, filter and math only when the live schema
lists them. For each operation, a successful result should contain a returned
task/job reference or updated view envelope; then verify with `view task list`,
`view task get`, `view pipeline items`, or preview according to its schema.

These examples use the released route IDs and input shapes documented by the
command manifest; substitute only observed view IDs and display names:

```bash
mammoth schema get view.transform.convert-type --output json --no-input
mammoth view transform convert-type VIEW_ID --project PROJECT_ID \
  --input '{"conversions":[{"column":"Amount","to":"NUMERIC"}]}' \
  --output json --no-input
mammoth schema get view.transform.math --output json --no-input
mammoth view transform math VIEW_ID --project PROJECT_ID \
  --input '{"expression":"GDP / Population","new_column":"GDP per capita"}' \
  --output json --no-input
```

The released catalog exposes typed dedupe through `schema find duplicate` as
`view.transform.discard-duplicates`. Inspect its optional `ignore_columns` and
`dataset_id` fields before submitting. For a join, verify both schemas and
expected multiplicity:

```bash
mammoth schema get view.transform.discard-duplicates --output json --no-input
mammoth view transform discard-duplicates VIEW_ID --project PROJECT_ID \
  --input '{"ignore_columns":["ID"]}' --output json --no-input
mammoth schema get view.transform.join --output json --no-input
mammoth view transform join VIEW_ID --project PROJECT_ID --input INPUT_JSON --output json --no-input
```

Reject malformed fields with the structured error envelope and stop rather than
guessing names. Verify exact display names, join multiplicity, math values and
remote task/pipeline readback. Draft submit is not proof all tasks persisted:
discover draft enter/status/submit/discard schemas and reconcile IDs/parents.
