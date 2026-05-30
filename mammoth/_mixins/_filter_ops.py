"""Filter operation mixins: filter_rows, set_values."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth._pure.builders import build_filter_params, build_set_params
from mammoth.models.pipeline import ColumnType, FilterType, SetValue

if TYPE_CHECKING:
    from mammoth._mixins._host import ViewHost
    from mammoth.condition import CompoundCondition, Condition, NotCondition
else:
    ViewHost = object


class FilterOpsMixin(ViewHost):
    """Mixin for filter and set_values operations on a View."""

    def filter_rows(
        self,
        condition: Condition | CompoundCondition | NotCondition,
        filter_type: FilterType = FilterType.SHOW,
        prompt: str = "",
    ) -> dict[str, Any]:
        """Filter rows by condition (SELECT task).

        Args:
            condition: Condition or CompoundCondition object.
            filter_type: SHOW to keep matching rows, REMOVE to discard them.
            prompt: Natural-language description of the filter intent (optional).

        Returns:
            API response dict.

        Example::

            view.filter_rows(Condition("Sales", Operator.GTE, 1000))
            view.filter_rows(cond1 & cond2, filter_type=FilterType.REMOVE)
        """
        return self._add_task(
            build_filter_params(condition, self.columns, self.column_types, filter_type, prompt)
        )

    def set_values(
        self,
        values: list[SetValue],
        new_column: str | None = None,
        column_type: ColumnType = ColumnType.TEXT,
        existing_column: str | None = None,
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Label and insert values into a new or existing column (SET task).

        Creates a VERSION 2 SET payload.

        Args:
            values: List of SetValue objects.
            new_column: Name for a new column (mutually exclusive with existing_column).
            column_type: Type for new column (default ColumnType.TEXT).
            existing_column: Display name of existing column to update.
            condition: Global condition applied to the whole task.

        Returns:
            API response dict.

        Example::

            view.set_values(
                new_column="Risk Level",
                column_type=ColumnType.TEXT,
                values=[
                    SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
                    SetValue("Low"),
                ],
            )
        """
        return self._add_task(
            build_set_params(
                values,
                self.columns,
                new_column=new_column,
                column_type=column_type,
                existing_column=existing_column,
                internal_names=self._internal_names,
                condition=condition,
                column_types=self.column_types,
                name_gen=self._next_internal_name,
            )
        )
