# Common Patterns & Examples

## End-to-End: Upload, Transform, Export

```python
from mammoth import MammothClient, Condition, Operator

# 1. Initialize
client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
)
client.set_project_id(10)

# 2. Upload CSV
ds_id = client.files.upload("sales_data.csv")

# 3. Get the default view
views = client.views.list(ds_id)
view = views[0]
print(view.display_names)  # ["Product", "Region", "Sales", "Date", ...]

# 4. Apply transformations
view.filter_rows(Condition("Sales", Operator.GTE, 100))
view.text_transform(columns=["Region"], case="UPPER")
view.math(
    expression=[
        {"TYPE": "COLUMN", "VALUE": "Sales"},
        {"TYPE": "OPERATOR", "VALUE": "*"},
        {"TYPE": "NUMBER", "VALUE": 0.1},
    ],
    new_column="Tax",
)

# 5. Export
view.export.to_csv("filtered_sales.csv")
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
view.filter_rows(high_sales & west_region)

# OR — keep rows matching ANY condition
view.filter_rows(
    Condition("Region", Operator.EQ, "West")
    | Condition("Region", Operator.EQ, "East")
)

# Nested
complex = (high_sales & west_region) | empty_email

# Use in set_values for conditional labeling
view.set_values(
    new_column="Priority",
    column_type="TEXT",
    values=[
        {"value": "Urgent", "condition": high_sales & west_region},
        {"value": "Review", "condition": high_sales},
        {"value": "Normal"},  # default — no condition
    ],
)
```

---

## Data Analysis Pipeline

```python
# Get a working view
view = client.views.create(dataset_id=ds_id, name="analysis")

# Convert date columns (required for CSV uploads)
view.convert_type([{"column": "order_date", "to": "DATE"}])

# Extract date components
view.extract_date("order_date", component="year", new_column="Year")
view.extract_date("order_date", component="month", new_column="Month")

# Calculate derived columns
view.math(
    expression=[
        {"TYPE": "COLUMN", "VALUE": "Revenue"},
        {"TYPE": "OPERATOR", "VALUE": "-"},
        {"TYPE": "COLUMN", "VALUE": "Cost"},
    ],
    new_column="Profit",
)

# Group and aggregate
view.pivot(
    group_by=["Year", "Region"],
    aggregations=[
        {"column": "Revenue", "function": "SUM", "as": "Total Revenue"},
        {"column": "Profit", "function": "AVG", "as": "Avg Profit"},
        {"column": "Order ID", "function": "COUNT", "as": "Order Count"},
    ],
)
```

---

## Window Functions

```python
# Rank employees by salary within each department
view.window(
    function="ROW_NUMBER",
    new_column="Salary Rank",
    partition_by=["department"],
    order_by=[["base_salary", "DESC"]],
)

# Running total of sales by region
view.window(
    function="SUM",
    column="Sales",
    new_column="Running Total",
    partition_by=["Region"],
    order_by=[["Order Date", "ASC"]],
)
```

---

## Join Two Views

```python
# Get both views
orders = client.views.get(view_id=1001)
customers = client.views.get(view_id=1002)

# Check foreign view's internal column names
customer_cols = customers.get_column_mapping()
# {"Customer ID": "column_abc", "Name": "column_def", "Segment": "column_ghi"}

# Join
orders.join(
    foreign_view_id=customers.id,
    join_type="LEFT",
    on=[{"left": "Customer ID", "right": customer_cols["Customer ID"]}],
    select=[
        {"column": customer_cols["Name"], "alias": "Customer Name"},
        {"column": customer_cols["Segment"], "alias": "Customer Segment"},
    ],
)
```

---

## Text Processing

```python
# Split full name
view.split_column(
    column="Full Name",
    delimiter=" ",
    new_columns=[
        {"name": "First Name", "type": "TEXT"},
        {"name": "Last Name", "type": "TEXT"},
    ],
)

# Combine columns
view.combine_columns(
    sources=["City", "State"],
    separator=", ",
    new_column="Location",
)

# Find and replace
view.replace_values(
    columns=["Status"],
    find="N/A",
    replace="Unknown",
)

# Bulk replace
view.bulk_replace(
    columns=["Category"],
    mapping=[
        {"search": ["Cat A", "Category A"], "replace": "A"},
        {"search": ["Cat B", "Category B"], "replace": "B"},
    ],
)

# Extract substring
view.substring(column="Phone", direction="START", num_char=3, new_column="Area Code")
```

---

## Cleaning Data

```python
# Remove duplicates
view.discard_duplicates()
view.discard_duplicates(ignore_columns=["Timestamp"])

# Fill missing values
view.fill_missing(column="Price", direction="LAST_VALUE")

# Remove rows with missing values
view.filter_rows(Condition("Email", Operator.IS_NOT_EMPTY))

# Trim whitespace
view.text_transform(columns=["Name", "City", "Email"], trim=True)

# Convert types
view.convert_type([
    {"column": "price", "to": "NUMERIC"},
    {"column": "date", "to": "DATE"},
])
```

---

## Export Destinations

```python
# CSV download
path = view.export.to_csv("output.csv")

# PostgreSQL
view.export.to_postgres(
    host="db.example.com", port=5432,
    database="analytics", table="sales_summary",
    username="user", password="pass",
)

# MySQL
view.export.to_mysql(
    host="mysql.example.com", port=3306,
    database="warehouse", table="output",
    username="user", password="pass",
)

# SFTP
view.export.to_sftp(
    host="sftp.example.com", port=22,
    path="/uploads/report.csv",
    username="user", password="pass",
)

# Email
view.export.to_email(recipients=["team@example.com", "manager@example.com"])

# S3
view.export.to_s3(file_name="report.csv", file_type="csv")

# Branch out to another dataset
view.branch_out(dest_dataset_id=42)
```

---

## AI Features

```python
# SQL from natural language
result = view.sql("count employees by department")

# Just generate the SQL without applying
sql = view.generate_sql("show top 10 products by revenue")
print(sql)  # "SELECT product, SUM(revenue) FROM ... GROUP BY product ORDER BY ..."

# Add custom SQL
view.add_sql("SELECT region, SUM(sales) AS total FROM __THIS__ GROUP BY region")

# AI-powered column generation
view.gen_ai(
    prompt="Classify the sentiment as positive, negative, or neutral",
    context_columns=["Review Text"],
    new_column="Sentiment",
)
```

---

## Pipeline Management

```python
# List all tasks in the pipeline
tasks = view.list_tasks()
for t in tasks:
    print(t["id"], t["sequence"], t["status"])

# Delete a specific task
view.delete_task(task_id=123)

# Preview a task before applying
preview = view.preview_task({"DELETE": [view.columns["Notes"]]})
```

---

## Inspecting a View

```python
view = client.views.get(1039)

# Column info
print(view.display_names)        # ["Sales", "Region", "Date", ...]
print(view.column_types)         # {"Sales": "NUMERIC", "Region": "TEXT", ...}
print(view.columns)              # {"Sales": "column_abc", "Region": "column_def", ...}
print(view.get_column_mapping()) # same as view.columns

# Data sample
data = view.data(limit=5)

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
with MammothClient(api_key="...", api_secret="...", workspace_id=11) as client:
    client.set_project_id(10)
    view = client.views.get(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
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
    view.filter_rows(Condition("NonexistentColumn", Operator.EQ, "x"))
except MammothColumnError as e:
    print(f"Column not found: {e}")
    print(f"Available columns: {view.display_names}")

try:
    view.sql("complex query that might fail")
except MammothAPIError as e:
    print(f"API error: {e}")

try:
    view.pivot(group_by=["Region"], aggregations=[...])
except MammothJobTimeoutError as e:
    print(f"Job timed out: {e}")
```
