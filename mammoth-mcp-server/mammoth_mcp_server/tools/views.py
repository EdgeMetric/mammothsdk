"""Create, copy and delete the views of a dataset.

A view is where transformations run, so a second view is the safe place to
experiment: copy the view, change the copy, delete the copy.
"""

from mcp.server.mcpserver.exceptions import ToolError

from ..consts import ViewFields
from ..jobs import wait_for_job
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import CHANGES, DESTRUCTIVE


@mcp_server.tool(annotations=CHANGES)
async def create_view(
    workspace_id: int,
    project_id: int,
    dataset_id: int,
    name: str,
    copy_from_view_id: int | None = None,
) -> dict[str, JsonValue]:
    """Create a view of a dataset, empty or as a copy of another view.

    Copy a view before experimenting with its transformations: the original
    stays as it is.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        dataset_id: Which dataset the new view belongs to.
        name: Name of the new view. Mammoth may add a number to it, e.g.
            "Scratch" becomes "Scratch 1"; read the name back with `list_views`.
        copy_from_view_id: A view of the same dataset whose transformations the
            new view starts with. Omit for a view with no transformations.

    Returns:
        The new view's id, under the key `dataview_id`.
    """
    # The SDK waits for the creation job itself, so the new view's id is
    # what comes back.
    async with build_client(workspace_id) as client:
        return await read_sdk_errors(
            client.dataviews.create(
                dataset_id,
                name=name,
                clone_config_from=copy_from_view_id,
                project_id=project_id,
            )
        )


@mcp_server.tool(annotations=DESTRUCTIVE)
async def delete_views(
    workspace_id: int, project_id: int, dataset_id: int, view_ids: list[int]
) -> dict[str, JsonValue]:
    """Delete views of a dataset.

    The views and their transformations are gone for good. Ask the user before
    calling this. A dataset keeps at least one view, so its last view cannot be
    deleted.

    Args:
        workspace_id: Which workspace the dataset is in.
        project_id: Which project the dataset is in.
        dataset_id: Which dataset the views belong to.
        view_ids: The views to delete.

    Returns:
        `deleted`: the ids that were deleted. `failed`: each id that was not,
        with the reason. One failure does not stop the others.
    """
    deleted: list[JsonValue] = []
    failed: list[JsonValue] = []
    # One client for the whole list: each one opens its own connections.
    async with build_client(workspace_id) as client:
        for view_id in view_ids:
            try:
                await wait_for_job(
                    workspace_id,
                    await read_sdk_errors(
                        client.dataviews.delete(dataset_id, view_id, project_id=project_id)
                    ),
                )
            except ToolError as error:
                failed.append({ViewFields.VIEW_ID: view_id, ViewFields.ERROR: str(error)})
            else:
                deleted.append(view_id)
    return {ViewFields.DELETED: deleted, ViewFields.FAILED: failed}
