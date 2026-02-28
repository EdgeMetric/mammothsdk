"""Column operation mixins: add, delete, copy, combine, convert."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.models.pipeline import ColumnType, ConversionSpec, CopySpec

if TYPE_CHECKING:
    from mammoth.condition import CompoundCondition, Condition, NotCondition


class ColumnOpsMixin:
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
        return self._add_task(
            {
                "ADD_COLUMN": [
                    {
                        "COLUMN": name,
                        "TYPE": column_type,
                        "INTERNAL_NAME": self._next_internal_name(),
                    }
                ],
            }
        )

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
        return self._add_task({"DELETE": self._resolve_columns(columns)})

    def copy_columns(self, copies: list[CopySpec]) -> dict[str, Any]:
        """Duplicate columns (COPY task).

        Args:
            copies: List of CopySpec objects::

                [CopySpec(source="Sales", as_name="Sales Copy", type=ColumnType.NUMERIC)]

        Returns:
            API response dict.
        """
        copy_items = []
        for c in copies:
            internal = self._next_internal_name()
            as_name = c.as_name or f"{c.source} Copy"
            item: dict[str, Any] = {
                "SOURCE": self._resolve_column(c.source),
                "AS": self._build_as_column(as_name, c.type, internal),
            }
            if c.condition is not None:
                item["CONDITION"] = self._build_condition(c.condition)
            copy_items.append(item)

        return self._add_task({"COPY": copy_items, "VERSION": 2})

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
        source_specs: list[dict[str, str]] = []
        for i, s in enumerate(sources):
            source_specs.append({"COLUMN": self._resolve_column(s)})
            if i < len(sources) - 1:
                source_specs.append({"STRING": separator})

        combine_spec: dict[str, Any] = {"SOURCE": source_specs}

        if new_column:
            combine_spec["AS"] = self._build_as_column(new_column, column_type)
        elif existing_column:
            combine_spec["DESTINATION"] = self._resolve_column(existing_column)

        spec: dict[str, Any] = {"COMBINE": combine_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)

    def convert_type(self, conversions: list[ConversionSpec]) -> dict[str, Any]:
        """Convert column data types (CONVERT task).

        Args:
            conversions: List of :class:`ConversionSpec` objects. For date
                conversions, provide the ``format`` that describes the
                *current* string format of the data.

        Returns:
            API response dict.

        Examples::

            from mammoth import ConversionSpec, ColumnType

            # Text to numeric
            view.convert_type([ConversionSpec(column="Sales", to=ColumnType.NUMERIC)])

            # Text to date (specify the source format)
            view.convert_type([
                ConversionSpec(column="Order Date", to=ColumnType.DATE,
                               format="MM/DD/YYYY"),
            ])

            # Multiple conversions at once
            view.convert_type([
                ConversionSpec(column="Price", to=ColumnType.NUMERIC),
                ConversionSpec(column="Qty", to=ColumnType.NUMERIC),
            ])
        """
        convert_items = []
        for c in conversions:
            item: dict[str, Any] = {
                "SOURCE": self._resolve_column(c.column),
                "TO_TYPE": c.to.value,
            }
            if c.format is not None:
                item["FORMAT"] = c.format
            convert_items.append(item)

        return self._add_task({"CONVERT": convert_items})
