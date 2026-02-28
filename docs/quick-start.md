# Quick Start Guide

Get up and running with the Mammoth Python SDK in five minutes.

## 1. Install the SDK

```bash
pip install mammoth-io==0.3.6
```

## 2. Get your API credentials

Log in to your Mammoth Analytics dashboard, navigate to your profile settings, and generate an API key and secret.

## 3. Create a client

```python
from mammoth import MammothClient

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,  # your workspace ID
)

# Set the project you want to work with
client.set_project_id(10)
```

The `workspace_id` is required at client creation. The `project_id` must be set before performing most operations.

!!! tip "Extract IDs from a Mammoth URL"
    Use `parse_path()` to extract IDs from a browser URL:

    ```python
    from mammoth import parse_path

    ids = parse_path("https://app.mammoth.io/#/workspaces/11/projects/10/views/1039")
    # {"workspace_id": 11, "project_id": 10, "dataview_id": 1039}
    ```

## 4. Get a View

A **View** is the central object in the SDK. It wraps a Mammoth dataview and provides transformation methods, data access, and export helpers.

```python
view = client.views.get(1039)

print(view.name)           # "My View"
print(view.display_names)  # ["Sales", "Region", "Date", ...]
print(view.column_types)   # {"Sales": "NUMERIC", "Region": "TEXT", ...}
```

## 5. Apply transformations

Transformations are applied in-place. Each method sends a task to the Mammoth pipeline, waits for it to complete, and refreshes the view metadata.

```python
from mammoth import Condition, Operator, ColumnType, SetValue

# Filter rows
view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Add a computed column
view.set_values(
    new_column="Category",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Low"),
    ],
)

# Math expression
view.math("Price * Quantity", new_column="Total")
```

## 6. Export data

```python
# Download as CSV
view.export.to_csv("output.csv")

# Export to S3
view.export.to_s3(file_name="report.csv")

# Export to PostgreSQL
view.export.to_postgres(
    host="db.example.com",
    port=5432,
    database="analytics",
    table="sales_data",
    username="user",
    password="pass",
)
```

## 7. Work with resources

The client provides sub-clients for every Mammoth API resource:

```python
# List projects — returns {"projects": [...], "offset": 0, ...}
resp = client.projects.list()
for p in resp["projects"]:      # plain dicts: p["id"], p["name"]
    print(p["id"], p["name"])

# List datasets in a project
datasets = client.datasets.list()

# Upload a file
client.files.upload("data.csv")
```

## Complete example

```python
import os
from mammoth import (
    MammothClient, Condition, Operator,
    ColumnType, SetValue, MammothAPIError,
)

client = MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,
)
client.set_project_id(10)

try:
    # Get a view
    view = client.views.get(1039)
    print(f"Working with: {view.name} ({len(view.display_names)} columns)")

    # Filter to high-value rows
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))

    # Add a label column
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
    print(f"API error: {e.message} (HTTP {e.status_code})")
```

## Key concepts

| Concept | Description |
|---------|-------------|
| **Workspace** | Top-level organization unit tied to your subscription |
| **Project** | Siloed area within a workspace for data management |
| **Dataset** | A data table stored in Mammoth (created from file uploads or connectors) |
| **Dataview** | A view of a dataset, with its own pipeline of transformations |
| **View** | The SDK's rich object wrapping a dataview -- the main interface for transformations |
| **Pipeline** | The ordered list of transformation tasks applied to a dataview |

## Next steps

- [Views reference](api/views.md) -- all transformation methods with signatures and examples
- [Conditions reference](api/conditions.md) -- filter builder with operator overloading
- [Exports reference](api/exports.md) -- all export destinations
- [Transformation examples](examples/transformations.md) -- practical workflow examples
