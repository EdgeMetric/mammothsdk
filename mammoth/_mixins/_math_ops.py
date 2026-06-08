"""Math operation mixin."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth._pure.builders import build_math_params, build_small_large_params
from mammoth.models.pipeline import ColumnType, SmallLargeFunction

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

    def small_large(
        self,
        function: SmallLargeFunction,
        columns: list[str],
        index: int = 1,
        constants: list[float] | None = None,
        new_column: str | None = None,
        existing_column: str | None = None,
    ) -> dict[str, Any]:
        """Return the Nth smallest or largest value across columns/constants (SMALL/LARGE task).

        Scans each row across *columns* and optional numeric *constants*, then
        writes the *index*-th smallest (``SmallLargeFunction.SMALL``) or largest
        (``SmallLargeFunction.LARGE``) value to a new or existing column.
        ``index=1`` means the most extreme value (minimum or maximum).

        Args:
            function: ``SmallLargeFunction.SMALL`` or ``SmallLargeFunction.LARGE``.
            columns: Display names of columns whose values participate in the
                ranking.  At least one column or constant must be supplied.
            index: 1-based rank to pick (``1`` = most extreme).  Must be >= 1.
            constants: Optional list of numeric constants that also participate
                in the ranking (appended after *columns* in the VALUES list).
            new_column: Name for a new result column (mutually exclusive with
                *existing_column*).
            existing_column: Display name of an existing column to overwrite.

        Returns:
            API response dict.

        Raises:
            MammothValidationError: If both or neither of *new_column* /
                *existing_column* are given, *columns* + *constants* are empty,
                or *index* < 1.

        Examples::

            from mammoth import SmallLargeFunction

            # 2nd largest value among three numeric columns
            view.small_large(
                SmallLargeFunction.LARGE,
                columns=["Q1 Sales", "Q2 Sales", "Q3 Sales"],
                index=2,
                new_column="2nd Best Quarter",
            )

            # Smallest of a column and the constant 0 (floor at zero)
            view.small_large(
                SmallLargeFunction.SMALL,
                columns=["Profit"],
                constants=[0.0],
                existing_column="Profit",
            )
        """
        values: list[str | int | float] = list(columns) + list(constants or [])
        return self._add_task(
            build_small_large_params(
                function,
                values,
                index,
                self.columns,
                self._internal_names,
                new_column=new_column,
                existing_column=existing_column,
                name_gen=self._next_internal_name,
            )
        )
