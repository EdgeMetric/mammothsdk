# Structured input

Drive multi-field commands with one strict document instead of many flags.

```bash
mammoth folder create --project 180 --output json --no-input \
  --input '{"name": "Reports", "parent_resource_id": "r_root"}'

mammoth view transform filter 1039 --project 180 --output json --no-input \
  --input '{"condition": {"and": [{"column": "status", "operator": "=", "value": "open"}, {"column": "age", "operator": ">", "value": 30}]}}'
```

- `--input FILE` reads a JSON or YAML file; the format is inferred from the
  extension.
- `--input -` reads stdin; then `--input-format json|yaml` is required.
- The top level must be a mapping. A bad path, format, or shape fails with exit
  code 2 and a stable error code.

## Condition specs
A `condition` field is a mapping:
- leaf: `{"column": ..., "operator": ..., "value": ...}` (plus optional
  `case_sensitive`, `value_is_column`, `component`, `truncate`).
- compound: `{"and": [spec, ...]}` or `{"or": [spec, ...]}`.
- negation: `{"not": spec}`.
