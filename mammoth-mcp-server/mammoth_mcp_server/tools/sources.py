"""Bring data in from a connected source: a database, a CRM, a spreadsheet service.

Connecting a source means signing in to it, and that stays with the user, in
Mammoth: no password or token passes through a model. So `connect_source`
(in `connect_app`) hands the user the page that opens the connector in their
project, and `find_new_datasets` finds what the project gained once they are done. From
there a dataset is read, transformed and built on like an uploaded one, and
Mammoth refreshes it on the schedule the user set when they brought it in.
"""

import asyncio
import time

from mcp.server.mcpserver.exceptions import ToolError

from ..connection_watch import list_connections_to, read_watch
from ..consts import (
    CONNECT_POLL_SECONDS,
    CONNECT_WAIT_SECONDS,
    CONNECT_WATCH_SECONDS,
    LIST_LIMIT_DEFAULT,
    ApiPaths,
    ConnectionFields,
    ConnectorFields,
    PageFields,
    UploadFields,
)
from ..sdk import JsonValue, build_client, request_api
from ..server import mcp_server
from ..shape import tidy_page
from ..store import Record
from ..telemetry import Events, TelemetryFields, record
from ..tool_kinds import READS
from ..upload_report import read_time, report_upload

NO_WATCH = (
    "That watch is over or was never started. Call `connect_source` with the"
    " connector again for a new one."
)
STILL_WAITING = (
    "No new connection yet. Call `find_new_connection` again: the watch runs"
    " five minutes from `connect_source`."
)
GAVE_UP = (
    "No new connection in five minutes. Ask the user whether they connected the"
    " source; when they say yes, call `connect_source` again to watch anew."
)
CONNECTED = (
    "The user connected the source. They may still be picking its data in"
    " Mammoth: call `find_new_datasets` with `since` for what they bring in. For"
    " a database, you can bring the data in yourself with `list_tables`,"
    " `preview_query` and `add_dataset_from_connection`."
)
NOT_A_TIME = (
    "`since` must be the time `connect_source` returned, such as 2026-10-14T09:00:00+00:00."
)


@mcp_server.tool(title="List connectors", annotations=READS)
async def list_connectors(
    workspace_id: int,
    project_id: int,
    connected_only: bool = False,
    limit: int = LIST_LIMIT_DEFAULT,
    offset: int = 0,
) -> dict[str, JsonValue]:
    """List the sources Mammoth can bring data in from: databases, CRMs, ads, files.

    Args:
        workspace_id: Which workspace to look in.
        project_id: Which project the data would go into.
        connected_only: Only the connectors the project already has a
            connection to.
        limit: How many connectors to return.
        offset: How many connectors to skip, for paging.

    Returns:
        `connectors`: each one's `name_key` (what `connect_source` takes),
        `disp_name`, and `is_available`: false when the workspace's plan does
        not include it. With `connected_only`, also `connection_count`, and
        `total`: how many are connected; `next_offset` is the offset of the
        next page, when there is one.
    """
    if connected_only:
        return await list_connected(workspace_id, project_id, limit, offset)
    query: dict[str, str | int] = {
        ConnectorFields.FIELDS: ConnectorFields.LISTED,
        ConnectorFields.LIMIT: limit,
        ConnectorFields.OFFSET: offset,
        ConnectorFields.PROJECT_ID: project_id,
    }
    async with build_client(workspace_id) as client:
        page = await request_api(
            client, "GET", ApiPaths.CONNECTORS.format(workspace_id=workspace_id), query=query
        )
    return tidy_page(page, ConnectorFields.CONNECTORS, limit)


async def list_connected(
    workspace_id: int, project_id: int, limit: int, offset: int
) -> dict[str, JsonValue]:
    """The connectors the project has a connection to, paged here.

    The route filters by connections only within the page it read, so a
    filtered page cannot say whether more come after it. Every page of the
    catalogue is read instead, and the connected ones are kept.
    """
    connected: list[JsonValue] = [
        connector
        for connector in await read_every_connector(workspace_id, project_id)
        if isinstance(connector, dict)
        and isinstance(count := connector.get(ConnectorFields.CONNECTION_COUNT), int)
        and count > 0
    ]
    listed: dict[str, JsonValue] = {
        ConnectorFields.CONNECTORS: connected[offset : offset + limit],
        PageFields.TOTAL: len(connected),
    }
    if offset + limit < len(connected):
        listed[PageFields.NEXT_OFFSET] = offset + limit
    return listed


async def read_every_connector(workspace_id: int, project_id: int) -> list[JsonValue]:
    """Every connector, with its connection count in the project, page by page."""
    connectors: list[JsonValue] = []
    async with build_client(workspace_id) as client:
        for start in range(0, ConnectorFields.MOST_CONNECTORS, ConnectorFields.EVERY_CONNECTOR):
            query: dict[str, str | int] = {
                ConnectorFields.FIELDS: ConnectorFields.LISTED_CONNECTED,
                ConnectorFields.LIMIT: ConnectorFields.EVERY_CONNECTOR,
                ConnectorFields.OFFSET: start,
                ConnectorFields.PROJECT_ID: project_id,
            }
            page = await request_api(
                client, "GET", ApiPaths.CONNECTORS.format(workspace_id=workspace_id), query=query
            )
            items = page.get(ConnectorFields.CONNECTORS)
            items = items if isinstance(items, list) else []
            connectors.extend(items)
            if len(items) < ConnectorFields.EVERY_CONNECTOR:
                break
    return connectors


@mcp_server.tool(title="Find new datasets", annotations=READS)
async def find_new_datasets(workspace_id: int, project_id: int, since: str) -> dict[str, JsonValue]:
    """Find the datasets a project gained since a time: what the user brought in from a source.

    Call this straight after giving the user the link. It waits while they
    connect the source, so do not end your turn asking them to say when they
    are done. `waiting` means nothing came in before the wait ran out: call
    again if they are still at it; after a couple of rounds say you are waiting.

    Only the datasets the user made are listed, not a teammate's. Mammoth
    records who made a dataset by name, so a teammate with the same name
    cannot be told apart: when one is not what the user expected, ask them.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project.
        since: The time `connect_source` returned.

    Returns:
        `status`: `waiting` (nothing new yet), `processing` (Mammoth is still
        bringing the data in) or `done`. `files`: each new dataset. A dataset
        that is ready carries `view_id`, to read, transform and build
        dashboards on, and `mammoth_url`. One that waits on the user carries
        `needs`, as `check_upload` reports it.
    """
    try:
        read_time(since)
    except ValueError as unread:
        raise ToolError(NOT_A_TIME) from unread
    report = await wait_for_new_datasets(
        {
            UploadFields.UPLOADED_AT: since,
            UploadFields.WORKSPACE_ID: workspace_id,
            UploadFields.PROJECT_ID: project_id,
        }
    )
    found = report[UploadFields.FILES]
    record(
        Events.NEW_DATASETS,
        **{
            TelemetryFields.STATUS: report[UploadFields.STATUS],
            TelemetryFields.DATASETS: len(found) if isinstance(found, list) else 0,
        },
    )
    return report


async def wait_for_new_datasets(ticket: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """What the project gained, once it is all in or the wait runs out.

    Answering at once ends the model's turn, and the user would then have to
    start another one just to say they are done.
    """
    give_up_at = time.monotonic() + CONNECT_WAIT_SECONDS
    while True:
        report = await report_upload(ticket, only_mine=True)
        if not report[UploadFields.FILES]:
            report[UploadFields.STATUS] = UploadFields.WAITING
        if report[UploadFields.STATUS] == UploadFields.DONE or time.monotonic() >= give_up_at:
            return report
        await asyncio.sleep(CONNECT_POLL_SECONDS)


@mcp_server.tool(title="Find new connection", annotations=READS)
async def find_new_connection(watch_id: str) -> dict[str, JsonValue]:
    """Wait for the connection the user makes in Mammoth after `connect_source`.

    Call it straight after giving the user the link. Each call waits up to 20
    seconds; `waiting` means call again. The watch ends five minutes after
    `connect_source`, with `gave_up`.

    Args:
        watch_id: What `connect_source` returned.

    Returns:
        `status`: `connected`, `waiting` or `gave_up`. `connector`: its key.
        `connections`: the new connections, each with its `connection_key`.
        `next_step`: what to do now.
    """
    watch = await read_watch(watch_id)
    if watch is None:
        raise ToolError(NO_WATCH)
    new = await wait_for_new_connections(watch)
    status = watch_status(watch, new)
    connector = str(watch[ConnectorFields.CONNECTOR])
    record(
        Events.SOURCE_CONNECTED,
        **{TelemetryFields.CONNECTOR: connector, TelemetryFields.STATUS: status},
    )
    return {
        ConnectorFields.STATUS: status,
        ConnectorFields.CONNECTOR: connector,
        ConnectionFields.CONNECTIONS: list[JsonValue](new),
        ConnectorFields.NEXT_STEP: NEXT_STEPS[status],
    }


async def wait_for_new_connections(watch: Record) -> list[dict[str, JsonValue]]:
    """The connections not there when the watch started, once one appears or the call must end."""
    ends_at = float(watch[ConnectorFields.STARTED]) + CONNECT_WATCH_SECONDS
    give_up_at = time.monotonic() + CONNECT_WAIT_SECONDS
    known = set(watch[ConnectorFields.KNOWN])
    while True:
        listed = await list_connections_to(
            int(watch[ConnectorFields.WORKSPACE_ID]),
            int(watch[ConnectorFields.PROJECT_ID_KEY]),
            str(watch[ConnectorFields.CONNECTOR]),
        )
        new = [one for one in listed if one.get(ConnectionFields.CONNECTION_KEY) not in known]
        if new or time.monotonic() >= give_up_at or time.time() >= ends_at:
            return new
        await asyncio.sleep(CONNECT_POLL_SECONDS)


def watch_status(watch: Record, new: list[dict[str, JsonValue]]) -> str:
    """`connected` once there is a new connection, `gave_up` once the watch is over."""
    if new:
        return ConnectorFields.CONNECTED
    if time.time() >= float(watch[ConnectorFields.STARTED]) + CONNECT_WATCH_SECONDS:
        return ConnectorFields.GAVE_UP
    return ConnectorFields.WAITING


NEXT_STEPS = {
    ConnectorFields.CONNECTED: CONNECTED,
    ConnectorFields.WAITING: STILL_WAITING,
    ConnectorFields.GAVE_UP: GAVE_UP,
}
