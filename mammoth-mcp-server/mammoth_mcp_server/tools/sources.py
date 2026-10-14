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

from ..consts import (
    CONNECT_POLL_SECONDS,
    CONNECT_WAIT_SECONDS,
    LIST_LIMIT_DEFAULT,
    ApiPaths,
    ConnectorFields,
    UploadFields,
)
from ..sdk import JsonValue, build_client, request_api
from ..server import mcp_server
from ..shape import tidy_page
from ..telemetry import Events, TelemetryFields, record
from ..tool_kinds import READS
from ..upload_report import read_time, report_upload

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
        not include it.
    """
    query: dict[str, str | int] = {
        ConnectorFields.FIELDS: ConnectorFields.LISTED,
        ConnectorFields.LIMIT: limit,
        ConnectorFields.OFFSET: offset,
        ConnectorFields.PROJECT_ID: project_id,
    }
    if connected_only:
        query[ConnectorFields.HAS_CONNECTIONS] = "true"
    async with build_client(workspace_id) as client:
        page = await request_api(
            client, "GET", ApiPaths.CONNECTORS.format(workspace_id=workspace_id), query=query
        )
    return tidy_page(page, ConnectorFields.CONNECTORS, limit)


@mcp_server.tool(title="Find new datasets", annotations=READS)
async def find_new_datasets(workspace_id: int, project_id: int, since: str) -> dict[str, JsonValue]:
    """Find the datasets a project gained since a time: what the user brought in from a source.

    Call this straight after giving the user the link. It waits while they
    connect the source, so do not end your turn asking them to say when they
    are done. `waiting` means nothing came in before the wait ran out: call
    again if they are still at it; after a couple of rounds say you are waiting.

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
        report = await report_upload(ticket)
        if not report[UploadFields.FILES]:
            report[UploadFields.STATUS] = UploadFields.WAITING
        if report[UploadFields.STATUS] == UploadFields.DONE or time.monotonic() >= give_up_at:
            return report
        await asyncio.sleep(CONNECT_POLL_SECONDS)
