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
            column_type: Column type (default ColumnType.TEXT).

        Returns:
            API response dict.
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
        """Remove columns (DELETE task).

        Args:
            columns: List of display names to delete.

        Returns:
            API response dict.
        """
        return self._add_task({"DELETE": self._resolve_columns(columns)})

    def copy_columns(self, copies: list[CopySpec | dict[str, Any]]) -> dict[str, Any]:
        """Duplicate columns (COPY task).

        Args:
            copies: List of CopySpec objects or dicts::

                [CopySpec(source="Sales", as_name="Sales Copy", type="NUMERIC")]
                [{"source": "Sales", "as": "Sales Copy", "type": "NUMERIC"}]

            Dicts can also include a ``condition`` key with a Condition
            object to apply per-item conditions.

        Returns:
            API response dict.
        """
        copy_items = []
        for c in copies:
            internal = self._next_internal_name()
            if isinstance(c, CopySpec):
                source = c.source
                as_name = c.as_name or f"{source} Copy"
                col_type = c.type
                cond = c.condition
            else:
                source = c["source"]
                as_name = c.get("as", f"{source} Copy")
                col_type = c.get("type", "TEXT")
                cond = c.get("condition")
            item: dict[str, Any] = {
                "SOURCE": self._resolve_column(source),
                "AS": self._build_as_column(as_name, col_type, internal),
            }
            if cond is not None:
                item["CONDITION"] = self._build_condition(cond)
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

    def convert_type(self, conversions: list[ConversionSpec | dict[str, str]]) -> dict[str, Any]:
        """Convert column types (CONVERT task).

        Args:
            conversions: List of ConversionSpec objects or dicts::

                [ConversionSpec(column="Sales", to="NUMERIC")]
                [{"column": "Sales", "to": "NUMERIC"}]
                [{"column": "Date Col", "to": "DATE", "format": "MM/DD/YYYY"}]

        Returns:
            API response dict.
        """
        convert_items = []
        for c in conversions:
            if isinstance(c, ConversionSpec):
                col, to_type, fmt = c.column, c.to, c.format
            else:
                col, to_type, fmt = c["column"], c["to"], c.get("format")
            item: dict[str, Any] = {
                "SOURCE": self._resolve_column(col),
                "TO_TYPE": to_type.upper(),
            }
            if fmt is not None:
                item["FORMAT"] = fmt
            convert_items.append(item)

        return self._add_task({"CONVERT": convert_items})
