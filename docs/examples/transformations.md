# Transformation Examples

Practical examples of common data transformation workflows using the Mammoth SDK.

## Setup

All examples assume the following setup:

```python
from mammoth import (
    MammothClient, Condition, CompoundCondition, Operator,
    ColumnType, SetValue, JoinType, AggregateFunction,
    WindowFunction, SortDirection, WindowRange, DateComponent,
    DateDiffUnit, TextCase, FillDirection, SubstringDirection,
    FilterType, JsonType,
)

client = MammothClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    workspace_id=11,
)
client.set_project_id(10)

view = client.views.get(1039)
```

---

## Filtering and labeling

### Filter to high-value rows

```python
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
```

### Filter with multiple conditions

```python
# Keep rows where Sales >= 1000 AND Region is "West"
view.filter_rows(
    Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
)

# Remove rows where Status is empty
view.filter_rows(
    Condition("Status", Operator.IS_EMPTY),
    filter_type=FilterType.REMOVE,
)
```

### Create a label column

```python
view.set_values(
    new_column="Tier",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Enterprise", condition=Condition("Revenue", Operator.GTE, 100000)),
        SetValue("Mid-Market", condition=Condition("Revenue", Operator.GTE, 10000)),
        SetValue("SMB"),
    ],
)
```

### Flag rows with a boolean column

```python
view.set_values(
    new_column="Is High Value",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Yes", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("No"),
    ],
)
```

---

## Math and calculations

### Compute a new column

```python
view.math("Price * Quantity", new_column="Total")
view.math("(Price + Tax) * 1.1", new_column="Grand Total")
```

### Update an existing column

```python
view.math("Sales * 1.1", existing_column="Sales")
```

### Conditional math

```python
view.math(
    "Price * 0.9",
    existing_column="Price",
    condition=Condition("Region", Operator.EQ, "West"),
)
```

---

## Joining views

### Left join with a View object

When you pass a View object, you can use display names for both sides:

```python
customers = client.views.get(2050)

view.join(
    foreign_view=customers,
    join_type=JoinType.LEFT,
    on=[{"left": "Customer ID", "right": "Customer ID"}],
    select=["Customer Name", "Email", "Segment"],
)
```

### Join with column prefix

```python
products = client.views.get(2051)

view.join(
    foreign_view=products,
    join_type=JoinType.INNER,
    on=[{"left": "Product Code", "right": "Product Code"}],
    select=["Product Name", "Category"],
    column_prefix="Product_",
)
```

---

## Aggregation

### Group by with multiple aggregations

```python
view.pivot(
    group_by=["Region", "Category"],
    aggregations=[
        {"column": "Sales", "function": AggregateFunction.SUM, "as": "Total Sales"},
        {"column": "Sales", "function": AggregateFunction.AVG, "as": "Avg Sale"},
        {"column": "Sales", "function": AggregateFunction.COUNT, "as": "Order Count"},
    ],
)
```

### Crosstab / pivot table

```python
view.crosstab(
    rows=["Region"],
    pivot_column="Quarter",
    select={"column": "Sales", "function": AggregateFunction.SUM},
)
```

---

## Window functions

### Row number / ranking

```python
view.window(
    function=WindowFunction.ROW_NUMBER,
    new_column="Rank",
    partition_by=["Region"],
    order_by=[["Sales", SortDirection.DESC]],
)
```

### Running total

```python
view.window(
    function=WindowFunction.SUM,
    column="Sales",
    new_column="Running Total",
    order_by=[["Date", SortDirection.ASC]],
    range_type=WindowRange.RUNNING,
)
```

### Lag / lead

```python
view.window(
    function=WindowFunction.LAG,
    column="Sales",
    new_column="Previous Sales",
    partition_by=["Region"],
    order_by=[["Date", SortDirection.ASC]],
)
```

---

## Column operations

### Rename by copy-and-delete

The SDK does not have a direct `rename_column` task. To rename, copy the column with a new name, then delete the original:

```python
view.copy_columns([{"source": "old_name", "as": "new_name", "type": "TEXT"}])
view.delete_columns(["old_name"])
```

### Combine columns

```python
view.combine_columns(
    sources=["First Name", "Last Name"],
    new_column="Full Name",
    separator=" ",
)
```

### Split a column

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

### Convert column types

```python
view.convert_type([
    {"column": "Sales", "to": "NUMERIC"},
    {"column": "Order Date", "to": "DATE"},
])
```

---

## Text operations

### Change text case

```python
view.text_transform(columns=["Name"], case=TextCase.UPPER)
view.text_transform(columns=["Description"], case=TextCase.TITLE)
```

### Trim whitespace

```python
view.text_transform(columns=["Name", "Email"], trim=True)
```

### Find and replace

```python
view.replace_values(columns=["Status"], find="N/A", replace="Unknown")
```

### Bulk replace

```python
view.bulk_replace(
    columns=["Item"],
    mapping=[
        {"search": ["6 inch CAKE", "8 inch CAKE", "10 inch CAKE"], "replace": "CAKE"},
        {"search": ["Small Coffee", "Large Coffee", "Iced Coffee"], "replace": "Coffee"},
    ],
)
```

### Substring extraction

```python
# First 3 characters
view.substring("Product Code", direction=SubstringDirection.START, num_char=3, new_column="Prefix")

# Regex extraction
view.substring("Email", regex_pattern=r"@(.+)$", new_column="Domain")
```

---

## Date operations

### Extract date parts

```python
view.extract_date("Order Date", DateComponent.YEAR, new_column="Year")
view.extract_date("Order Date", DateComponent.MONTH_TEXT, new_column="Month Name")
view.extract_date("Order Date", DateComponent.QUARTER, new_column="Quarter")
```

### Date difference

```python
view.date_diff(
    DateDiffUnit.DAY,
    start="Ship Date",
    end="Delivery Date",
    new_column="Delivery Days",
)
```

### Increment a date

```python
view.increment_date("Due Date", delta={"DAYS": 30}, new_column="Extended Due")
```

---

## Row operations

### Remove duplicates

```python
view.discard_duplicates()

# Ignore specific columns when checking for duplicates
view.discard_duplicates(ignore_columns=["Timestamp", "Notes"])
```

### Limit rows

```python
# Top 100 by sales
view.limit_rows(100, order_by=[["Sales", SortDirection.DESC]])

# Bottom 10
view.limit_rows(10, bottom=True, order_by=[["Sales", SortDirection.ASC]])
```

### Fill missing values

```python
view.fill_missing(
    "Price",
    direction=FillDirection.LAST_VALUE,
    order_by=[["Date", SortDirection.ASC]],
)
```

### Unnest (unpivot)

```python
view.unnest(
    columns=["Q1", "Q2", "Q3", "Q4"],
    label_column="Quarter",
    value_column="Revenue",
)
```

---

## Advanced operations

### Lookup from another view

```python
view.lookup(
    source="Product Code",
    lookup_view_id=2050,
    key="code",
    value="name",
    new_column="Product Name",
)
```

### JSON extraction

```python
# Object keys to columns
view.json_extract("data", keys=["name", "email", "age"])

# With type control
view.json_extract(
    "data",
    extractions=[
        {"key": "name", "as": "Name", "type": "TEXT"},
        {"key": "score", "as": "Score", "type": "NUMERIC"},
    ],
)

# JSON list to rows
view.json_extract("items", json_type=JsonType.LIST)
```

### AI-powered transformation

```python
view.gen_ai(
    prompt="Classify the sentiment as positive, negative, or neutral",
    context_columns=["Review Text"],
    new_column="Sentiment",
)
```

### SQL

```python
# Generate SQL from natural language
sql = view.generate_sql("count employees by department and sort by count descending")
print(sql)

# Add raw SQL
view.add_sql("SELECT region, SUM(sales) as total FROM data GROUP BY region")
```

---

## Draft mode (batch transformations)

By default each transformation runs the pipeline immediately. Use draft mode to queue multiple tasks and run the pipeline once -- much faster for large datasets.

### Context manager (recommended)

```python
with view.draft():
    view.text_transform(columns=["Name", "Email"], trim=True)
    view.convert_type([
        {"column": "Sales", "to": "NUMERIC"},
        {"column": "Order Date", "to": "DATE"},
    ])
    view.filter_rows(Condition("Sales", Operator.IS_NOT_EMPTY))
    view.math("Price * Quantity", new_column="Revenue")
# Pipeline runs once for all 4 tasks
```

### Explicit enter/submit

```python
view.enter_draft_mode()
view.add_column("Notes")
view.set_values(
    new_column="Flag",
    column_type=ColumnType.TEXT,
    values=[SetValue("Yes", condition=Condition("Sales", Operator.GTE, 10000)), SetValue("No")],
)
view.submit_draft()  # runs pipeline, refreshes metadata
```

### Discard on error

If an exception occurs inside `with view.draft():`, queued tasks are automatically discarded. You can also discard explicitly:

```python
view.enter_draft_mode()
view.add_column("Temp")
view.discard_draft()  # reverts, "Temp" is not added
```

### Toggle auto-run

```python
view.set_auto_run(False)   # enters draft mode, tasks queue without running
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
view.math("Sales * 1.1", new_column="Adjusted")
view.set_auto_run(True)    # re-enables auto-run
```

---

## End-to-end workflow

A complete example: load data, clean it, transform it, and export.

```python
from mammoth import (
    MammothClient, Condition, Operator, ColumnType,
    SetValue, AggregateFunction, SortDirection, TextCase,
)

client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
client.set_project_id(10)

# 1. Get the view
view = client.views.get(1039)
print(f"Starting with {len(view.display_names)} columns")

# 2. Clean: trim whitespace, convert types
view.text_transform(columns=["Customer Name", "Region"], trim=True)
view.convert_type([
    {"column": "Sales", "to": "NUMERIC"},
    {"column": "Order Date", "to": "DATE"},
])

# 3. Filter: remove empty sales
view.filter_rows(Condition("Sales", Operator.IS_NOT_EMPTY))

# 4. Transform: add calculated columns
view.math("Price * Quantity", new_column="Revenue")
view.set_values(
    new_column="Segment",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Enterprise", condition=Condition("Revenue", Operator.GTE, 100000)),
        SetValue("Mid-Market", condition=Condition("Revenue", Operator.GTE, 10000)),
        SetValue("SMB"),
    ],
)

# 5. Aggregate
view.pivot(
    group_by=["Region", "Segment"],
    aggregations=[
        {"column": "Revenue", "function": AggregateFunction.SUM, "as": "Total Revenue"},
        {"column": "Revenue", "function": AggregateFunction.COUNT, "as": "Order Count"},
    ],
)

# 6. Export
view.export.to_csv("revenue_summary.csv")
view.export.to_postgres(
    host="db.example.com", port=5432,
    database="analytics", table="revenue_summary",
    username="user", password="pass",
)

print("Done!")
```

## See also

- [Views reference](../api/views.md) -- all method signatures
- [Conditions reference](../api/conditions.md) -- filter builder
- [Enums reference](../api/enums.md) -- all parameter values
- [Exports reference](../api/exports.md) -- all export destinations
