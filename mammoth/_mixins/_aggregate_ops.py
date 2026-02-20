"""Aggregate operation mixins: pivot, window, crosstab."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.models.pipeline import (
    ColumnType,
    SortDirection,
    WindowFunction,
    WindowRange,
)

if TYPE_CHECKING:
    from mammoth.condition import CompoundCondition, Condition, NotCondition


class AggregateOpsMixin:
    """Mixin for aggregation operations on a View."""

    def _resolve_order_by(self, order_by: list[list[str | SortDirection]]) -> list[list[str]]:
        """Resolve order_by specs, mapping display names to internal names."""
        resolved: list[list[str]] = []
        for ob in order_by:
            col_name = str(ob[0])
            col = self._resolve_column(col_name) if col_name in self.columns else col_name
            direction = ob[1] if len(ob) > 1 else "ASC"
            resolved.append([col, direction])
        return resolved

    def pivot(
        self,
        group_by: list[str],
        aggregations: list[dict[str, Any]],
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Group / aggregate / pivot (PIVOT task).

        Args:
            group_by: List of display names to group by.
            aggregations: List of aggregation specs::

                [{"column": "Sales", "function": AggregateFunction.SUM, "as": "Total Sales"}]

            condition: Condition to apply.

        Returns:
            API response dict.

        Example::

            view.pivot(
                group_by=["Region"],
                aggregations=[{
                    "column": "Sales",
                    "function": AggregateFunction.SUM,
                    "as": "Total Sales",
                }],
            )
        """
        group_specs = []
        for idx, g in enumerate(group_by):
            group_specs.append(
                {
                    "COLUMN": self._resolve_column(g),
                    "ORDER": idx,
                }
            )

        select_specs = []
        base_order = len(group_by)
        for idx, agg in enumerate(aggregations):
            func = agg["function"]
            func_str = func.upper() if isinstance(func, str) else str(func)
            sel: dict[str, Any] = {
                "ORDER": base_order + idx,
                "FUNCTION": func_str,
                "COLUMN": self._resolve_column(agg["column"]),
                "AS": agg.get("as", f"{func_str}_{agg['column']}"),
            }
            if "delimiter" in agg:
                sel["DELIMITER"] = agg["delimiter"]
            select_specs.append(sel)

        pivot_spec: dict[str, Any] = {"GROUP_BY": group_specs, "SELECT": select_specs}
        if condition:
            pivot_spec["CONDITION"] = self._build_condition(condition)

        return self._add_task({"PIVOT": pivot_spec})

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
        evaluate: dict[str, Any] = {"FUNCTION": function}
        if column:
            resolved = self._resolve_column(column)
            evaluate["SOURCES"] = resolved
            evaluate["ARGUMENTS"] = [resolved]

        window_spec: dict[str, Any] = {
            "EVALUATE": evaluate,
            "RANGE": range_type,
        }

        if new_column:
            window_spec["AS"] = self._build_as_column(new_column, column_type)
        elif existing_column:
            window_spec["DESTINATION"] = self._resolve_column(existing_column)

        if partition_by:
            window_spec["GROUP_BY"] = [{"COLUMN": self._resolve_column(p)} for p in partition_by]

        if order_by:
            window_spec["ORDER_BY"] = self._resolve_order_by(order_by)

        return self._add_task({"WINDOW": window_spec})

    def crosstab(
        self,
        rows: list[str],
        pivot_column: str,
        select: dict[str, Any],
    ) -> dict[str, Any]:
        """Crosstab / pivot table (CROSSTAB task).

        Args:
            rows: List of display names for row grouping.
            pivot_column: Display name of column whose values become columns.
            select: Aggregation spec::

                {"column": "Sales", "function": AggregateFunction.SUM}

        Returns:
            API response dict.
        """
        func = select["function"]
        func_str = func.upper() if isinstance(func, str) else str(func)
        select_spec: dict[str, Any] = {"FUNCTION": func_str}
        if "column" in select:
            select_spec["COLUMN"] = self._resolve_column(select["column"])
        return self._add_task(
            {
                "CROSSTAB": {
                    "ROWS": [
                        {
                            "COLUMN": self._resolve_column(r),
                            "TYPE": self.column_types.get(r, "TEXT"),
                        }
                        for r in rows
                    ],
                    "COLUMNS": [
                        {
                            "COLUMN": self._resolve_column(pivot_column),
                            "TYPE": self.column_types.get(pivot_column, "TEXT"),
                        }
                    ],
                    "SELECT": select_spec,
                },
            }
        )
