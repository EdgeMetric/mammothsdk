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

## Data access

### data()

Fetch rows from the dataview.

```python
view.data(
    limit: int = 400,
    offset: int = 1,
    columns: list[str] | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
    sort: str | None = None,
) -> dict[str, Any]
```

Returns a dict with two keys:

- `"data"` — list of row dicts (keys are internal column names like `"column_1"`)
- `"paging"` — pagination info

```python
# Fetch first 100 rows
result = view.data(limit=100)
rows = result["data"]       # list of row dicts
print(len(rows))            # number of rows returned

# Fetch specific columns
result = view.data(columns=["Sales", "Region"])

# Fetch with a filter
result = view.data(condition=Condition("Sales", Operator.GTE, 1000))
```

### get_metadata()

Return the current column list as a list of dicts. Useful for inspecting the full column state after transformations.

```python
meta = view.get_metadata()
# [
#   {"display_name": "Sales", "internal_name": "column_1", "type": "NUMERIC"},
#   {"display_name": "Revenue", "internal_name": "column_xyzabc", "type": "NUMERIC"},
#   ...
# ]
```

### refresh()

Re-fetch metadata from the API and update local state. Returns `self` for chaining.

```python
view.refresh()
```

## Pipeline management

### list_tasks()

List all pipeline tasks on this dataview.

```python
tasks = view.list_tasks()
for task in tasks:
    print(task["id"], task["task_key"])
```

### delete_task()

Delete a pipeline task by ID. Refreshes view metadata after deletion.

```python
view.delete_task(task_id=42)
```

### preview_task()

Preview a task without applying it.

```python
preview = view.preview_task({"SELECT": "ALL", "CONDITION": {...}})
```

### get_column_mapping()

Return a copy of the display-name-to-internal-name mapping.

```python
mapping = view.get_column_mapping()
# {"Sales": "column_1", "Region": "column_2", ...}
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

### enter_draft_mode()

Enter draft mode explicitly. All subsequent `_add_task()` calls skip pipeline execution.

```python
view.enter_draft_mode() -> dict[str, Any]
```

### submit_draft()

Submit queued tasks, run the pipeline, refresh metadata, and exit draft mode.

```python
view.submit_draft() -> dict[str, Any]
```

### discard_draft()

Discard all queued tasks, exit draft mode, and refresh metadata to the pre-draft state.

```python
view.discard_draft() -> dict[str, Any]
```

### set_auto_run()

Toggle auto-run on the pipeline. When disabled (``False``), the view enters draft mode and tasks are queued. When re-enabled (``True``), the view returns to auto-run mode.

```python
view.set_auto_run(enabled: bool) -> dict[str, Any]

view.set_auto_run(False)   # enter draft mode
view.set_auto_run(True)    # back to auto-run
```

### is_draft_mode (property)

Check whether the view is currently in draft mode.

```python
if view.is_draft_mode:
    print("Tasks are being queued")
```

### Explicit draft workflow

```python
view.enter_draft_mode()
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
view.math("Price * 2", new_column="Double")
view.submit_draft()  # pipeline runs once, metadata refreshed
```

---

## Transformation methods

All transformation methods are synchronous — they block until the operation completes and the view metadata is refreshed (unless in draft mode, where tasks are queued). Each method returns the API response dict.

### filter_rows

Filter rows by condition (SELECT task).

```python
view.filter_rows(
    condition: Condition | CompoundCondition | NotCondition,
    filter_type: FilterType = FilterType.SHOW,
    prompt: str = "",
) -> dict[str, Any]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `condition` | `Condition \| CompoundCondition \| NotCondition` | *required* | Filter condition |
| `filter_type` | `FilterType` | `SHOW` | `SHOW` to keep matching rows, `REMOVE` to discard |
| `prompt` | `str` | `""` | Natural-language description of the filter intent |

```python
from mammoth import Condition, Operator, FilterType

# Keep rows where Sales >= 1000
view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Remove rows where Region is empty
view.filter_rows(
    Condition("Region", Operator.IS_EMPTY),
    filter_type=FilterType.REMOVE,
)

# Combine conditions
view.filter_rows(
    Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
)
```

### set_values

Create or update a column with conditional values (SET task).

```python
view.set_values(
    values: list[SetValue],
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.TEXT,
    existing_column: str | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `values` | `list[SetValue]` | *required* | List of value specs (last one without a condition is the default) |
| `new_column` | `str \| None` | `None` | Name for a new column |
| `column_type` | `ColumnType` | `TEXT` | Type for the new column |
| `existing_column` | `str \| None` | `None` | Display name of existing column to update |
| `condition` | `Condition \| CompoundCondition \| NotCondition \| None` | `None` | Global condition applied to the whole task |

```python
from mammoth import SetValue, Condition, Operator, ColumnType

view.set_values(
    new_column="Risk Level",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Medium", condition=Condition("Sales", Operator.GTE, 5000)),
        SetValue("Low"),  # default
    ],
)
```

### math

Apply arithmetic operations (MATH task). Accepts a string expression that is parsed automatically.

```python
view.math(
    expression: str,
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.NUMERIC,
    existing_column: str | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
# String expression (recommended)
view.math("Price * Quantity", new_column="Total")
view.math("(Price + Tax) * 1.1", new_column="Grand Total")

# Write to an existing column
view.math("Sales * 1.1", existing_column="Sales")
```

### join

Join with another dataview (JOIN task).

```python
view.join(
    foreign_view: int | View,
    join_type: JoinType,
    on: list[JoinKeySpec],
    select: list[str | JoinSelectSpec],
    column_prefix: str | None = None,
) -> dict[str, Any]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `foreign_view` | `int \| View` | View object or dataview ID to join with |
| `join_type` | `JoinType` | `INNER`, `LEFT`, `RIGHT`, or `OUTER` |
| `on` | `list[JoinKeySpec]` | Join keys as JoinKeySpec objects |
| `select` | `list[str \| JoinSelectSpec]` | Column names (str) or JoinSelectSpec objects |
| `column_prefix` | `str \| None` | Prefix for joined columns |

```python
from mammoth import JoinType, JoinKeySpec, JoinSelectSpec

# Join with a View object (display names everywhere)
other = client.views.get(2050)
view.join(
    foreign_view=other,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
    select=["Category", "Name"],
)

# Join with a view ID (use internal names for the foreign view)
view.join(
    foreign_view=2050,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="column_1")],
    select=[JoinSelectSpec(column="column_7", alias="Category")],
)
```

### pivot

Group and aggregate (PIVOT task).

```python
view.pivot(
    group_by: list[str],
    aggregations: list[AggregationSpec],
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
from mammoth import AggregateFunction, AggregationSpec

view.pivot(
    group_by=["Region"],
    aggregations=[
        AggregationSpec(column="Sales", function=AggregateFunction.SUM, as_name="Total Sales"),
        AggregationSpec(column="Sales", function=AggregateFunction.COUNT, as_name="Order Count"),
    ],
)
```

### window

Apply a window function (WINDOW task).

```python
view.window(
    function: WindowFunction,
    column: str | None = None,
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.NUMERIC,
    existing_column: str | None = None,
    partition_by: list[str] | None = None,
    order_by: list[list[str | SortDirection]] | None = None,
    range_type: WindowRange = WindowRange.UNBOUNDED,
) -> dict[str, Any]
```

```python
from mammoth import WindowFunction, SortDirection, WindowRange

# Row number per region, ordered by sales descending
view.window(
    function=WindowFunction.ROW_NUMBER,
    new_column="Rank",
    partition_by=["Region"],
    order_by=[["Sales", SortDirection.DESC]],
)

# Running sum
view.window(
    function=WindowFunction.SUM,
    column="Sales",
    new_column="Running Total",
    order_by=[["Date", SortDirection.ASC]],
    range_type=WindowRange.RUNNING,
)
```

### crosstab

Crosstab / pivot table (CROSSTAB task).

```python
view.crosstab(
    rows: list[str],
    pivot_column: str,
    select: CrosstabSpec,
) -> dict[str, Any]
```

```python
from mammoth import CrosstabSpec

view.crosstab(
    rows=["Region"],
    pivot_column="Quarter",
    select=CrosstabSpec(column="Sales", function=AggregateFunction.SUM),
)
```

### add_column

Add an empty column (ADD_COLUMN task).

```python
view.add_column(name: str, column_type: ColumnType = ColumnType.TEXT) -> dict
```

```python
view.add_column("Notes", ColumnType.TEXT)
```

### delete_columns

Remove columns (DELETE task).

```python
view.delete_columns(columns: list[str]) -> dict
```

```python
view.delete_columns(["Temp Column", "Debug"])
```

### copy_columns

Duplicate columns (COPY task).

```python
view.copy_columns(copies: list[CopySpec]) -> dict
```

```python
from mammoth import CopySpec, ColumnType

view.copy_columns([
    CopySpec(source="Sales", as_name="Sales Backup", type=ColumnType.NUMERIC),
])
```

### combine_columns

Concatenate columns with a separator (COMBINE task).

```python
view.combine_columns(
    sources: list[str],
    new_column: str | None = None,
    column_type: ColumnType = ColumnType.TEXT,
    existing_column: str | None = None,
    separator: str = " ",
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
view.combine_columns(
    sources=["First Name", "Last Name"],
    new_column="Full Name",
    separator=" ",
)
```

### convert_type

Convert column data types (CONVERT task).

```python
view.convert_type(conversions: list[ConversionSpec]) -> dict
```

```python
from mammoth import ConversionSpec, ColumnType

view.convert_type([
    ConversionSpec(column="Sales", to=ColumnType.NUMERIC),
    ConversionSpec(column="Date", to=ColumnType.DATE),
])
```

### text_transform

Change text case or trim whitespace (TEXT_TRANSFORM task).

```python
view.text_transform(
    columns: list[str],
    case: TextCase | None = None,
    trim: bool = False,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
from mammoth import TextCase

view.text_transform(columns=["Name"], case=TextCase.UPPER)
view.text_transform(columns=["Notes"], trim=True)
```

### replace_values

Find and replace text (REPLACE task).

```python
view.replace_values(
    columns: list[str],
    find: str,
    replace: str,
    match_case: bool = False,
    match_words: bool = False,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
view.replace_values(columns=["Status"], find="N/A", replace="Unknown")
```

### bulk_replace

Bulk find-and-replace with multiple mappings (REPLACE with MAPPING).

```python
view.bulk_replace(
    columns: list[str],
    mapping: list[BulkReplaceMapping],
    match_case: bool = True,
    match_words: bool = False,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
from mammoth import BulkReplaceMapping

view.bulk_replace(
    columns=["Item"],
    mapping=[
        BulkReplaceMapping(search=["6 inch CAKE", "8 inch CAKE"], replace="CAKE"),
        BulkReplaceMapping(search=["Small Coffee", "Large Coffee"], replace="Coffee"),
    ],
)
```

### split_column

Split a column by delimiter (SPLIT task).

```python
view.split_column(
    column: str,
    delimiter: str,
    new_columns: list[SplitColumnSpec],
) -> dict[str, Any]
```

```python
from mammoth import SplitColumnSpec

view.split_column(
    column="Full Name",
    delimiter=" ",
    new_columns=[
        SplitColumnSpec(name="First Name"),
        SplitColumnSpec(name="Last Name"),
    ],
)
```

### substring

Extract a substring (SUBSTRING task).

```python
view.substring(
    column: str,
    direction: SubstringDirection | None = None,
    num_char: int | None = None,
    char_position: int | None = None,
    regex_pattern: str | None = None,
    regex_invert: bool = False,
    new_column: str | None = None,
    existing_column: str | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

| Direction | Use with | Meaning |
|-----------|----------|---------|
| `START` | `num_char` | First N characters |
| `END` | `num_char` | Last N characters |
| `LEFT` | `char_position` | Characters before position |
| `RIGHT` | `char_position` | Characters after position |

```python
from mammoth import SubstringDirection

# First 3 characters
view.substring("Code", direction=SubstringDirection.START, num_char=3, new_column="Prefix")

# Regex extraction
view.substring("Email", regex_pattern=r"@(.+)$", new_column="Domain")
```

### extract_date

Extract date components (EXTRACT_DATE task).

```python
view.extract_date(
    column: str,
    component: DateComponent,
    new_column: str | None = None,
    existing_column: str | None = None,
) -> dict[str, Any]
```

```python
from mammoth import DateComponent

view.extract_date("Order Date", DateComponent.YEAR, new_column="Order Year")
view.extract_date("Order Date", DateComponent.MONTH_TEXT, new_column="Month Name")
```

### date_diff

Calculate date difference (DATE_DIFF task).

```python
view.date_diff(
    component: DateDiffUnit,
    start: str,
    end: str,
    new_column: str | None = None,
    existing_column: str | None = None,
) -> dict[str, Any]
```

```python
from mammoth import DateDiffUnit

view.date_diff(
    DateDiffUnit.DAY,
    start="Start Date",
    end="End Date",
    new_column="Duration Days",
)
```

### increment_date

Add or subtract from a date (INCREMENT_DATE task).

```python
view.increment_date(
    column: str,
    delta: DateDelta,
    new_column: str | None = None,
    existing_column: str | None = None,
    condition: Condition | CompoundCondition | NotCondition | None = None,
) -> dict[str, Any]
```

```python
from mammoth import DateDelta

view.increment_date("Due Date", delta=DateDelta(days=30), new_column="Extended Due Date")
view.increment_date("Start Date", delta=DateDelta(months=-1, years=2), new_column="Adjusted")
```

### fill_missing

Fill missing values forward or backward (FILL task).

```python
view.fill_missing(
    column: str,
    direction: FillDirection,
    partition_by: str | None = None,
    order_by: list[list[str | SortDirection]] | None = None,
) -> dict[str, Any]
```

```python
from mammoth import FillDirection, SortDirection

view.fill_missing(
    "Price",
    direction=FillDirection.LAST_VALUE,
    order_by=[["Date", SortDirection.ASC]],
)
```

### limit_rows

Keep top or bottom N rows (LIMIT task).

```python
view.limit_rows(
    n: int,
    bottom: bool = False,
    order_by: list[list[str | SortDirection]] | None = None,
) -> dict[str, Any]
```

```python
view.limit_rows(100, order_by=[["Sales", SortDirection.DESC]])
```

### discard_duplicates

Remove duplicate rows (DISCARD_DUPLICATES task).

```python
view.discard_duplicates(
    ignore_columns: list[str] | None = None,
) -> dict[str, Any]
```

```python
view.discard_duplicates()
view.discard_duplicates(ignore_columns=["Timestamp", "Notes"])
```

### unnest

Unpivot columns to rows (UNNEST task).

```python
view.unnest(
    columns: list[str],
    label_column: str = "Label",
    value_column: str = "Value",
) -> dict[str, Any]
```

```python
view.unnest(
    columns=["Q1 Sales", "Q2 Sales", "Q3 Sales", "Q4 Sales"],
    label_column="Quarter",
    value_column="Sales",
)
```

### lookup

Look up values from another dataview (LOOKUP task).

```python
view.lookup(
    source: str,
    lookup_view_id: int,
    key: str,
    value: str,
    new_column: str | None = None,
    existing_column: str | None = None,
) -> dict[str, Any]
```

```python
view.lookup(
    source="Product Code",
    lookup_view_id=2050,
    key="code",         # key column in the lookup view
    value="name",       # value column in the lookup view
    new_column="Product Name",
)
```

### json_extract

Extract data from a JSON column (JSON_HANDLE task).

```python
view.json_extract(
    column: str,
    json_type: JsonType = JsonType.OBJECT,
    keys: list[str] | None = None,
    extractions: list[JsonExtractionSpec] | None = None,
    keep_source: bool = False,
    op_type: JsonOpType | None = None,
) -> dict[str, Any]
```

```python
from mammoth import JsonType, JsonExtractionSpec, ColumnType

# Simple key extraction
view.json_extract("data", keys=["name", "email", "age"])

# Advanced with custom types
view.json_extract(
    "data",
    extractions=[
        JsonExtractionSpec(key="name", as_name="Name", type=ColumnType.TEXT),
        JsonExtractionSpec(key="age", as_name="Age", type=ColumnType.NUMERIC),
    ],
)

# JSON list to rows
view.json_extract("items", json_type=JsonType.LIST)
```

### gen_ai

AI-powered transformation (GEN_AI task).

```python
view.gen_ai(
    prompt: str,
    context_columns: list[str],
    new_column: str = "AI Result",
    assistant_data: list[str] | None = None,
    context_columns_derivation: bool | None = None,
) -> dict[str, Any]
```

```python
view.gen_ai(
    prompt="Classify the sentiment of the review as positive, negative, or neutral",
    context_columns=["Review Text"],
    new_column="Sentiment",
)
```

### generate_sql

Generate SQL from a natural language intent using Mammoth's LLM. Returns the generated SQL string. Also adds the task to the pipeline automatically.

```python
view.generate_sql(intent: str) -> str
```

```python
sql = view.generate_sql("count employees by department")
print(sql)  # "SELECT department, COUNT(*) ..."
```

### add_sql

Add a raw SQL query as a pipeline task.

```python
view.add_sql(query: str) -> dict[str, Any]
```

```python
view.add_sql("SELECT department, COUNT(*) as cnt FROM data GROUP BY department")
```

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
