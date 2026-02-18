"""Column operation mixins: add, delete, copy, combine, convert."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.models.pipeline import ColumnType

if TYPE_CHECKING:
    from mammoth.condition import CompoundCondition, Condition


class ColumnOpsMixin:
    """Mixin for column-level operations on a View."""

    def add_column(self, name: str, column_type: ColumnType = ColumnType.TEXT) -> dict[str, Any]:
        """Add an empty column (ADD_COLUMN task).

        Args:
            name: Display name for the new column.
            column_type: Column type (default ColumnType.TEXT).

        Returns:
            API response dict.
        """
        return self._add_task(  # type: ignore[attr-defined]
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
        """Remove columns (DELETE task).

        Args:
            columns: List of display names to delete.

        Returns:
            API response dict.
        """
        return self._add_task({"DELETE": self._resolve_columns(columns)})

    def copy_columns(self, copies: list[dict[str, Any]]) -> dict[str, Any]:
        """Duplicate columns (COPY task).

        Args:
            copies: List of copy specs::

                [{"source": "Sales", "as": "Sales Copy", "type": "NUMERIC"}]

        Returns:
            API response dict.
        """
        copy_items = []
        for c in copies:
            internal = self._next_internal_name()
            copy_items.append(
                {
                    "SOURCE": self._resolve_column(c["source"]),
                    "AS": self._build_as_column(
                        c.get("as", f"{c['source']} Copy"),
                        c.get("type", "TEXT"),
                        internal,
                    ),
                }
            )

        return self._add_task({"COPY": copy_items, "VERSION": 2})

    def combine_columns(
        self,
        sources: list[str],
        new_column: str | None = None,
        column_type: ColumnType = ColumnType.TEXT,
        existing_column: str | None = None,
        separator: str = " ",
        condition: Condition | CompoundCondition | None = None,
    ) -> dict[str, Any]:
        """Concatenate columns (COMBINE task).

        Args:
            sources: List of display names to combine.
            new_column: Name for result column.
            column_type: Type for new column (default ColumnType.TEXT).
            existing_column: Existing column to overwrite.
            separator: Separator between values (default space).
            condition: Condition to apply.

        Returns:
            API response dict.
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

    def convert_type(self, conversions: list[dict[str, str]]) -> dict[str, Any]:
        """Convert column types (CONVERT task).

        Args:
            conversions: List of conversion specs::

                [{"column": "Sales", "to": "NUMERIC"}]

        Returns:
            API response dict.
        """
        convert_items = []
        for c in conversions:
            convert_items.append(
                {
                    "SOURCE": self._resolve_column(c["column"]),
                    "TO_TYPE": c["to"].upper(),
                }
            )

        return self._add_task({"CONVERT": convert_items})
