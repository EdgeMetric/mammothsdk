"""Math operation mixin."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth._expression_parser import parse_expression
from mammoth.models.pipeline import ColumnType

if TYPE_CHECKING:
    from mammoth.condition import CompoundCondition, Condition, NotCondition


class MathOpsMixin:
    """Mixin for arithmetic operations on a View."""

    def math(
        self,
        expression: str | list[dict[str, Any]],
        new_column: str | None = None,
        column_type: ColumnType = ColumnType.NUMERIC,
        existing_column: str | None = None,
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Apply arithmetic operations (MATH task).

        Args:
            expression: Either a string expression (e.g. ``"Price * Quantity"``)
                that will be parsed automatically, or a raw list of expression
                parts in backend format for power users.
            new_column: Name for result column (creates new).
            column_type: Type for new column (default ColumnType.NUMERIC).
            existing_column: Existing column to overwrite.
            condition: Condition to apply.

        Returns:
            API response dict.

        Examples::

            # String expression (recommended)
            view.math("Price * Quantity", new_column="Total")
            view.math("(Price + Tax) * 1.1", new_column="Grand Total")

            # Raw backend format (power users)
            view.math(
                [{"TYPE": "COLUMN", "VALUE": "Price"},
                 {"TYPE": "OPERATOR", "VALUE": "*"},
                 {"TYPE": "COLUMN", "VALUE": "Quantity"}],
                new_column="Total",
            )
        """
        if isinstance(expression, str):
            resolved_expr = parse_expression(expression, self.columns)
        else:
            # Raw list — resolve column references
            resolved_expr = []
            for part in expression:
                p = dict(part)
                if p.get("TYPE") == "COLUMN" and p.get("VALUE") in self.columns:
                    p["VALUE"] = self.columns[p["VALUE"]]
                resolved_expr.append(p)

        math_spec: dict[str, Any] = {"EXPRESSION": resolved_expr}

        if new_column:
            math_spec["AS"] = self._build_as_column(new_column, column_type)
        elif existing_column:
            math_spec["DESTINATION"] = self._resolve_column(existing_column)

        spec: dict[str, Any] = {"MATH": math_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)
