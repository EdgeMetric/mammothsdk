# mammoth-io

Python SDK for the [Mammoth Analytics](https://mammoth.io) platform. Build data pipelines, apply transformations, and export results -- all from Python.

[![PyPI](https://img.shields.io/pypi/v/mammoth-io)](https://pypi.org/project/mammoth-io/)
[![Python](https://img.shields.io/pypi/pyversions/mammoth-io)](https://pypi.org/project/mammoth-io/)

## Installation

```bash
pip install mammoth-io
```

Requires Python 3.10+.

## Quick Start

```python
from mammoth import MammothClient

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
)
client.set_project_id(42)

# Get a view and inspect its columns
view = client.views.get(1039)
print(view.display_names)   # ["Customer", "Region", "Sales", "Date"]
print(view.column_types)    # {"Customer": "TEXT", "Region": "TEXT", "Sales": "NUMERIC", ...}

# After any transformation, display_names is automatically refreshed
# (including pipeline-added columns like those created by math/set_values/add_column).
# Use get_metadata() to inspect the full list:
view.math("Sales * 1.1", new_column="Revenue")
print(view.display_names)   # now includes "Revenue"
meta = view.get_metadata()  # [{"display_name": "Revenue", "internal_name": "column_x1y2", "type": "NUMERIC"}, ...]

# Fetch data — returns {"data": [rows...], "paging": {...}}
result = view.data(limit=100)
rows = result["data"]
```

You can also extract IDs directly from a Mammoth URL:

```python
from mammoth import MammothClient, parse_path

ids = parse_path("https://app.mammoth.io/#/workspaces/11/projects/42/views/1039")
# {"workspace_id": 11, "project_id": 42, "dataview_id": 1039}

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=ids["workspace_id"],
)
client.set_project_id(ids["project_id"])
view = client.views.get(ids["dataview_id"])
```

## Views & Transformations

The `View` object is the central interface. It wraps a single dataview and exposes 25+ transformation methods. Each method sends a pipeline task to the API and automatically refreshes the view metadata — including any new columns added by the transformation.

```python
view.math(expression="Price * Quantity", new_column="Revenue")
print("Revenue" in view.display_names)   # True — refreshed automatically

# Inspect full column list (display_name, internal_name, type)
for col in view.get_metadata():
    print(col)
```

### Filter Rows

```python
from mammoth import Condition, Operator, FilterType

# Keep rows where Sales >= 1000
view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Remove rows where Region is empty
view.filter_rows(
    Condition("Region", Operator.IS_EMPTY),
    filter_type=FilterType.REMOVE,
)
```

### Set Values (Conditional Labeling)

```python
from mammoth import SetValue, ColumnType

view.set_values(
    new_column="Risk Level",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Medium", condition=Condition("Sales", Operator.GTE, 5000)),
        SetValue("Low"),
    ],
)
```

### Math

```python
# String expressions are parsed automatically
view.math("Price * Quantity", new_column="Revenue")
view.math("(Price + Tax) * 1.1", new_column="Grand Total")
```

### Join

```python
from mammoth import JoinType, JoinKeySpec

other_view = client.views.get(2050)

view.join(
    foreign_view=other_view,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
    select=["Category", "Tier"],
)
```

### Pivot (Group By / Aggregate)

```python
from mammoth import AggregateFunction, AggregationSpec

view.pivot(
    group_by=["Region"],
    aggregations=[
        AggregationSpec(column="Sales", function=AggregateFunction.SUM, as_name="Total Sales"),
        AggregationSpec(column="Sales", function=AggregateFunction.AVG, as_name="Avg Sales"),
    ],
)
```

### Window Functions

```python
from mammoth import WindowFunction, SortDirection

view.window(
    function=WindowFunction.ROW_NUMBER,
    new_column="Rank",
    partition_by=["Region"],
    order_by=[["Sales", SortDirection.DESC]],
)
```

### Text Operations

```python
from mammoth import TextCase

# Change case
view.text_transform(["Customer Name"], case=TextCase.UPPER)

# Find and replace
view.replace_values(columns=["Status"], find="Pending", replace="In Progress")

# Split column
view.split_column(
    "Full Name",
    delimiter=" ",
    new_columns=[{"name": "First", "type": "TEXT"}, {"name": "Last", "type": "TEXT"}],
)
```

### Date Operations

```python
from mammoth import DateComponent, DateDiffUnit

# Extract year from a date column
view.extract_date("Order Date", DateComponent.YEAR, new_column="Order Year")

# Calculate difference between two dates
view.date_diff(DateDiffUnit.DAY, start="Start Date", end="End Date", new_column="Duration")

# Add 30 days to a date
view.increment_date("Ship Date", delta={"DAYS": 30}, new_column="Expected Arrival")
```

### Column Operations

```python
from mammoth import CopySpec, ConversionSpec

# Add an empty column
view.add_column("Notes", ColumnType.TEXT)

# Delete columns
view.delete_columns(["Temp1", "Temp2"])

# Copy a column
view.copy_columns([CopySpec(source="Sales", as_name="Sales Backup", type="NUMERIC")])

# Combine (concatenate) columns
view.combine_columns(["First Name", "Last Name"], new_column="Full Name", separator=" ")

# Convert column type
view.convert_type([ConversionSpec(column="ZipCode", to="TEXT")])
view.convert_type([ConversionSpec(column="Order Date", to="DATE", format="MM/DD/YYYY")])
```

### Row Operations

```python
from mammoth import FillDirection

# Fill missing values
view.fill_missing("Revenue", direction=FillDirection.LAST_VALUE)

# Keep top 100 rows
view.limit_rows(100)

# Remove duplicates
view.discard_duplicates()

# Unpivot columns to rows
view.unnest(["Q1", "Q2", "Q3", "Q4"], label_column="Quarter", value_column="Revenue")
```

### AI and SQL

```python
# AI-powered transformation
view.gen_ai(
    prompt="Classify the sentiment of the review as Positive, Negative, or Neutral",
    context_columns=["Review Text"],
    new_column="Sentiment",
)

# Generate SQL from natural language (also adds pipeline task)
sql_query = view.generate_sql("count customers by region")

# Add a raw SQL query as a pipeline task
view.add_sql("SELECT region, COUNT(*) as cnt FROM data GROUP BY region")
```

### Pipeline Management

```python
# List all tasks on a view
tasks = view.list_tasks()

# Delete a specific task
view.delete_task(task_id=123)

# Preview a task before applying
preview = view.preview_task({"MATH": {"EXPRESSION": [...]}})
```

### All Transformation Methods

| Method | Description |
|--------|-------------|
| `filter_rows()` | Filter rows by condition |
| `set_values()` | Label/insert values with conditional logic |
| `math()` | Arithmetic expressions |
| `join()` | Join with another view |
| `pivot()` | Group by and aggregate |
| `window()` | Window functions (rank, lag, running sum, etc.) |
| `crosstab()` | Pivot table |
| `text_transform()` | Change case, trim whitespace |
| `replace_values()` | Find and replace |
| `bulk_replace()` | Bulk find-and-replace with mapping |
| `split_column()` | Split by delimiter |
| `substring()` | Extract text by position or regex |
| `extract_date()` | Extract date components |
| `date_diff()` | Date difference |
| `increment_date()` | Add/subtract from dates |
| `add_column()` | Add empty column |
| `delete_columns()` | Remove columns |
| `copy_columns()` | Duplicate columns |
| `combine_columns()` | Concatenate columns |
| `convert_type()` | Change column data type |
| `fill_missing()` | Fill gaps forward/backward |
| `limit_rows()` | Keep top/bottom N rows |
| `discard_duplicates()` | Remove duplicate rows |
| `unnest()` | Unpivot columns to rows |
| `lookup()` | Lookup values from another view |
| `json_extract()` | Extract from JSON columns |
| `gen_ai()` | AI-powered transformation |
| `generate_sql()` | Generate SQL from natural language |
| `add_sql()` | Add raw SQL as pipeline task |

### Parameter Spec Dataclasses

Methods that accept structured parameters use typed dataclasses for IDE autocomplete:

| Dataclass | Used by |
|-----------|---------|
| `CopySpec` | `copy_columns()` |
| `ConversionSpec` | `convert_type()` |
| `AggregationSpec` | `pivot()` |
| `CrosstabSpec` | `crosstab()` |
| `JoinKeySpec` | `join()` on |
| `JoinSelectSpec` | `join()` select |
| `JsonExtractionSpec` | `json_extract()` |

## Conditions

The `Condition` class supports Python's `&` (AND), `|` (OR), and `~` (NOT) operators for composing filter logic.

```python
from mammoth import Condition, Operator

# Simple conditions
high_sales = Condition("Sales", Operator.GTE, 10000)
west_region = Condition("Region", Operator.EQ, "West")
active = Condition("Status", Operator.IN_LIST, ["Active", "Pending"])
has_email = Condition("Email", Operator.IS_NOT_EMPTY)

# Combine with & (AND), | (OR), and ~ (NOT)
priority = high_sales & west_region          # Both must be true
either = high_sales | west_region            # At least one true
not_active = ~active                         # Negate a condition
complex_filter = (high_sales & west_region) | ~active  # Nested logic

# Use anywhere conditions are accepted
view.filter_rows(priority)
view.set_values(
    new_column="Flag",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Priority", condition=high_sales & west_region),
        SetValue("Normal"),
    ],
)
view.math("Sales * 1.1", new_column="Adjusted", condition=west_region)
```

### Supported Operators

| Operator | Description |
|----------|-------------|
| `EQ`, `NE` | Equal, not equal |
| `GT`, `GTE`, `LT`, `LTE` | Comparison |
| `IN_LIST`, `NOT_IN_LIST` | Value in/not in list |
| `CONTAINS`, `NOT_CONTAINS` | Text contains/not contains |
| `STARTS_WITH`, `ENDS_WITH` | Text prefix/suffix |
| `NOT_STARTS_WITH`, `NOT_ENDS_WITH` | Negated prefix/suffix |
| `IS_EMPTY`, `IS_NOT_EMPTY` | Null check |
| `IS_MAXVAL`, `IS_NOT_MAXVAL` | Max value in column |
| `IS_MINVAL`, `IS_NOT_MINVAL` | Min value in column |

## File Upload

```python
# Upload a single file (returns dataset ID)
dataset_id = client.files.upload("sales_data.csv")

# Upload multiple files
dataset_ids = client.files.upload(["sales.csv", "customers.xlsx"])

# Upload an entire folder
dataset_ids = client.files.upload_folder("./data/")
```

Supported formats: CSV, TSV, PSV, XLS, XLSX, ZIP, BZ2, GZ, TAR, 7Z, PDF, TIFF, JPEG, PNG, HEIC, WEBP. Maximum file size: 50 MB.

After upload, get a view for the new dataset:

```python
dataset_id = client.files.upload("sales_data.csv")
views = client.views.list(dataset_id)
view = views[0]  # Default view created on upload
print(view.display_names)
```

## Exports

### Download as CSV

```python
# From a View object
path = view.export.to_csv("output.csv")

# From client with a known dataview ID
path = client.exports.to_csv(dataview_id=1039, output_path="output.csv")
```

### Export to S3

```python
# From a View object
result = view.export.to_s3(file_name="monthly_report.csv")

# From client with a known dataview ID
result = client.exports.to_s3(dataview_id=1039, file="monthly_report.csv")
```

### Export to Database

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

### Branch Out (Export to Another Dataset)

```python
# From a View object
view.export.to_dataset(dest_dataset_id=500)

# Or using the shorthand
view.branch_out(dest_dataset_id=500)
```

### Other Export Targets

```python
view.export.to_bigquery(...)
view.export.to_redshift(...)
view.export.to_elasticsearch(...)
view.export.to_ftp(host="ftp.example.com", path="/exports/data.csv", username="user", password="pass")
view.export.to_sftp(host="sftp.example.com", path="/exports/data.csv", username="user", password="pass")
view.export.to_email(recipients=["team@example.com"])
```

## MCP Server

The SDK includes a companion MCP (Model Context Protocol) server that lets AI assistants interact with Mammoth directly. Install it separately:

```bash
pip install mammoth-mcp
```

See the [mammoth-mcp](https://github.com/EdgeMetric/mm-pysdk/tree/main/mammoth-mcp) directory for configuration and usage details.
