"""Make a folder in a project, and read the project's folders.

A folder automation consolidates what lands in a folder, so the model needs a
folder to point it at and a way to put files there: `upload_file` and
`request_upload` take the `folder_resource_id` these name.
"""

from mammoth.client import MammothClient

from ..consts import FolderFields
from ..sdk import JsonValue, build_client, read_sdk_errors
from ..server import mcp_server
from ..tool_kinds import CHANGES


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
    parent = None if parent_folder_resource_id is None else str(parent_folder_resource_id)
    async with build_client(workspace_id, project_id) as client:
        made = await read_sdk_errors(
            client.folders.create(name, parent, workspace_id=workspace_id, project_id=project_id)
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


def _shown(folder: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """A folder under the names the tools take it by."""
    return {
        FolderFields.FOLDER_ID: folder.get(FolderFields.ID),
        FolderFields.FOLDER_RESOURCE_ID: folder.get(FolderFields.RESOURCE_ID),
        FolderFields.NAME: folder.get(FolderFields.NAME),
        FolderFields.PARENT_ID: folder.get(FolderFields.PARENT_ID),
    }
