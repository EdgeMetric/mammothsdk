# Views Reference

The `View` class is the central interface for data transformations in the Mammoth SDK. It wraps a single dataview and provides 25+ transformation methods, data access, pipeline management, and export helpers.

## Getting a View

Views are created via `client.views.get()` -- not instantiated directly:

```python
from mammoth import MammothClient

client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(10)

view = client.views.get(1039)
```

You can also list, create, and delete views:

```python
# List all views in the project
views = client.views.list()

# Create a new view
view = client.views.create(dataset_id=42, name="My Analysis")

# Create by cloning
view = client.views.create(dataset_id=42, name="Copy", clone_from=1039)
```

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `int` | Dataview ID |
| `name` | `str` | Dataview display name |
| `dataset_id` | `int` | Parent dataset ID |
| `columns` | `dict[str, str]` | Mapping of display names to internal names |
| `display_names` | `list[str]` | Ordered list of column display names |
| `column_types` | `dict[str, str]` | Mapping of display names to types (`TEXT`, `NUMERIC`, `DATE`) |
| `raw` | `dict` | Full raw API response dict |
| `export` | `ViewExport` | Export helper (see [Exports](exports.md)) |

After every transformation, `display_names`, `columns`, and `column_types` are automatically refreshed — including columns added by pipeline tasks (`math`, `set_values`, `add_column`, etc.).

```python
view = client.views.get(1039)

print(view.id)             # 1039
print(view.name)           # "Sales Data"
print(view.display_names)  # ["Sales", "Region", "Date"]
print(view.columns)        # {"Sales": "column_1", "Region": "column_2", ...}
print(view.column_types)   # {"Sales": "NUMERIC", "Region": "TEXT", "Date": "DATE"}

# After a transform, new columns appear immediately:
view.math("Sales * 1.1", new_column="Revenue")
print("Revenue" in view.display_names)   # True
```

## Draft mode

By default, each transformation triggers an immediate pipeline run (auto-run mode). For large datasets or multi-step workflows, use **draft mode** to queue tasks and run the pipeline once.

### draft() (context manager)

The recommended approach. Enters draft mode on entry, submits and runs on clean exit, discards on exception:

```python
with view.draft():
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.math("Price * 2", new_column="Double")
    view.add_column("Notes")
# Pipeline runs once for all 3 tasks, metadata refreshed
```

If an exception occurs inside the block, all queued tasks are discarded:

```python
try:
    with view.draft():
        view.add_column("Temp")
        raise ValueError("something went wrong")
except ValueError:
    pass  # "Temp" column was NOT added — draft was discarded
```

### Explicit draft workflow

```python
view.enter_draft_mode()
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
view.math("Price * 2", new_column="Double")
view.submit_draft()  # pipeline runs once, metadata refreshed
```

---

## Full API Reference

::: mammoth.view.View
    options:
      members:
        - data
        - refresh
        - get_metadata
        - list_tasks
        - delete_task
        - preview_task
        - get_column_mapping
        - draft
        - enter_draft_mode
        - submit_draft
        - discard_draft
        - set_auto_run
        - is_draft_mode
        - branch_out
        - filter_rows
        - set_values
        - math
        - join
        - pivot
        - window
        - crosstab
        - add_column
        - delete_columns
        - copy_columns
        - combine_columns
        - convert_type
        - text_transform
        - replace_values
        - bulk_replace
        - split_column
        - substring
        - extract_date
        - date_diff
        - increment_date
        - fill_missing
        - limit_rows
        - discard_duplicates
        - unnest
        - lookup
        - json_extract
        - gen_ai
        - generate_sql
        - add_sql

---

## Exports

Export operations are accessed via `view.export`. See the [Exports reference](exports.md) for full documentation.

```python
view.export.to_csv("output.csv")
view.export.to_s3(file_name="report.csv")
view.export.to_postgres(host="...", port=5432, database="...", table="...", username="...", password="...")
view.branch_out(dest_dataset_id=42)
```

## See also

- [Conditions](conditions.md) -- filter builder
- [Enums](enums.md) -- all parameter enums
- [Exports](exports.md) -- export destinations
- [Transformation examples](../examples/transformations.md) -- practical workflows
