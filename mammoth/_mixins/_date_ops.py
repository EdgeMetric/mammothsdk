"""Date operation mixins: extract_date, date_diff, increment_date."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth._pure.builders import (
    build_date_diff_params,
    build_extract_date_params,
    build_increment_date_params,
)
from mammoth.models.pipeline import DateComponent, DateDelta, DateDiffUnit

if TYPE_CHECKING:
    from mammoth._mixins._host import ViewHost
    from mammoth.condition import CompoundCondition, Condition, NotCondition
else:
    ViewHost = object


class DateOpsMixin(ViewHost):
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
        return self._add_task(
            build_extract_date_params(
                column,
                component,
                self.columns,
                self._internal_names,
                new_column=new_column,
                existing_column=existing_column,
                name_gen=self._next_internal_name,
            )
        )

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
        return self._add_task(
            build_date_diff_params(
                component,
                start,
                end,
                self.columns,
                self._internal_names,
                new_column=new_column,
                existing_column=existing_column,
                name_gen=self._next_internal_name,
            )
        )

    def increment_date(
        self,
        column: str,
        delta: DateDelta,
        new_column: str | None = None,
        existing_column: str | None = None,
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Add or subtract from a date column (INCREMENT_DATE task).

        Args:
            column: Source date column display name.
            delta: :class:`DateDelta` specifying the increment. Use negative
                values to subtract::

                    DateDelta(days=30)
                    DateDelta(years=1, months=-3)

            new_column: Name for a new result column.
            existing_column: Display name of existing column to overwrite.
            condition: Only apply to rows matching this condition.

        Returns:
            API response dict.

        Examples::

            from mammoth import DateDelta

            # Add 30 days
            view.increment_date("Order Date", DateDelta(days=30),
                                new_column="Due Date")

            # Subtract 1 year, add 6 months
            view.increment_date("Start Date", DateDelta(years=-1, months=6),
                                new_column="Adjusted Date")

            # Conditional increment
            view.increment_date(
                "Ship Date", DateDelta(days=7),
                existing_column="Ship Date",
                condition=Condition("Priority", Operator.EQ, "Low"),
            )
        """
        return self._add_task(
            build_increment_date_params(
                column,
                delta,
                self.columns,
                self._internal_names,
                new_column=new_column,
                existing_column=existing_column,
                condition=condition,
                column_types=self.column_types,
                name_gen=self._next_internal_name,
            )
        )
