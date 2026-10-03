# Transformations Reference

All transformation methods are on the `View` class. Each method:
1. Accepts display names (e.g. "Sales"), not internal names
2. Sends a pipeline task to the API
3. Returns, once awaited, when the operation completes (unless in draft mode)
4. Refreshes view metadata (unless in draft mode)
5. Returns the add-task response; outside draft mode `status` is `"done"` and `pipeline_state` the final state (0.7.14+). Do not poll its `future_id`

---

## Column Operations

### add_column(name, column_type=ColumnType.TEXT)

Add an empty column.

```python
from mammoth import ColumnType

await view.add_column("Status", column_type=ColumnType.TEXT)
await view.add_column("Score", column_type=ColumnType.NUMERIC)
```

### delete_columns(columns)

Remove columns by display name.

```python
await view.delete_columns(["Notes", "Temp Column"])
```

### copy_columns(copies)

Duplicate columns.

```python
from mammoth import CopySpec, ColumnType

await view.copy_columns([
    CopySpec(source="Sales", as_name="Sales Backup", type=ColumnType.NUMERIC),
    CopySpec(source="Name", as_name="Name Copy"),
])
```

### convert_type(conversions)

Change column data types. Required before date operations on CSV-uploaded text columns.

```python
from mammoth import ConversionSpec, ColumnType

await view.convert_type([
    ConversionSpec(column="joining_date", to=ColumnType.DATE),
    ConversionSpec(column="price", to=ColumnType.NUMERIC),
])
```

---

## Filter & Select

### filter_rows(condition, filter_type=FilterType.SHOW, prompt="")

Filter rows by condition.

```python
# Simple filter
await view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Compound filter
await view.filter_rows(
    Condition("department", Operator.EQ, "Engineering")
    & Condition("base_salary", Operator.GTE, 80000)
)

# OR filter
await view.filter_rows(
    Condition("department", Operator.EQ, "Engineering")
    | Condition("department", Operator.EQ, "Sales")
)

# Remove matching rows instead of keeping them
from mammoth import FilterType
await view.filter_rows(Condition("Status", Operator.EQ, "Deleted"), filter_type=FilterType.REMOVE)
```

**Payload**: `{"SELECT": "ALL", "CONDITION": {..., "FILTER_TYPE": "SHOW", "PROMPT": ""}}`

---

## SET (Label / Insert Values)

### set_values(values, new_column=None, column_type=ColumnType.TEXT, existing_column=None, condition=None)

Insert values into a new or existing column, optionally with conditions.

```python
from mammoth import SetValue, Condition, Operator, ColumnType

# New column with conditional values (evaluated top-to-bottom, first match wins)
await view.set_values(
    new_column="Risk Level",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Medium", condition=Condition("Sales", Operator.GTE, 5000)),
        SetValue("Low"),  # default (no condition)
    ],
)

# Update existing column with a fixed value
await view.set_values(
    existing_column="Status",
    values=[SetValue("Active")],
)
```

**Payload**: `{"SET": {"VALUES": [{"PROVIDER_TYPE": "FIXED", "PROVIDER": val, "CONDITION": {...}}], "AS": {...}}, "VERSION": 2}`

---

## Math

### math(expression, new_column=None, column_type=ColumnType.NUMERIC, existing_column=None, condition=None)

Arithmetic operations between columns and constants.

```python
# String expression — column names resolved automatically
await view.math("Price * Quantity", new_column="Total")

# With a constant multiplier
await view.math("base_salary * 1.1", new_column="salary_with_raise")

# Complex expression
await view.math("(Revenue - Cost) / Revenue * 100", new_column="Margin %")
```

String expression parser: column names are auto-resolved, supports `+`, `-`, `*`, `/`, `%`, and parentheses. A multi-word name works bare (`Unit Price * Quantity`) or quoted (`"Unit Price"` or `` `Unit Price` ``, 0.7.15+).

### small_large(function, columns, index=1, constants=None, new_column=None, existing_column=None)

Per row, write the `index`-th smallest or largest value among `columns` (and optional numeric `constants`) to a new or existing column; give exactly one of `new_column` / `existing_column`.

```python
from mammoth import SmallLargeFunction

await view.small_large(SmallLargeFunction.LARGE, columns=["Q1", "Q2", "Q3"], index=2, new_column="2nd Best")
```

---

## Text Operations

### combine_columns(sources, new_column=None, column_type=ColumnType.TEXT, existing_column=None, separator=" ", condition=None)

Concatenate multiple columns with a separator.

```python
await view.combine_columns(
    sources=["First Name", "Last Name"],
    separator=" ",
    new_column="Full Name",
)

await view.combine_columns(
    sources=["City", "State", "Country"],
    separator=", ",
    new_column="Full Address",
)
```

**Payload**: Alternating `{"COLUMN": internal_name}` and `{"STRING": separator}` items in SOURCE array.

### replace_values(columns, find, replace, match_case=False, match_words=False, condition=None)

Find and replace text values.

```python
await view.replace_values(
    columns=["department"],
    find="Engineering",
    replace="Eng",
)
```

**Payload**: Uses `SEARCH_VALUE`/`REPLACE_VALUE` keys (not FIND/REPLACE).

### bulk_replace(columns, mapping, match_case=True, match_words=False, condition=None)

Bulk find-and-replace mapping multiple search values to one replacement.

```python
from mammoth import BulkReplaceMapping

await view.bulk_replace(
    columns=["Item"],
    mapping=[
        BulkReplaceMapping(search=["6 inch CAKE", "8 inch CAKE"], replace="CAKE"),
        BulkReplaceMapping(search=["small PIE", "large PIE"], replace="PIE"),
    ],
)
```

### text_transform(columns, case=None, trim=False, condition=None)

Change text case or trim whitespace.

```python
from mammoth import TextCase

await view.text_transform(columns=["department"], case=TextCase.UPPER)
await view.text_transform(columns=["name"], trim=True)
await view.text_transform(columns=["city"], case=TextCase.TITLE, trim=True)
```

Case values: `TextCase.UPPER`, `TextCase.LOWER`, `TextCase.TITLE`

### split_column(column, delimiter, new_columns)

Split a column by delimiter into multiple new columns.

```python
from mammoth import SplitColumnSpec

await view.split_column(
    column="Full Name",
    delimiter=" ",
    new_columns=[
        SplitColumnSpec(name="First Name"),
        SplitColumnSpec(name="Last Name"),
    ],
)
```

### substring(column, direction=None, num_char=None, char_position=None, regex_pattern=None, regex_invert=False, new_column=None, existing_column=None, condition=None)

Extract text from a column.

```python
from mammoth import SubstringDirection

# First 5 characters
await view.substring("Name", direction=SubstringDirection.START, num_char=5, new_column="Prefix")

# Last 3 characters
await view.substring("Code", direction=SubstringDirection.END, num_char=3, new_column="Suffix")

# Characters left of position 5
await view.substring("Name", direction=SubstringDirection.LEFT, char_position=5, new_column="Left Part")

# Regex extraction (use regex_pattern string, NOT a dict)
await view.substring(
    "Email",
    regex_pattern=r"@(.+)",
    new_column="Domain",
)

# Inverted regex (return the non-matching part)
await view.substring(
    "Phone",
    regex_pattern=r"\d{3}-",
    regex_invert=True,
    new_column="Without Area Code",
)
```

**Direction rules**:
- `START`/`END` + `num_char` → first/last N characters
- `LEFT`/`RIGHT` + `char_position` → characters left/right of position

---

## Date Operations

**Important**: CSV-uploaded date columns are TEXT. Convert first:
```python
from mammoth import ConversionSpec, ColumnType
await view.convert_type([ConversionSpec(column="date_col", to=ColumnType.DATE)])
```

### extract_date(column, component, new_column=None, existing_column=None)

Extract a date component.

```python
from mammoth import DateComponent

await view.extract_date("Order Date", component=DateComponent.YEAR, new_column="Order Year")
await view.extract_date("Order Date", component=DateComponent.MONTH, new_column="Order Month")
await view.extract_date("Order Date", component=DateComponent.WEEKDAY_TEXT, new_column="Day Name")
```

Components (always lowercase): `year`, `month`, `day`, `hour`, `minute`, `second`, `week`, `quarter`, `day_of_week`, `day_of_year`, `weekday_text`, `month_text`, `year_month`, `year_week`, `year_quarter`, `month_day`, `hour_minute`, `date_only`

### date_diff(component, start, end, new_column=None, existing_column=None)

Calculate difference between two date columns.

```python
from mammoth import DateDiffUnit

await view.date_diff(DateDiffUnit.DAY, start="Start Date", end="End Date", new_column="Duration")
await view.date_diff(DateDiffUnit.MONTH, start="Hire Date", end="Exit Date", new_column="Tenure Months")
```

Components (uppercase): `YEAR`, `MONTH`, `DAY`, `HOUR`, `MINUTE`, `SECOND`

### increment_date(column, delta, new_column=None, existing_column=None, condition=None)

Add or subtract from a date.

```python
from mammoth import DateDelta

await view.increment_date(
    column="Order Date",
    delta=DateDelta(days=30),
    new_column="Due Date",
)

await view.increment_date(
    column="Start Date",
    delta=DateDelta(months=-1, days=15),
    new_column="Adjusted Date",
)
```

Delta fields: `days`, `months`, `years`, `hours`, `minutes`, `seconds` (use negative values to subtract)

---

## Row Operations

### fill_missing(column, direction, partition_by=None, order_by=None)

Fill missing values forward or backward.

```python
from mammoth import FillDirection

await view.fill_missing(column="Price", direction=FillDirection.LAST_VALUE)
await view.fill_missing(column="Category", direction=FillDirection.FIRST_VALUE)
```

Directions: `FillDirection.FIRST_VALUE` (forward fill), `FillDirection.LAST_VALUE` (backward fill)

### limit_rows(n, bottom=False, order_by=None)

Keep only the top or bottom N rows.

```python
await view.limit_rows(n=10)
await view.limit_rows(n=5, order_by=[["Sales", SortDirection.DESC]])
await view.limit_rows(n=5, bottom=True)
```

### sort_rows(order_by) and rename_columns(renames)

View settings, like the web grid's sort and column rename: no pipeline task
is added. Data reads and exports use the order and the new names.

```python
await view.sort_rows([["Sales", "DESC"]])          # up to three columns; [] clears
await view.rename_columns({"cust_id": "Customer ID"})
```

### discard_duplicates(ignore_columns=None)

Remove duplicate rows.

```python
await view.discard_duplicates()
await view.discard_duplicates(ignore_columns=["Timestamp", "Notes"])
```

---

## Aggregation

### pivot(group_by, aggregations, condition=None)

Group by columns and apply aggregation functions.

```python
from mammoth import AggregationSpec, AggregateFunction

await view.pivot(
    group_by=["department"],
    aggregations=[
        AggregationSpec(column="base_salary", function=AggregateFunction.AVG, as_name="avg_salary"),
        AggregationSpec(column="base_salary", function=AggregateFunction.COUNT, as_name="headcount"),
    ],
)

await view.pivot(
    group_by=["Region", "Category"],
    aggregations=[
        AggregationSpec(column="Sales", function=AggregateFunction.SUM, as_name="Total Sales"),
        AggregationSpec(column="Profit", function=AggregateFunction.AVG, as_name="Avg Profit"),
    ],
)
```

Aggregate functions: `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`, `COUNT_DISTINCT`, `STDDEV`, `VARIANCE`, `MEDIAN`, `FIRST`, `LAST`, `CONCAT`

**Payload**: GROUP_BY uses `COLUMN`/`ORDER` keys. SELECT uses `FUNCTION`/`COLUMN`/`AS`/`ORDER` keys.

### crosstab(rows, pivot_column, select, *, dataset_name, save_as_mode=SaveAsDatasetMode.REPLACE, target_ds_id=None, condition=None, timeout=None)

Pivot table: row values become columns. Unlike other transforms it does not edit the view: it writes a NEW dataset (or `target_ds_id`, replacing or appending per `save_as_mode`) through an export job, waits for it, and returns the dataset id. `dataset_name` is required.

```python
from mammoth import CrosstabSpec, AggregateFunction

await view.crosstab(
    rows=["Region"],
    pivot_column="Quarter",
    select=CrosstabSpec(function=AggregateFunction.SUM, column="Sales"),
    dataset_name="Sales by Region x Quarter",
)
```

---

## Window Functions

### window(function, column=None, new_column=None, column_type=ColumnType.NUMERIC, existing_column=None, partition_by=None, order_by=None, range_type=WindowRange.UNBOUNDED)

Apply window functions.

```python
from mammoth import WindowFunction, SortDirection

# Row number within partitions
await view.window(
    function=WindowFunction.ROW_NUMBER,
    new_column="Row #",
    partition_by=["department"],
    order_by=[["base_salary", SortDirection.DESC]],
)

# Running sum
await view.window(
    function=WindowFunction.SUM,
    column="Sales",
    new_column="Running Total",
    partition_by=["Region"],
    order_by=[["Order Date", SortDirection.ASC]],
)

# Rank
await view.window(
    function=WindowFunction.RANK,
    new_column="Sales Rank",
    partition_by=["Region"],
    order_by=[["Sales", SortDirection.DESC]],
)
```

Window functions: `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`, `LEAD`, `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`, `FIRST_VALUE`, `LAST_VALUE`, `STDDEV`, `VARIANCE`, `PERCENT_RANK`, `NTILE`

**Payload**: EVALUATE uses `FUNCTION`/`SOURCES`/`ARGUMENTS` keys. GROUP_BY uses `COLUMN` key.

---

## Join

### join(foreign_view, join_type, on, select, column_prefix=None, foreign_dataset_id=None)

Join with another dataview. Pass `foreign_dataset_id` with an ID-only `foreign_view` so metadata is read from that dataset instead of probing parents.

```python
from mammoth import JoinType, JoinKeySpec, JoinSelectSpec

# Join with View object (recommended — auto-resolves display names)
other = await client.views.get(2050)
await view.join(
    foreign_view=other,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
    select=["Category", "Segment"],
)

# Join with view ID (use internal column names for the foreign view)
await view.join(
    foreign_view=2050,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="column_1")],
    select=[
        JoinSelectSpec(column="column_7", alias="Category"),
        JoinSelectSpec(column="column_8", alias="Segment"),
    ],
)
```

- `foreign_view`: View object (display names auto-resolved) or int view ID (requires internal names for right-side keys and select columns)
- `on`: list of `JoinKeySpec` -- when using a View object, both sides accept display names; when using an int ID, `right` must be internal names
- `select`: list of display names (str) when using a View object, or `JoinSelectSpec` for aliasing with internal names when using an int ID

Join types: `JoinType.INNER`, `JoinType.LEFT`, `JoinType.RIGHT`, `JoinType.OUTER`

**Payload**: ON uses `LEFT`/`RIGHT` keys. SELECT uses `COLUMN`/`ALIAS` keys.

---

## Lookup

### lookup(source, lookup_view_id, key, value, new_column=None, new_column_type="TEXT", existing_column=None, lookup_dataset_id=None)

Lookup values from another dataview (like VLOOKUP). The new column is TEXT unless you pass `new_column_type` (use the real type of `value` for numbers or dates, or they will not sum or sort). `lookup_dataset_id` names the parent dataset of an ID-only lookup view.

```python
await view.lookup(
    source="Product ID",        # column in this view
    lookup_view_id=3000,        # foreign view
    key="column_1",             # key column in foreign view (internal name)
    value="column_3",           # value column in foreign view (internal name)
    new_column="Product Name",
)
```

**Payload**: Uses `DATAVIEW_ID` for the lookup view reference.

---

## SQL

### generate_sql(intent) -> str

Generate SQL from natural language using the LLM backend. It returns the
query only; the view does not change until you pass it to `add_sql`.

```python
sql = await view.generate_sql("count employees by department")
# Returns: "SELECT department, COUNT(*) FROM ... GROUP BY department"
await view.add_sql(sql)  # apply it
```

### add_sql(query) -> dict

Add a raw SQL query as a pipeline task. Reference the view as the quoted table
`"view:<dataview_id>"` (or its quoted display name) and columns by display name;
placeholder table names are rejected. The result replaces the view's columns.

```python
await view.add_sql('SELECT department, AVG(base_salary) FROM "view:123" GROUP BY department')
```

---

## Unnest (Unpivot)

### unnest(columns, label_column="Label", value_column="Value", value_type=None)

Unpivot columns to rows. `value_type` is derived when left unset (one shared type is kept; mixed types fall back to TEXT).

```python
await view.unnest(
    columns=["Q1 Sales", "Q2 Sales", "Q3 Sales", "Q4 Sales"],
    label_column="Quarter",
    value_column="Amount",
)
```

**Payload**: COLUMNS items use `COLUMN`/`LABEL` keys.

---

## JSON

### json_extract(column, json_type=JsonType.OBJECT, keys=None, extractions=None, keep_source=False, op_type=None)

Extract data from JSON columns.

```python
from mammoth import JsonExtractionSpec, JsonType, JsonOpType, ColumnType

# Simple shorthand: extract keys by name (all as TEXT)
await view.json_extract("metadata", keys=["name", "email", "age"])

# Advanced: extract with custom types and aliases
await view.json_extract(
    "metadata",
    json_type=JsonType.OBJECT,
    extractions=[
        JsonExtractionSpec(key="name", as_name="Name"),
        JsonExtractionSpec(key="age", as_name="Age", type=ColumnType.NUMERIC),
    ],
)

# List: expand to rows
await view.json_extract("tags", json_type=JsonType.LIST)
```

**Payload**: TYPE is `"JSON_OBJECT"`/`"JSON_LIST"`. Requires `JSON_OBJECT_OP_TYPE` or `JSON_LIST_OP_TYPE`.

---

## AI

### gen_ai(prompt, context_columns, new_column="AI Result", assistant_data=None, context_columns_derivation=None)

AI-powered transformation using LLM.

```python
await view.gen_ai(
    prompt="Classify the sentiment of the review",
    context_columns=["Review Text"],
    new_column="Sentiment",
)

# With derivation context
await view.gen_ai(
    prompt="Summarize the order details",
    context_columns=["Product", "Quantity", "Price"],
    new_column="Summary",
    context_columns_derivation=True,
)
```

**Payload**: Uses lowercase `query` and `context_columns` keys (AI_KEYWORDS convention).

---

## Common Patterns

### Target Column: New vs Existing

Most methods accept both `new_column` and `existing_column`:
- `new_column="Name"` → creates a new column (uses `AS` key in payload)
- `existing_column="Name"` → overwrites existing column (uses `DESTINATION` key in payload)
- Provide exactly one (mutually exclusive)

### Conditional Transformations

Many methods accept an optional `condition` parameter that limits which rows are affected:
- `set_values`, `math`, `combine_columns`, `replace_values`, `text_transform`, `substring`, `increment_date`, `bulk_replace`

### Math String Expressions

```python
await view.math("Price * Quantity", new_column="Total")
await view.math("(Revenue - Cost) / Revenue * 100", new_column="Margin")
```

Column names are auto-resolved. Supports: `+`, `-`, `*`, `/`, `%`, and parentheses.

