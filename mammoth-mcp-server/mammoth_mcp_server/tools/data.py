"""Read the rows a view holds, and the totals Mammoth works out from them.

The API answers both asynchronously: the request starts a job and the answer
arrives when the job finishes. The SDK waits, so the model gets its answer
from one call and never has to poll for itself.
"""

import asyncio

from mcp.server.mcpserver.exceptions import ToolError

from ..aggregate import Aggregation, DateGroup, build_query
from ..consts import (
    DATA_LIMIT_DEFAULT,
    DATA_LIMIT_MAX,
    GROUPS_LIMIT_DEFAULT,
    GROUPS_LIMIT_MAX,
    ApiFields,
)
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..shape import not_found_message, read_rows
from ..tool_kinds import READS

LIMIT_TOO_LOW = "`limit` must be at least 1."


@mcp_server.tool(title="Read rows", annotations=READS)
async def get_data(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    view_id: int,
    limit: int = DATA_LIMIT_DEFAULT,
    offset: int = 1,
    columns: list[str] | None = None,
    condition: dict[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    """Read rows from a view.

    Rows come back under the column names the user sees, with numeric columns
    as numbers. A numeric column the user has given a display format (currency,
    percentage, thousands separators) stays text. Call `get_view` first for
    the columns and their types. Ask for the columns you need rather than all
    of them.

    Read rows to see what the data looks like. For a total, a count, an
    average or a ranking, call `aggregate_data`: never add up these rows
    yourself. One page holds at most 400 rows, and rows come in no set order.

    Returns:
        `data`: the rows. `paging`: `total` rows in the view when it is known,
        and `next_offset` only when more rows follow — pass it as `offset` for
        the next page.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view to read.
        limit: How many rows to return. At most 400.
        offset: The first row to return, counting from 1.
        columns: Internal column names to return, as `get_view` reports them.
            Omit for every column.
        condition: Filter the rows. One test reads
            `{"column_1": {"EQ": "paid"}}` — the operator is the only key
            inside, and it is upper case. Join tests with `{"AND": [...]}`,
            `{"OR": [...]}` or `{"NOT": ...}`. Operators: EQ, NE, GT, LT, GTE,
            LTE, CONTAINS, NOT_CONTAINS, ICONTAINS, STARTS_WITH, ENDS_WITH,
            NOT_STARTS_WITH, NOT_ENDS_WITH; IN_LIST and NOT_IN_LIST take a
            list; IS_EMPTY, IS_NOT_EMPTY, IS_MAXVAL, IS_MINVAL, IS_NOT_MAXVAL
            and IS_NOT_MINVAL take true.
    """
    page_size = min(limit, DATA_LIMIT_MAX)
    missing = not_found_message(workspace_id, project_id, dataset_id, view_id)
    async with build_client(workspace_id) as client:
        answer, view = await asyncio.gather(
            read_sdk_errors(
                client.dataviews.query_data(
                    dataset_id,
                    view_id,
                    offset=offset,
                    limit=page_size,
                    columns=columns,
                    condition=condition,
                    project_id=project_id,
                ),
                missing,
            ),
            read_sdk_errors(
                client.dataviews.get(
                    dataset_id, view_id, project_id=project_id, fields=ApiFields.STANDARD
                ),
                missing,
            ),
        )
    return read_rows(answer, view, offset, page_size, condition is not None)


@mcp_server.tool(title="Total and group rows", annotations=READS)
async def aggregate_data(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    view_id: int,
    aggregations: list[Aggregation],
    group_by: list[str | DateGroup] | None = None,
    condition: dict[str, JsonValue] | None = None,
    order_by: str | None = None,
    ascending: bool = False,
    limit: int = GROUPS_LIMIT_DEFAULT,
) -> dict[str, JsonValue]:
    """Have Mammoth work out totals, counts, averages, lows and highs over a view.

    Use this for every number you give the user. Mammoth reads every row of
    the view, so the answer is exact; rows read with `get_data` are a page, not
    the whole view. Nothing is added to the view's pipeline.

    Returns:
        `data`: one row per group, under the group columns' names and the
        results' names. With no `group_by`, one row for the whole view. `note`
        when there may be more groups than came back.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view to read.
        aggregations: The numbers to work out, such as
            `[{"function": "SUM", "column": "Revenue"}]`.
        group_by: Columns to group by, by the names the user sees. Group a date
            by a period with `{"column": "Order Date", "truncate": "MONTH"}`.
            Omit for one total over the whole view.
        condition: Count only the rows that pass, written as `get_data` takes
            it, with internal column names.
        order_by: Rank the groups by this result's name, before `limit` cuts
            them. Without it, which groups come back is not defined.
        ascending: Rank from lowest to highest. Default: highest first.
        limit: How many groups to return. At least 1, at most 1000.
    """
    if limit < 1:
        raise ToolError(LIMIT_TOO_LOW)
    missing = not_found_message(workspace_id, project_id, dataset_id, view_id)
    page_size = min(limit, GROUPS_LIMIT_MAX)
    async with build_client(workspace_id) as client:
        view = await read_sdk_errors(
            client.dataviews.get(
                dataset_id, view_id, project_id=project_id, fields=ApiFields.STANDARD
            ),
            missing,
        )
        query = build_query(view, aggregations, group_by or [])
        answer = await read_sdk_errors(
            client.dataviews.aggregate(
                dataset_id,
                view_id,
                aggregations=list(query.aggregations),
                group_by=list(query.group_by) or None,
                condition=condition,
                limit=page_size,
                sort=query.sort(order_by, ascending),
                project_id=project_id,
            ),
            missing,
        )
    return query.read(answer, page_size)
