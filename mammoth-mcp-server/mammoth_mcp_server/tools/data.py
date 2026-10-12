"""Read the rows a view holds.

The API answers this one asynchronously: the request starts a job and the rows
arrive when the job finishes. The SDK waits, so the model gets rows from one
call and never has to poll for itself.
"""

import asyncio

from ..consts import DATA_LIMIT_DEFAULT, DATA_LIMIT_MAX, ApiFields
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..shape import not_found_message, read_rows
from ..tool_kinds import READS


@mcp_server.tool(annotations=READS)
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
    percentage, thousands separators) stays text, so do not assume arithmetic
    is safe. Call `get_view` first for the columns and their types. Ask for
    the columns you need rather than all of them.

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
