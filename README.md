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
from mammoth import SplitColumnSpec

view.split_column(
    "Full Name",
    delimiter=" ",
    new_columns=[SplitColumnSpec(name="First"), SplitColumnSpec(name="Last")],
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
from mammoth import DateDelta

view.increment_date("Ship Date", delta=DateDelta(days=30), new_column="Expected Arrival")
```

### Column Operations

```python
from mammoth import CopySpec, ConversionSpec

# Add an empty column
view.add_column("Notes", ColumnType.TEXT)

# Delete columns
view.delete_columns(["Temp1", "Temp2"])

# Copy a column
view.copy_columns([CopySpec(source="Sales", as_name="Sales Backup", type=ColumnType.NUMERIC)])

# Combine (concatenate) columns
view.combine_columns(["First Name", "Last Name"], new_column="Full Name", separator=" ")

# Convert column type
view.convert_type([ConversionSpec(column="ZipCode", to=ColumnType.TEXT)])
view.convert_type([ConversionSpec(column="Order Date", to=ColumnType.DATE, format="MM/DD/YYYY")])
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
| `IN_RANGE` | Between two bounds (inclusive); value is a 2-element list |
| `CONTAINS`, `NOT_CONTAINS` | Text contains/not contains |
| `ICONTAINS` | Case-insensitive text contains |
| `STARTS_WITH`, `ENDS_WITH` | Text prefix/suffix |
| `NOT_STARTS_WITH`, `NOT_ENDS_WITH` | Negated prefix/suffix |
| `IS_EMPTY`, `IS_NOT_EMPTY` | Null check |
| `IS_MAXVAL`, `IS_NOT_MAXVAL` | Max value in column |
| `IS_MINVAL`, `IS_NOT_MINVAL` | Min value in column |

#### `IN_RANGE` — numeric or date range

```python
# Keep rows where Amount is between 100 and 500 (inclusive)
view.filter_rows(Condition("Amount", Operator.IN_RANGE, [100, 500]))
```

#### `ICONTAINS` — case-insensitive substring match

```python
# Match "York", "york", "YORK" in City column
view.filter_rows(Condition("City", Operator.ICONTAINS, "york"))
```

#### Date-relative function operands via `DateFunction`

Pass a `DateFunction` enum member as the value with `value_is_date_fn=True` to compare against a dynamic date/time:

```python
from mammoth import Condition, Operator, DateFunction

# Rows where Order Date is after today
view.filter_rows(Condition("Order Date", Operator.GT, DateFunction.TODAY, value_is_date_fn=True))

# Rows where Timestamp is on or after the current instant
view.filter_rows(Condition("Timestamp", Operator.GTE, DateFunction.NOW, value_is_date_fn=True))

# Rows where Date equals the maximum date value in that column
view.filter_rows(Condition("Date", Operator.EQ, DateFunction.MAX, value_is_date_fn=True))
```

Available `DateFunction` values: `NOW`, `TODAY`, `MAX`, `MIN`, `SYSTEM_DATE`, `SYSTEM_TIME`.

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
views = client.views.list()
view = next(v for v in views if v.dataset_id == dataset_id)
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

# From client with a known dataview ID (parameter name is `file=`, not `file_name=`)
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
# From a View object — creates a new dataset named "Q1 snapshot"
new_dataset_id = view.export.to_dataset(dataset_name="Q1 snapshot")

# Shorthand
new_dataset_id = view.branch_out(dataset_name="Q1 snapshot")

# Append into an existing dataset
view.branch_out(dataset_name="Sales Archive", target_ds_id=500)
```

### Export to FTP / SFTP

```python
# FTP — parameters: domain, directory, file, username, password
view.export.to_ftp(
    domain="ftp.example.com",
    directory="/exports",
    file="sales.csv",
    username="user",
    password="pass",
)

# SFTP — password auth
view.export.to_sftp(
    host="sftp.example.com",
    username="user",
    password="pass",
    directory="/exports",
    file_name="data.csv",
)

# SFTP — private-key auth
view.export.to_sftp(
    host="sftp.example.com",
    username="user",
    ssh_key_authentication=True,
    private_key="-----BEGIN OPENSSH PRIVATE KEY-----\n...",
)
```

### Email Export

```python
# `emails` is a list of recipient addresses (not `recipients`)
view.export.to_email(
    emails=["team@example.com"],
    subject="Q1 Sales Report",
)
```

### BigQuery Export

```python
from mammoth import BigQueryExportType

view.export.to_bigquery(
    selected_profile={"name": "my_dataset", "value": [["project_id", "dataset_id"]]},
    selected_identity={"identity_config": {...}, "host": "sa@project.iam.gserviceaccount.com"},
    table="sales_summary",
    export_type=BigQueryExportType.REPLACE,
)
```

### Publish to Managed DB (for Dashboards)

```python
from mammoth import OdbcType

# Publishes to a Mammoth-managed Postgres or BigQuery connection
view.export.publish_to_db(table="sales_dashboard", odbc_type=OdbcType.POSTGRES)
```

### REST API Export

```python
from mammoth import RestAuthType, HttpMethod

view.export.to_rest_api(
    base_url="https://api.example.com",
    endpoint_path="/v1/records",
    auth_type=RestAuthType.BEARER,
    http_method=HttpMethod.POST,
    auth={"token": "my-bearer-token"},
    batch_size=500,       # 1–10 000
    timeout_seconds=30,   # 5–300
)
```

### Other Export Targets

```python
view.export.to_redshift(...)
view.export.to_elasticsearch(...)
view.export.to_azure_blob(...)
view.export.to_sharepoint(...)
view.export.to_onedrive(...)
view.export.to_tableau(...)
view.export.to_powerbi(...)
view.export.to_mssql(...)
```

## Error Handling

The SDK validates arguments **before** making any network call and raises specific exceptions so failures are caught early with an actionable message.

### Exception hierarchy

```
MammothError                    # base; all SDK exceptions inherit from this
├── MammothValidationError      # invalid SDK arguments (raised before any API call)
├── MammothAPIError             # API returned an error response
│   └── MammothAuthError        # HTTP 401 — invalid credentials
├── MammothColumnError          # column display name not found in view metadata
├── MammothExportError          # export submitted but result dataset id didn't resolve
├── MammothJobTimeoutError      # async job polling exceeded the timeout
├── MammothJobFailedError       # async job completed with a failure status
└── MammothTransformError       # pipeline transformation task failed
```

All exceptions expose a `.message` attribute. `MammothAPIError` additionally exposes `.status_code` (int | None) and `.response_body` (dict).

### Example

```python
from mammoth import (
    MammothClient,
    MammothValidationError,
    MammothAPIError,
)

client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(42)
view = client.views.get(1039)

try:
    # Validation fires before any network call
    view.export.to_email(emails=[])          # raises MammothValidationError
except MammothValidationError as e:
    print("Bad arguments:", e.message)

try:
    client.views.get(99999)                  # raises MammothAPIError if not found
except MammothAPIError as e:
    print(f"API error {e.status_code}: {e.response_body}")
```

## Resource APIs

The SDK exposes typed resource APIs on the client for managing workspace entities. All public types are importable directly from `mammoth`.

### External Keys

```python
from mammoth import ExternalKeyType

key = client.external_keys.create(
    key_type=ExternalKeyType.ANTHROPIC,
    key_name="My Claude key",
    secure_key="sk-ant-...",
)
client.external_keys.delete(key["id"])
```

### Addons (storage, users, connectors)

```python
# Add 50 GB storage
client.addons.add_storage(additional_storage_gb=50)

# Add 5 user seats
client.addons.add_users(user_count=5)

# Add a connector addon (single or bulk)
client.addons.add_connector(connector_id=42)
client.addons.add_connector(connector_ids=[42, 43])
```

### Dashboards

```python
dashboard = client.dashboards.create(
    intent="Show quarterly revenue by region and product",
    source=[1039, 1040],       # dataview IDs
    enable_filters=True,
)
```

### Automations

```python
from mammoth import (
    AutomationTaskSpec, AutomationTaskType,
    TaskDetailsSpec, DataRefreshConfig,
)

automation = client.automations.create(
    name="Nightly refresh",
    description="Pulls cloud data every night",
    tasks=[
        AutomationTaskSpec(
            task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
            details=TaskDetailsSpec(
                ds_details=[DataRefreshConfig(ds_id=42)],
            ),
        )
    ],
)
```

### Schedules

```python
from datetime import datetime
from mammoth import ScheduleCreateSpec, RruleSpec, RruleFrequency

schedule = client.automations.create_schedule(
    spec=ScheduleCreateSpec(
        rrule=RruleSpec(
            frequency=RruleFrequency.DAILY,
            start=datetime(2025, 1, 1, 6, 0),
        ),
    )
)
```

### Workspace — update settings and user roles

```python
from mammoth import WorkspacePatchOp, WorkspacePatchPath, UserRolePatchOp, WorkspaceRoleType

# Rename the workspace
client.workspaces.update(patches=[
    WorkspacePatchOp(op="replace", path=WorkspacePatchPath.NAME, value="My Workspace"),
])

# Change a user's role
client.workspaces.update_user(
    user_id="user-uuid-here",
    patches=[UserRolePatchOp(op="replace", path="role", value=WorkspaceRoleType.WORKSPACE_ADMIN)],
)
```

### Connectors — create a connection and data source config

```python
# Create a PostgreSQL connection (config shape varies by connector_key)
conn = client.connectors.create_connection(
    connector_key="postgres",
    config={
        "hostname": "db.example.com",
        "port": 5432,
        "database": "analytics",
        "username": "user",
        "password": "pass",
    },
)

# Create a data source config (query-based for DB connectors)
ds_config = client.connectors.create_ds_config(
    connector_key="postgres",
    connection_key=conn["connection_key"],
    query="SELECT * FROM sales WHERE year = 2024",
    validate=True,
)
```

## MCP Server

The SDK includes a companion MCP (Model Context Protocol) server that lets AI assistants interact with Mammoth directly. Install it separately:

```bash
pip install mammoth-mcp
```

See the [mammoth-mcp](https://github.com/EdgeMetric/mm-pysdk/tree/main/mammoth-mcp) directory for configuration and usage details.
