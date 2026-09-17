# Typed transformations and drafts

```bash
mammoth schema find "convert type duplicate join math" --output json --no-input
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
  --input '{"expression":"GDP / Population"}' \
  --output json --no-input
```

The released manifest includes a typed dedupe route even when broad
`schema find duplicate` searches fail to surface it. Use the exact route and
inspect its optional key/retention fields before submitting. For a join, verify
both schemas and expected multiplicity:

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
