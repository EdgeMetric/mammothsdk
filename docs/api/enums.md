# Enums Reference

The SDK provides enums for all transformation parameters. Import them directly from `mammoth`:

```python
from mammoth import Operator, ColumnType, JoinType, DateComponent
```

All enums are `str` subclasses (`class MyEnum(str, Enum)`) so they can be used directly as strings where needed.

---

## Operator

Filter operators for use with `Condition`.

```python
from mammoth import Operator
```

| Value | Description | Example value |
|-------|-------------|---------------|
| `Operator.GT` | Greater than | `1000` |
| `Operator.LT` | Less than | `5.0` |
| `Operator.GTE` | Greater than or equal | `1000` |
| `Operator.LTE` | Less than or equal | `100` |
| `Operator.EQ` | Equal | `"West"` |
| `Operator.NE` | Not equal | `"Cancelled"` |
| `Operator.IN_LIST` | Value is in list | `["West", "East"]` |
| `Operator.NOT_IN_LIST` | Value is not in list | `["Cancelled"]` |
| `Operator.CONTAINS` | String contains | `"Corp"` |
| `Operator.NOT_CONTAINS` | String does not contain | `"test"` |
| `Operator.STARTS_WITH` | String starts with | `"A"` |
| `Operator.ENDS_WITH` | String ends with | `"Inc"` |
| `Operator.NOT_STARTS_WITH` | String does not start with | `"X"` |
| `Operator.NOT_ENDS_WITH` | String does not end with | `"Ltd"` |
| `Operator.IS_EMPTY` | Value is null/empty | *(no value)* |
| `Operator.IS_NOT_EMPTY` | Value is not null/empty | *(no value)* |
| `Operator.IS_MAXVAL` | Value is the column max | *(no value)* |
| `Operator.IS_NOT_MAXVAL` | Value is not the column max | *(no value)* |
| `Operator.IS_MINVAL` | Value is the column min | *(no value)* |
| `Operator.IS_NOT_MINVAL` | Value is not the column min | *(no value)* |

---

## ColumnType

Column data types for new columns and type conversions.

```python
from mammoth import ColumnType
```

| Value | Description |
|-------|-------------|
| `ColumnType.TEXT` | Text/string data |
| `ColumnType.NUMERIC` | Numeric data (integers and decimals) |
| `ColumnType.DATE` | Date/datetime data |

---

## ValueType

Value types for expressions in pipeline tasks.

```python
from mammoth import ValueType
```

| Value | Description |
|-------|-------------|
| `ValueType.FIXED` | A literal value |
| `ValueType.EXPRESSION` | A system expression |
| `ValueType.COLUMN` | A column reference |
| `ValueType.NUMBER` | A numeric literal |
| `ValueType.OPERATOR` | An arithmetic operator |

---

## JoinType

Join types for combining dataviews.

```python
from mammoth import JoinType
```

| Value | Description |
|-------|-------------|
| `JoinType.INNER` | Inner join -- only matching rows |
| `JoinType.LEFT` | Left join -- all rows from left, matching from right |
| `JoinType.RIGHT` | Right join -- all rows from right, matching from left |
| `JoinType.OUTER` | Outer join -- all rows from both sides |

---

## TextCase

Text case transformations for `text_transform()`.

```python
from mammoth import TextCase
```

| Value | Description |
|-------|-------------|
| `TextCase.UPPER` | Convert to UPPERCASE |
| `TextCase.LOWER` | Convert to lowercase |
| `TextCase.TITLE` | Convert to Title Case |

---

## DateComponent

Date components for `extract_date()`. Values are lowercase to match the backend format.

```python
from mammoth import DateComponent
```

### Basic components

| Value | Output type | Description |
|-------|-------------|-------------|
| `DateComponent.YEAR` | NUMERIC | Year (e.g., 2025) |
| `DateComponent.MONTH` | NUMERIC | Month number (1-12) |
| `DateComponent.DAY` | NUMERIC | Day of month (1-31) |
| `DateComponent.HOUR` | NUMERIC | Hour (0-23) |
| `DateComponent.MINUTE` | NUMERIC | Minute (0-59) |
| `DateComponent.SECOND` | NUMERIC | Second (0-59) |
| `DateComponent.WEEK` | NUMERIC | Week of year |
| `DateComponent.QUARTER` | NUMERIC | Quarter (1-4) |
| `DateComponent.DAY_OF_WEEK` | NUMERIC | Day of week number |
| `DateComponent.DAY_OF_YEAR` | NUMERIC | Day of year (1-366) |

### Text-based extractions

| Value | Output type | Description |
|-------|-------------|-------------|
| `DateComponent.WEEKDAY_TEXT` | TEXT | Day name (e.g., "Monday") |
| `DateComponent.MONTH_TEXT` | TEXT | Month name (e.g., "January") |

### Composite formats

| Value | Output type | Description |
|-------|-------------|-------------|
| `DateComponent.YEAR_MONTH` | NUMERIC | Year-month composite |
| `DateComponent.YEAR_WEEK` | NUMERIC | Year-week composite |
| `DateComponent.YEAR_QUARTER` | NUMERIC | Year-quarter composite |
| `DateComponent.MONTH_DAY` | NUMERIC | Month-day composite |
| `DateComponent.HOUR_MINUTE` | NUMERIC | Hour-minute composite |
| `DateComponent.HOUR_MINUTE_SECOND` | NUMERIC | Hour-minute-second composite |
| `DateComponent.YEAR_MONTH_DAY` | NUMERIC | Year-month-day composite |
| `DateComponent.YEAR_MONTH_DAY_AS_DATE` | TEXT | Date as formatted text |
| `DateComponent.MONTH_DAY_YEAR_HOUR_MINUTE_SECOND` | TEXT | Full datetime as text |
| `DateComponent.DATE_ONLY` | NUMERIC | Date-only component |

---

## DateDiffUnit

Units for `date_diff()` calculations. Values are UPPERCASE (distinct from `DateComponent`).

```python
from mammoth import DateDiffUnit
```

| Value | Description |
|-------|-------------|
| `DateDiffUnit.YEAR` | Difference in years |
| `DateDiffUnit.MONTH` | Difference in months |
| `DateDiffUnit.DAY` | Difference in days |
| `DateDiffUnit.HOUR` | Difference in hours |
| `DateDiffUnit.MINUTE` | Difference in minutes |
| `DateDiffUnit.SECOND` | Difference in seconds |
| `DateDiffUnit.WEEK` | Difference in weeks |
| `DateDiffUnit.QUARTER` | Difference in quarters |

---

## AggregateFunction

Aggregate functions for `pivot()` and group operations.

```python
from mammoth import AggregateFunction
```

| Value | Description |
|-------|-------------|
| `AggregateFunction.SUM` | Sum of values |
| `AggregateFunction.AVG` | Average of values |
| `AggregateFunction.MIN` | Minimum value |
| `AggregateFunction.MAX` | Maximum value |
| `AggregateFunction.COUNT` | Count of values |
| `AggregateFunction.COUNT_DISTINCT` | Count of distinct values |
| `AggregateFunction.STDDEV` | Standard deviation |
| `AggregateFunction.VARIANCE` | Variance |
| `AggregateFunction.MEDIAN` | Median value |
| `AggregateFunction.FIRST` | First value |
| `AggregateFunction.LAST` | Last value |
| `AggregateFunction.CONCAT` | Concatenate values |

---

## WindowFunction

Window functions for `window()`.

```python
from mammoth import WindowFunction
```

| Value | Description |
|-------|-------------|
| `WindowFunction.ROW_NUMBER` | Sequential row number |
| `WindowFunction.RANK` | Rank with gaps |
| `WindowFunction.DENSE_RANK` | Rank without gaps |
| `WindowFunction.LAG` | Previous row value |
| `WindowFunction.LEAD` | Next row value |
| `WindowFunction.SUM` | Window sum |
| `WindowFunction.AVG` | Window average |
| `WindowFunction.MIN` | Window minimum |
| `WindowFunction.MAX` | Window maximum |
| `WindowFunction.COUNT` | Window count |
| `WindowFunction.FIRST_VALUE` | First value in window |
| `WindowFunction.LAST_VALUE` | Last value in window |
| `WindowFunction.STDDEV` | Window standard deviation |
| `WindowFunction.VARIANCE` | Window variance |
| `WindowFunction.PERCENT_RANK` | Percent rank |
| `WindowFunction.NTILE` | N-tile distribution |

---

## WindowRange

Window range types for `window()`.

```python
from mammoth import WindowRange
```

| Value | Description |
|-------|-------------|
| `WindowRange.UNBOUNDED` | Entire partition |
| `WindowRange.RUNNING` | Running window (start of partition to current row) |

---

## FillDirection

Fill directions for `fill_missing()`.

```python
from mammoth import FillDirection
```

| Value | Description |
|-------|-------------|
| `FillDirection.FIRST_VALUE` | Fill with the first non-null value going forward |
| `FillDirection.LAST_VALUE` | Fill with the last non-null value going backward |

---

## SortDirection

Sort direction for `order_by` parameters.

```python
from mammoth import SortDirection
```

| Value | Description |
|-------|-------------|
| `SortDirection.ASC` | Ascending order |
| `SortDirection.DESC` | Descending order |

---

## MathOperator

Arithmetic operators for math expressions.

```python
from mammoth import MathOperator
```

| Value | Symbol | Description |
|-------|--------|-------------|
| `MathOperator.ADD` | `+` | Addition |
| `MathOperator.SUBTRACT` | `-` | Subtraction |
| `MathOperator.MULTIPLY` | `*` | Multiplication |
| `MathOperator.DIVIDE` | `/` | Division |
| `MathOperator.MODULO` | `%` | Modulo (remainder) |

---

## SubstringDirection

Extraction direction for `substring()`.

```python
from mammoth import SubstringDirection
```

| Value | Use with | Description |
|-------|----------|-------------|
| `SubstringDirection.START` | `num_char` | Extract first N characters |
| `SubstringDirection.END` | `num_char` | Extract last N characters |
| `SubstringDirection.LEFT` | `char_position` | Extract characters before position |
| `SubstringDirection.RIGHT` | `char_position` | Extract characters after position |

---

## JsonType

JSON structure types for `json_extract()`.

```python
from mammoth import JsonType
```

| Value | Description |
|-------|-------------|
| `JsonType.OBJECT` | JSON object (`{...}`) -- extract keys to columns |
| `JsonType.LIST` | JSON list (`[...]`) -- extract items to rows |

---

## FilterType

Filter types for `filter_rows()`.

```python
from mammoth import FilterType
```

| Value | Description |
|-------|-------------|
| `FilterType.SHOW` | Keep rows that match the condition |
| `FilterType.REMOVE` | Discard rows that match the condition |

---

## ProviderType

Value provider types for SET task values.

```python
from mammoth import ProviderType
```

| Value | Description |
|-------|-------------|
| `ProviderType.FIXED` | A literal value (e.g., `"High"`, `42`) |
| `ProviderType.EXPRESSION` | A system expression (e.g., `"__TIME__"` for current timestamp) |

---

## TaskType

Pipeline task type identifiers.

```python
from mammoth import TaskType
```

| Value | Description |
|-------|-------------|
| `TaskType.SET` | Set/label values |
| `TaskType.SELECT` | Filter rows |
| `TaskType.MATH` | Arithmetic operations |
| `TaskType.JOIN` | Join dataviews |
| `TaskType.PIVOT` | Group and aggregate |
| `TaskType.WINDOW` | Window functions |
| `TaskType.FILL` | Fill missing values |
| `TaskType.LIMIT` | Limit rows |
| `TaskType.LOOKUP` | Lookup from another view |
| `TaskType.COMBINE` | Concatenate columns |
| `TaskType.CONVERT` | Convert column types |
| `TaskType.COPY` | Copy columns |
| `TaskType.DELETE` | Delete columns |
| `TaskType.ADD_COLUMN` | Add empty column |
| `TaskType.REPLACE` | Find and replace |
| `TaskType.SPLIT` | Split column |
| `TaskType.SUBSTRING` | Extract substring |
| `TaskType.TEXT_TRANSFORM` | Text case / trim |
| `TaskType.EXTRACT_DATE` | Extract date part |
| `TaskType.DATE_DIFF` | Date difference |
| `TaskType.INCREMENT_DATE` | Add/subtract from date |
| `TaskType.UNNEST` | Unpivot columns to rows |
| `TaskType.CROSSTAB` | Crosstab / pivot table |
| `TaskType.JSON_HANDLE` | JSON extraction |
| `TaskType.GEN_AI` | AI transformation |
| `TaskType.SQL` | SQL query |
| `TaskType.DISCARD_DUPLICATES` | Remove duplicate rows |

---

## SetValue dataclass

Not an enum, but frequently used alongside enums. A dataclass for `set_values()` value specs.

```python
from mammoth import SetValue

SetValue(
    value: Any,
    condition: Condition | CompoundCondition | None = None,
)
```

```python
from mammoth import SetValue, Condition, Operator

values = [
    SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
    SetValue("Low"),  # default value (no condition)
]
```

## See also

- [Conditions](conditions.md) -- using `Operator` with `Condition`
- [Views](views.md) -- transformation methods that use these enums
