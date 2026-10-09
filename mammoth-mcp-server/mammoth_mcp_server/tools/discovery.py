"""Tools that let an AI client find its way around a Mammoth account.

Mammoth holds data as workspace > project > dataset > view. A view is a pipeline
of transformation tasks over a dataset. These tools walk that hierarchy; every
one of them calls the same API route the web app calls, as the signed-in user.
"""

from ..consts import LIST_LIMIT_DEFAULT, ApiFields, ApiPaths, BrowseFields, ListFields
from ..sdk import JsonValue, build_client, own_project, read_sdk_errors, request_api
from ..server import mcp_server
from ..tool_kinds import READS


@mcp_server.tool(annotations=READS)
async def list_workspaces(limit: int = LIST_LIMIT_DEFAULT, offset: int = 0) -> dict[str, JsonValue]:
    """List the workspaces the signed-in user can open.

    A workspace is the top level of a Mammoth account. Start here when you do
    not know which workspace to work in.

    Args:
        limit: How many workspaces to return.
        offset: How many workspaces to skip, for paging.
    """
    # The one call made before a workspace is known, so the client is given none.
    async with build_client(None) as client:
        return await request_api(
            client,
            "GET",
            ApiPaths.WORKSPACES,
            query={
                ApiFields.FIELDS: ApiFields.MINIMAL,
                "limit": limit,
                "offset": offset,
            },
        )


@mcp_server.tool(annotations=READS)
async def list_projects(
    workspace_id: int, limit: int = LIST_LIMIT_DEFAULT, offset: int = 0
) -> dict[str, JsonValue]:
    """List the projects in a workspace.

    A project groups datasets, views and dashboards that belong together.

    A connection the user limited to one project lists that project alone, and
    that is the project every other tool must name.

    Args:
        workspace_id: Which workspace to look in.
        limit: How many projects to return.
        offset: How many projects to skip, for paging.
    """
    pinned = own_project()
    if pinned is not None:
        return await _the_pinned_project(workspace_id, pinned)
    async with build_client(workspace_id) as client:
        return await read_sdk_errors(
            client.browse.projects(
                workspace_id=workspace_id,
                fields=ApiFields.MINIMAL,
                limit=limit,
                offset=offset,
            )
        )


async def _the_pinned_project(workspace_id: int, pinned: int) -> dict[str, JsonValue]:
    """The one project a pinned connection may act in, asked for by its id.

    Paging is why this is not a filtered list: the pinned project sits on
    whichever page of the workspace's projects its name sorts to, so filtering
    one page answers "no projects" to a connection that has exactly one. The
    browse route is the one route that takes a resource id, and the rows it
    answers with are reshaped into the list this tool has always returned.
    """
    async with build_client(workspace_id) as client:
        found = await request_api(
            client,
            "GET",
            ApiPaths.BROWSE.format(workspace_id=workspace_id),
            query={
                ApiFields.FIELDS: ApiFields.MINIMAL,
                BrowseFields.TYPE: BrowseFields.PROJECT,
                BrowseFields.IDS: pinned,
                BrowseFields.LEVEL: BrowseFields.ITSELF,
            },
        )
    return {ListFields.PROJECTS: _as_projects(found.get(BrowseFields.RESOURCES))}


def _as_projects(rows: JsonValue) -> JsonValue:
    """The id and name of each browsed resource, as a project list's rows."""
    if not isinstance(rows, list):
        return []
    return [
        {ListFields.ID: row.get(ListFields.ID), ListFields.NAME: row.get(ListFields.NAME)}
        for row in rows
        if isinstance(row, dict)
    ]


@mcp_server.tool(annotations=READS)
async def list_datasets(
    workspace_id: int,
    project_id: int,
    limit: int = LIST_LIMIT_DEFAULT,
    offset: int = 0,
) -> dict[str, JsonValue]:
    """List the datasets in a project.

    A dataset is data brought into Mammoth, for example an uploaded file or a
    connector import. Its views are where the data is shaped.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project to look in.
        limit: How many datasets to return.
        offset: How many datasets to skip, for paging.
    """
    async with build_client(workspace_id) as client:
        return await read_sdk_errors(
            client.browse.datasets(
                project_id=project_id,
                workspace_id=workspace_id,
                fields=ApiFields.MINIMAL,
                limit=limit,
                offset=offset,
            )
        )


@mcp_server.tool(annotations=READS)
async def get_dataset(workspace_id: int, project_id: int, dataset_id: int) -> dict[str, JsonValue]:
    """Get one dataset with its columns, row counts and status.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        dataset_id: Which dataset to read.

    Returns:
        The dataset, under the key `dataset`.
    """
    async with build_client(workspace_id) as client:
        return await read_sdk_errors(
            client.datasets.get(
                dataset_id,
                project_id=project_id,
                fields=ApiFields.STANDARD,
            )
        )


@mcp_server.tool(annotations=READS)
async def list_views(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    limit: int = LIST_LIMIT_DEFAULT,
    offset: int = 0,
) -> dict[str, JsonValue]:
    """List the views of a dataset.

    Read data and run transformations against a view, not the dataset itself.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        dataset_id: Which dataset the views belong to.
        limit: How many views to return.
        offset: How many views to skip, for paging.
    """
    async with build_client(workspace_id) as client:
        return await read_sdk_errors(
            client.browse.dataviews(
                dataset_id,
                project_id=project_id,
                workspace_id=workspace_id,
                fields=ApiFields.MINIMAL,
                limit=limit,
                offset=offset,
            )
        )


@mcp_server.tool(annotations=READS)
async def get_view(
    workspace_id: int, project_id: int, dataset_id: int, view_id: int
) -> dict[str, JsonValue]:
    """Get one view with its columns and their types.

    Read this before writing any transformation, so column names and types are
    exact.

    Args:
        workspace_id: Which workspace the view is in.
        project_id: Which project the view is in.
        dataset_id: Which dataset the view belongs to.
        view_id: Which view to read.
    """
    # The SDK finds the view's latest pipeline step first, so the columns
    # reported are the ones the transformations left — at the cost of a second
    # request, which the route worked out for itself.
    async with build_client(workspace_id, project_id) as client:
        return await read_sdk_errors(
            client.dataviews.get(
                dataset_id,
                view_id,
                project_id=project_id,
                fields=ApiFields.STANDARD,
            )
        )
