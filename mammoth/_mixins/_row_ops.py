"""Row operation mixins: fill_missing, limit_rows, discard_duplicates, unnest."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth._pure.builders import (
    build_discard_duplicates_params,
    build_fill_params,
    build_limit_params,
    build_unnest_params,
)
from mammoth.models.pipeline import FillDirection, SortDirection

if TYPE_CHECKING:
    from mammoth._mixins._host import ViewHost
else:
    ViewHost = object


class RowOpsMixin(ViewHost):
    """Mixin for row-level operations on a View."""

    def fill_missing(
        self,
        column: str,
        direction: FillDirection,
        partition_by: str | None = None,
        order_by: list[list[str | SortDirection]] | None = None,
    ) -> dict[str, Any]:
        """Fill missing (null/empty) values using adjacent rows (FILL task).

        Args:
            column: Display name of column to fill.
            direction: Fill direction — ``FillDirection.LAST_VALUE``
                fills downward (forward-fill), ``FillDirection.FIRST_VALUE``
                fills upward (back-fill).
            partition_by: Display name of column to partition by (optional).
                Fill restarts at each partition boundary.
            order_by: Sort order applied before filling (optional)::

                    [["Date", SortDirection.ASC]]

        Returns:
            API response dict.

        Examples::

            from mammoth import FillDirection, SortDirection

            # Forward-fill missing values
            view.fill_missing("Price", FillDirection.LAST_VALUE)

            # Fill within partitions, ordered by date
            view.fill_missing(
                "Metric", FillDirection.LAST_VALUE,
                partition_by="Region",
                order_by=[["Date", SortDirection.ASC]],
            )
        """
        return self._add_task(
            build_fill_params(
                column,
                direction,
                self.columns,
                self._internal_names,
                partition_by=partition_by,
                order_by=order_by,
            )
        )

    def limit_rows(
        self,
        n: int,
        bottom: bool = False,
        order_by: list[list[str | SortDirection]] | None = None,
    ) -> dict[str, Any]:
        """Keep top or bottom N rows (LIMIT task).

        Args:
            n: Number of rows to keep.
            bottom: If True, keep bottom N rows instead of top N
                (default False).
            order_by: Sort order applied *before* limiting (optional)::

                    [["Sales", SortDirection.DESC]]

        Returns:
            API response dict.

        Examples::

            from mammoth import SortDirection

            view.limit_rows(100)
            view.limit_rows(10, order_by=[["Sales", SortDirection.DESC]])
            view.limit_rows(5, bottom=True)
        """
        return self._add_task(build_limit_params(n, self.columns, bottom=bottom, order_by=order_by))

    def discard_duplicates(
        self,
        ignore_columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Remove duplicate rows (DISCARD_DUPLICATES task).

        Args:
            ignore_columns: Display names of columns to ignore when detecting
                duplicates. Empty/None means consider all columns.

        Returns:
            API response dict.

        Example::

            view.discard_duplicates()
            view.discard_duplicates(ignore_columns=["Notes", "Timestamp"])
        """
        return self._add_task(
            build_discard_duplicates_params(self.columns, self._internal_names, ignore_columns)
        )

    def unnest(
        self,
        columns: list[str],
        label_column: str = "Label",
        value_column: str = "Value",
    ) -> dict[str, Any]:
        """Unpivot (melt) columns to rows (UNNEST task).

        Converts multiple columns into rows. Each original column becomes a
        label/value pair, multiplying the row count accordingly.

        Args:
            columns: Display names of columns to unnest.
            label_column: Name for the new label column that holds the
                original column names (default ``"Label"``).
            value_column: Name for the new value column that holds the
                original cell values (default ``"Value"``).

        Returns:
            API response dict.

        Example::

            # Columns "Q1", "Q2", "Q3", "Q4" → rows with Label/Value
            view.unnest(["Q1", "Q2", "Q3", "Q4"],
                        label_column="Quarter", value_column="Revenue")
        """
        return self._add_task(
            build_unnest_params(
                columns,
                self.columns,
                self._internal_names,
                label_column=label_column,
                value_column=value_column,
                name_gen=self._next_internal_name,
            )
        )
