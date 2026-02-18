"""Pythonic condition builder with operator overloading.

Build filter conditions using Python's ``&`` (AND) and ``|`` (OR) operators,
then pass them to View transformation methods like ``filter_rows()``,
``set_values()``, or ``math()``.

Creating conditions::

    from mammoth import Condition, Operator

    high_sales = Condition("Sales", Operator.GTE, 10000)
    west = Condition("Region", Operator.IN_LIST, ["West", "East"])
    empty_name = Condition("Name", Operator.IS_EMPTY)

Combining conditions::

    combined = high_sales & west         # AND
    either = high_sales | west           # OR
    complex_cond = (high_sales & west) | empty_name  # nested

Using with View methods::

    view.filter_rows(high_sales & west)
    view.set_values(
        new_column="Label", column_type=ColumnType.TEXT,
        values=[
            SetValue("Priority", condition=high_sales),
            SetValue("Normal"),
        ],
    )

Conditions are resolved to Mammoth API format via ``build(column_map)``::

    payload = combined.build({"Sales": "column_1", "Region": "column_2"})
    # {"AND": [{"column_1": {"GTE": {"VALUE": 10000}}}, ...]}

Supported operators (from ``mammoth.Operator`` enum):
    Comparison: GT, LT, GTE, LTE, EQ, NE
    List: IN_LIST, NOT_IN_LIST, CONTAINS, NOT_CONTAINS
    String: STARTS_WITH, ENDS_WITH, NOT_STARTS_WITH, NOT_ENDS_WITH
    Null: IS_EMPTY, IS_NOT_EMPTY
    Aggregate: IS_MAXVAL, IS_NOT_MAXVAL, IS_MINVAL, IS_NOT_MINVAL
"""

from __future__ import annotations

from typing import Any


class Condition:
    """Single column condition. Supports & (AND) and | (OR) operators.

    Args:
        column: Display name of the column (e.g. "Sales", "Region").
        operator: Operator enum value (e.g. Operator.GTE, Operator.IN_LIST).
        value: Comparison value. Required for most operators, omit for IS_EMPTY.
        case_sensitive: Whether string comparisons are case-sensitive (default False).

    Examples::

        Condition("Sales", Operator.GTE, 1000)
        Condition("Region", Operator.IN_LIST, ["West", "East"])
        Condition("Name", Operator.IS_NOT_EMPTY)
        Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
    """

    def __init__(
        self,
        column: str,
        operator: str | Any,
        value: Any = None,
        case_sensitive: bool = False,
    ) -> None:
        self.column = column
        self.operator: str = operator.value if hasattr(operator, "value") else str(operator)
        self.value = value
        self.case_sensitive = case_sensitive

    def __and__(self, other: Condition | CompoundCondition) -> CompoundCondition:
        """Combine with AND: cond1 & cond2."""
        if isinstance(other, CompoundCondition) and other.logic == "AND":
            return CompoundCondition("AND", [self, *other.conditions])
        return CompoundCondition("AND", [self, other])

    def __or__(self, other: Condition | CompoundCondition) -> CompoundCondition:
        """Combine with OR: cond1 | cond2."""
        if isinstance(other, CompoundCondition) and other.logic == "OR":
            return CompoundCondition("OR", [self, *other.conditions])
        return CompoundCondition("OR", [self, other])

    def build(self, column_map: dict[str, str] | None = None) -> dict[str, Any]:
        """Build API-format condition dict.

        Args:
            column_map: Mapping of display names to internal names.

        Returns:
            dict in Mammoth API condition format.
        """
        internal_name = column_map.get(self.column, self.column) if column_map else self.column

        # Boolean operators (no value needed)
        if self.operator in (
            "IS_EMPTY",
            "IS_NOT_EMPTY",
            "IS_MAXVAL",
            "IS_NOT_MAXVAL",
            "IS_MINVAL",
            "IS_NOT_MINVAL",
        ):
            return {internal_name: {self.operator: True}}

        # List operators
        if self.operator in ("IN_LIST", "NOT_IN_LIST", "CONTAINS", "NOT_CONTAINS"):
            val = self.value if isinstance(self.value, list) else [self.value]
            return {internal_name: {self.operator: {"VALUE": val}}}

        # All other operators (comparison, string)
        return {internal_name: {self.operator: {"VALUE": self.value}}}

    def __repr__(self) -> str:
        return f"Condition({self.column!r}, {self.operator!r}, {self.value!r})"


class CompoundCondition:
    """AND/OR composition of conditions. Supports further chaining with & and |.

    Created automatically when combining Conditions with & or |::

        combined = cond1 & cond2  # CompoundCondition("AND", [cond1, cond2])
        triple = combined & cond3  # Flat AND of all three
    """

    def __init__(
        self,
        logic: str,
        conditions: list[Condition | CompoundCondition],
    ) -> None:
        self.logic = logic  # "AND" or "OR"
        self.conditions = conditions

    def __and__(self, other: Condition | CompoundCondition) -> CompoundCondition:
        """Combine with AND."""
        if self.logic == "AND":
            if isinstance(other, CompoundCondition) and other.logic == "AND":
                return CompoundCondition("AND", [*self.conditions, *other.conditions])
            return CompoundCondition("AND", [*self.conditions, other])
        return CompoundCondition("AND", [self, other])

    def __or__(self, other: Condition | CompoundCondition) -> CompoundCondition:
        """Combine with OR."""
        if self.logic == "OR":
            if isinstance(other, CompoundCondition) and other.logic == "OR":
                return CompoundCondition("OR", [*self.conditions, *other.conditions])
            return CompoundCondition("OR", [*self.conditions, other])
        return CompoundCondition("OR", [self, other])

    def build(self, column_map: dict[str, str] | None = None) -> dict[str, Any]:
        """Build API-format condition dict.

        Args:
            column_map: Mapping of display names to internal names.

        Returns:
            dict in Mammoth API condition format with AND/OR keys.
        """
        built = [cond.build(column_map) for cond in self.conditions]
        return {self.logic: built}

    def __repr__(self) -> str:
        return f"CompoundCondition({self.logic!r}, {self.conditions!r})"
