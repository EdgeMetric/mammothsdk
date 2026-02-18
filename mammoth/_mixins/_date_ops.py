"""Date operation mixins: extract_date, date_diff, increment_date."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.models.pipeline import DateComponent, DateDiffUnit

if TYPE_CHECKING:
    from mammoth.condition import CompoundCondition, Condition


class DateOpsMixin:
    """Mixin for date transformation operations on a View."""

    def extract_date(
        self,
        column: str,
        component: DateComponent,
        new_column: str | None = None,
        existing_column: str | None = None,
    ) -> dict[str, Any]:
        """Extract date parts (EXTRACT_DATE task).

        Args:
            column: Source date column display name.
            component: Date component to extract.
            new_column: Name for result column.
            existing_column: Existing column to overwrite.

        Returns:
            API response dict.

        Example::

            view.extract_date("Order Date", DateComponent.YEAR, new_column="Order Year")
        """
        ed_spec: dict[str, Any] = {
            "SOURCE": self._resolve_column(column),
            "COMPONENT": component,
        }

        # Choose output type based on component
        text_components = {
            "weekday_text",
            "month_text",
            "month_day_year_hour_minute_second",
            "year_month_day_as_date",
        }
        output_type = "TEXT" if component in text_components else "NUMERIC"

        if new_column:
            ed_spec["AS"] = self._build_as_column(new_column, output_type)
        elif existing_column:
            ed_spec["DESTINATION"] = self._resolve_column(existing_column)

        return self._add_task({"EXTRACT_DATE": ed_spec})

    def date_diff(
        self,
        component: DateDiffUnit,
        start: str,
        end: str,
        new_column: str | None = None,
        existing_column: str | None = None,
    ) -> dict[str, Any]:
        """Calculate date difference (DATE_DIFF task).

        Args:
            component: Unit of difference (e.g. DateDiffUnit.DAY).
            start: Start date column display name.
            end: End date column display name.
            new_column: Name for result column.
            existing_column: Existing column to overwrite.

        Returns:
            API response dict.

        Example::

            view.date_diff(DateDiffUnit.DAY, start="Start Date", end="End Date",
                           new_column="Duration")
        """
        dd_spec: dict[str, Any] = {
            "COMPONENT": component,
            "MINUEND": {
                "TYPE": "COLUMN",
                "VALUE": self._resolve_column(end),
            },
            "SUBTRAHEND": {
                "TYPE": "COLUMN",
                "VALUE": self._resolve_column(start),
            },
        }

        if new_column:
            dd_spec["AS"] = self._build_as_column(new_column, "NUMERIC")
        elif existing_column:
            dd_spec["DESTINATION"] = self._resolve_column(existing_column)

        return self._add_task({"DATE_DIFF": dd_spec})

    def increment_date(
        self,
        column: str,
        delta: dict[str, int],
        new_column: str | None = None,
        existing_column: str | None = None,
        condition: Condition | CompoundCondition | None = None,
    ) -> dict[str, Any]:
        """Add or subtract from a date column (INCREMENT_DATE task).

        Args:
            column: Source date column display name.
            delta: Delta spec: {"DAYS": 30} or {"MONTHS": -1, "YEARS": 2}.
            new_column: Name for result column.
            existing_column: Existing column to overwrite.
            condition: Condition to apply.

        Returns:
            API response dict.
        """
        id_spec: dict[str, Any] = {
            "SOURCE": self._resolve_column(column),
            "DELTA": delta,
        }

        if new_column:
            id_spec["AS"] = self._build_as_column(new_column, "DATE")
        elif existing_column:
            id_spec["DESTINATION"] = self._resolve_column(existing_column)

        spec: dict[str, Any] = {"INCREMENT_DATE": id_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)
