"""Bring data in from a connected source: a database, a CRM, a spreadsheet service.

Connecting a source means signing in to it, and that stays with the user, in
Mammoth: no password or token passes through a model. So `connect_source`
hands the user the page that opens the connector in their project, and
`find_new_datasets` finds what the project gained once they are done. From
there a dataset is read, transformed and built on like an uploaded one, and
Mammoth refreshes it on the schedule the user set when they brought it in.
"""

from datetime import UTC, datetime
from urllib.parse import urlencode

from mcp.server.mcpserver.exceptions import ToolError

from ..consts import (
    LIST_LIMIT_DEFAULT,
    MAMMOTH_DATA_URL,
    ApiPaths,
    ConnectorFields,
    ListFields,
    UploadFields,
)
from ..sdk import JsonValue, build_client, read_sdk_errors, request_api
from ..server import mcp_server
from ..shape import tidy_page
from ..tool_kinds import READS
from ..upload_report import read_time, report_upload

CHECK_THE_KEY = "Check the key with `list_connectors`."
IN_MAMMOTH = (
    "Give the user `mammoth_url`. In Mammoth they sign in to the source, pick"
    " the data to bring in and, if they like, how often to refresh it. When"
    " they say it is done, call `find_new_datasets` with `since`."
)
OFF_THE_PLAN = (
    " This connector is not on the workspace's plan: Mammoth offers the upgrade"
    " on that page. Tell the user before they open it."
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


@mcp_server.tool(title="Connect a data source", annotations=READS)
async def connect_source(
    workspace_id: int, project_id: int, connector_key: str | None = None
) -> dict[str, JsonValue]:
    """Give the user the page in Mammoth where they connect a source and bring its data in.

    Nothing is connected here: the user signs in to the source themselves, in
    Mammoth. Use this when the user wants data from a database or an app
    rather than a file; for a file, use `request_upload`.

    Args:
        workspace_id: Which workspace to act in.
        project_id: Which project the data goes into.
        connector_key: The connector's `name_key`, as `list_connectors` lists
            it, such as "postgres" or "hubspot". Omit to let the user pick one.

    Returns:
        `mammoth_url`: the page to give the user. `since`: the time to pass to
        `find_new_datasets` once they are done. `next_step`: what to do now.
        `connector`: its `key` and `name`, when one was named.
    """
    handed: dict[str, JsonValue] = {ConnectorFields.SINCE: datetime.now(UTC).isoformat()}
    link: dict[str, str] = {ConnectorFields.ACTION: ConnectorFields.ADD_CONNECTOR}
    next_step = IN_MAMMOTH
    if connector_key is not None:
        connector = await read_connector(workspace_id, connector_key)
        link[ConnectorFields.CONNECTOR] = connector_key
        handed[ConnectorFields.CONNECTOR] = {
            ConnectorFields.SHOWN_KEY: connector_key,
            ConnectorFields.SHOWN_NAME: connector.get(ConnectorFields.NAME),
        }
        if connector.get(ConnectorFields.AVAILABLE) is False:
            next_step += OFF_THE_PLAN
    page = MAMMOTH_DATA_URL.format(workspace_id=workspace_id, project_id=project_id)
    handed[ListFields.MAMMOTH_URL] = f"{page}?{urlencode(link)}"
    handed[ConnectorFields.NEXT_STEP] = next_step
    return handed


async def read_connector(workspace_id: int, connector_key: str) -> dict[str, JsonValue]:
    """The connector Mammoth has under this key, or a refusal that says where to look."""
    async with build_client(workspace_id) as client:
        try:
            return await read_sdk_errors(client.connectors.get(connector_key))
        except ToolError as refused:
            raise ToolError(f"{refused}. {CHECK_THE_KEY}") from refused


@mcp_server.tool(title="Find new datasets", annotations=READS)
async def find_new_datasets(workspace_id: int, project_id: int, since: str) -> dict[str, JsonValue]:
    """Find the datasets a project gained since a time: what the user brought in from a source.

    Call this when the user says they have connected the source in Mammoth.

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
    report = await report_upload(
        {
            UploadFields.UPLOADED_AT: since,
            UploadFields.WORKSPACE_ID: workspace_id,
            UploadFields.PROJECT_ID: project_id,
        }
    )
    if not report[UploadFields.FILES]:
        report[UploadFields.STATUS] = UploadFields.WAITING
    return report
