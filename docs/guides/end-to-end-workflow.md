# End-to-End Workflow

This guide walks through a complete Mammoth SDK workflow: install, authenticate, upload data, apply transformations, and export results.

## 1. Install the SDK

```bash
pip install mammoth-io
```

Requires Python 3.10+.

## 2. Authenticate

```python
import os
from mammoth import MammothClient

client = MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,  # your workspace ID
)

# Set the project to work in
client.set_project_id(42)
```

!!! tip "Extract IDs from a Mammoth URL"
    ```python
    from mammoth import parse_path

    ids = parse_path("https://app.mammoth.io/#/workspaces/11/projects/42/views/1039")
    # {"workspace_id": 11, "project_id": 42, "dataview_id": 1039}
    ```

## 3. Upload a file

```python
# Upload a CSV file -- returns the new dataset ID
dataset_id = client.files.upload("sales_data.csv")
print(f"Created dataset: {dataset_id}")

# Get the default View for the uploaded dataset
views = client.views.list(dataset_id)
view = views[0]
```

Other upload options:

```python
# Multiple files at once
dataset_ids = client.files.upload(["sales.csv", "customers.xlsx"])

# Upload an entire folder
dataset_ids = client.files.upload_folder("./data/")

# Append to an existing dataset
client.files.upload("new_rows.csv", append_to_ds_id=dataset_id)
```

See the [Files API reference](../api/files.md) for the full `upload()` signature.

## 4. Inspect the View

```python
print(f"View: {view.name}")
print(f"Columns: {view.display_names}")
# e.g., ["Customer", "Region", "Sales", "Order Date"]

print(f"Types: {view.column_types}")
# e.g., {"Customer": "TEXT", "Region": "TEXT", "Sales": "NUMERIC", "Order Date": "TEXT"}

# Preview the data
data = view.data(limit=5)
```

!!! note "CSV dates upload as TEXT"
    Date columns in CSV files are uploaded as TEXT type. Use `convert_type()` to convert them before applying date operations:

    ```python
    from mammoth import ConversionSpec

    view.convert_type([ConversionSpec(column="Order Date", to="DATE", format="MM/DD/YYYY")])
    ```

## 5. Apply transformations

### Filter rows

```python
from mammoth import Condition, Operator, FilterType

# Keep rows where Sales >= 1000
view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Remove rows where Region is empty
view.filter_rows(
    Condition("Region", Operator.IS_EMPTY),
    filter_type=FilterType.REMOVE,
)

# Negate a condition with ~
view.filter_rows(~Condition("Status", Operator.EQ, "Cancelled"))
```

### Add computed columns

```python
from mammoth import ColumnType, SetValue

# Conditional labeling
view.set_values(
    new_column="Tier",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Standard", condition=Condition("Sales", Operator.GTE, 1000)),
        SetValue("Basic"),
    ],
)

# Math expression
view.math("Price * Quantity", new_column="Revenue")
```

### Aggregate with pivot

```python
from mammoth import AggregateFunction, AggregationSpec

view.pivot(
    group_by=["Region"],
    aggregations=[
        AggregationSpec(column="Sales", function=AggregateFunction.SUM, as_name="Total Sales"),
        AggregationSpec(column="Sales", function=AggregateFunction.AVG, as_name="Avg Sales"),
        AggregationSpec(column="Sales", function=AggregateFunction.COUNT, as_name="Order Count"),
    ],
)
```

### Other common transformations

```python
from mammoth import TextCase, DateComponent, WindowFunction, SortDirection

# Text: change case
view.text_transform(["Customer"], case=TextCase.UPPER)

# Date: extract year
view.extract_date("Order Date", DateComponent.YEAR, new_column="Year")

# Window: rank within groups
view.window(
    function=WindowFunction.ROW_NUMBER,
    new_column="Rank",
    partition_by=["Region"],
    order_by=[["Sales", SortDirection.DESC]],
)
```

See the [Views reference](../api/views.md) for all 25+ transformation methods.

## 6. Export results

### Download as CSV

```python
path = view.export.to_csv("output.csv")
print(f"Saved to {path}")
```

### Export to S3

```python
result = view.export.to_s3(file_name="monthly_report.csv")
```

### Export to a database

```python
# PostgreSQL
view.export.to_postgres(
    host="db.example.com",
    port=5432,
    database="analytics",
    table="sales_summary",
    username="user",
    password="pass",
)

# MySQL
view.export.to_mysql(
    host="db.example.com",
    port=3306,
    database="analytics",
    table="sales_summary",
    username="user",
    password="pass",
)
```

### Other export targets

```python
view.export.to_bigquery(...)
view.export.to_redshift(...)
view.export.to_sftp(host="sftp.example.com", path="/exports/data.csv", username="user", password="pass")
view.export.to_email(recipients=["team@example.com"])
```

See the [Exports reference](../api/exports.md) for all destinations.

## Complete script

Here's a full, copy-paste-ready script:

```python
import os
from mammoth import (
    MammothClient,
    Condition,
    Operator,
    ColumnType,
    SetValue,
    AggregateFunction,
    AggregationSpec,
    FilterType,
    MammothAPIError,
)

# 1. Authenticate
client = MammothClient(
    api_key=os.getenv("MAMMOTH_API_KEY"),
    api_secret=os.getenv("MAMMOTH_API_SECRET"),
    workspace_id=11,
)
client.set_project_id(42)

try:
    # 2. Upload data
    dataset_id = client.files.upload("sales_data.csv")
    views = client.views.list(dataset_id)
    view = views[0]
    print(f"Uploaded: {view.name} ({len(view.display_names)} columns)")

    # 3. Clean data
    view.filter_rows(
        Condition("Region", Operator.IS_EMPTY),
        filter_type=FilterType.REMOVE,
    )
    view.filter_rows(Condition("Sales", Operator.GTE, 0))

    # 4. Transform
    view.set_values(
        new_column="Tier",
        column_type=ColumnType.TEXT,
        values=[
            SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
            SetValue("Standard", condition=Condition("Sales", Operator.GTE, 1000)),
            SetValue("Basic"),
        ],
    )
    view.math("Price * Quantity", new_column="Revenue")

    # 5. Export
    path = view.export.to_csv("output.csv")
    print(f"Exported to {path}")

except MammothAPIError as e:
    print(f"API error: {e.message} (HTTP {e.status_code})")
```

## See also

- [Quick Start](../quick-start.md) -- shorter getting-started guide
- [Files API](../api/files.md) -- full upload/file management reference
- [Views API](../api/views.md) -- all transformation methods
- [Conditions](../api/conditions.md) -- filter builder with `&`, `|`, `~`
- [Exports](../api/exports.md) -- all export destinations
- [Transformation examples](../examples/transformations.md) -- more transformation workflows
