"""Read the rows a view holds.

The API answers this one asynchronously: the request starts a job and the rows
arrive when the job finishes. The SDK waits, so the model gets rows from one
call and never has to poll for itself.
"""

from ..consts import DATA_LIMIT_DEFAULT, DATA_LIMIT_MAX
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
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

    Returns the values, not the column definitions — call `get_view` first for
    column names and types. Ask for the columns you need rather than all of them.

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
    async with build_client(workspace_id) as client:
        return await read_sdk_errors(
            client.dataviews.query_data(
                dataset_id,
                view_id,
                offset=offset,
                limit=min(limit, DATA_LIMIT_MAX),
                columns=columns,
                condition=condition,
                project_id=project_id,
            )
        )
