# Conditions Reference

The condition module provides a Pythonic filter builder with operator overloading. Build conditions using `Condition` objects, combine them with `&` (AND) and `|` (OR), and pass them to View transformation methods.

## Condition

A single-column condition.

```python
from mammoth import Condition, Operator

Condition(
    column: str,
    operator: Operator,
    value: Any = None,
    case_sensitive: bool = False,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `column` | `str` | *required* | Display name of the column |
| `operator` | `Operator` | *required* | Comparison operator |
| `value` | `Any` | `None` | Comparison value (omit for `IS_EMPTY` / `IS_NOT_EMPTY`) |
| `case_sensitive` | `bool` | `False` | Case-sensitive string comparison |

### Examples

```python
from mammoth import Condition, Operator

# Numeric comparisons
high_sales = Condition("Sales", Operator.GTE, 10000)
low_price = Condition("Price", Operator.LT, 5.0)

# Equality
west = Condition("Region", Operator.EQ, "West")

# List membership
selected = Condition("Region", Operator.IN_LIST, ["West", "East"])
excluded = Condition("Status", Operator.NOT_IN_LIST, ["Cancelled", "Refunded"])

# String matching
contains_corp = Condition("Name", Operator.CONTAINS, "Corp")
starts_with_a = Condition("Name", Operator.STARTS_WITH, "A")

# Null checks (no value needed)
empty = Condition("Name", Operator.IS_EMPTY)
not_empty = Condition("Email", Operator.IS_NOT_EMPTY)

# Aggregate checks
is_max = Condition("Sales", Operator.IS_MAXVAL)
is_min = Condition("Sales", Operator.IS_MINVAL)
```

## CompoundCondition

An AND/OR composition of conditions. Normally created automatically via `&` and `|` operators -- you rarely need to construct one directly.

```python
from mammoth import CompoundCondition

CompoundCondition(
    logic: str,          # "AND" or "OR"
    conditions: list,    # list of Condition or CompoundCondition
)
```

## Operator overloading

Combine conditions with `&` (AND) and `|` (OR). Use parentheses for grouping.

```python
from mammoth import Condition, Operator

high_sales = Condition("Sales", Operator.GTE, 10000)
west = Condition("Region", Operator.EQ, "West")
active = Condition("Status", Operator.EQ, "Active")

# AND: all conditions must be true
both = high_sales & west

# OR: at least one must be true
either = high_sales | west

# Nested: parentheses control grouping
complex_cond = (high_sales & west) | active

# Chain multiple
all_three = high_sales & west & active
```

Chaining is flat when using the same operator:

```python
# These are equivalent:
a & b & c           # CompoundCondition("AND", [a, b, c])
(a & b) & c         # CompoundCondition("AND", [a, b, c])
```

Mixing operators creates nesting:

```python
(a & b) | c         # CompoundCondition("OR", [CompoundCondition("AND", [a, b]), c])
```

## Using conditions with View methods

### filter_rows

```python
view.filter_rows(Condition("Sales", Operator.GTE, 1000))
view.filter_rows(
    Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
)
```

### set_values

Conditions can be attached to individual `SetValue` items to create conditional columns:

```python
from mammoth import SetValue, ColumnType

view.set_values(
    new_column="Tier",
    column_type=ColumnType.TEXT,
    values=[
        SetValue("Premium", condition=Condition("Sales", Operator.GTE, 10000)),
        SetValue("Standard", condition=Condition("Sales", Operator.GTE, 1000)),
        SetValue("Basic"),  # default (no condition)
    ],
)
```

A global condition can also be applied to the entire task:

```python
view.set_values(
    existing_column="Label",
    values=[SetValue("Active")],
    condition=Condition("Status", Operator.EQ, "Active"),
)
```

### math, combine_columns, and other methods

Many transformation methods accept an optional `condition` parameter:

```python
view.math(
    "Price * 0.9",
    existing_column="Price",
    condition=Condition("Region", Operator.EQ, "West"),
)
```

## build()

The `build()` method converts a condition to the Mammoth API dict format. The SDK calls this automatically -- you normally do not need to call it yourself.

```python
cond = Condition("Sales", Operator.GTE, 1000)
payload = cond.build({"Sales": "column_1"})
# {"column_1": {"GTE": {"VALUE": 1000}}}

compound = cond & Condition("Region", Operator.EQ, "West")
payload = compound.build({"Sales": "column_1", "Region": "column_2"})
# {"AND": [{"column_1": {"GTE": {"VALUE": 1000}}}, {"column_2": {"EQ": {"VALUE": "West"}}}]}
```

## All operators

See the [Operator enum](enums.md#operator) for the complete list. Summary:

| Category | Operators |
|----------|-----------|
| Comparison | `GT`, `LT`, `GTE`, `LTE`, `EQ`, `NE` |
| List | `IN_LIST`, `NOT_IN_LIST`, `CONTAINS`, `NOT_CONTAINS` |
| String | `STARTS_WITH`, `ENDS_WITH`, `NOT_STARTS_WITH`, `NOT_ENDS_WITH` |
| Null | `IS_EMPTY`, `IS_NOT_EMPTY` |
| Aggregate | `IS_MAXVAL`, `IS_NOT_MAXVAL`, `IS_MINVAL`, `IS_NOT_MINVAL` |

## See also

- [Enums](enums.md) -- all enum values
- [Views](views.md) -- transformation methods that use conditions
- [Transformation examples](../examples/transformations.md) -- practical workflows
