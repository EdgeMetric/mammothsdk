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
        """Fill missing values forward or backward (FILL task).

        Args:
            column: Display name of column to fill.
            direction: Fill direction.
            partition_by: Column to partition by (optional).
            order_by: Sort order for fill direction (optional).

        Returns:
            API response dict.
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
            bottom: If True, keep bottom N instead of top N (default False).
            order_by: Sort order before limiting (optional).

        Returns:
            API response dict.
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
        return self._add_task(  # type: ignore[attr-defined]
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
        """Unpivot columns to rows (UNNEST task).

        Args:
            columns: Display names of columns to unnest.
            label_column: Name for the label column (default "Label").
            value_column: Name for the value column (default "Value").

        Returns:
            API response dict.
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

        return self._add_task(  # type: ignore[attr-defined]
            {
                "UNNEST": {
                    "COLUMNS": col_specs,
                    "LABEL": {"COLUMN": label_column, "TYPE": "TEXT"},
                    "VALUE": {"COLUMN": value_column, "TYPE": "TEXT"},
                },
            }
        )
