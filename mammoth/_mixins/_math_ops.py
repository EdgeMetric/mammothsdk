"""Math operation mixin."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth._pure.builders import build_math_params
from mammoth.models.pipeline import ColumnType

if TYPE_CHECKING:
    from mammoth._mixins._host import ViewHost
    from mammoth.condition import CompoundCondition, Condition, NotCondition
else:
    ViewHost = object


class MathOpsMixin(ViewHost):
    """Mixin for arithmetic operations on a View."""

    def math(
        self,
        expression: str,
        new_column: str | None = None,
        column_type: ColumnType = ColumnType.NUMERIC,
        existing_column: str | None = None,
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Apply arithmetic operations (MATH task).

        Args:
            expression: A string expression (e.g. ``"Price * Quantity"``)
                that will be parsed automatically.
            new_column: Name for result column (creates new).
            column_type: Type for new column (default ColumnType.NUMERIC).
            existing_column: Existing column to overwrite.
            condition: Condition to apply.

        Returns:
            API response dict.

        Examples::

            view.math("Price * Quantity", new_column="Total")
            view.math("(Price + Tax) * 1.1", new_column="Grand Total")
        """
        return self._add_task(
            build_math_params(
                expression,
                self.columns,
                new_column=new_column,
                column_type=column_type,
                existing_column=existing_column,
                internal_names=self._internal_names,
                condition=condition,
                column_types=self.column_types,
                name_gen=self._next_internal_name,
            )
        )
