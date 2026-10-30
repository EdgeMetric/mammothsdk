"""How well a join or a lookup matched, read from the view before and after it ran.

A join that matches few rows still "works": the pipeline reports the step as
done. The model is told how many rows matched, so it can tell the user, or
compare the key columns, before it builds on the result.
"""

from mammoth.client import MammothClient
from mcp.server.mcpserver.exceptions import ToolError

from .consts import ApiFields, ColumnFields, JoinCheckFields, ViewShape
from .sdk import JsonValue, build_client, read_sdk_errors

# The operations that bring in columns from another view by key.
MATCHING_OPERATIONS = frozenset({"join", "lookup"})


def columns_of(view: dict[str, JsonValue]) -> dict[str, str]:
    """Each column's internal name and the name the user sees."""
    columns = view.get(ViewShape.METADATA)
    return {
        str(column[ColumnFields.INTERNAL_NAME]): str(column.get(ColumnFields.DISPLAY_NAME))
        for column in (columns if isinstance(columns, list) else [])
        if isinstance(column, dict) and ColumnFields.INTERNAL_NAME in column
    }


def added_columns(before: dict[str, JsonValue], after: dict[str, JsonValue]) -> dict[str, str]:
    """The columns the step added: internal name -> the name the user sees."""
    old = columns_of(before)
    return {name: shown for name, shown in columns_of(after).items() if name not in old}


def join_check(
    before: dict[str, JsonValue],
    after: dict[str, JsonValue],
    unmatched: int | None,
    not_counted: str | None = None,
) -> dict[str, JsonValue]:
    """The match check of one join or lookup.

    Args:
        before: The view as `get_view` reads it, before the step.
        after: The view after the step ran.
        unmatched: Rows in which every added column is empty, counted over
            the whole view; None when the step added no column, or when
            they could not be counted.
        not_counted: Why the rows could not be counted, when they could not.
    """
    rows_before, rows_after = before.get(ViewShape.ROW_COUNT), after.get(ViewShape.ROW_COUNT)
    check: dict[str, JsonValue] = {
        JoinCheckFields.ROWS_BEFORE: rows_before,
        JoinCheckFields.ROWS_AFTER: rows_after,
        JoinCheckFields.COLUMNS_ADDED: list(added_columns(before, after).values()),
    }
    notes: list[JsonValue] = []
    if unmatched is not None and isinstance(rows_after, int) and rows_after > 0:
        check[JoinCheckFields.UNMATCHED_ROWS] = unmatched
        check[JoinCheckFields.MATCH_RATE] = round((rows_after - unmatched) / rows_after, 3)
        if unmatched:
            notes.append(JoinCheckFields.UNMATCHED_NOTE.format(unmatched, rows_after))
    if not_counted is not None:
        notes.append(JoinCheckFields.NOT_COUNTED_NOTE.format(not_counted))
    elif unmatched is None:
        notes.append(JoinCheckFields.NO_NEW_COLUMN_NOTE)
    if isinstance(rows_before, int) and isinstance(rows_after, int):
        if rows_after > rows_before:
            notes.append(JoinCheckFields.ROWS_REPEAT_NOTE.format(rows_after - rows_before))
        elif rows_after < rows_before:
            notes.append(JoinCheckFields.ROWS_DROPPED_NOTE.format(rows_before - rows_after))
    if notes:
        check[JoinCheckFields.NOTES] = notes
    return check


async def read_view(client: MammothClient, ids: dict[str, int]) -> dict[str, JsonValue]:
    """The view's row count and columns, as the pipeline left them."""
    return await read_sdk_errors(
        client.dataviews.get(
            ids["dataset_id"],
            ids["dataview_id"],
            project_id=ids["project_id"],
            fields=ApiFields.STANDARD,
        )
    )


async def count_unmatched(client: MammothClient, ids: dict[str, int], added: list[str]) -> int:
    """Rows of the whole view in which every one of `added` is empty.

    Raises:
        ToolError: If Mammoth's answer holds no count. Zero would read as a full match.
    """
    condition: dict[str, JsonValue] = {"AND": [{name: {"IS_EMPTY": True}} for name in added]}
    answer = await read_sdk_errors(
        client.dataviews.aggregate(
            ids["dataset_id"],
            ids["dataview_id"],
            aggregations=[{"function": "COUNT"}],
            condition=condition,
            project_id=ids["project_id"],
        )
    )
    rows = answer.get("data")
    first = rows[0] if isinstance(rows, list) and rows and isinstance(rows[0], dict) else {}
    count = first.get(JoinCheckFields.COUNT)
    if isinstance(count, int | float | str):
        try:
            return int(float(count))
        except ValueError:
            pass
    raise ToolError(f"Mammoth's answer held no count of the unmatched rows: {answer}")


async def read_before(ids: dict[str, int]) -> dict[str, JsonValue]:
    """The view before a join or a lookup runs on it."""
    async with build_client(ids["workspace_id"], ids["project_id"]) as client:
        return await read_view(client, ids)


async def measure(ids: dict[str, int], before: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """The join check of the step that ran since `before` was read.

    A read that fails here is reported in the check, never raised: the step has run.
    """
    async with build_client(ids["workspace_id"], ids["project_id"]) as client:
        try:
            after = await read_view(client, ids)
        except ToolError as why:
            return not_measured(before, str(why))
        added = list(added_columns(before, after))
        try:
            unmatched = await count_unmatched(client, ids, added) if added else None
        except ToolError as why:
            return join_check(before, after, None, not_counted=str(why))
    return join_check(before, after, unmatched)


def not_measured(before: dict[str, JsonValue], why: str) -> dict[str, JsonValue]:
    """The check of a step that ran on a view that could not be read after it.

    Not an error: the step is in, and an error would read as a failed add.
    """
    return {
        JoinCheckFields.ROWS_BEFORE: before.get(ViewShape.ROW_COUNT),
        JoinCheckFields.NOTES: [JoinCheckFields.NOT_COUNTED_NOTE.format(why)],
    }
