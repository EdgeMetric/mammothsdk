# Structured input

Drive multi-field commands with one strict document instead of many flags.

```bash
mammoth folder create --project 180 \
  --input '{"name": "Reports", "parent_resource_id": "r_root"}'

mammoth view transform filter 1039 --project 180 \
  --input '{"condition": {"and": [{"column": "Order Status", "operator": "EQ", "value": "Open"}, {"column": "Customer Age", "operator": "GT", "value": 30}]}}'
```

- `--input FILE` (or `--input @FILE`) reads a JSON or YAML file; the format
  is inferred from the extension.
- `--input -` reads stdin; then `--input-format json|yaml` is required.
- `--dry-run` admits and resolves the document, then reports the SDK call
  instead of making it ([safety](safety.md)).
- The top level must be a mapping. A bad path, format, or shape fails with exit
  code 2 and a stable error code.
- Column references use display names returned by the exact view schema. Do not
  manufacture or copy backend/internal column identifiers. Pass explicit
  workspace/project/dataset/view parent IDs when the schema provides them.

## Condition specs
A `condition` field is a mapping:
- leaf: `{"column": ..., "operator": ..., "value": ...}` (plus optional
  `case_sensitive`, `value_is_column`, `component`, `truncate`).
- compound: `{"and": [spec, ...]}` or `{"or": [spec, ...]}`.
- negation: `{"not": spec}`.

Operators: `EQ NE GT GTE LT LTE IN_LIST NOT_IN_LIST IN_RANGE CONTAINS
NOT_CONTAINS ICONTAINS STARTS_WITH ENDS_WITH NOT_STARTS_WITH NOT_ENDS_WITH
IS_EMPTY IS_NOT_EMPTY IS_MAXVAL IS_NOT_MAXVAL IS_MINVAL IS_NOT_MINVAL`. The
symbols `= == != <> > >= < <=` are accepted as aliases for the first six;
anything else fails with `invalid_condition` before any request is sent.
`IS_EMPTY` / `IS_NOT_EMPTY` take no `value`; `IN_LIST` takes a list;
`IN_RANGE` takes `[low, high]`.

## Enum cheat sheet for the common transforms

| Command | Field | Values |
|---|---|---|
| `view transform filter` | `filter_type` | `SHOW` (keep matches, default), `REMOVE` |
| `view transform text` | `case` | `UPPER`, `LOWER`, `TITLE`; `trim`: true/false |
| `view transform convert-type` | `conversions[].to` | `TEXT`, `NUMERIC`, `DATE` |
| `view transform fill-missing` | `direction` | `LAST_VALUE` (forward fill), `FIRST_VALUE` |
| `view transform join` | `join_type` | `INNER`, `LEFT`, `RIGHT`, `OUTER` |
| `view transform set-values` | `column_type` (new column) | `TEXT`, `NUMERIC`, `DATE` |

Confirm any value you are unsure of with `schema get COMMAND_ID`; the
`input_schema` lists the enum.
