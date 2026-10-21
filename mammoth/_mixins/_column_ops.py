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
from mammoth.exceptions import MammothError, MammothValidationError
from mammoth.models.pipeline import ColumnType, ConversionSpec, CopySpec

#: Keys a column's ``FORMAT_INFO`` entry holds (what the web grid's format menu writes).
COLUMN_FORMAT_KEYS = frozenset(
    {
        "date_format",
        "postgres_date_format",
        "date_format_type",
        "tz",
        "decimal_spec",
        "numtype",
        "currency_symbol",
        "is_percentage",
        "thousands_separator",
        "decimal_separator",
        "scientific",
        "numeric_precision",
        "enabled",
    }
)

if TYPE_CHECKING:
    from mammoth._mixins._host import ViewHost
    from mammoth.condition import CompoundCondition, Condition, NotCondition
else:
    ViewHost = object


class ColumnOpsMixin(ViewHost):
    """Mixin for column-level operations on a View."""

    async def add_column(
        self, name: str, column_type: ColumnType = ColumnType.TEXT
    ) -> dict[str, Any]:
        """Add an empty column (ADD_COLUMN task).

        Args:
            name: Display name for the new column.
            column_type: Column type (default ``ColumnType.TEXT``).

        Returns:
            API response dict.

        Examples::

            await view.add_column("Notes")
            await view.add_column("Score", column_type=ColumnType.NUMERIC)
            await view.add_column("Created", column_type=ColumnType.DATE)
        """
        return await self._add_task(
            build_add_column_params(name, column_type, self._next_internal_name)
        )

    async def delete_columns(self, columns: list[str]) -> dict[str, Any]:
        """Remove one or more columns (DELETE task).

        Args:
            columns: List of display names to delete.

        Returns:
            API response dict.

        Examples::

            await view.delete_columns(["Temp"])
            await view.delete_columns(["Notes", "Internal ID", "Debug"])
        """
        return await self._add_task(
            build_delete_params(columns, self.columns, self._internal_names)
        )

    async def copy_columns(self, copies: list[CopySpec]) -> dict[str, Any]:
        """Duplicate columns (COPY task).

        Args:
            copies: List of :class:`CopySpec` objects::

                    [CopySpec(source="Sales", as_name="Sales Copy")]

        Returns:
            API response dict.
        """
        return await self._add_task(
            build_copy_params(
                copies,
                self.columns,
                self._internal_names,
                self.column_types,
                self._next_internal_name,
            )
        )

    async def combine_columns(
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
            await view.combine_columns(
                ["First Name", "Last Name"],
                new_column="Full Name", separator=" ",
            )

            # Combine with custom separator, overwrite existing column
            await view.combine_columns(
                ["City", "State", "Zip"],
                existing_column="Address", separator=", ",
            )
        """
        return await self._add_task(
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

    async def convert_type(self, conversions: list[ConversionSpec]) -> dict[str, Any]:
        """Convert column data types (CONVERT task).

        Args:
            conversions: List of :class:`ConversionSpec` objects::

                    [ConversionSpec(column="Sales", to=ColumnType.NUMERIC)]

        Returns:
            API response dict.

        Examples::

            from mammoth import ConversionSpec, ColumnType

            # Text to numeric
            await view.convert_type([ConversionSpec(column="Sales", to=ColumnType.NUMERIC)])

            # Text to date (specify the source format)
            await view.convert_type([
                ConversionSpec(column="Order Date", to=ColumnType.DATE,
                               format="MM/DD/YYYY"),
            ])
        """
        return await self._add_task(
            build_convert_params(conversions, self.columns, self._internal_names)
        )

    async def rename_columns(self, renames: dict[str, str]) -> dict[str, Any]:
        """Rename columns (the web grid's rename; not a pipeline task).

        The new name is a view display property (``COLUMN_NAMES``), the same
        change as renaming a column header in the web app. The column keeps
        its internal name, so pipeline tasks that use it keep working, and
        later operations, data reads, exports and dashboards use the new name.

        Args:
            renames: ``{current display name: new display name}``.

        Returns:
            ``{"renamed": {old: new}, "columns": [display names after]}``.

        Raises:
            MammothColumnError: A current name is not a column of the view.
            MammothError: A new name is not among the view's columns after the
                rename (the server accepted the change but did not apply it).
            ValueError: ``renames`` is empty, a new name is blank, or two
                columns would end up with the same name.

        Example::

            await view.rename_columns({"cust_id": "Customer ID", "amt": "Amount"})
        """
        if not renames:
            raise ValueError("renames must name at least one column")
        value: dict[str, str] = {}
        cleaned: dict[str, str] = {}
        for old, new in renames.items():
            new_name = " ".join(str(new).split())
            if not new_name:
                raise ValueError(f"new name for {old!r} is blank")
            value[self._resolve_column(old)] = new_name
            cleaned[old] = new_name
        final = [cleaned.get(name, name).lower() for name in self.columns]
        if len(final) != len(set(final)):
            raise ValueError("two columns would have the same name after the rename")
        if self._build_only:
            return {"status": "validated", "renamed": cleaned}
        await self._client.dataviews.update(
            self.dataset_id,
            self.id,
            [{"op": "replace", "path": "display_properties/COLUMN_NAMES", "value": value}],
        )
        await self.refresh()
        # The refreshed columns are the proof: a PATCH the server accepted
        # but did not apply must not read as a rename that happened.
        not_applied = {old: new for old, new in cleaned.items() if new not in self.columns}
        if not_applied:
            raise MammothError(
                "The server accepted the rename but did not apply it.",
                details={
                    "reason": (
                        "rename not applied: the view's columns after the change"
                        " do not show the new name"
                    ),
                    "not_applied": not_applied,
                    "columns_after": list(self.columns),
                },
            )
        return {"renamed": cleaned, "columns": list(self.columns)}

    async def set_column_format(self, formats: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Set how columns are displayed (the web grid's column format; not a pipeline task).

        The format is a view display property (``FORMAT_INFO``), the same change as
        the format menu of a column header in the web app. It changes how values show
        in the grid, exports that use the format and dashboards, never the stored
        values. Keys you give replace the same keys of the column's current format;
        keys you leave out are kept.

        Args:
            formats: ``{display name: {format key: value}}``. Keys by column type:
                DATE ``date_format`` (python style, ``"%d-%b-%Y"``),
                ``postgres_date_format`` (``"DD-Mon-YYYY"``), ``tz``;
                NUMERIC ``decimal_spec`` (decimal places), ``numtype`` (``"float"`` or
                ``"int"``), ``currency_symbol``, ``is_percentage``,
                ``thousands_separator``, ``decimal_separator``, ``scientific``.

        Returns:
            ``{"formatted": {display name: the column's format after}}``.

        Raises:
            MammothColumnError: A name is not a column of the view.
            MammothValidationError: ``formats`` is empty, or a column's format is
                empty or uses a key that is not a format key.

        Example::

            await view.set_column_format({
                "Admitted": {"date_format": "%d-%b-%Y"},
                "Revenue": {"decimal_spec": 2, "currency_symbol": "$"},
            })
        """
        if not formats:
            raise MammothValidationError("formats must name at least one column")
        value: dict[str, dict[str, Any]] = {}
        current = (self.raw.get("display_properties") or {}).get("FORMAT_INFO") or {}
        for name, fmt in formats.items():
            internal = self._resolve_column(name)
            unknown = sorted(set(fmt) - COLUMN_FORMAT_KEYS) if isinstance(fmt, dict) else []
            if not isinstance(fmt, dict) or not fmt or unknown:
                raise MammothValidationError(
                    f"format for {name!r} must be a non-empty object of format keys; "
                    f"{'unknown: ' + ', '.join(unknown) + '. ' if unknown else ''}"
                    f"allowed: {', '.join(sorted(COLUMN_FORMAT_KEYS))}",
                    details={"column": name},
                )
            value[internal] = {**(current.get(internal) or {}), **fmt}
        if self._build_only:
            return {"status": "validated", "formatted": dict(formats)}
        await self._client.dataviews.update(
            self.dataset_id,
            self.id,
            [{"op": "replace", "path": "display_properties/FORMAT_INFO", "value": value}],
        )
        await self.refresh()
        after = (self.raw.get("display_properties") or {}).get("FORMAT_INFO") or {}
        return {"formatted": {name: after.get(self._resolve_column(name), {}) for name in formats}}
