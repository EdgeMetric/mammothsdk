"""Math operation mixin."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth._expression_parser import parameter_names
from mammoth._pure.builders import build_math_params, build_small_large_params
from mammoth.exceptions import MammothValidationError
from mammoth.models.pipeline import ColumnType, SmallLargeFunction

if TYPE_CHECKING:
    from mammoth._mixins._host import ViewHost
    from mammoth.condition import CompoundCondition, Condition, NotCondition
else:
    ViewHost = object


_PARAMETER_PAGE = 100


class MathOpsMixin(ViewHost):
    """Mixin for arithmetic operations on a View."""

    async def math(
        self,
        expression: str,
        new_column: str | None = None,
        column_type: ColumnType = ColumnType.NUMERIC,
        existing_column: str | None = None,
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Apply arithmetic operations (MATH task).

        Args:
            expression: A string expression (e.g. ``"Price * Quantity"``)
                that will be parsed automatically. ``{name}`` uses the
                workspace or project parameter of that name; the step re-runs
                when the parameter's value changes.
            new_column: Name for result column (creates new).
            column_type: Type for new column (default ColumnType.NUMERIC).
            existing_column: Existing column to overwrite.
            condition: Condition to apply.

        Returns:
            API response dict.

        Examples::

            await view.math("Price * Quantity", new_column="Total")
            await view.math("(Price + Tax) * 1.1", new_column="Grand Total")
            await view.math("Price * {tax_rate}", new_column="Gross")
        """
        # The parser consumes a scoped display-name map. Add exact internal
        # identities as aliases so callers can use either form without any
        # substring replacement (and keep unknown tokens fatal).
        # Preserve display-name precedence when a display name happens to be
        # identical to another column's backend identity.  For example,
        # ``A -> B`` and ``B -> column_2`` must resolve ``B`` to
        # ``column_2``; an unconditional alias merge would silently replace
        # that valid display reference with the internal ``B`` alias.
        expression_columns = dict(self.columns)
        expression_columns.update(
            {name: name for name in self._internal_names if name not in expression_columns}
        )
        return await self._add_task(
            build_math_params(
                expression,
                expression_columns,
                new_column=new_column,
                column_type=column_type,
                existing_column=existing_column,
                internal_names=self._internal_names,
                condition=condition,
                column_types=self.column_types,
                name_gen=self._next_internal_name,
                parameter_ids=await self._parameter_ids(parameter_names(expression)),
            )
        )

    async def _parameter_ids(self, names: list[str]) -> dict[str, int]:
        """The id of each named parameter: the client's project's first, then the workspace's."""
        if not names:
            return {}
        known = await self._scope_parameter_ids(None)
        if self._client.project_id is not None:
            known.update(await self._scope_parameter_ids(self._client.project_id))
        missing = [name for name in names if name not in known]
        if missing:
            raise MammothValidationError(f"math: no parameter named {missing[0]!r}")
        return {name: known[name] for name in names}

    async def _scope_parameter_ids(self, project_id: int | None) -> dict[str, int]:
        """Every parameter of one scope (a project, or the workspace) as name -> id."""
        ids: dict[str, int] = {}
        offset = 0
        while True:
            page = await self._client.parameters.list(
                limit=_PARAMETER_PAGE, offset=offset, project_id=project_id
            )
            items = page["items"]
            ids.update({item["name"]: item["id"] for item in items})
            offset += len(items)
            if not items or offset >= page["total_count"]:
                return ids

    async def small_large(
        self,
        function: SmallLargeFunction,
        columns: list[str],
        index: int = 1,
        constants: list[float] | None = None,
        new_column: str | None = None,
        existing_column: str | None = None,
    ) -> dict[str, Any]:
        """Return the Nth smallest or largest value across columns/constants (SMALL/LARGE task).

        Scans each row across *columns* and optional numeric *constants*, then
        writes the *index*-th smallest (``SmallLargeFunction.SMALL``) or largest
        (``SmallLargeFunction.LARGE``) value to a new or existing column.
        ``index=1`` means the most extreme value (minimum or maximum).

        Args:
            function: ``SmallLargeFunction.SMALL`` or ``SmallLargeFunction.LARGE``.
            columns: Display names of columns whose values participate in the
                ranking.  At least one column or constant must be supplied.
            index: 1-based rank to pick (``1`` = most extreme).  Must be >= 1.
            constants: Optional list of numeric constants that also participate
                in the ranking (appended after *columns* in the VALUES list).
            new_column: Name for a new result column (mutually exclusive with
                *existing_column*).
            existing_column: Display name of an existing column to overwrite.

        Returns:
            API response dict.

        Raises:
            MammothValidationError: If both or neither of *new_column* /
                *existing_column* are given, *columns* + *constants* are empty,
                or *index* < 1.

        Examples::

            from mammoth import SmallLargeFunction

            # 2nd largest value among three numeric columns
            await view.small_large(
                SmallLargeFunction.LARGE,
                columns=["Q1 Sales", "Q2 Sales", "Q3 Sales"],
                index=2,
                new_column="2nd Best Quarter",
            )

            # Smallest of a column and the constant 0 (floor at zero)
            await view.small_large(
                SmallLargeFunction.SMALL,
                columns=["Profit"],
                constants=[0.0],
                existing_column="Profit",
            )
        """
        values: list[str | int | float] = list(columns) + list(constants or [])
        return await self._add_task(
            build_small_large_params(
                function,
                values,
                index,
                self.columns,
                self._internal_names,
                new_column=new_column,
                existing_column=existing_column,
                name_gen=self._next_internal_name,
            )
        )
