"""Pythonic condition builder with operator overloading.

Build filter conditions using Python's ``&`` (AND), ``|`` (OR), and ``~``
(NOT) operators, then pass them to View transformation methods like
``filter_rows()``, ``set_values()``, or ``math()``.

Creating conditions::

    from mammoth import Condition, Operator

    high_sales = Condition("Sales", Operator.GTE, 10000)
    west = Condition("Region", Operator.IN_LIST, ["West", "East"])
    empty_name = Condition("Name", Operator.IS_EMPTY)

Combining conditions::

    combined = high_sales & west         # AND
    either = high_sales | west           # OR
    negated = ~high_sales                # NOT
    complex_cond = (high_sales & west) | empty_name  # nested

Using with View methods::

    view.filter_rows(high_sales & west)
    view.filter_rows(~Condition("Status", Operator.EQ, "Closed"))
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

import warnings
from typing import Any

# Type alias for any condition type
ConditionType = "Condition | CompoundCondition | NotCondition"

# Operators that take no value
_NULL_OPERATORS = frozenset({
    "IS_EMPTY",
    "IS_NOT_EMPTY",
    "IS_MAXVAL",
    "IS_NOT_MAXVAL",
    "IS_MINVAL",
    "IS_NOT_MINVAL",
})


class Condition:
    """Single column condition. Supports ``&`` (AND), ``|`` (OR), ``~`` (NOT).

    Args:
        column: Display name of the column (e.g. "Sales", "Region").
        operator: Operator enum value (e.g. Operator.GTE, Operator.IN_LIST).
        value: Comparison value. Required for most operators, omit for IS_EMPTY.
        case_sensitive: Controls string comparison case sensitivity.
            ``None`` (default) — don't emit STRING_PROP (backend default: case-sensitive).
            ``True`` — emit CASE-SENSITIVE.
            ``False`` — emit CASE-INSENSITIVE.

    Examples::

        Condition("Sales", Operator.GTE, 1000)
        Condition("Region", Operator.IN_LIST, ["West", "East"])
        Condition("Name", Operator.IS_NOT_EMPTY)
        Condition("Sales", Operator.GTE, 1000) & Condition("Region", Operator.EQ, "West")
        ~Condition("Status", Operator.EQ, "Closed")

    Raises:
        ValueError: If column is empty or a non-null operator is used without a value.
    """

    def __init__(
        self,
        column: str,
        operator: str | Any,
        value: Any = None,
        case_sensitive: bool | None = None,
        value_is_column: bool = False,
        component: str | None = None,
        truncate: str | None = None,
    ) -> None:
        if not column or not isinstance(column, str):
            raise ValueError(f"column must be a non-empty string, got {column!r}")

        self.column = column
        self.operator: str = operator.value if hasattr(operator, "value") else str(operator)
        self.value = value
        self.case_sensitive = case_sensitive
        self.value_is_column = value_is_column
        self.component = component
        self.truncate = truncate

        # Validation: null operators with a value, non-null without
        if self.operator in _NULL_OPERATORS and value is not None:
            warnings.warn(
                f"Operator {self.operator!r} does not use a value, but got {value!r}. "
                "The value will be ignored.",
                UserWarning,
                stacklevel=2,
            )
        elif self.operator not in _NULL_OPERATORS and value is None:
            raise ValueError(
                f"Operator {self.operator!r} requires a value, but none was provided."
            )

    def __and__(self, other: ConditionType) -> CompoundCondition:
        """Combine with AND: cond1 & cond2."""
        if isinstance(other, CompoundCondition) and other.logic == "AND":
            return CompoundCondition("AND", [self, *other.conditions])
        return CompoundCondition("AND", [self, other])

    def __or__(self, other: ConditionType) -> CompoundCondition:
        """Combine with OR: cond1 | cond2."""
        if isinstance(other, CompoundCondition) and other.logic == "OR":
            return CompoundCondition("OR", [self, *other.conditions])
        return CompoundCondition("OR", [self, other])

    def __invert__(self) -> NotCondition:
        """Negate: ~condition."""
        return NotCondition(self)

    def _build_inner(
        self,
        column_map: dict[str, str] | None = None,
        column_types: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Build the pure condition structure (no STRING_PROP)."""
        internal_name = column_map.get(self.column, self.column) if column_map else self.column

        # Workaround: backend falsely rejects TEXT + EQ/NE as "type mismatch".
        # Use IN_LIST/NOT_IN_LIST (single-element) which bypasses the broken validation.
        operator = self.operator
        if column_types and operator in ("EQ", "NE") and not self.value_is_column:
            col_type = column_types.get(self.column) or column_types.get(internal_name)
            if col_type == "TEXT":
                operator = "IN_LIST" if operator == "EQ" else "NOT_IN_LIST"

        # Boolean operators (no value needed)
        if operator in _NULL_OPERATORS:
            return {internal_name: {operator: True}}

        # List operators — also catches remapped EQ/NE
        if operator in ("IN_LIST", "NOT_IN_LIST", "CONTAINS", "NOT_CONTAINS"):
            val = self.value if isinstance(self.value, list) else [self.value]
            return {internal_name: {operator: {"VALUE": val}}}

        # Column-to-column comparison
        if self.value_is_column:
            resolved_val = column_map.get(self.value, self.value) if column_map else self.value
            return {internal_name: {operator: {"COLUMN": resolved_val}}}

        # Date component wrapper
        if self.component is not None:
            return {internal_name: {operator: {"VALUE": {"COMPONENT": self.component, "VALUE": self.value}}}}

        # Date truncation wrapper
        if self.truncate is not None:
            return {internal_name: {operator: {"VALUE": {"TRUNCATE": self.truncate, "VALUE": self.value}}}}

        # All other operators (comparison, string)
        return {internal_name: {operator: {"VALUE": self.value}}}

    def _collect_case_sensitive(self) -> bool | None:
        """Return this leaf's case_sensitive setting."""
        return self.case_sensitive

    def build(
        self,
        column_map: dict[str, str] | None = None,
        column_types: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Build API-format condition dict.

        Args:
            column_map: Mapping of display names to internal names.
            column_types: Mapping of display names to column types (e.g. TEXT, NUMERIC).

        Returns:
            dict in Mammoth API condition format.
        """
        result = self._build_inner(column_map, column_types)
        cs = self._collect_case_sensitive()
        if cs is not None:
            case_str = "CASE-SENSITIVE" if cs else "CASE-INSENSITIVE"
            result["STRING_PROP"] = {"CASE": case_str}
        return result

    def __repr__(self) -> str:
        return f"Condition({self.column!r}, {self.operator!r}, {self.value!r})"


class NotCondition:
    """Negation of a condition. Created via ``~condition``.

    Examples::

        ~Condition("Status", Operator.EQ, "Closed")
        ~(cond1 & cond2)  # NOT of an AND

    Raises:
        TypeError: If the inner condition is not a valid condition type.
    """

    def __init__(self, condition: ConditionType) -> None:
        if not isinstance(condition, (Condition, CompoundCondition, NotCondition)):
            raise TypeError(
                f"NotCondition requires a Condition, CompoundCondition, or NotCondition, "
                f"got {type(condition).__name__}"
            )
        self.condition = condition

    def __and__(self, other: ConditionType) -> CompoundCondition:
        """Combine with AND: ~c1 & c2."""
        if isinstance(other, CompoundCondition) and other.logic == "AND":
            return CompoundCondition("AND", [self, *other.conditions])
        return CompoundCondition("AND", [self, other])

    def __or__(self, other: ConditionType) -> CompoundCondition:
        """Combine with OR: ~c1 | c2."""
        if isinstance(other, CompoundCondition) and other.logic == "OR":
            return CompoundCondition("OR", [self, *other.conditions])
        return CompoundCondition("OR", [self, other])

    def __invert__(self) -> Condition | CompoundCondition | NotCondition:
        """Double negation cancels: ~~cond returns original."""
        return self.condition

    def _build_inner(
        self,
        column_map: dict[str, str] | None = None,
        column_types: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Build the NOT structure (no STRING_PROP)."""
        inner = self.condition._build_inner(column_map, column_types)
        return {"NOT": inner}

    def _collect_case_sensitive(self) -> bool | None:
        """Delegate to inner condition."""
        return self.condition._collect_case_sensitive()

    def build(
        self,
        column_map: dict[str, str] | None = None,
        column_types: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Build API-format condition dict.

        Args:
            column_map: Mapping of display names to internal names.
            column_types: Mapping of display names to column types (e.g. TEXT, NUMERIC).

        Returns:
            dict with NOT key wrapping the inner condition.
        """
        result = self._build_inner(column_map, column_types)
        cs = self._collect_case_sensitive()
        if cs is not None:
            case_str = "CASE-SENSITIVE" if cs else "CASE-INSENSITIVE"
            result["STRING_PROP"] = {"CASE": case_str}
        return result

    def __repr__(self) -> str:
        return f"NotCondition({self.condition!r})"


class CompoundCondition:
    """AND/OR composition of conditions. Supports further chaining with ``&``, ``|``, ``~``.

    Created automatically when combining Conditions with & or |::

        combined = cond1 & cond2  # CompoundCondition("AND", [cond1, cond2])
        triple = combined & cond3  # Flat AND of all three

    Raises:
        ValueError: If logic is not AND/OR or conditions has fewer than 2 elements.
        TypeError: If any element is not a valid condition type.
    """

    def __init__(
        self,
        logic: str,
        conditions: list[Condition | CompoundCondition | NotCondition],
    ) -> None:
        if logic not in ("AND", "OR"):
            raise ValueError(f"logic must be 'AND' or 'OR', got {logic!r}")
        if len(conditions) < 2:
            raise ValueError(
                f"CompoundCondition requires at least 2 conditions, got {len(conditions)}"
            )
        for i, c in enumerate(conditions):
            if not isinstance(c, (Condition, CompoundCondition, NotCondition)):
                raise TypeError(
                    f"conditions[{i}] must be a Condition, CompoundCondition, or NotCondition, "
                    f"got {type(c).__name__}"
                )
        self.logic = logic
        self.conditions = conditions

    def __and__(self, other: ConditionType) -> CompoundCondition:
        """Combine with AND."""
        if self.logic == "AND":
            if isinstance(other, CompoundCondition) and other.logic == "AND":
                return CompoundCondition("AND", [*self.conditions, *other.conditions])
            return CompoundCondition("AND", [*self.conditions, other])
        return CompoundCondition("AND", [self, other])

    def __or__(self, other: ConditionType) -> CompoundCondition:
        """Combine with OR."""
        if self.logic == "OR":
            if isinstance(other, CompoundCondition) and other.logic == "OR":
                return CompoundCondition("OR", [*self.conditions, *other.conditions])
            return CompoundCondition("OR", [*self.conditions, other])
        return CompoundCondition("OR", [self, other])

    def __invert__(self) -> NotCondition:
        """Negate: ~(cond1 & cond2)."""
        return NotCondition(self)

    def _build_inner(
        self,
        column_map: dict[str, str] | None = None,
        column_types: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Build the AND/OR structure (no STRING_PROP)."""
        built = [cond._build_inner(column_map, column_types) for cond in self.conditions]
        return {self.logic: built}

    def _collect_case_sensitive(self) -> bool | None:
        """Collect case_sensitive from any child leaf."""
        for cond in self.conditions:
            cs = cond._collect_case_sensitive()
            if cs is not None:
                return cs
        return None

    def build(
        self,
        column_map: dict[str, str] | None = None,
        column_types: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Build API-format condition dict.

        Args:
            column_map: Mapping of display names to internal names.
            column_types: Mapping of display names to column types (e.g. TEXT, NUMERIC).

        Returns:
            dict in Mammoth API condition format with AND/OR keys.
        """
        result = self._build_inner(column_map, column_types)
        cs = self._collect_case_sensitive()
        if cs is not None:
            case_str = "CASE-SENSITIVE" if cs else "CASE-INSENSITIVE"
            result["STRING_PROP"] = {"CASE": case_str}
        return result

    def __repr__(self) -> str:
        return f"CompoundCondition({self.logic!r}, {self.conditions!r})"
