"""Turn an `aggregate_data` request into the SDK's query, and its answer back into names.

The model names columns as the user sees them and calls each result what it
likes. The query route takes internal column names and answers under `agg_<n>`
and `group_<n>`, so both directions are translated here.
"""

from dataclasses import dataclass

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from .consts import AggregateFields, ColumnFields, ViewShape
from .sdk import JsonValue
from .shape import typed

# MIN and MAX keep the column's own type; every other function counts or adds.
KEEPS_THE_COLUMN_TYPE = frozenset({"MIN", "MAX"})


class Aggregation(BaseModel):
    """One number to work out, for each group or for the whole view."""

    function: str = Field(
        description="SUM, COUNT, AVG, MIN, MAX, STDDEV or DISTINCT_COUNT.",
    )
    column: str | None = Field(
        default=None,
        description="The column, by the name the user sees. COUNT needs none: it counts rows.",
    )
    as_name: str | None = Field(
        default=None,
        description='What to call the result, such as "Total Revenue". Default: "Sum of Revenue".',
    )


class DateGroup(BaseModel):
    """Group a date column by a period rather than by each date."""

    column: str = Field(description="The date column, by the name the user sees.")
    truncate: str = Field(description="DAY, WEEK, MONTH, QUARTER or YEAR.")


@dataclass(frozen=True)
class Query:
    """What to send the query route, and how to read its answer."""

    aggregations: list[dict[str, JsonValue]]
    group_by: list[str | dict[str, JsonValue]]
    # `agg_<n>` and `group_<n>` -> the name the model asked for, and the type
    # the value is read as.
    names: dict[str, tuple[str, str | None]]

    def sort(self, order_by: str | None, ascending: bool) -> list[list[str]] | None:
        """The route's sort for a result named `order_by`, or none."""
        if order_by is None:
            return None
        for key, (name, _) in self.names.items():
            if name == order_by:
                direction = AggregateFields.ASCENDING if ascending else AggregateFields.DESCENDING
                return [[key, direction]]
        known = ", ".join(name for name, _ in self.names.values())
        raise ToolError(f"There is no result called {order_by!r} to rank by. Results: {known}.")

    def read(self, answer: dict[str, JsonValue], limit: int) -> dict[str, JsonValue]:
        """The answer's rows under the names asked for, and a note when more groups may follow."""
        rows = answer.get(AggregateFields.DATA)
        named: list[JsonValue] = [
            {
                self.names.get(key, (key, None))[0]: typed(
                    value, self.names.get(key, (key, None))[1]
                )
                for key, value in row.items()
            }
            for row in (rows if isinstance(rows, list) else [])
            if isinstance(row, dict)
        ]
        read: dict[str, JsonValue] = {AggregateFields.DATA: named}
        if self.group_by and len(named) >= limit:
            read[AggregateFields.NOTE] = (
                f"Only the first {limit} groups came back, and there may be more groups."
                " Rank them with order_by, or narrow them with a condition."
            )
        return read


def build_query(
    view: dict[str, JsonValue], aggregations: list[Aggregation], group_by: list[str | DateGroup]
) -> Query:
    """Resolve every column the request names against the view's columns."""
    columns = _columns(view)
    names: dict[str, tuple[str, str | None]] = {}
    sent_aggregations: list[dict[str, JsonValue]] = []
    for index, wanted in enumerate(aggregations):
        sent, label, value_type = _aggregation(wanted, columns)
        sent_aggregations.append(sent)
        names[f"{AggregateFields.AGG}{index}"] = (label, value_type)
    sent_groups: list[str | dict[str, JsonValue]] = []
    for index, group in enumerate(group_by):
        sent_group, label, value_type = _group(group, columns)
        sent_groups.append(sent_group)
        names[f"{AggregateFields.GROUP}{index}"] = (label, value_type)
    return Query(sent_aggregations, sent_groups, names)


def _aggregation(
    wanted: Aggregation, columns: dict[str, tuple[str, str | None]]
) -> tuple[dict[str, JsonValue], str, str | None]:
    """The SDK's aggregation, the result's name, and the type its value is read as."""
    function = wanted.function.upper()
    sent: dict[str, JsonValue] = {AggregateFields.FUNCTION: function}
    value_type: str | None = ViewShape.NUMERIC
    label = AggregateFields.NAMES.get(function, function)
    if wanted.column is not None:
        internal, column_type = _column(wanted.column, columns)
        sent[AggregateFields.COLUMN] = internal
        label = f"{label} of {wanted.column}"
        if function in KEEPS_THE_COLUMN_TYPE:
            value_type = column_type
    label = wanted.as_name or label
    sent[AggregateFields.AS_NAME] = label
    return sent, label, value_type


def _group(
    group: str | DateGroup, columns: dict[str, tuple[str, str | None]]
) -> tuple[str | dict[str, JsonValue], str, str | None]:
    """The SDK's group, its name in the rows, and the type its value is read as."""
    if isinstance(group, str):
        internal, column_type = _column(group, columns)
        return internal, group, column_type
    internal, _ = _column(group.column, columns)
    sent: dict[str, JsonValue] = {
        AggregateFields.COLUMN: internal,
        AggregateFields.TRUNCATE: group.truncate.upper(),
    }
    return sent, group.column, None


def _columns(view: dict[str, JsonValue]) -> dict[str, tuple[str, str | None]]:
    """Each column by the name the user sees, and by its internal name: its internal name and type."""
    metadata = view.get(ViewShape.METADATA)
    columns: dict[str, tuple[str, str | None]] = {}
    for column in metadata if isinstance(metadata, list) else []:
        if not isinstance(column, dict) or ColumnFields.INTERNAL_NAME not in column:
            continue
        internal = str(column[ColumnFields.INTERNAL_NAME])
        found = (internal, str(column.get(ColumnFields.TYPE)))
        columns[internal] = found
        columns.setdefault(str(column.get(ColumnFields.DISPLAY_NAME)), found)
    return columns


def _column(name: str, columns: dict[str, tuple[str, str | None]]) -> tuple[str, str | None]:
    if name in columns:
        return columns[name]
    shown = ", ".join(n for n, (internal, _) in columns.items() if n != internal)
    raise ToolError(f"The view has no column called {name!r}. Its columns: {shown}.")
