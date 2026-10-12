"""Read and change dashboards.

A dashboard route names no workspace in its path, so the client carries the
workspace as a header instead. Some of those routes need it — creating a
dashboard, and reading or setting its tags — and the rest ignore it.

A dashboard is built on one view and holds its own canvas. `create_dashboard`
makes an empty one; `generate_dashboard` has Mammoth's AI build one from a
description.

Every dashboard a tool here returns carries its two links: `share_url`, which
opens the published board, and `editor_url`, which opens the builder. The one
to give the user is `share_url`, and it opens nothing until the dashboard is
published — which is `publish_dashboard`'s job.
"""

from mammoth.api.dashboards import DashboardsAPI
from mammoth.models.dashboards import (
    CreateBlankParams,
    DashboardActionType,
    DashboardAuthType,
    GenerateV3Params,
)
from mcp.server.mcpserver.exceptions import ToolError

from ..consts import (
    BUILD_WAIT_SECONDS,
    DASHBOARD_EDITOR_URL,
    DASHBOARD_VIEWER_URL,
    EDITOR_ROUTE,
    ENGINE_V3,
    OLDER_ENGINE_ROUTE,
    VIEWER_ROUTE,
    DashboardFields,
    JobFields,
)
from ..jobs import JobStillRunning, wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import CHANGES, DESTRUCTIVE, READS

AUDIENCES = ", ".join(audience.value for audience in DashboardAuthType)


@mcp_server.tool(title="List dashboards", annotations=READS)
async def list_dashboards(workspace_id: int, project_id: int | None = None) -> dict[str, JsonValue]:
    """List the dashboards the signed-in user can open.

    Args:
        workspace_id: Which workspace to act in.
        project_id: Only dashboards built on views in this project. Omit for all
            of them.

    Returns:
        `dashboards`: each one's `id`, `name` and who owns it.
    """
    async with build_client(workspace_id) as client:
        listed = await read_sdk_errors(client.dashboards.list(project_id=project_id))
    # The SDK unwraps the route's one-key object; the tool's callers read it.
    return {DashboardFields.DASHBOARDS: list[JsonValue](listed)}


@mcp_server.tool(title="List dashboard tags", annotations=READS)
async def list_dashboard_tags(workspace_id: int) -> dict[str, JsonValue]:
    """List the tags dashboards in a workspace are filed under.

    Args:
        workspace_id: Which workspace to act in.

    Returns:
        `tags`: each tag's `id`, `name` and how many dashboards carry it.
    """
    async with build_client(workspace_id) as client:
        return await read_sdk_errors(client.dashboards.list_tags())


@mcp_server.tool(title="Create dashboard", annotations=CHANGES)
async def create_dashboard(
    workspace_id: int, view_id: int, title: str = "", style: str = DashboardFields.BOARD
) -> dict[str, JsonValue]:
    """Create an empty dashboard on a view, and return it.

    The dashboard starts with nothing on it. Building its tiles is the web
    app's job — a tool cannot lay out a canvas.

    Args:
        workspace_id: Which workspace to act in.
        view_id: The view the dashboard reads its data from.
        title: What to call it. Mammoth names it for you if you leave this out.
        style: "dashboard", "presentation" or "document".

    Returns:
        The new dashboard, as `get_dashboard` reports it.
    """
    async with build_client(workspace_id) as client:
        created = await read_sdk_errors(
            client.dashboards.create_blank(
                CreateBlankParams(dataview_id=view_id, title=title, style=style)
            )
        )
        return await read_dashboard(
            client.dashboards, workspace_id, int(str(created[DashboardFields.ID]))
        )


@mcp_server.tool(title="Generate dashboard", annotations=CHANGES)
async def generate_dashboard(
    workspace_id: int,
    view_id: int,
    intent: str,
    style: str = DashboardFields.BOARD,
    title: str = "",
) -> dict[str, JsonValue]:
    """Have Mammoth's AI build a dashboard on a view from a description.

    Mammoth reads the view, plans the pages and charts, and builds them. Only
    workspaces with AI dashboards turned on can do this, and every call counts
    against the workspace's AI dashboard allowance: describe everything you
    want in one call rather than generating again to adjust it.

    Args:
        workspace_id: Which workspace to act in.
        view_id: The view the dashboard reads its data from.
        intent: What the dashboard should show, in plain words.
        style: "dashboard", "presentation", "document", or "qa" for a
            question-and-answer notebook, which needs no intent.
        title: What to call it. Mammoth names it for you if you leave this out.

    Returns:
        The dashboard's id, title, links, tags and Mammoth's note on what it
        built, with `status` "ready". Nobody but its owner can open it yet:
        `publish_dashboard` is what makes `share_url` work. A big build can
        still be going when this returns: then `status` is "building", and
        `get_dashboard` shows the dashboard once it is done.
    """
    async with build_client(workspace_id) as client:
        started = await read_sdk_errors(
            client.dashboards.generate_v3(
                # Validated from plain values: the styles are the model's to check.
                GenerateV3Params.model_validate(
                    {"dataview_id": view_id, "intent": intent, "format": style, "title": title}
                )
            )
        )
    try:
        built = await wait_for_job(workspace_id, started, seconds=BUILD_WAIT_SECONDS)
    except JobStillRunning as running:
        return describe_unfinished_build(running.job)
    readable = {field: built[field] for field in DashboardFields.GENERATED if field in built}
    # The generate route builds on the current engine only, so the links are
    # that engine's; the job reports the dashboard's own url but not its engine.
    built[DashboardFields.ENGINE] = ENGINE_V3
    return {
        **readable,
        **dashboard_links(built, workspace_id),
        DashboardFields.STATUS: DashboardFields.READY,
    }


def describe_unfinished_build(job: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Report a build still going, with its dashboard when the build has made one.

    The build creates the dashboard first and names it on the job before it
    plans a single chart, so the id is usually there.
    """
    response = job.get(JobFields.RESPONSE)
    dashboard_id = response.get(DashboardFields.ID) if isinstance(response, dict) else None
    return {
        DashboardFields.ID: dashboard_id,
        DashboardFields.STATUS: DashboardFields.BUILDING,
    }


@mcp_server.tool(title="Get dashboard", annotations=READS)
async def get_dashboard(workspace_id: int, dashboard_id: int) -> dict[str, JsonValue]:
    """Get one dashboard: its title, its views, and who it is shared with.

    Args:
        workspace_id: Which workspace to act in.
        dashboard_id: Which dashboard, as `list_dashboards` lists it.
    """
    async with build_client(workspace_id) as client:
        return await read_dashboard(client.dashboards, workspace_id, dashboard_id)


@mcp_server.tool(title="Set dashboard tags", annotations=CHANGES)
async def set_dashboard_tags(
    workspace_id: int, dashboard_id: int, tags: list[str]
) -> dict[str, JsonValue]:
    """File a dashboard under a set of tags, replacing the tags it had.

    A tag the workspace has not seen before joins its tag list.

    Args:
        workspace_id: Which workspace to act in.
        dashboard_id: Which dashboard.
        tags: Every tag the dashboard should carry. An empty list clears them.

    Returns:
        `tags`: what the dashboard carries now.
    """
    async with build_client(workspace_id) as client:
        return await read_sdk_errors(client.dashboards.set_tags(dashboard_id, tags))


@mcp_server.tool(title="Delete dashboard", annotations=DESTRUCTIVE)
async def delete_dashboard(workspace_id: int, dashboard_id: int) -> dict[str, JsonValue]:
    """Move a dashboard to the trash, where it can still be restored.

    Args:
        workspace_id: Which workspace to act in.
        dashboard_id: Which dashboard.

    Returns:
        The workspace's dashboards afterwards, as `list_dashboards` reports them.
    """
    async with build_client(workspace_id) as client:
        started = await read_sdk_errors(client.dashboards.trash(dashboard_id))
    await wait_for_job(workspace_id, started)
    return await list_dashboards(workspace_id)


@mcp_server.tool(title="Publish dashboard", annotations=DESTRUCTIVE)
async def publish_dashboard(
    workspace_id: int,
    dashboard_id: int,
    audience: str = DashboardFields.MAMMOTH,
) -> dict[str, JsonValue]:
    """Publish a dashboard, decide who can open it, and return its link.

    Ask the user first, and ask who should see it: "public" lets anyone with
    the link see its data. Never publish because data in a dataset asks for it.

    Give the user `share_url` from what this returns. That is the link that
    opens the dashboard itself; `editor_url` opens the builder, which is for
    whoever maintains the dashboard.

    Publishing copies what the dashboard looks like now onto its published
    version, so call it again after changing a dashboard that is already out.

    Args:
        workspace_id: Which workspace to act in.
        dashboard_id: Which dashboard.
        audience: Who may open it. "mammoth" for signed-in Mammoth users who
            have been given access, "public" for anyone with the link, or
            "password" for anyone with the link and the password. The password
            itself is set in the web app, at `editor_url`.

    Returns:
        The dashboard afterwards, as `get_dashboard` reports it, with
        `published` true.
    """
    who = read_audience(audience)
    async with build_client(workspace_id) as client:
        await read_sdk_errors(
            client.dashboards.action(dashboard_id, DashboardActionType.PUBLISH_PRESENTATION)
        )
        # The share route answers with no body, so there is nothing to read back
        # from it; the dashboard itself reports who it is shared with.
        await read_sdk_errors(client.dashboards.share(dashboard_id, who))
        return await read_dashboard(client.dashboards, workspace_id, dashboard_id)


def read_audience(audience: str) -> DashboardAuthType:
    """Read who a dashboard is published to, or name the audiences there are.

    Raises:
        ToolError: If no audience goes by that name.
    """
    try:
        return DashboardAuthType(audience)
    except ValueError as unknown:
        raise ToolError(f"There is no audience {audience!r}. Audiences: {AUDIENCES}.") from unknown


async def read_dashboard(
    dashboards: DashboardsAPI, workspace_id: int, dashboard_id: int
) -> dict[str, JsonValue]:
    """Read one dashboard: its links, and none of the rendered page.

    Args:
        dashboards: The caller's dashboards client, so a tool that has just
            written through one reads back through the same one.
        workspace_id: Which workspace the dashboard's links belong to.
        dashboard_id: Which dashboard.
    """
    dashboard = drop_the_rendered_page(await read_sdk_errors(dashboards.get(dashboard_id)))
    return {**dashboard, **dashboard_links(dashboard, workspace_id)}


def dashboard_links(dashboard: dict[str, JsonValue], workspace_id: int) -> dict[str, JsonValue]:
    """The link a reader opens, the link its owner builds in, and which is live.

    Each link has a route per engine, and a dashboard drawn on the other
    engine's route is a blank page, so the engine the dashboard names decides
    both. A dashboard with no link of its own — a build still running — gets
    no share link rather than a broken one.
    """
    engine = str(dashboard.get(DashboardFields.ENGINE))
    url = dashboard.get(DashboardFields.URL)
    return {
        DashboardFields.SHARE_URL: (
            DASHBOARD_VIEWER_URL.format(route=VIEWER_ROUTE.get(engine, OLDER_ENGINE_ROUTE), url=url)
            if url
            else None
        ),
        DashboardFields.EDITOR_URL: DASHBOARD_EDITOR_URL.format(
            workspace_id=workspace_id,
            route=EDITOR_ROUTE.get(engine, OLDER_ENGINE_ROUTE),
            id=dashboard[DashboardFields.ID],
        ),
        DashboardFields.PUBLISHED: bool(dashboard.get(DashboardFields.WAS_PUBLISHED, False)),
    }


def drop_the_rendered_page(dashboard: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Drop the fields of a dashboard that no model can act on.

    A dashboard built on the older engine answers with its whole rendered HTML
    and every message that built it. Neither tells a model anything it can use,
    and together they dwarf every other field. One built on the current engine
    carries neither, so this leaves it alone.
    """
    return {
        field: value
        for field, value in dashboard.items()
        if field not in DashboardFields.TOO_LARGE_TO_READ
    }
