# Basic Usage Examples

Practical examples to get started with the Mammoth Python SDK.

## Client setup

```python
import os
from mammoth import MammothClient, parse_path

client = MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,
)
client.set_project_id(10)
```

## Parse a Mammoth URL

Extract IDs from a browser URL:

```python
from mammoth import parse_path

ids = parse_path("https://app.mammoth.io/#/workspaces/11/projects/10/views/1039")
print(ids)
# {"workspace_id": 11, "project_id": 10, "dataview_id": 1039}
```

## Upload files

```python
# Upload a single CSV file (returns dataset ID)
dataset_id = client.files.upload("sales_data.csv")

# Upload multiple files at once
dataset_ids = client.files.upload(["sales.csv", "customers.xlsx"])

# Upload all files in a folder
dataset_ids = client.files.upload_folder("./data/")

# After upload, get the view for the new dataset
views = client.views.list(dataset_id)
view = views[0]
print(view.display_names)
```

## List resources

```python
# List projects — returns envelope dict, unwrap "projects" key
resp = client.projects.list()
projects = resp["projects"]                 # list of plain dicts
for p in projects:
    print(p["id"], p["name"])               # dict access, NOT p.id / p.name

# List datasets
datasets = client.datasets.list()

# List views in a dataset
views = client.views.list(dataset_id=42)
for v in views:
    print(f"{v.id}: {v.name} ({len(v.display_names)} columns)")
```

## Get a View and inspect it

```python
view = client.views.get(1039)

print(f"Name: {view.name}")
print(f"Columns: {view.display_names}")
print(f"Types: {view.column_types}")
print(f"Column mapping: {view.columns}")
```

## Fetch data

```python
# First 100 rows
result = view.data(limit=100)

# Specific columns
result = view.data(columns=["Sales", "Region"], limit=50)

# With a condition
from mammoth import Condition, Operator
result = view.data(
    condition=Condition("Sales", Operator.GTE, 1000),
    limit=200,
)
```

## Apply a transformation

```python
from mammoth import Condition, Operator

view.filter_rows(Condition("Sales", Operator.GTE, 1000))
print(f"Columns after filter: {view.display_names}")
```

## Export to CSV

```python
path = view.export.to_csv("output.csv")
print(f"Saved to {path}")
```

## Context manager

```python
with MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,
) as client:
    client.set_project_id(10)
    view = client.views.get(1039)
    view.export.to_csv("output.csv")
# Session closed automatically
```

## Pipeline management

```python
# List tasks on a view
tasks = view.list_tasks()
for task in tasks:
    print(f"Task {task['id']}: {task.get('task_key', 'unknown')}")

# Delete a task
view.delete_task(task_id=42)

# Preview a task before applying
preview = view.preview_task({"SELECT": "ALL", "CONDITION": {...}})
```

## Create and clone views

```python
# Create a new empty view
new_view = client.views.create(dataset_id=42, name="My Analysis")

# Clone from an existing view
clone = client.views.create(dataset_id=42, name="Copy of Analysis", clone_from=1039)

# Delete a view
client.views.delete(view_id=new_view.id)
```

## Complete workflow

```python
import os
from mammoth import (
    MammothClient, Condition, Operator,
    ColumnType, SetValue, MammothAPIError,
)

def main():
    client = MammothClient(
        api_key=os.getenv("MAMMOTH_API_KEY"),
        api_secret=os.getenv("MAMMOTH_API_SECRET"),
        workspace_id=11,
    )
    client.set_project_id(10)

    try:
        view = client.views.get(1039)
        print(f"View: {view.name} ({len(view.display_names)} columns)")

        # Filter
        view.filter_rows(Condition("Sales", Operator.GTE, 1000))

        # Add a label
        view.set_values(
            new_column="Tier",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
                SetValue("Standard"),
            ],
        )

        # Export
        path = view.export.to_csv("output.csv")
        print(f"Exported to {path}")

    except MammothAPIError as e:
        print(f"Error: {e.message} (HTTP {e.status_code})")

if __name__ == "__main__":
    main()
```

## See also

- [Transformation examples](transformations.md) -- 25+ transformation workflows
- [Error handling](error-handling.md) -- handling errors gracefully
- [Views reference](../api/views.md) -- complete View API
