# Typed transformations and drafts

```bash
mammoth schema find "convert type" --output json --no-input
mammoth schema find "duplicate" --output json --no-input
mammoth schema find "fill missing" --output json --no-input
mammoth schema find "join" --output json --no-input
mammoth schema get view.transform.join --output json --no-input
mammoth view transform OPERATION VIEW_ID --project PROJECT_ID --input INPUT_JSON --output json --no-input
```

Every `view transform *` and `view draft *` mutation needs the exact parent
dataset: put `"dataset_id": DATASET_ID` in `--input` (these commands take no
DATASET_ID positional). Without it the command fails closed with
`missing_argument`; it never falls back to project-wide discovery, which on
large projects browses every folder and can 500 or miss the view. Get the
parent from `view list DATASET_ID` (you already know it after upload) or
`view get VIEW_ID` (a read, which may discover it).

Prefer typed operations such as convert-type, fill-missing, replace, join,
lookup, filter and math only when the live schema
lists them. Pick the operation by what it does, not by its name:

- `fill-missing` copies the previous/next row's value into blanks
  (`direction` = `LAST_VALUE` forward-fill or `FIRST_VALUE`). It cannot write a
  literal. To fill blanks with a constant (for example `0`), use `set-values`
  on the existing column with an `IS_EMPTY` condition:

```bash
mammoth view transform set-values VIEW_ID --project PROJECT_ID \
  --input '{"dataset_id":DATASET_ID,"existing_column":"revenue","values":[{"value":0}],"condition":{"column":"revenue","operator":"IS_EMPTY"}}' \
  --output json --no-input
```

- `filter` keeps matching rows by default (`filter_type: "SHOW"`); to drop
  rows, say so: `{"condition":{"column":"units","operator":"LT","value":0},"filter_type":"REMOVE"}`. For each operation, a successful result should contain a returned
task/job reference or updated view envelope; then verify with `view task list`,
`view task get`, `view pipeline items`, or preview according to its schema.

These examples use the released route IDs and input shapes documented by the
command manifest; substitute only observed view IDs and display names:

```bash
mammoth schema get view.transform.convert-type --output json --no-input
mammoth view transform convert-type VIEW_ID --project PROJECT_ID \
  --input '{"dataset_id":DATASET_ID,"conversions":[{"column":"Amount","to":"NUMERIC"}]}' \
  --output json --no-input
mammoth schema get view.transform.math --output json --no-input
mammoth view transform math VIEW_ID --project PROJECT_ID \
  --input '{"dataset_id":DATASET_ID,"expression":"GDP / Population","new_column":"GDP per capita"}' \
  --output json --no-input
```

The released catalog exposes typed dedupe through `schema find duplicate` as
`view.transform.discard-duplicates`. Inspect its optional `ignore_columns`
field before submitting. For a join, verify both schemas and
expected multiplicity:

```bash
mammoth schema get view.transform.discard-duplicates --output json --no-input
mammoth view transform discard-duplicates VIEW_ID --project PROJECT_ID \
  --input '{"dataset_id":DATASET_ID,"ignore_columns":["ID"]}' --output json --no-input
mammoth schema get view.transform.join --output json --no-input
mammoth view transform join VIEW_ID --project PROJECT_ID --input INPUT_JSON --output json --no-input
```

Reject malformed fields with the structured error envelope and stop rather than
guessing names. Verify exact display names, join multiplicity, math values and
remote task/pipeline readback. Draft submit is not proof all tasks persisted:
discover draft enter/status/submit/discard schemas and reconcile IDs/parents.
