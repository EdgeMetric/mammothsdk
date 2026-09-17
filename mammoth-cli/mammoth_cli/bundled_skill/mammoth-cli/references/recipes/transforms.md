# Typed transformations and drafts

```bash
mammoth schema find "convert type duplicate join math" --output json --no-input
mammoth schema get view.transform.join --output json --no-input
mammoth view transform OPERATION VIEW_ID --project PROJECT_ID --input INPUT_JSON --output json --no-input
```

Prefer typed operations such as convert-type, fill-missing, replace,
discard-duplicates, join, lookup, filter and math only when the live schema
lists them. Verify exact display names, join multiplicity, math values and
remote task/pipeline readback. Draft submit is not proof all tasks persisted:
discover draft enter/status/submit/discard schemas and reconcile IDs/parents.
