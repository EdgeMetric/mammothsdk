"""Bring data in through a connection the project already has: no link, no leaving the chat.

The user signs in to a source once, in Mammoth, and that makes a connection.
From then on the model can bring more data in through it. Databases first:
their data is chosen with SQL, and the database account of the connection
decides what the query may read.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from mcp.server.mcpserver.exceptions import ToolError

from ..consts import ConnectionFields, ConnectorFields
from ..dataset_app import check_query
from ..jobs import JobStillRunning, wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import DESTRUCTIVE, READS

type Json = dict[str, JsonValue]
type Repeat = Literal["once", "hourly", "daily", "weekly", "monthly"]
type OnRefresh = Literal["replace", "append", "combine"]

NEEDS_A_COLUMN = (
    "`combine` updates the rows it matches, so it needs `unique_column`: a column"
    " whose value tells rows apart, such as an id or an update time."
)
NOT_A_TIME = "`{field}` must be a time such as 2026-10-16T06:00:00+00:00."
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


@mcp_server.tool(title="Add a dataset from a connection", annotations=DESTRUCTIVE)
async def add_dataset_from_connection(
    workspace_id: int,
    project_id: int,
    connector_key: str,
    connection_key: str,
    name: str,
    query: str,
    table: str | None = None,
    repeat: Repeat = "once",
    every: int = 1,
    start_at: str | None = None,
    until: str | None = None,
    on_refresh: OnRefresh = "replace",
    unique_column: str | None = None,
    unique_column_type: Literal["numeric", "date"] = "numeric",
) -> dict[str, JsonValue]:
    """Make a dataset from a query on a database connection the project already has.

    Settle the query, the schedule and the refresh with the user, all in one
    message, or through the form `preview_query` draws.
    Ask the user first: the query runs on their own database.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project the dataset goes into.
        connector_key: The database's `name_key`, such as "postgres".
        connection_key: What `list_connections` returned.
        name: The dataset's name.
        query: One SQL query that reads. Check it first with `preview_query`.
        table: The main table the query reads. Defaults to `name`.
        repeat: `once` (the default: one pull, now), or how often to pull again.
        every: Pull every this many hours, days, weeks or months.
        start_at: When the first pull runs, for a repeat. Defaults to now.
        until: When the repeats stop. Defaults to never.
        on_refresh: What a pull does with the rows there: `replace` them (the
            default), `append` the new ones, or `combine`: update the rows it
            matches on `unique_column` and add the rest.
        unique_column: For `combine`: the column that tells rows apart.
        unique_column_type: For `combine`: `numeric` (an id) or `date`.

    Returns:
        `since`: the time to pass to `find_new_datasets`. `schedule`: the
        schedule in words, to tell the user. `next_step`.
    """
    check_query(connector_key, query)
    since = datetime.now(UTC).isoformat()
    choice = Schedule(
        repeat,
        every,
        read_time(start_at, ConnectionFields.START_AT),
        read_time(until, ConnectionFields.UNTIL),
        on_refresh,
        unique_column,
        unique_column_type,
    )
    spec: Json = {
        ConnectionFields.CONNECTOR_KEY: connector_key,
        ConnectionFields.CONNECTION_KEY: connection_key,
        ConnectionFields.QUERY_PROPERTIES: {
            ConnectionFields.DS_NAME: name,
            ConnectionFields.TABLE_NAME: table or name,
            ConnectionFields.QUERY: query,
        },
        **choice.spec(),
    }
    async with build_client(workspace_id, project_id) as client:
        started = await read_sdk_errors(
            client.datasets.create(spec, ConnectionFields.CREATION_TYPE, project_id=project_id)
        )
    await check_it_started(workspace_id, started)
    return {
        ConnectorFields.SINCE: since,
        ConnectionFields.SCHEDULE: choice.in_words(),
        ConnectorFields.NEXT_STEP: ADDED,
    }


def read_time(stamp: str | None, field: str) -> str | None:
    """The time as given, once it reads as one; None when there is none."""
    if stamp is None:
        return None
    try:
        datetime.fromisoformat(stamp)
    except ValueError as unread:
        raise ToolError(NOT_A_TIME.format(field=field)) from unread
    return stamp


@dataclass(frozen=True)
class Schedule:
    """How often a dataset pulls, and what a pull does, as Mammoth takes it."""

    repeat: Repeat
    every: int
    start_at: str | None
    until: str | None
    on_refresh: OnRefresh
    unique_column: str | None
    unique_column_type: str

    def __post_init__(self) -> None:
        if self.on_refresh == ConnectionFields.COMBINE and not self.unique_column:
            raise ToolError(NEEDS_A_COLUMN)
        if self.every < 1:
            raise ToolError("`every` must be 1 or more.")

    def spec(self) -> Json:
        """`schedule_properties`, and `recurrence_info` for a repeat."""
        once = self.repeat == ConnectionFields.ONCE
        pull: Json = {
            ConnectionFields.SCHEDULE_TYPE: (
                ConnectionFields.MOMENT if once else ConnectionFields.PERIOD
            ),
            ConnectionFields.FIRST_PULL_AT: (
                ConnectionFields.LATER if self.start_at and not once else ConnectionFields.NOW
            ),
            ConnectionFields.ON_REFRESH_ACTION: self.on_refresh,
        }
        if self.on_refresh == ConnectionFields.COMBINE:
            pull[ConnectionFields.UNIQUE_SEQUENCE_COLUMN] = {
                ConnectionFields.C_NAME: self.unique_column,
                ConnectionFields.C_TYPE: self.unique_column_type,
            }
        if once:
            return {ConnectionFields.SCHEDULE_PROPERTIES: pull}
        return {
            ConnectionFields.SCHEDULE_PROPERTIES: pull,
            ConnectionFields.RECURRENCE_INFO: self.recurrence(),
        }

    def recurrence(self) -> Json:
        recurrence: Json = {
            ConnectionFields.INTERVAL: self.every,
            ConnectionFields.FREQUENCY: self.repeat,
            ConnectionFields.START_AT: self.start_at or datetime.now(UTC).isoformat(),
        }
        if self.until:
            recurrence[ConnectionFields.UNTIL] = self.until
        return recurrence

    def in_words(self) -> str:
        """The schedule as the user would say it, such as "Every 2 days from now"."""
        if self.repeat == ConnectionFields.ONCE:
            return "Once, now."
        unit = ConnectionFields.UNITS[self.repeat]
        words = f"Every {unit}" if self.every == 1 else f"Every {self.every} {unit}s"
        words += f" from {self.start_at or 'now'}"
        if self.until:
            words += f" until {self.until}"
        refresh = ConnectionFields.REFRESH_WORDS.get(
            self.on_refresh, f"updating the rows matched on {self.unique_column}"
        )
        return f"{words}, {refresh}."


async def check_it_started(workspace_id: int, started: dict[str, JsonValue]) -> None:
    """Wait briefly on the job, so a dataset Mammoth refuses is reported now.

    Left to `find_new_datasets`, a failed job would read as "nothing yet" until
    its watch ran out. A pull still running when the check ends is fine.
    """
    try:
        await wait_for_job(workspace_id, started, ConnectionFields.CHECK_SECONDS)
    except JobStillRunning:
        return
