"""Make a folder in a project, and read the project's folders.

A folder automation consolidates what lands in a folder, so the model needs a
folder to point it at and a way to put files there: `upload_file` and
`request_upload` take the `folder_resource_id` these name.
"""

from mammoth.client import MammothClient
from mcp.server.mcpserver.exceptions import ToolError

from ..consts import FolderFields
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import CHANGES


_FOLDER_PAGE = 100
NO_SUCH_FOLDER = "No folder with folder_resource_id {0} in this project. list_files names them."


@mcp_server.tool(title="Create folder", annotations=CHANGES)
async def create_folder(
    workspace_id: int,
    project_id: int,
    name: str,
    parent_folder_resource_id: int | None = None,
) -> dict[str, JsonValue]:
    """Create a folder in a project, for files and folder automations.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project to create it in.
        name: Name of the new folder.
        parent_folder_resource_id: A folder to create it inside, as
            `list_files` names it. Leave out for the project itself.

    Returns:
        `folder_id`, `name`, and `folder_resource_id`: what `upload_file`,
        `request_upload` and a folder automation take.
    """
    async with build_client(workspace_id, project_id) as client:
        parent = (
            None
            if parent_folder_resource_id is None
            else await _folder_id(client, workspace_id, project_id, parent_folder_resource_id)
        )
        made = await read_sdk_errors(
            client.folders.create(
                name, parent_folder_id=parent, workspace_id=workspace_id, project_id=project_id
            )
        )
    shown = _shown(made.model_dump(mode="json"))
    shown.pop(FolderFields.PARENT_ID, None)
    return shown


async def read_folders(
    client: MammothClient, workspace_id: int, project_id: int
) -> list[JsonValue]:
    """The project's folders, as `list_files` reports them."""
    listed = await read_sdk_errors(
        client.folders.list(workspace_id=workspace_id, project_id=project_id)
    )
    return [_shown(folder.model_dump(mode="json")) for folder in listed.folders]


async def _folder_id(
    client: MammothClient, workspace_id: int, project_id: int, resource_id: int
) -> int:
    """The id the API creates a folder inside, for the resource id the tools show.

    Args:
        client: The caller's client.
        workspace_id: Which workspace the project is in.
        project_id: Which project the folder is in.
        resource_id: The folder's `folder_resource_id`.

    Returns:
        The folder's own id.

    Raises:
        ToolError: If the project has no such folder.
    """
    offset = 0
    while True:
        page = await read_sdk_errors(
            client.folders.list(
                workspace_id=workspace_id,
                project_id=project_id,
                limit=_FOLDER_PAGE,
                offset=offset,
            )
        )
        for folder in page.folders:
            if folder.id is not None and str(folder.resource_id) == str(resource_id):
                return folder.id
        offset += len(page.folders)
        if len(page.folders) < _FOLDER_PAGE:
            raise ToolError(NO_SUCH_FOLDER.format(resource_id))


def _shown(folder: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """A folder under the names the tools take it by."""
    return {
        FolderFields.FOLDER_ID: folder.get(FolderFields.ID),
        FolderFields.FOLDER_RESOURCE_ID: folder.get(FolderFields.RESOURCE_ID),
        FolderFields.NAME: folder.get(FolderFields.NAME),
        FolderFields.PARENT_ID: folder.get(FolderFields.PARENT_ID),
    }
