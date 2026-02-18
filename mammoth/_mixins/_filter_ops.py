"""Filter operation mixins: filter_rows, set_values."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.models.pipeline import ColumnType, FilterType, SetValue

if TYPE_CHECKING:
    from mammoth.condition import CompoundCondition, Condition


class FilterOpsMixin:
    """Mixin for filter and set_values operations on a View."""

    def filter_rows(
        self,
        condition: Condition | CompoundCondition,
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
        built_condition = self._build_condition(condition)
        if isinstance(built_condition, dict):
            built_condition["FILTER_TYPE"] = filter_type
            built_condition["PROMPT"] = prompt
        spec: dict[str, Any] = {"SELECT": "ALL", "CONDITION": built_condition}
        return self._add_task(spec)

    def set_values(
        self,
        values: list[SetValue | dict[str, Any]],
        new_column: str | None = None,
        column_type: ColumnType = ColumnType.TEXT,
        existing_column: str | None = None,
        condition: Condition | CompoundCondition | None = None,
    ) -> dict[str, Any]:
        """Label and insert values into a new or existing column (SET task).

        Creates a VERSION 2 SET payload.

        Args:
            values: List of SetValue objects or dicts with ``value`` and
                optional ``condition`` keys.
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
        value_items: list[dict[str, Any]] = []
        for v in values:
            if isinstance(v, SetValue):
                item: dict[str, Any] = {"PROVIDER_TYPE": "FIXED", "PROVIDER": v.value}
                cond = v.condition
            else:
                item = {"PROVIDER_TYPE": "FIXED", "PROVIDER": v["value"]}
                cond = v.get("condition")
            if cond is not None:
                item["CONDITION"] = self._build_condition(cond)
            value_items.append(item)

        set_dict: dict[str, Any] = {"VALUES": value_items}

        if new_column:
            set_dict["AS"] = self._build_as_column(new_column, column_type)
        elif existing_column:
            set_dict["DESTINATION"] = self._resolve_column(existing_column)

        spec: dict[str, Any] = {"SET": set_dict, "VERSION": 2}

        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)
