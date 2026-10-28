"""Make a project, and rename a project, a dataset or a view.

Deleting a dataset is `delete_views` with `whole_dataset`: Mammoth moves a
dataset to the trash with its last view anyway, so one tool owns both.
"""

from typing import Literal

from mcp.server.mcpserver.exceptions import ToolError

from ..consts import MAMMOTH_PROJECT_URL, ListFields, RenameFields
from ..sdk import JsonValue, build_client, named_projects, own_projects, read_sdk_errors
from ..server import mcp_server
from ..shape import dataset_url, view_url
from ..tool_kinds import CHANGES


@mcp_server.tool(title="Create project", annotations=CHANGES)
async def create_project(workspace_id: int, name: str) -> dict[str, JsonValue]:
    """Create a project in a workspace, seen only by the user who made it.

    Args:
        workspace_id: Which workspace to create it in.
        name: Name of the new project.

    Returns:
        `project_id`, `name`, and `mammoth_url`, the page in Mammoth it opens on.
    """
    pinned = own_projects()
    if pinned is not None:
        raise ToolError(
            f"This connection is limited to {named_projects(pinned)}, so it could not reach"
            " a new project. Ask the user to create it in Mammoth, or to connect again"
            " without choosing projects."
        )
    async with build_client(workspace_id) as client:
        made = await read_sdk_errors(client.projects.create(name, workspace_id=workspace_id))
    project_id = made[ListFields.ID]
    return {
        RenameFields.PROJECT_ID: project_id,
        ListFields.NAME: made.get(ListFields.NAME, name),
        ListFields.MAMMOTH_URL: MAMMOTH_PROJECT_URL.format(
            workspace_id=workspace_id, project_id=project_id
        ),
    }


@mcp_server.tool(title="Rename project, dataset or view", annotations=CHANGES)
async def rename(
    workspace_id: int,
    project_id: int,
    what: Literal["project", "dataset", "view"],
    name: str,
    dataset_id: int | None = None,
    view_id: int | None = None,
) -> dict[str, JsonValue]:
    """Rename a project, a dataset or a view.

    Renaming a project needs the workspace's admin role.

    Args:
        workspace_id: Which workspace it is in.
        project_id: The project, or the project the dataset or view is in.
        what: "project", "dataset" or "view".
        name: The new name.
        dataset_id: The dataset, or the dataset the view belongs to.
        view_id: The view, when `what` is "view".

    Returns:
        `renamed` (what), its `id`, the new `name`, and its `mammoth_url`.
    """
    async with build_client(workspace_id, project_id) as client:
        if what == RenameFields.PROJECT:
            await read_sdk_errors(
                client.projects.update(project_id, name=name, workspace_id=workspace_id)
            )
            return _renamed(
                what,
                project_id,
                name,
                MAMMOTH_PROJECT_URL.format(workspace_id=workspace_id, project_id=project_id),
            )
        dataset = _needed(dataset_id, RenameFields.DATASET_ID)
        if what == RenameFields.DATASET:
            await read_sdk_errors(client.datasets.rename(dataset, name, project_id=project_id))
            return _renamed(what, dataset, name, dataset_url(workspace_id, project_id, dataset))
        view = _needed(view_id, RenameFields.VIEW_ID)
        patch = [{"op": "replace", "path": ListFields.NAME, "value": name}]
        await read_sdk_errors(client.dataviews.update(dataset, view, patch, project_id=project_id))
        return _renamed(what, view, name, view_url(workspace_id, project_id, view))


def _needed(given: int | None, argument: str) -> int:
    if given is None:
        raise ToolError(f"Renaming this needs {argument}.")
    return given


def _renamed(what: str, renamed_id: int, name: str, url: str) -> dict[str, JsonValue]:
    return {
        RenameFields.RENAMED: what,
        ListFields.ID: renamed_id,
        ListFields.NAME: name,
        ListFields.MAMMOTH_URL: url,
    }
