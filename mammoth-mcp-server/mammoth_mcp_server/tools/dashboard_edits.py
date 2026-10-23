"""Change a dashboard: Mammoth's AI edits it, or its title, tags or embed change.

An AI edit is one turn of the editor's chat. Mammoth's AI reads the board and
the change asked for, and changes the board's draft. The share link opens the
published version, so it shows the board as it was until the board is
published again — which is `publish_dashboard`'s job, and the user's to ask
for. Tags and embed settings are not part of the draft: they apply at once.

Mammoth reports `changed` when the turn saved a new board, not when the board
does what was asked: an AI that swaps a chart for one that still misses the ask
has changed the board. What did not land is in the reply itself, written by
Mammoth's own check rather than by the AI, in two forms (mvc-service
`dashboards_v3/llm/controls.py`): a line per ask, `- <ask> — <status>`, when the
user asked for two things or more, and a `Couldn’t do: <note>; <note>` block.
"""

import re

from mammoth.api.dashboard_generated import chat_edit
from mammoth.api.dashboards import DashboardsAPI
from mammoth.models.dashboard_generated import ChatEditParams, ChatEditSpec
from mammoth.models.dashboards import DashboardPatchItem, DashboardPatchOp, DashboardPatchPath
from mcp.server.mcpserver.exceptions import ToolError

from ..consts import ENGINE_V3, DashboardFields, JobFields
from ..jobs import JobStillRunning, wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import DESTRUCTIVE
from .dashboard_embed import EmbedMode, change_embed, check_embed_change
from .dashboards import read_dashboard

NOTHING_TO_CHANGE = "Say what to change: a change, a new title, tags, or the embed settings."
JOB_ALONE = (
    "job_id picks up an edit already sent: call it with nothing else to change, then"
    " send any new change on its own."
)
OLDER_ENGINE_EDIT = (
    "Dashboard {id} is on Mammoth's older engine, which Mammoth's AI cannot edit."
    " The user can change it in the editor, at {editor_url}."
)
NOT_APPLIED = (
    "Nothing on the dashboard changed. Do not tell the user the change was made:"
    " tell them why from `message`, and ask them to put the change in other words"
    " or make it in the editor, at `editor_url`."
)
STILL_PUBLISHED = (
    "The share link still shows the published version. Ask the user, then call"
    " publish_dashboard to put this change out."
)
PARTLY_DONE = (
    "Part of the change did not land: `not_done` lists it, from Mammoth's own check."
    " Tell the user what was done and what was not; do not say the whole change was made."
)
ALREADY_CHANGED = "These changes were made before that, and stay: {done}. Tell the user."
STILL_EDITING = (
    "Mammoth's AI is still making the change. Call edit_dashboard with job_id={job_id}"
    " and nothing else to get what it did: do not send the change again."
)
# One line per ask, as Mammoth lists them when the user asked for several things.
ASK_LINE = re.compile(r"^- (?P<ask>.+?) — (?P<status>.+?)\s*$", re.MULTILINE)
COULD_NOT = re.compile(r"Couldn[’']t do:\s*(?P<notes>.+?)[._\s]*(?:\n\s*\n|$)", re.DOTALL)


@mcp_server.tool(title="Edit dashboard, tags or embed", annotations=DESTRUCTIVE)
async def edit_dashboard(
    workspace_id: int,
    dashboard_id: int,
    change: str = "",
    title: str = "",
    embed_mode: EmbedMode | None = None,
    any_site: bool | None = None,
    allowed_sites: list[str] | None = None,
    tags: list[str] | None = None,
    job_id: int | None = None,
) -> dict[str, JsonValue]:
    """Have Mammoth's AI change a dashboard, rename it, set its tags, or choose how it embeds.

    The AI changes what the user asks for: add, remove or restyle a card or
    chart, filter it, add a page. Send the whole change in one call. A board
    that has nothing on it yet is built from the change, and that build counts
    against the workspace's AI dashboard allowance.

    The change and the title go to the board's draft. A published board's
    share link shows the board as it was until `publish_dashboard` runs again:
    never publish without asking the user. Tags and the embed settings apply
    at once.
    Ask the user before changing them: they decide who outside Mammoth sees
    the data. `get_dashboard` with `include_embed` gives the code to paste.

    Args:
        workspace_id: Which workspace to act in.
        dashboard_id: Which dashboard, as `list_dashboards` lists it.
        change: What to change, in plain words.
        title: The dashboard's new title.
        embed_mode: "key" (the embed code carries the board's embed key) or
            "signed" (the user's server signs a token per viewer; the
            workspace needs a signing secret, set in the web app). A board
            whose link is public embeds as "public" whatever this is.
        any_site: true lets any site show the board.
        allowed_sites: Only these sites may show the board, as origins
            ("https://acme.com", "https://*.acme.com"). At most 20.
        tags: Every tag the dashboard should carry, replacing the ones it has;
            an empty list clears them. A new tag joins the workspace's list,
            which `list_dashboards` with `include_tags` shows.
        job_id: Pick up an edit an earlier call left "editing", from its
            `job_id`, and report what it did. Sends nothing new.

    Returns:
        The dashboard afterwards, as `get_dashboard` reports it without
        numbers. After an AI edit, `changed` says whether anything changed,
        and `message` is the AI's reply. When `changed` is false, nothing was
        applied, whatever `message` says. When `partial` is true, part of it
        did not land: `not_done` lists what. After tags are set, `tags` is what
        the dashboard carries. After an embed change, `embed` is the embed
        afterwards. `next_step`, when present, says what to tell the
        user. A big change can still be going when this returns: then `status`
        is "editing", with the `job_id` to pick it up by.
    """
    embeds = not (embed_mode is None and any_site is None and allowed_sites is None)
    if job_id is not None:
        if change or title or embeds or tags is not None:
            raise ToolError(JOB_ALONE)
        return await finish_edit(workspace_id, dashboard_id, {JobFields.JOB_ID: job_id})
    if not (change or title or embeds or tags is not None):
        raise ToolError(NOTHING_TO_CHANGE)
    check_embed_change(any_site, allowed_sites)
    # What landed so far, for the error when a later change is refused.
    done: list[str] = []
    async with build_client(workspace_id) as client:
        before = await read_dashboard(client.dashboards, workspace_id, dashboard_id)
        refuse_older_engine(before, change)
        try:
            if title:
                await read_sdk_errors(client.dashboards.update(dashboard_id, [new_title(title)]))
                done.append("the title")
            embed = (
                await change_embed(
                    client.dashboards, dashboard_id, embed_mode, any_site, allowed_sites
                )
                if embeds
                else None
            )
            done += ["the embed settings"] if embeds else []
            tagged = (
                await read_sdk_errors(client.dashboards.set_tags(dashboard_id, tags))
                if tags is not None
                else {}
            )
            done += ["the tags"] if tags is not None else []
            started = await start_edit(client.dashboards, dashboard_id, change) if change else None
        except ToolError as refused:
            raise said_what_changed(refused, done) from refused
    # Tags and embed settings are off the draft: the board read before is still the board.
    finished = await finish_edit(workspace_id, dashboard_id, started) if change or title else before
    carried = {DashboardFields.TAGS: tagged[DashboardFields.TAGS]} if tagged else {}
    return {**finished, **carried, **({} if embed is None else {DashboardFields.EMBED: embed})}


async def finish_edit(
    workspace_id: int,
    dashboard_id: int,
    started: dict[str, JsonValue] | None,
) -> dict[str, JsonValue]:
    """Wait for the AI edit, if one was sent, and report the dashboard after it."""
    try:
        edit = {} if started is None else await wait_for_edit(workspace_id, started)
    except JobStillRunning as running:
        job_id = running.job[JobFields.ID]
        return {
            DashboardFields.ID: dashboard_id,
            DashboardFields.STATUS: DashboardFields.EDITING,
            DashboardFields.JOB_ID: job_id,
            DashboardFields.NEXT_STEP: STILL_EDITING.format(job_id=job_id),
        }
    async with build_client(workspace_id) as client:
        after = await read_dashboard(client.dashboards, workspace_id, dashboard_id)
    return {**after, **edit, **what_to_tell(edit, after)}


def said_what_changed(refused: ToolError, done: list[str]) -> ToolError:
    """The refusal, naming what changed before it, which a model would otherwise say did not."""
    if not done:
        return refused
    return ToolError(f"{refused} {ALREADY_CHANGED.format(done=', '.join(done))}")


def refuse_older_engine(dashboard: dict[str, JsonValue], change: str) -> None:
    """Refuse an AI edit of a board on the older engine, which the AI cannot edit.

    Raises:
        ToolError: If it is one, naming the editor that can change it.
    """
    if change and dashboard.get(DashboardFields.ENGINE) != ENGINE_V3:
        raise ToolError(
            OLDER_ENGINE_EDIT.format(
                id=dashboard[DashboardFields.ID], editor_url=dashboard[DashboardFields.EDITOR_URL]
            )
        )


async def start_edit(
    dashboards: DashboardsAPI, dashboard_id: int, change: str
) -> dict[str, JsonValue]:
    """Send the change as one turn of the editor's chat, and return the job it started."""
    turn = ChatEditSpec(params=ChatEditParams(prompt=change))
    started = await read_sdk_errors(chat_edit(dashboards, dashboard_id, turn))
    return dict(started.model_dump(mode="json"))


async def wait_for_edit(workspace_id: int, started: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Wait for an AI edit, and keep what it reports that a model can use.

    It waits as long as the tool call may, not the shorter wait of a build: the
    edit's result is in its job alone, and no tool reads the job afterwards.
    """
    edited = await wait_for_job(workspace_id, started)
    edit = {field: edited[field] for field in DashboardFields.EDITED if field in edited}
    missed: list[JsonValue] = list(not_done(edited.get(DashboardFields.MESSAGE)))
    if missed and edit.get(DashboardFields.CHANGED) is True:
        edit[DashboardFields.PARTIAL] = True
    return {**edit, **({DashboardFields.NOT_DONE: missed} if missed else {})}


def not_done(message: object) -> list[str]:
    """What Mammoth's own check says did not land, from the reply to an edit.

    An ask listed with a status Mammoth gives one that missed, and each note
    under "Couldn’t do:". The AI's own list lines take the same "- a — b"
    shape, so only those statuses mark a line as Mammoth's check.
    """
    if not isinstance(message, str):
        return []
    asks = [
        f"{line['ask']}: {line['status']}"
        for line in ASK_LINE.finditer(message)
        if line["status"].startswith(DashboardFields.ASK_MISSED)
    ]
    refused = COULD_NOT.search(message)
    notes = refused["notes"].split(";") if refused else []
    return [*asks, *(note.strip() for note in notes if note.strip())]


def new_title(title: str) -> DashboardPatchItem:
    """The patch that renames a dashboard."""
    return DashboardPatchItem(
        op=DashboardPatchOp.REPLACE, path=DashboardPatchPath.TITLE, value=title
    )


def what_to_tell(
    edit: dict[str, JsonValue], dashboard: dict[str, JsonValue]
) -> dict[str, JsonValue]:
    """The note on an edit that did not land, in full or in part, or not yet on the share link."""
    if edit.get(DashboardFields.CHANGED) is False:
        return {DashboardFields.NEXT_STEP: NOT_APPLIED}
    notes = [
        *([PARTLY_DONE] if edit.get(DashboardFields.PARTIAL) else []),
        *([STILL_PUBLISHED] if dashboard.get(DashboardFields.PUBLISHED) else []),
    ]
    return {DashboardFields.NEXT_STEP: " ".join(notes)} if notes else {}
