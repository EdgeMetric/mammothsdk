# Common Patterns & Examples

## End-to-End: Upload, Transform, Export

```python
from mammoth import MammothClient, Condition, Operator

# 1. Initialize
client = MammothClient(
    api_token="mm_your-token",
    workspace_id=11,
)
client.set_project_id(10)

# 2. Upload CSV
ds_id = await client.files.upload("sales_data.csv")

# 3. Create a named working view (listing may be empty or contain multiple views)
view = await client.views.create(dataset_id=ds_id, name="sales-analysis")
print(view.display_names)  # ["Product", "Region", "Sales", "Date", ...]

# 4. Apply transformations
await view.filter_rows(Condition("Sales", Operator.GTE, 100))
from mammoth import TextCase

await view.text_transform(columns=["Region"], case=TextCase.UPPER)
await view.math("Sales * 0.1", new_column="Tax")

# 5. Export
await view.export.to_csv("filtered_sales.csv")
```

---

## Working with Conditions

```python
from mammoth import Condition, Operator

# Simple conditions
high_sales = Condition("Sales", Operator.GTE, 10000)
west_region = Condition("Region", Operator.EQ, "West")
empty_email = Condition("Email", Operator.IS_EMPTY)
in_list = Condition("Status", Operator.IN_LIST, ["Active", "Pending"])

# AND — keep rows matching ALL conditions
await view.filter_rows(high_sales & west_region)

# OR — keep rows matching ANY condition
await view.filter_rows(
    Condition("Region", Operator.EQ, "West")
    | Condition("Region", Operator.EQ, "East")
)

# Nested
complex = (high_sales & west_region) | empty_email

# Use in set_values for conditional labeling
from mammoth import SetValue, ColumnType

await view.set_values(
    new_column="Priority",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Urgent", condition=high_sales & west_region),
        SetValue("Review", condition=high_sales),
        SetValue("Normal"),  # default — no condition
    ],
)
```

---

## Data Analysis Pipeline

```python
# Get a working view
view = await client.views.create(dataset_id=ds_id, name="analysis")

# Convert date columns (required for CSV uploads)
from mammoth import ConversionSpec, ColumnType
await view.convert_type([ConversionSpec(column="order_date", to=ColumnType.DATE)])

# Extract date components
from mammoth import DateComponent

await view.extract_date("order_date", component=DateComponent.YEAR, new_column="Year")
await view.extract_date("order_date", component=DateComponent.MONTH, new_column="Month")

# Calculate derived columns
await view.math("Revenue - Cost", new_column="Profit")

# Group and aggregate
from mammoth import AggregationSpec, AggregateFunction

await view.pivot(
    group_by=["Year", "Region"],
    aggregations=[
        AggregationSpec(column="Revenue", function=AggregateFunction.SUM, as_name="Total Revenue"),
        AggregationSpec(column="Profit", function=AggregateFunction.AVG, as_name="Avg Profit"),
        AggregationSpec(column="Order ID", function=AggregateFunction.COUNT, as_name="Order Count"),
    ],
)
```

---

## Window Functions

```python
from mammoth import WindowFunction, SortDirection

# Rank employees by salary within each department
await view.window(
    function=WindowFunction.ROW_NUMBER,
    new_column="Salary Rank",
    partition_by=["department"],
    order_by=[["base_salary", SortDirection.DESC]],
)

# Running total of sales by region
await view.window(
    function=WindowFunction.SUM,
    column="Sales",
    new_column="Running Total",
    partition_by=["Region"],
    order_by=[["Order Date", SortDirection.ASC]],
)
```

---

## Join Two Views

```python
from mammoth import JoinType, JoinKeySpec

# Get both views
orders = await client.views.get(view_id=1001)
customers = await client.views.get(view_id=1002)

# Join — View object auto-resolves display names
await orders.join(
    foreign_view=customers,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
    select=["Name", "Segment"],
)
```

---

## Text Processing

```python
# Split full name
from mammoth import SplitColumnSpec

await view.split_column(
    column="Full Name",
    delimiter=" ",
    new_columns=[
        SplitColumnSpec(name="First Name"),
        SplitColumnSpec(name="Last Name"),
    ],
)

# Combine columns
await view.combine_columns(
    sources=["City", "State"],
    separator=", ",
    new_column="Location",
)

# Find and replace
await view.replace_values(
    columns=["Status"],
    find="N/A",
    replace="Unknown",
)

# Bulk replace
from mammoth import BulkReplaceMapping

await view.bulk_replace(
    columns=["Category"],
    mapping=[
        BulkReplaceMapping(search=["Cat A", "Category A"], replace="A"),
        BulkReplaceMapping(search=["Cat B", "Category B"], replace="B"),
    ],
)

# Extract substring
from mammoth import SubstringDirection

await view.substring(column="Phone", direction=SubstringDirection.START, num_char=3, new_column="Area Code")
```

---

## Cleaning Data

```python
# Remove duplicates
await view.discard_duplicates()
await view.discard_duplicates(ignore_columns=["Timestamp"])

# Fill missing values
from mammoth import FillDirection

# FIRST_VALUE: forward fill (previous row); LAST_VALUE: back-fill (next row)
await view.fill_missing(column="Price", direction=FillDirection.FIRST_VALUE)

# Remove rows with missing values
await view.filter_rows(Condition("Email", Operator.IS_NOT_EMPTY))

# Trim whitespace
await view.text_transform(columns=["Name", "City", "Email"], trim=True)

# Convert types
from mammoth import ConversionSpec, ColumnType

await view.convert_type([
    ConversionSpec(column="price", to=ColumnType.NUMERIC),
    ConversionSpec(column="date", to=ColumnType.DATE),
])
```

---

## Export Destinations

```python
# CSV download
path = await view.export.to_csv("output.csv")

# PostgreSQL
await view.export.to_postgres(
    host="db.example.com", port=5432,
    database="analytics", table="sales_summary",
    username="user", password="pass",
)

# MySQL
await view.export.to_mysql(
    host="mysql.example.com", port=3306,
    database="warehouse", table="output",
    username="user", password="pass",
)

# SFTP
await view.export.to_sftp(
    host="sftp.example.com", port=22,
    path="/uploads/report.csv",
    username="user", password="pass",
)

# Email
await view.export.to_email(recipients=["team@example.com", "manager@example.com"])

# S3
from mammoth import ExportFileType
await view.export.to_s3(file_name="report.csv", file_type=ExportFileType.CSV)

# Branch out to another dataset
await view.branch_out(dest_dataset_id=42)
```

---

## AI Features

```python
# Generate SQL from natural language (returns the query; the view is unchanged)
sql = await view.generate_sql("count employees by department")
print(sql)  # "SELECT department, COUNT(*) FROM ..."
await view.add_sql(sql)  # apply it

# Generate SQL for a different intent
sql = await view.generate_sql("show top 10 products by revenue")
print(sql)  # "SELECT product, SUM(revenue) FROM ... GROUP BY product ORDER BY ..."

# Add custom SQL
await view.add_sql('SELECT region, SUM(sales) AS total FROM "view:123" GROUP BY region')

# AI-powered column generation
await view.gen_ai(
    prompt="Classify the sentiment as positive, negative, or neutral",
    context_columns=["Review Text"],
    new_column="Sentiment",
)
```

---

## Pipeline Management

```python
# List all tasks in the pipeline
tasks = await view.list_tasks()
for t in tasks:
    print(t["id"], t["sequence"], t["status"])

# Delete a specific task
await view.delete_task(task_id=123)

# Preview a task before applying
preview = await view.preview_task({"DELETE": [view.columns["Notes"]]})
```

---

## Draft Mode (Batch Transformations)

```python
# Context manager — pipeline runs once on clean exit, discards on exception
async with view.draft():
    await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    await view.math("Price * 2", new_column="Double")
    await view.add_column("Notes")
# Pipeline runs once for all 3 tasks

# Explicit approach
await view.enter_draft_mode()
await view.add_column("Status")
await view.set_values(
    new_column="Flag", column_type=ColumnType.TEXT,
    values=[SetValue("x")],
)
await view.submit_draft()  # runs pipeline, refreshes metadata, exits draft

# Discard queued tasks
await view.enter_draft_mode()
await view.add_column("Temp")
await view.discard_draft()  # reverts, "Temp" is not added

# Check mode
print(await view.is_draft_mode)  # False
```

---

## Inspecting a View

```python
view = await client.views.get(1039)

# Column info
print(view.display_names)        # ["Sales", "Region", "Date", ...]
print(view.column_types)         # {"Sales": "NUMERIC", "Region": "TEXT", ...}
print(view.columns)              # {"Sales": "column_abc", "Region": "column_def", ...}
print(view.get_column_mapping()) # same as view.columns

# Data sample
data = await view.data(limit=5)

# Full metadata
print(view.raw)  # complete API response dict
print(view.id, view.dataset_id, view.name)
```

---

## Using parse_path Helper

```python
from mammoth import parse_path

ids = parse_path("https://app.mammoth.io/#/workspaces/11/projects/10/views/1039")
# {"workspace_id": 11, "project_id": 10, "dataview_id": 1039}
```

---

## Context Manager

```python
async with MammothClient(api_token="mm_...", workspace_id=11) as client:
    client.set_project_id(10)
    view = await client.views.get(1039)
    await view.filter_rows(Condition("Sales", Operator.GTE, 1000))
# Session is cleaned up on exit
```

---

## Error Handling

```python
from mammoth import (
    MammothError, MammothAPIError, MammothAuthError,
    MammothColumnError, MammothJobTimeoutError,
)

try:
    await view.filter_rows(Condition("NonexistentColumn", Operator.EQ, "x"))
except MammothColumnError as e:
    print(f"Column not found: {e}")
    print(f"Available columns: {view.display_names}")

try:
    await view.add_sql('SELECT * FROM "view:123" WHERE sales > 1000')
except MammothAPIError as e:
    print(f"API error: {e}")

try:
    await view.pivot(group_by=["Region"], aggregations=[...])
except MammothJobTimeoutError as e:
    print(f"Job timed out: {e}")
```
