"""Change a dashboard: Mammoth's AI edits it, or it gets a new title.

An AI edit is one turn of the editor's chat. Mammoth's AI reads the board and
the change asked for, and changes the board's draft. The share link opens the
published version, so it shows the board as it was until the board is
published again — which is `publish_dashboard`'s job, and the user's to ask
for.
"""

from mammoth.api.dashboard_generated import chat_edit
from mammoth.api.dashboards import DashboardsAPI
from mammoth.models.dashboard_generated import ChatEditParams, ChatEditSpec
from mammoth.models.dashboards import DashboardPatchItem, DashboardPatchOp, DashboardPatchPath
from mcp.server.mcpserver.exceptions import ToolError

from ..consts import BUILD_WAIT_SECONDS, ENGINE_V3, DashboardFields
from ..jobs import JobStillRunning, wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import DESTRUCTIVE
from .dashboards import read_dashboard

NOTHING_TO_CHANGE = "Say what to change, or give a new title."
OLDER_ENGINE_EDIT = (
    "Dashboard {id} is on Mammoth's older engine, which Mammoth's AI cannot edit."
    " The user can change it in the editor, at {editor_url}."
)
NOT_APPLIED = (
    "Nothing on the dashboard changed. `message` is what Mammoth's AI meant to do,"
    " not what it did. Tell the user, and ask them to put the change in other words"
    " or make it in the editor, at `editor_url`."
)
STILL_PUBLISHED = (
    "The share link still shows the published version. Ask the user, then call"
    " publish_dashboard to put this change out."
)
STILL_EDITING = (
    "Mammoth's AI is still making the change. get_dashboard shows the dashboard once"
    " it is done: do not send the change again."
)


@mcp_server.tool(title="Edit dashboard", annotations=DESTRUCTIVE)
async def edit_dashboard(
    workspace_id: int, dashboard_id: int, change: str = "", title: str = ""
) -> dict[str, JsonValue]:
    """Have Mammoth's AI change a dashboard, or give it a new title.

    The AI changes what the user asks for: add, remove or restyle a card or
    chart, filter it, add a page. Send the whole change in one call. A board
    that has nothing on it yet is built from the change, and that build counts
    against the workspace's AI dashboard allowance.

    The change is made to the board's draft. A published board's share link
    shows the board as it was until `publish_dashboard` runs again: never
    publish without asking the user.

    Args:
        workspace_id: Which workspace to act in.
        dashboard_id: Which dashboard, as `list_dashboards` lists it.
        change: What to change, in plain words. Leave it out to only rename.
        title: The dashboard's new title. Leave it out to keep the title.

    Returns:
        The dashboard afterwards, as `get_dashboard` reports it without
        numbers. After an AI edit, `changed` says whether anything changed,
        and `message` is the AI's reply. When `changed` is false, nothing was
        applied, whatever `message` says. `next_step`, when present, says what
        to tell the user. A big change can still be going when this returns:
        then `status` is "editing".
    """
    if not change and not title:
        raise ToolError(NOTHING_TO_CHANGE)
    async with build_client(workspace_id) as client:
        before = await read_dashboard(client.dashboards, workspace_id, dashboard_id)
        if change and before.get(DashboardFields.ENGINE) != ENGINE_V3:
            raise ToolError(
                OLDER_ENGINE_EDIT.format(
                    id=dashboard_id, editor_url=before[DashboardFields.EDITOR_URL]
                )
            )
        if title:
            await read_sdk_errors(client.dashboards.update(dashboard_id, [new_title(title)]))
        started = await start_edit(client.dashboards, dashboard_id, change) if change else None
    try:
        edit = {} if started is None else await wait_for_edit(workspace_id, started)
    except JobStillRunning:
        return {
            DashboardFields.ID: dashboard_id,
            DashboardFields.STATUS: DashboardFields.EDITING,
            DashboardFields.NEXT_STEP: STILL_EDITING,
        }
    async with build_client(workspace_id) as client:
        after = await read_dashboard(client.dashboards, workspace_id, dashboard_id)
    return {**after, **edit, **what_to_tell(edit, after)}


async def start_edit(
    dashboards: DashboardsAPI, dashboard_id: int, change: str
) -> dict[str, JsonValue]:
    """Send the change as one turn of the editor's chat, and return the job it started."""
    turn = ChatEditSpec(params=ChatEditParams(prompt=change))
    started = await read_sdk_errors(chat_edit(dashboards, dashboard_id, turn))
    return dict(started.model_dump(mode="json"))


async def wait_for_edit(workspace_id: int, started: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Wait for an AI edit, and keep what it reports that a model can use."""
    edited = await wait_for_job(workspace_id, started, seconds=BUILD_WAIT_SECONDS)
    return {field: edited[field] for field in DashboardFields.EDITED if field in edited}


def new_title(title: str) -> DashboardPatchItem:
    """The patch that renames a dashboard."""
    return DashboardPatchItem(
        op=DashboardPatchOp.REPLACE, path=DashboardPatchPath.TITLE, value=title
    )


def what_to_tell(
    edit: dict[str, JsonValue], dashboard: dict[str, JsonValue]
) -> dict[str, JsonValue]:
    """The note on an edit that did not land, or on a change its share link does not show yet."""
    if edit.get(DashboardFields.CHANGED) is False:
        return {DashboardFields.NEXT_STEP: NOT_APPLIED}
    if dashboard.get(DashboardFields.PUBLISHED):
        return {DashboardFields.NEXT_STEP: STILL_PUBLISHED}
    return {}
