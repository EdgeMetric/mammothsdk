# Typed ETL discovery

For union/append and how to combine or append across views, see
[operations](../operations.md).

Start with typed transforms rather than raw `view task` payloads:

```bash
mammoth schema get view.transform.filter
mammoth schema get view.transform.join
mammoth schema get view.transform.math
```

Use each returned `input_schema` and runnable example to build the request.
`view task add`, `view task preview`, and `view task update` remain available
for experts, but their `task_spec` nested shape is opaque: inspect
`contract_level` and do not treat those routes as autonomous/self-disclosing.
