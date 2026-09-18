# Typed ETL discovery

There is no pipeline union or append transform. `join` and `lookup` are the
typed routes for combining views; neither appends rows across two views.
Appending rows is a dataset-level operation: upload into the existing dataset
with `mammoth file upload FILE --project PROJECT_ID --input
'{"append_to_ds_id": DATASET_ID}' --output json --no-input`. Confirm the exact
field name first with `mammoth schema get file.upload --output json
--no-input`; do not guess a `union`/`append` command id.

Start with typed transforms rather than raw `view task` payloads:

```bash
mammoth schema get view.transform.filter --output json --no-input
mammoth schema get view.transform.join --output json --no-input
mammoth schema get view.transform.math --output json --no-input
```

Use each returned `input_schema` and runnable example to build the request.
`view task add`, `view task preview`, and `view task update` remain available
for experts, but their `task_spec` nested shape is opaque: inspect
`contract_level` and do not treat those routes as autonomous/self-disclosing.
