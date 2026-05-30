"""Aggregate operation mixins: pivot, window, crosstab."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth._pure.builders import (
    build_crosstab_params,
    build_pivot_params,
    build_window_params,
)
from mammoth.models.pipeline import (
    AggregationSpec,
    ColumnType,
    CrosstabSpec,
    SortDirection,
    WindowFunction,
    WindowRange,
)

if TYPE_CHECKING:
    from mammoth._mixins._host import ViewHost
    from mammoth.condition import CompoundCondition, Condition, NotCondition
else:
    ViewHost = object


class AggregateOpsMixin(ViewHost):
    """Mixin for aggregation operations on a View."""

    def pivot(
        self,
        group_by: list[str],
        aggregations: list[AggregationSpec | dict[str, Any]],
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Group / aggregate / pivot (PIVOT task).

        Args:
            group_by: List of display names to group by.
            aggregations: List of :class:`AggregationSpec` objects or dicts
                with matching keys (``column``, ``function``, ``as_name``)::

                    [AggregationSpec(
                        column="Sales", function=AggregateFunction.SUM,
                        as_name="Total",
                    )]
                    [{"column": "Sales", "function": "SUM", "as_name": "Total"}]

            condition: Condition to apply.

        Returns:
            API response dict.

        Example::

            view.pivot(
                group_by=["Region"],
                aggregations=[AggregationSpec(
                    column="Sales",
                    function=AggregateFunction.SUM,
                    as_name="Total Sales",
                )],
            )
        """
        resolved = [AggregationSpec(**a) if isinstance(a, dict) else a for a in aggregations]
        return self._add_task(
            build_pivot_params(
                group_by,
                resolved,
                self.columns,
                self._internal_names,
                condition=condition,
                column_types=self.column_types,
            )
        )

    def window(
        self,
        function: WindowFunction,
        column: str | None = None,
        new_column: str | None = None,
        column_type: ColumnType = ColumnType.NUMERIC,
        existing_column: str | None = None,
        partition_by: list[str] | None = None,
        order_by: list[list[str | SortDirection]] | None = None,
        range_type: WindowRange = WindowRange.UNBOUNDED,
    ) -> dict[str, Any]:
        """Apply window function (WINDOW task).

        Args:
            function: Window function to apply.
            column: Source column for aggregate window functions.
            new_column: Name for result column.
            column_type: Type for new column (default ColumnType.NUMERIC).
            existing_column: Existing column to overwrite.
            partition_by: List of display names to partition by.
            order_by: Sort spec::

                [["column_name", SortDirection.DESC]]

            range_type: Window range (default WindowRange.UNBOUNDED).

        Returns:
            API response dict.

        Example::

            view.window(
                function=WindowFunction.ROW_NUMBER,
                new_column="Row #",
                partition_by=["Region"],
                order_by=[["Sales", SortDirection.DESC]],
            )
        """
        return self._add_task(
            build_window_params(
                function,
                self.columns,
                self._internal_names,
                column=column,
                new_column=new_column,
                column_type=column_type,
                existing_column=existing_column,
                partition_by=partition_by,
                order_by=order_by,
                range_type=range_type,
                name_gen=self._next_internal_name,
            )
        )

    def crosstab(
        self,
        rows: list[str],
        pivot_column: str,
        select: CrosstabSpec,
    ) -> dict[str, Any]:
        """Crosstab / pivot table (CROSSTAB task).

        Creates a matrix where row grouping columns define the rows, the
        ``pivot_column``'s distinct values become new columns, and cells
        contain the aggregated result.

        .. note::

            Crosstab uses the exports endpoint internally rather than
            standard pipeline tasks. Some post-crosstab operations may
            behave differently from standard pipeline views.

        Args:
            rows: List of display names for row grouping.
            pivot_column: Display name of column whose distinct values
                become the output columns.
            select: :class:`CrosstabSpec` defining the aggregation function
                and (optionally) the value column.

        Returns:
            API response dict.

        Example::

            from mammoth import CrosstabSpec, AggregateFunction

            view.crosstab(
                rows=["Region"],
                pivot_column="Product",
                select=CrosstabSpec(
                    function=AggregateFunction.SUM, column="Sales",
                ),
            )
        """
        return self._add_task(
            build_crosstab_params(
                rows,
                pivot_column,
                select,
                self.columns,
                self._internal_names,
                self.column_types,
            )
        )
