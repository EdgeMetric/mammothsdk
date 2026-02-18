# Transformations Reference

All transformation methods are on the `View` class. Each method:
1. Accepts display names (e.g. "Sales"), not internal names
2. Sends a pipeline task to the API
3. Waits for the async job to complete
4. Refreshes view metadata
5. Returns the API response dict

---

## Column Operations

### add_column(name, column_type="TEXT")

Add an empty column.

```python
view.add_column("Status", column_type="TEXT")
view.add_column("Score", column_type="NUMERIC")
```

### delete_columns(columns)

Remove columns by display name.

```python
view.delete_columns(["Notes", "Temp Column"])
```

### copy_columns(copies)

Duplicate columns.

```python
view.copy_columns([
    {"source": "Sales", "as": "Sales Backup", "type": "NUMERIC"},
    {"source": "Name", "as": "Name Copy", "type": "TEXT"},
])
```

### convert_type(conversions)

Change column data types. Required before date operations on CSV-uploaded text columns.

```python
view.convert_type([
    {"column": "joining_date", "to": "DATE"},
    {"column": "price", "to": "NUMERIC"},
])
```

---

## Filter & Select

### filter_rows(condition, filter_type="SHOW", prompt="")

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
view.filter_rows(Condition("Status", Operator.EQ, "Deleted"), filter_type="REMOVE")
```

**Payload**: `{"SELECT": "ALL", "CONDITION": {..., "FILTER_TYPE": "SHOW", "PROMPT": ""}}`

---

## SET (Label / Insert Values)

### set_values(values, new_column=None, column_type="TEXT", existing_column=None, condition=None)

Insert values into a new or existing column, optionally with conditions.

```python
# New column with conditional values (evaluated top-to-bottom, first match wins)
view.set_values(
    new_column="Risk Level",
    column_type="TEXT",
    values=[
        {"value": "High", "condition": Condition("Sales", Operator.GTE, 10000)},
        {"value": "Medium", "condition": Condition("Sales", Operator.GTE, 5000)},
        {"value": "Low"},  # default (no condition)
    ],
)

# Update existing column with a fixed value
view.set_values(
    existing_column="Status",
    values=[{"value": "Active"}],
)
```

**Payload**: `{"SET": {"VALUES": [{"PROVIDER_TYPE": "FIXED", "PROVIDER": val, "CONDITION": {...}}], "AS": {...}}, "VERSION": 2}`

---

## Math

### math(expression, new_column=None, column_type="NUMERIC", existing_column=None, condition=None)

Arithmetic operations between columns and constants.

```python
view.math(
    expression=[
        {"TYPE": "COLUMN", "VALUE": "Price"},
        {"TYPE": "OPERATOR", "VALUE": "*"},
        {"TYPE": "COLUMN", "VALUE": "Quantity"},
    ],
    new_column="Total",
)

# With a constant multiplier
view.math(
    expression=[
        {"TYPE": "COLUMN", "VALUE": "base_salary"},
        {"TYPE": "OPERATOR", "VALUE": "*"},
        {"TYPE": "NUMBER", "VALUE": 1.1},
    ],
    new_column="salary_with_raise",
)
```

Expression part types: `COLUMN`, `NUMBER`, `OPERATOR`
Operators: `+`, `-`, `*`, `/`

---

## Text Operations

### combine_columns(sources, new_column=None, separator=" ", existing_column=None, condition=None)

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
view.bulk_replace(
    columns=["Item"],
    mapping=[
        {"search": ["6 inch CAKE", "8 inch CAKE"], "replace": "CAKE"},
        {"search": ["small PIE", "large PIE"], "replace": "PIE"},
    ],
)
```

### text_transform(columns, case=None, trim=False, condition=None)

Change text case or trim whitespace.

```python
view.text_transform(columns=["department"], case="UPPER")
view.text_transform(columns=["name"], trim=True)
view.text_transform(columns=["city"], case="TITLE", trim=True)
```

Case values: `"UPPER"`, `"LOWER"`, `"TITLE"`

### split_column(column, delimiter, new_columns)

Split a column by delimiter into multiple new columns.

```python
view.split_column(
    column="Full Name",
    delimiter=" ",
    new_columns=[
        {"name": "First Name", "type": "TEXT"},
        {"name": "Last Name", "type": "TEXT"},
    ],
)
```

### substring(column, regex=None, direction=None, num_char=None, char_position=None, new_column=None, existing_column=None, condition=None)

Extract text from a column.

```python
# First 5 characters
view.substring(column="Name", direction="START", num_char=5, new_column="Prefix")

# Last 3 characters
view.substring(column="Code", direction="END", num_char=3, new_column="Suffix")

# Characters left of position 5
view.substring(column="Name", direction="LEFT", char_position=5, new_column="Left Part")

# Regex extraction
view.substring(
    column="Email",
    regex={"EXPRESSION": "@(.+)", "INVERT": False},
    new_column="Domain",
)
```

**Direction rules**:
- `START`/`END` + `num_char` → first/last N characters
- `LEFT`/`RIGHT` + `char_position` → characters left/right of position

---

## Date Operations

**Important**: CSV-uploaded date columns are TEXT. Convert first:
```python
view.convert_type([{"column": "date_col", "to": "DATE"}])
```

### extract_date(column, component, new_column=None, existing_column=None)

Extract a date component.

```python
view.extract_date("Order Date", component="year", new_column="Order Year")
view.extract_date("Order Date", component="month", new_column="Order Month")
view.extract_date("Order Date", component="weekday_text", new_column="Day Name")
```

Components (always lowercase): `year`, `month`, `day`, `hour`, `minute`, `second`, `week`, `quarter`, `day_of_week`, `day_of_year`, `weekday_text`, `month_text`, `year_month`, `year_week`, `year_quarter`, `month_day`, `hour_minute`, `date_only`

### date_diff(component, start, end, new_column=None, existing_column=None)

Calculate difference between two date columns.

```python
view.date_diff("DAY", start="Start Date", end="End Date", new_column="Duration")
view.date_diff("MONTH", start="Hire Date", end="Exit Date", new_column="Tenure Months")
```

Components (uppercase): `YEAR`, `MONTH`, `DAY`, `HOUR`, `MINUTE`, `SECOND`

### increment_date(column, delta, new_column=None, existing_column=None, condition=None)

Add or subtract from a date.

```python
view.increment_date(
    column="Order Date",
    delta={"DAY": 30},
    new_column="Due Date",
)

view.increment_date(
    column="Start Date",
    delta={"MONTH": -1, "DAY": 15},
    new_column="Adjusted Date",
)
```

Delta keys: `DAY`, `MONTH`, `YEAR`, `HOUR`, `MINUTE`, `SECOND`

---

## Row Operations

### fill_missing(column, direction, partition_by=None, order_by=None)

Fill missing values forward or backward.

```python
view.fill_missing(column="Price", direction="LAST_VALUE")
view.fill_missing(column="Category", direction="FIRST_VALUE")
```

Directions: `"FIRST_VALUE"` (forward fill), `"LAST_VALUE"` (backward fill)

### limit_rows(n, bottom=False, order_by=None)

Keep only the top or bottom N rows.

```python
view.limit_rows(n=10)
view.limit_rows(n=5, order_by=[["Sales", "DESC"]])
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
view.pivot(
    group_by=["department"],
    aggregations=[
        {"column": "base_salary", "function": "AVG", "as": "avg_salary"},
        {"column": "base_salary", "function": "COUNT", "as": "headcount"},
    ],
)

view.pivot(
    group_by=["Region", "Category"],
    aggregations=[
        {"column": "Sales", "function": "SUM", "as": "Total Sales"},
        {"column": "Profit", "function": "AVG", "as": "Avg Profit"},
    ],
)
```

Aggregate functions: `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`, `COUNT_DISTINCT`, `STDDEV`, `VARIANCE`, `MEDIAN`, `FIRST`, `LAST`, `CONCAT`

**Payload**: GROUP_BY uses `COLUMN`/`ORDER` keys. SELECT uses `FUNCTION`/`COLUMN`/`AS`/`ORDER` keys.

### crosstab(rows, pivot_column, select)

Pivot table: row values become columns.

```python
view.crosstab(
    rows=["Region"],
    pivot_column="Quarter",
    select={"column": "Sales", "function": "SUM"},
)
```

---

## Window Functions

### window(function, column=None, new_column=None, column_type="NUMERIC", existing_column=None, partition_by=None, order_by=None, range_type="UNBOUNDED")

Apply window functions.

```python
# Row number within partitions
view.window(
    function="ROW_NUMBER",
    new_column="Row #",
    partition_by=["department"],
    order_by=[["base_salary", "DESC"]],
)

# Running sum
view.window(
    function="SUM",
    column="Sales",
    new_column="Running Total",
    partition_by=["Region"],
    order_by=[["Order Date", "ASC"]],
)

# Rank
view.window(
    function="RANK",
    new_column="Sales Rank",
    partition_by=["Region"],
    order_by=[["Sales", "DESC"]],
)
```

Window functions: `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`, `LEAD`, `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`, `FIRST_VALUE`, `LAST_VALUE`, `STDDEV`, `VARIANCE`, `PERCENT_RANK`, `NTILE`

**Payload**: EVALUATE uses `FUNCTION`/`SOURCES`/`ARGUMENTS` keys. GROUP_BY uses `COLUMN` key.

---

## Join

### join(foreign_view_id, join_type, on, select, column_prefix=None)

Join with another dataview.

```python
view.join(
    foreign_view_id=2050,
    join_type="LEFT",
    on=[{"left": "Customer ID", "right": "column_1"}],
    select=[
        {"column": "column_7", "alias": "Category"},
        {"column": "column_8", "alias": "Segment"},
    ],
)
```

- `on.left`: Display name in this view (resolved to internal)
- `on.right`: Internal column name in the foreign view
- `select.column`: Internal column name in the foreign view
- `select.alias`: Display name for the joined column

Join types: `"INNER"`, `"LEFT"`, `"RIGHT"`, `"OUTER"`

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

### sql(intent) -> dict

Combined convenience method: generates SQL from intent and adds pipeline task.

```python
result = view.sql("count employees by department")
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

### json_extract(column, json_type="object", extractions=None, keep_source=False, op_type=None)

Extract data from JSON columns.

```python
# Object: extract specific keys
view.json_extract(
    column="metadata",
    json_type="object",
    extractions=[
        {"key": "name", "as": "Name", "type": "TEXT"},
        {"key": "age", "as": "Age", "type": "NUMERIC"},
    ],
)

# List: expand to rows
view.json_extract(
    column="tags",
    json_type="list",
)
```

**Payload**: TYPE is `"JSON_OBJECT"`/`"JSON_LIST"`. Requires `JSON_OBJECT_OP_TYPE` or `JSON_LIST_OP_TYPE`.

---

## AI

### gen_ai(prompt, context_columns, new_column="AI Result", assistant_data=None)

AI-powered transformation using LLM.

```python
view.gen_ai(
    prompt="Classify the sentiment of the review",
    context_columns=["Review Text"],
    new_column="Sentiment",
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

### Expression Parts for Math

```python
{"TYPE": "COLUMN", "VALUE": "display_name"}   # column reference
{"TYPE": "NUMBER", "VALUE": 42}               # numeric constant
{"TYPE": "OPERATOR", "VALUE": "+"}            # operator: +, -, *, /
```
