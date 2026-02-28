# Transformations Reference

All transformation methods are on the `View` class. Each method:
1. Accepts display names (e.g. "Sales"), not internal names
2. Sends a pipeline task to the API
3. Blocks until the operation completes (unless in draft mode)
4. Refreshes view metadata (unless in draft mode)
5. Returns the API response dict

---

## Column Operations

### add_column(name, column_type=ColumnType.TEXT)

Add an empty column.

```python
from mammoth import ColumnType

view.add_column("Status", column_type=ColumnType.TEXT)
view.add_column("Score", column_type=ColumnType.NUMERIC)
```

### delete_columns(columns)

Remove columns by display name.

```python
view.delete_columns(["Notes", "Temp Column"])
```

### copy_columns(copies)

Duplicate columns.

```python
from mammoth import CopySpec, ColumnType

view.copy_columns([
    CopySpec(source="Sales", as_name="Sales Backup", type=ColumnType.NUMERIC),
    CopySpec(source="Name", as_name="Name Copy"),
])
```

### convert_type(conversions)

Change column data types. Required before date operations on CSV-uploaded text columns.

```python
from mammoth import ConversionSpec, ColumnType

view.convert_type([
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
view.filter_rows(Condition("Sales", Operator.GTE, 1000))

# Compound filter
view.filter_rows(
    Condition("department", Operator.EQ, "Engineering")
    & Condition("base_salary", Operator.GTE, 80000)
)

# OR filter
view.filter_rows(
    Condition("department", Operator.EQ, "Engineering")
    | Condition("department", Operator.EQ, "Sales")
)

# Remove matching rows instead of keeping them
from mammoth import FilterType
view.filter_rows(Condition("Status", Operator.EQ, "Deleted"), filter_type=FilterType.REMOVE)
```

**Payload**: `{"SELECT": "ALL", "CONDITION": {..., "FILTER_TYPE": "SHOW", "PROMPT": ""}}`

---

## SET (Label / Insert Values)

### set_values(values, new_column=None, column_type=ColumnType.TEXT, existing_column=None, condition=None)

Insert values into a new or existing column, optionally with conditions.

```python
from mammoth import SetValue, Condition, Operator, ColumnType

# New column with conditional values (evaluated top-to-bottom, first match wins)
view.set_values(
    new_column="Risk Level",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Medium", condition=Condition("Sales", Operator.GTE, 5000)),
        SetValue("Low"),  # default (no condition)
    ],
)

# Update existing column with a fixed value
view.set_values(
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
view.math("Price * Quantity", new_column="Total")

# With a constant multiplier
view.math("base_salary * 1.1", new_column="salary_with_raise")

# Complex expression
view.math("(Revenue - Cost) / Revenue * 100", new_column="Margin %")
```

String expression parser: column names are auto-resolved, supports `+`, `-`, `*`, `/`, `%`, and parentheses.

---

## Text Operations

### combine_columns(sources, new_column=None, column_type=ColumnType.TEXT, existing_column=None, separator=" ", condition=None)

Concatenate multiple columns with a separator.

```python
view.combine_columns(
    sources=["First Name", "Last Name"],
    separator=" ",
    new_column="Full Name",
)

view.combine_columns(
    sources=["City", "State", "Country"],
    separator=", ",
    new_column="Full Address",
)
```

**Payload**: Alternating `{"COLUMN": internal_name}` and `{"STRING": separator}` items in SOURCE array.

### replace_values(columns, find, replace, match_case=False, match_words=False, condition=None)

Find and replace text values.

```python
view.replace_values(
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

view.bulk_replace(
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

view.text_transform(columns=["department"], case=TextCase.UPPER)
view.text_transform(columns=["name"], trim=True)
view.text_transform(columns=["city"], case=TextCase.TITLE, trim=True)
```

Case values: `TextCase.UPPER`, `TextCase.LOWER`, `TextCase.TITLE`

### split_column(column, delimiter, new_columns)

Split a column by delimiter into multiple new columns.

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

### substring(column, direction=None, num_char=None, char_position=None, regex_pattern=None, regex_invert=False, new_column=None, existing_column=None, condition=None)

Extract text from a column.

```python
from mammoth import SubstringDirection

# First 5 characters
view.substring("Name", direction=SubstringDirection.START, num_char=5, new_column="Prefix")

# Last 3 characters
view.substring("Code", direction=SubstringDirection.END, num_char=3, new_column="Suffix")

# Characters left of position 5
view.substring("Name", direction=SubstringDirection.LEFT, char_position=5, new_column="Left Part")

# Regex extraction (use regex_pattern string, NOT a dict)
view.substring(
    "Email",
    regex_pattern=r"@(.+)",
    new_column="Domain",
)

# Inverted regex (return the non-matching part)
view.substring(
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
view.convert_type([ConversionSpec(column="date_col", to=ColumnType.DATE)])
```

### extract_date(column, component, new_column=None, existing_column=None)

Extract a date component.

```python
from mammoth import DateComponent

view.extract_date("Order Date", component=DateComponent.YEAR, new_column="Order Year")
view.extract_date("Order Date", component=DateComponent.MONTH, new_column="Order Month")
view.extract_date("Order Date", component=DateComponent.WEEKDAY_TEXT, new_column="Day Name")
```

Components (always lowercase): `year`, `month`, `day`, `hour`, `minute`, `second`, `week`, `quarter`, `day_of_week`, `day_of_year`, `weekday_text`, `month_text`, `year_month`, `year_week`, `year_quarter`, `month_day`, `hour_minute`, `date_only`

### date_diff(component, start, end, new_column=None, existing_column=None)

Calculate difference between two date columns.

```python
from mammoth import DateDiffUnit

view.date_diff(DateDiffUnit.DAY, start="Start Date", end="End Date", new_column="Duration")
view.date_diff(DateDiffUnit.MONTH, start="Hire Date", end="Exit Date", new_column="Tenure Months")
```

Components (uppercase): `YEAR`, `MONTH`, `DAY`, `HOUR`, `MINUTE`, `SECOND`

### increment_date(column, delta, new_column=None, existing_column=None, condition=None)

Add or subtract from a date.

```python
from mammoth import DateDelta

view.increment_date(
    column="Order Date",
    delta=DateDelta(days=30),
    new_column="Due Date",
)

view.increment_date(
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

view.fill_missing(column="Price", direction=FillDirection.LAST_VALUE)
view.fill_missing(column="Category", direction=FillDirection.FIRST_VALUE)
```

Directions: `FillDirection.FIRST_VALUE` (forward fill), `FillDirection.LAST_VALUE` (backward fill)

### limit_rows(n, bottom=False, order_by=None)

Keep only the top or bottom N rows.

```python
view.limit_rows(n=10)
view.limit_rows(n=5, order_by=[["Sales", SortDirection.DESC]])
view.limit_rows(n=5, bottom=True)
```

### discard_duplicates(ignore_columns=None)

Remove duplicate rows.

```python
view.discard_duplicates()
view.discard_duplicates(ignore_columns=["Timestamp", "Notes"])
```

---

## Aggregation

### pivot(group_by, aggregations, condition=None)

Group by columns and apply aggregation functions.

```python
from mammoth import AggregationSpec, AggregateFunction

view.pivot(
    group_by=["department"],
    aggregations=[
        AggregationSpec(column="base_salary", function=AggregateFunction.AVG, as_name="avg_salary"),
        AggregationSpec(column="base_salary", function=AggregateFunction.COUNT, as_name="headcount"),
    ],
)

view.pivot(
    group_by=["Region", "Category"],
    aggregations=[
        AggregationSpec(column="Sales", function=AggregateFunction.SUM, as_name="Total Sales"),
        AggregationSpec(column="Profit", function=AggregateFunction.AVG, as_name="Avg Profit"),
    ],
)
```

Aggregate functions: `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`, `COUNT_DISTINCT`, `STDDEV`, `VARIANCE`, `MEDIAN`, `FIRST`, `LAST`, `CONCAT`

**Payload**: GROUP_BY uses `COLUMN`/`ORDER` keys. SELECT uses `FUNCTION`/`COLUMN`/`AS`/`ORDER` keys.

### crosstab(rows, pivot_column, select)

Pivot table: row values become columns.

```python
from mammoth import CrosstabSpec, AggregateFunction

view.crosstab(
    rows=["Region"],
    pivot_column="Quarter",
    select=CrosstabSpec(function=AggregateFunction.SUM, column="Sales"),
)
```

---

## Window Functions

### window(function, column=None, new_column=None, column_type=ColumnType.NUMERIC, existing_column=None, partition_by=None, order_by=None, range_type=WindowRange.UNBOUNDED)

Apply window functions.

```python
from mammoth import WindowFunction, SortDirection

# Row number within partitions
view.window(
    function=WindowFunction.ROW_NUMBER,
    new_column="Row #",
    partition_by=["department"],
    order_by=[["base_salary", SortDirection.DESC]],
)

# Running sum
view.window(
    function=WindowFunction.SUM,
    column="Sales",
    new_column="Running Total",
    partition_by=["Region"],
    order_by=[["Order Date", SortDirection.ASC]],
)

# Rank
view.window(
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

### join(foreign_view, join_type, on, select, column_prefix=None)

Join with another dataview.

```python
from mammoth import JoinType, JoinKeySpec, JoinSelectSpec

# Join with View object (recommended — auto-resolves display names)
other = client.views.get(2050)
view.join(
    foreign_view=other,
    join_type=JoinType.LEFT,
    on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
    select=["Category", "Segment"],
)

# Join with view ID (use internal column names for the foreign view)
view.join(
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

### lookup(source, lookup_view_id, key, value, new_column=None, existing_column=None)

Lookup values from another dataview (like VLOOKUP).

```python
view.lookup(
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

Generate SQL from natural language using the LLM backend.

```python
sql = view.generate_sql("count employees by department")
# Returns: "SELECT department, COUNT(*) FROM ... GROUP BY department"
```

### add_sql(query) -> dict

Add a raw SQL query as a pipeline task.

```python
view.add_sql("SELECT department, AVG(base_salary) FROM __THIS__ GROUP BY department")
```

---

## Unnest (Unpivot)

### unnest(columns, label_column="Label", value_column="Value")

Unpivot columns to rows.

```python
view.unnest(
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
view.json_extract("metadata", keys=["name", "email", "age"])

# Advanced: extract with custom types and aliases
view.json_extract(
    "metadata",
    json_type=JsonType.OBJECT,
    extractions=[
        JsonExtractionSpec(key="name", as_name="Name"),
        JsonExtractionSpec(key="age", as_name="Age", type=ColumnType.NUMERIC),
    ],
)

# List: expand to rows
view.json_extract("tags", json_type=JsonType.LIST)
```

**Payload**: TYPE is `"JSON_OBJECT"`/`"JSON_LIST"`. Requires `JSON_OBJECT_OP_TYPE` or `JSON_LIST_OP_TYPE`.

---

## AI

### gen_ai(prompt, context_columns, new_column="AI Result", assistant_data=None, context_columns_derivation=None)

AI-powered transformation using LLM.

```python
view.gen_ai(
    prompt="Classify the sentiment of the review",
    context_columns=["Review Text"],
    new_column="Sentiment",
)

# With derivation context
view.gen_ai(
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
view.math("Price * Quantity", new_column="Total")
view.math("(Revenue - Cost) / Revenue * 100", new_column="Margin")
```

Column names are auto-resolved. Supports: `+`, `-`, `*`, `/`, `%`, and parentheses.

