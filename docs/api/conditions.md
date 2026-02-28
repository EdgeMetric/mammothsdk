# Conditions Reference

The condition module provides a Pythonic filter builder with operator overloading. Build conditions using `Condition` objects, combine them with `&` (AND), `|` (OR), and `~` (NOT), and pass them to View transformation methods.

## Quick examples

```python
from mammoth import Condition, Operator

# Numeric comparisons
high_sales = Condition("Sales", Operator.GTE, 10000)

# List membership
selected = Condition("Region", Operator.IN_LIST, ["West", "East"])

# Null checks (no value needed)
empty = Condition("Name", Operator.IS_EMPTY)

# Combine with & (AND), | (OR), ~ (NOT)
both = high_sales & selected
negated = ~Condition("Status", Operator.EQ, "Closed")
complex_cond = (high_sales & selected) | negated
```

## Operator overloading

Combine conditions with `&` (AND), `|` (OR), and `~` (NOT). Use parentheses for grouping.

```python
high_sales = Condition("Sales", Operator.GTE, 10000)
west = Condition("Region", Operator.EQ, "West")
active = Condition("Status", Operator.EQ, "Active")

# AND: all conditions must be true
both = high_sales & west

# OR: at least one must be true
either = high_sales | west

# Nested: parentheses control grouping
complex_cond = (high_sales & west) | active

# Chain multiple — flat when using the same operator
all_three = high_sales & west & active  # AND of all three
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

### math, combine_columns, and other methods

Many transformation methods accept an optional `condition` parameter:

```python
view.math(
    "Price * 0.9",
    existing_column="Price",
    condition=Condition("Region", Operator.EQ, "West"),
)
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

---

## Full API Reference

::: mammoth.condition.Condition
    options:
      members:
        - __init__
        - build

::: mammoth.condition.CompoundCondition
    options:
      members:
        - __init__
        - build

::: mammoth.condition.NotCondition
    options:
      members:
        - __init__
        - build

## See also

- [Enums](enums.md) -- all enum values
- [Views](views.md) -- transformation methods that use conditions
- [Transformation examples](../examples/transformations.md) -- practical workflows
