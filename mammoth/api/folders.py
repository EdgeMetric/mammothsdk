"""
Folders API client for managing folders in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient

from ..models.folders import BulkFolderPatchRequest, CreateFolder, FolderSchema, FoldersList
from ..models.jobs import ObjectJobSchema

_list = list  # Alias to avoid shadowing by method name


class FoldersAPI:
    """Client for interacting with Mammoth Folders API.

    Access via client.folders:
        folders = client.folders.list()
        folder = client.folders.create(name="Reports")
        client.folders.delete([folder_id])
        client.folders.move(resource_ids=[...], target_folder_resource_id="...")
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self, project_id: int | None = None) -> int:
        if project_id is not None:
            return project_id
        proj = getattr(self._client, "project_id", None)
        if proj is not None:
            return proj
        raise ValueError("project_id must be set on the client using client.set_project_id()")

    def list(
        self,
        workspace_id: int | None = None,
        project_id: int | None = None,
        fields: str | None = None,
        folder_ids: _list[int] | None = None,
        names: _list[str] | None = None,
        statuses: _list[str] | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        created_by: _list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> FoldersList:
        """List folders in a project with optional filtering and pagination.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            fields: Fields to return (e.g., "__standard", "__full", "__min").
            folder_ids: List of specific folder IDs to retrieve.
            names: List of folder names to filter by.
            statuses: List of statuses to filter by.
            created_at: Date range filter for creation date.
            updated_at: Date range filter for update date.
            created_by: List of user names who created folders.
            limit: Maximum number of results (0-100, default 50).
            offset: Number of results to skip (default 0).
            sort: Sort specification (e.g., "(id:asc),(name:desc)").

        Returns:
            FoldersList with folders and pagination info.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)

        params: dict[str, Any] = {}
        if fields:
            params["fields"] = fields
        if folder_ids:
            params["id"] = ",".join(str(fid) for fid in folder_ids)
        if names:
            params["name"] = ",".join(names)
        if statuses:
            params["status"] = ",".join(statuses)
        if created_at:
            params["created_at"] = created_at
        if updated_at:
            params["updated_at"] = updated_at
        if created_by:
            params["created_by"] = ",".join(created_by)
        if limit != 50:
            params["limit"] = limit
        if offset != 0:
            params["offset"] = offset
        if sort:
            params["sort"] = sort

        response = self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/folders", params=params
        )
        return FoldersList(**response)

    def create(
        self,
        name: str,
        parent_resource_id: str | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> FolderSchema:
        """Create a new folder.

        Args:
            name: Name for the new folder.
            parent_resource_id: Parent folder resource ID (optional).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            FolderSchema with created folder info (id, name, resource_id, etc.).
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        folder_data = CreateFolder(name=name, parent_resource_id=parent_resource_id)
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/folders",
            json=folder_data.model_dump(exclude_none=True),
        )
        return FolderSchema(**response.get("folder", response))

    def delete(
        self,
        folder_ids: _list[int],
        workspace_id: int | None = None,
        project_id: int | None = None,
        check_dependency: bool = True,
        remove_contents: bool = True,
    ) -> None:
        """Delete multiple folders.

        Args:
            folder_ids: List of folder IDs to delete.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            check_dependency: Check for dependency before deleting.
            remove_contents: Remove folder contents before deleting.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        params = {
            "ids": ",".join(str(fid) for fid in folder_ids),
            "check_dependency": check_dependency,
            "remove_contents": remove_contents,
        }
        self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/folders", params=params
        )

    def move(
        self,
        resource_ids: _list[str],
        target_folder_resource_id: str | None = None,
        source_folder_resource_id: str | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> ObjectJobSchema:
        """Move resources between folders.

        Args:
            resource_ids: List of resource IDs to move.
            target_folder_resource_id: Target folder resource ID (None for root).
            source_folder_resource_id: Source folder resource ID (optional).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            ObjectJobSchema with job information for the move.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        move_request = BulkFolderPatchRequest(
            source_folder_resource_id=source_folder_resource_id,
            target_folder_resource_id=target_folder_resource_id,
            resource_ids=resource_ids,
            operation="move",
        )
        response = self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/folders",
            json=move_request.model_dump(exclude_none=True),
        )
        return ObjectJobSchema(**response)
