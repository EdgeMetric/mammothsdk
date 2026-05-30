"""Column operation mixins: add, delete, copy, combine, convert."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth._pure.builders import (
    build_add_column_params,
    build_combine_params,
    build_convert_params,
    build_copy_params,
    build_delete_params,
)
from mammoth.models.pipeline import ColumnType, ConversionSpec, CopySpec

if TYPE_CHECKING:
    from mammoth._mixins._host import ViewHost
    from mammoth.condition import CompoundCondition, Condition, NotCondition
else:
    ViewHost = object


class ColumnOpsMixin(ViewHost):
    """Mixin for column-level operations on a View."""

    def add_column(self, name: str, column_type: ColumnType = ColumnType.TEXT) -> dict[str, Any]:
        """Add an empty column (ADD_COLUMN task).

        Args:
            name: Display name for the new column.
            column_type: Column type (default ``ColumnType.TEXT``).

        Returns:
            API response dict.

        Examples::

            view.add_column("Notes")
            view.add_column("Score", column_type=ColumnType.NUMERIC)
            view.add_column("Created", column_type=ColumnType.DATE)
        """
        return self._add_task(build_add_column_params(name, column_type, self._next_internal_name))

    def delete_columns(self, columns: list[str]) -> dict[str, Any]:
        """Remove one or more columns (DELETE task).

        Args:
            columns: List of display names to delete.

        Returns:
            API response dict.

        Examples::

            view.delete_columns(["Temp"])
            view.delete_columns(["Notes", "Internal ID", "Debug"])
        """
        return self._add_task(build_delete_params(columns, self.columns, self._internal_names))

    def copy_columns(self, copies: list[CopySpec | dict[str, Any]]) -> dict[str, Any]:
        """Duplicate columns (COPY task).

        Args:
            copies: List of :class:`CopySpec` objects or dicts with
                matching keys (``source``, ``as_name``, ``type``)::

                    [CopySpec(source="Sales", as_name="Sales Copy")]
                    [{"source": "Sales", "as_name": "Sales Copy"}]

        Returns:
            API response dict.
        """
        resolved = [CopySpec(**c) if isinstance(c, dict) else c for c in copies]
        return self._add_task(
            build_copy_params(
                resolved,
                self.columns,
                self._internal_names,
                self.column_types,
                self._next_internal_name,
            )
        )

    def combine_columns(
        self,
        sources: list[str],
        new_column: str | None = None,
        column_type: ColumnType = ColumnType.TEXT,
        existing_column: str | None = None,
        separator: str = " ",
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Concatenate multiple columns into one (COMBINE task).

        Args:
            sources: List of display names to combine (in order).
            new_column: Name for a new result column. Mutually exclusive with
                ``existing_column``.
            column_type: Type for the new column (default ``ColumnType.TEXT``).
            existing_column: Display name of an existing column to overwrite
                with the combined values.
            separator: String inserted between each column's value
                (default ``" "``).
            condition: Only combine in rows matching this condition.

        Returns:
            API response dict.

        Examples::

            # Combine first + last name into a new column
            view.combine_columns(
                ["First Name", "Last Name"],
                new_column="Full Name", separator=" ",
            )

            # Combine with custom separator, overwrite existing column
            view.combine_columns(
                ["City", "State", "Zip"],
                existing_column="Address", separator=", ",
            )
        """
        return self._add_task(
            build_combine_params(
                sources,
                self.columns,
                self._internal_names,
                new_column=new_column,
                column_type=column_type,
                existing_column=existing_column,
                separator=separator,
                condition=condition,
                column_types=self.column_types,
                name_gen=self._next_internal_name,
            )
        )

    def convert_type(self, conversions: list[ConversionSpec | dict[str, Any]]) -> dict[str, Any]:
        """Convert column data types (CONVERT task).

        Args:
            conversions: List of :class:`ConversionSpec` objects or dicts with
                matching keys (``column``, ``to``, ``format``)::

                    [ConversionSpec(column="Sales", to=ColumnType.NUMERIC)]
                    [{"column": "Sales", "to": "NUMERIC"}]

        Returns:
            API response dict.

        Examples::

            from mammoth import ConversionSpec, ColumnType

            # Text to numeric
            view.convert_type([ConversionSpec(column="Sales", to=ColumnType.NUMERIC)])

            # Using plain dicts
            view.convert_type([{"column": "Sales", "to": "NUMERIC"}])

            # Text to date (specify the source format)
            view.convert_type([
                ConversionSpec(column="Order Date", to=ColumnType.DATE,
                               format="MM/DD/YYYY"),
            ])
        """
        resolved = [ConversionSpec(**c) if isinstance(c, dict) else c for c in conversions]
        return self._add_task(build_convert_params(resolved, self.columns, self._internal_names))
