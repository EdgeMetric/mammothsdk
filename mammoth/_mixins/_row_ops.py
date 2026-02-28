"""Row operation mixins: fill_missing, limit_rows, discard_duplicates, unnest."""

from __future__ import annotations

from typing import Any

from mammoth.models.pipeline import FillDirection, SortDirection


class RowOpsMixin:
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
        fill_spec: dict[str, Any] = {
            "COLUMN": self._resolve_column(column),
            "WITH": direction,
        }
        if partition_by:
            fill_spec["PARTITION_BY"] = self._resolve_column(partition_by)
        if order_by:
            fill_spec["ORDER_BY"] = self._resolve_order_by(order_by)

        return self._add_task({"FILL": fill_spec})

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
        spec: dict[str, Any] = {"LIMIT": {"LIMIT": n, "BOTTOM": bottom}}
        if order_by:
            spec["ORDER_BY"] = self._resolve_order_by(order_by)

        return self._add_task(spec)

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
        resolved = self._resolve_columns(ignore_columns) if ignore_columns else []
        return self._add_task(
            {
                "DISCARD_DUPLICATES": True,
                "IGNORE_COLUMNS": resolved,
            }
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
        col_specs = []
        for c in columns:
            display = c
            if c in self._internal_names:
                for dname, iname in self.columns.items():
                    if iname == c:
                        display = dname
                        break
            col_specs.append(
                {
                    "COLUMN": self._resolve_column(c),
                    "LABEL": display,
                }
            )

        return self._add_task(
            {
                "UNNEST": {
                    "COLUMNS": col_specs,
                    "LABEL": {"COLUMN": label_column, "TYPE": "TEXT"},
                    "VALUE": {"COLUMN": value_column, "TYPE": "TEXT"},
                },
            }
        )
