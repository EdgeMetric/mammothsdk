"""
Folders API client for managing folders in Mammoth.
"""

from typing import Optional, Dict, Any, List, Union
from ..models.folders import FoldersList, FolderDetails, CreateFolder, BulkFolderPatchRequest
from ..models.jobs import ObjectJobSchema


class FoldersAPI:
    """Client for interacting with Mammoth Folders API."""
    
    def __init__(self, client):
        self._client = client
    
    def list_folders(
        self,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        fields: Optional[str] = None,
        folder_ids: Optional[List[int]] = None,
        names: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        created_by: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
        sort: Optional[str] = None
    ) -> FoldersList:
        """
        List folders in a project with optional filtering and pagination.
        
        Args:
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            fields: Fields to return (e.g., "__standard", "__full", "__min", or comma-separated)
            folder_ids: List of specific folder IDs to retrieve
            names: List of folder names to filter by
            statuses: List of statuses to filter by
            created_at: Date range filter for creation date
            updated_at: Date range filter for update date
            created_by: List of user names who created folders
            limit: Maximum number of results (0-100, default: 50)
            offset: Number of results to skip (default: 0)
            sort: Sort specification (e.g., "(id:asc),(name:desc)")
            
        Returns:
            FoldersList: List of folders with pagination info
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project()
            project_id = project["id"]
        
        params = {}
        
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
            
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/projects/{project_id}/folders",
            params=params
        )
        return FoldersList(**response)
    
    def create_folder(
        self,
        name: str,
        parent_resource_id: Optional[str] = None,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> FolderDetails:
        """
        Create a new folder.
        
        Args:
            name: Name for the new folder
            parent_resource_id: Parent folder resource ID (optional)
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            FolderDetails: Created folder details
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project()
            project_id = project["id"]
        
        folder_data = CreateFolder(name=name, parent_resource_id=parent_resource_id)
        
        response = self._client._request(
            "POST",
            f"/workspaces/{workspace_id}/projects/{project_id}/folders",
            json=folder_data.dict(exclude_none=True)
        )
        return FolderDetails(**response)
    
    def delete_folders(
        self,
        folder_ids: List[int],
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        check_dependency: bool = True,
        remove_contents: bool = True
    ) -> None:
        """
        Delete multiple folders.
        
        Args:
            folder_ids: List of folder IDs to delete
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            check_dependency: Check for dependency before deleting
            remove_contents: Remove folder contents before deleting
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project()
            project_id = project["id"]
        
        params = {
            "ids": ",".join(str(fid) for fid in folder_ids),
            "check_dependency": check_dependency,
            "remove_contents": remove_contents
        }
        
        self._client._request(
            "DELETE",
            f"/workspaces/{workspace_id}/projects/{project_id}/folders",
            params=params
        )
    
    def move_resources(
        self,
        resource_ids: List[str],
        target_folder_resource_id: Optional[str] = None,
        source_folder_resource_id: Optional[str] = None,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> ObjectJobSchema:
        """
        Move resources from/to folders.
        
        Args:
            resource_ids: List of resource IDs to move
            target_folder_resource_id: Target folder resource ID (None for root)
            source_folder_resource_id: Source folder resource ID (optional)
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            ObjectJobSchema: Job information for the move operation
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project()
            project_id = project["id"]
        
        move_request = BulkFolderPatchRequest(
            source_folder_resource_id=source_folder_resource_id,
            target_folder_resource_id=target_folder_resource_id,
            resource_ids=resource_ids,
            operation="move"
        )
        
        response = self._client._request(
            "PATCH",
            f"/workspaces/{workspace_id}/projects/{project_id}/folders",
            json=move_request.dict(exclude_none=True)
        )
        return ObjectJobSchema(**response)