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
    SaveAsDatasetMode,
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
        aggregations: list[AggregationSpec],
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Group / aggregate / pivot (PIVOT task).

        Args:
            group_by: List of display names to group by.
            aggregations: List of :class:`AggregationSpec` objects::

                    [AggregationSpec(
                        column="Sales", function=AggregateFunction.SUM,
                        as_name="Total",
                    )]

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
        return self._add_task(
            build_pivot_params(
                group_by,
                aggregations,
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
        select: CrosstabSpec | list[CrosstabSpec],
        *,
        dataset_name: str,
        save_as_mode: SaveAsDatasetMode = SaveAsDatasetMode.REPLACE,
        target_ds_id: int | None = None,
        condition: Condition | CompoundCondition | NotCondition | None = None,
        timeout: int | None = None,
    ) -> int:
        """Crosstab / group-and-pivot — materialise a new pivoted dataset.

        Row grouping columns define the rows, the ``pivot_column``'s distinct
        values become new columns, and cells hold the aggregated result.

        Unlike standard transforms, a crosstab produces a NEW dataset, so it is
        submitted through the internal-dataset export handler and run as an
        async job. This method blocks until the dataset is materialised.

        Args:
            rows: Display names of the row-grouping columns.
            pivot_column: Display name of the column whose distinct values
                become the output columns.
            select: A :class:`CrosstabSpec` (or list of them) defining each
                aggregation function and (except for COUNT) its value column.
            dataset_name: Name for the dataset the crosstab creates.
            save_as_mode: Whether to replace or append when writing the output
                dataset (defaults to :attr:`SaveAsDatasetMode.REPLACE`).
            target_ds_id: Existing dataset to write into; ``None`` creates a
                new one.
            condition: Optional row filter applied before aggregating.
            timeout: Max seconds to wait for the job (defaults to the client's
                ``job_timeout``).

        Returns:
            The id of the dataset the crosstab wrote to (the new dataset when
            ``target_ds_id`` is None, otherwise ``target_ds_id``).

        Example::

            from mammoth import CrosstabSpec, AggregateFunction

            view.crosstab(
                rows=["Region"],
                pivot_column="Product",
                select=CrosstabSpec(function=AggregateFunction.SUM, column="Sales"),
                dataset_name="Sales by Region x Product",
            )
        """
        target_properties = build_crosstab_params(
            rows,
            pivot_column,
            select,
            dataset_name,
            self.columns,
            self._internal_names,
            self.column_types,
            save_as_mode=save_as_mode,
            target_ds_id=target_ds_id,
        )
        return self._run_internal_dataset_export(target_properties, timeout, condition)
