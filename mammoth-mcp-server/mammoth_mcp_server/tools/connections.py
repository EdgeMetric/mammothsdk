"""Bring data in through a connection the project already has: no link, no leaving the chat.

The user signs in to a source once, in Mammoth, and that makes a connection.
From then on the model can bring more data in through it. Databases first:
their data is chosen with SQL, and the database account of the connection
decides what the query may read.
"""

from datetime import UTC, datetime

from mcp.server.mcpserver.exceptions import ToolError

from ..consts import ConnectionFields, ConnectorFields
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import DESTRUCTIVE, READS

NOT_A_DATABASE = (
    "Only a database connection can be read from here. For this source, use"
    " `connect_source`: the user picks the data in Mammoth."
)
NOT_A_READ = "Send one query that reads: it must start with SELECT or WITH."
ADDED = (
    "Mammoth is bringing the data in. Call `find_new_datasets` with `since`"
    " now: it waits until the dataset is ready."
)


@mcp_server.tool(title="List connections", annotations=READS)
async def list_connections(
    workspace_id: int, project_id: int, connector_key: str
) -> dict[str, JsonValue]:
    """List the connections a project has to one source, to bring more data in through.

    Find which sources have one with `list_connectors` and `connected_only`.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project.
        connector_key: The connector's `name_key`, such as "postgres".

    Returns:
        `connections`: each one's `connection_key` and `connection_config`,
        which says what it connects to, such as the host and the database.
        Mammoth leaves the passwords out.
    """
    async with build_client(workspace_id, project_id) as client:
        listed = await read_sdk_errors(
            client.connectors.list_connections(connector_key, project_id=project_id)
        )
    return {ConnectionFields.CONNECTIONS: list[JsonValue](listed)}


@mcp_server.tool(title="Preview a query", annotations=DESTRUCTIVE)
async def preview_query(
    workspace_id: int,
    project_id: int,
    connector_key: str,
    connection_key: str,
    query: str,
    profile: str | None = None,
) -> dict[str, JsonValue]:
    """Run a query on a database connection and show its first rows. Nothing is saved.

    Use it to check a query before `add_dataset_from_connection`.
    Ask the user first: the query runs on their own database. Show it to them.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project.
        connector_key: The database's `name_key`, such as "postgres".
        connection_key: What `list_connections` returned.
        query: One SQL query that reads.
        profile: The schema, where the database has them, such as "dbo".

    Returns:
        `columns` and the first `rows`.
    """
    check_query(connector_key, query)
    async with build_client(workspace_id, project_id) as client:
        answer = await read_sdk_errors(
            client.connectors.query_connection(
                connector_key,
                connection_key,
                query,
                profile=profile,
                project_id=project_id,
                timeout=ConnectionFields.PREVIEW_SECONDS,
            )
        )
    return shape_sample(answer.get(ConnectionFields.SAMPLE))


@mcp_server.tool(title="Add a dataset from a connection", annotations=DESTRUCTIVE)
async def add_dataset_from_connection(
    workspace_id: int,
    project_id: int,
    connector_key: str,
    connection_key: str,
    name: str,
    table: str,
    query: str,
) -> dict[str, JsonValue]:
    """Make a dataset from a query on a database connection the project already has.

    Mammoth brings the rows in once. The user sets a refresh schedule in
    Mammoth. Ask the user first: the query runs on their own database.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project the dataset goes into.
        connector_key: The database's `name_key`, such as "postgres".
        connection_key: What `list_connections` returned.
        name: The dataset's name.
        table: The main table the query reads.
        query: One SQL query that reads. Check it first with `preview_query`.

    Returns:
        `since`: the time to pass to `find_new_datasets`. `next_step`.
    """
    check_query(connector_key, query)
    since = datetime.now(UTC).isoformat()
    spec: dict[str, JsonValue] = {
        ConnectionFields.CONNECTOR_KEY: connector_key,
        ConnectionFields.CONNECTION_KEY: connection_key,
        ConnectionFields.QUERY_PROPERTIES: {
            ConnectionFields.DS_NAME: name,
            ConnectionFields.TABLE_NAME: table,
            ConnectionFields.QUERY: query,
        },
    }
    async with build_client(workspace_id, project_id) as client:
        await read_sdk_errors(
            client.datasets.create(spec, ConnectionFields.CREATION_TYPE, project_id=project_id)
        )
    return {ConnectorFields.SINCE: since, ConnectorFields.NEXT_STEP: ADDED}


def check_query(connector_key: str, query: str) -> None:
    """Refuse a source that is not a database, and a query that does not start as a read."""
    if connector_key not in ConnectionFields.DATABASES:
        raise ToolError(NOT_A_DATABASE)
    words = query.strip().split(maxsplit=1)
    if not words or words[0].lower() not in ConnectionFields.READING:
        raise ToolError(NOT_A_READ)


def shape_sample(sample: JsonValue) -> dict[str, JsonValue]:
    """The sample's column names and its first rows."""
    sample = sample if isinstance(sample, dict) else {}
    schema = sample.get(ConnectionFields.SCHEMA)
    rows = sample.get(ConnectionFields.ROWS)
    columns: list[JsonValue] = [
        one.get(ConnectionFields.NAME)
        for one in (schema if isinstance(schema, list) else [])
        if isinstance(one, dict)
    ]
    shown = rows[: ConnectionFields.ROWS_SHOWN] if isinstance(rows, list) else []
    return {ConnectionFields.COLUMNS: columns, ConnectionFields.ROWS: shown}
