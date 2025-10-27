"""
Dataviews API client for managing dataviews in Mammoth.
"""

from typing import Optional, Dict, Any, Union, List


class DataviewsAPI:
    """Client for interacting with Mammoth Dataviews API."""
    
    def __init__(self, client):
        self._client = client
    
    def list_dataviews(
        self,
        dataset_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        limit: int = 100,
        sort: str = "(created_at:desc)"
    ) -> Dict[str, Any]:
        """
        Get list of dataviews present in a dataset.
        
        Args:
            dataset_id: ID of the dataset
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            limit: Maximum number of results (default: 100)
            sort: Sort order (default: "(created_at:desc)")
            
        Returns:
            Dict containing dataviews list
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project(workspace_id=workspace_id)
            project_id = project['id']
            
        params = {
            "limit": limit,
            "sort": sort
        }
        
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews",
            params=params
        )
        return response
    
    def get_dataview(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get dataview information like id, row_count, column_count, metadata, taskwise info, status, etc.
        
        Args:
            dataset_id: ID of the dataset
            dataview_id: ID of the dataview
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            Dict: Complete dataview information
            
        Raises:
            ValueError: If dataview cannot be found
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project(workspace_id=workspace_id)
            project_id = project['id']
            
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}"
        )
        return response
    
    def create_dataview(
        self,
        dataset_id: int,
        name: Optional[str] = "View",
        clone_config_from: Optional[int] = None,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create or duplicate dataview.
        
        Args:
            dataset_id: ID of the dataset
            name: Name of the dataview (default: "View")
            clone_config_from: ID of dataview to clone config from (optional)
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            Dict: Created dataview information
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project(workspace_id=workspace_id)
            project_id = project['id']
        
        payload = {
            "name": name
        }
        
        if clone_config_from is not None:
            payload["clone_config_from"] = clone_config_from
            
        response = self._client._request(
            "POST",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews",
            json=payload
        )
        return response
    
    def update_dataview(
        self,
        dataset_id: int,
        dataview_id: int,
        patch_data: List[Dict[str, Any]],
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update dataview properties like rename a dataview, reset a dataview, or apply display properties.
        
        Args:
            dataset_id: ID of the dataset
            dataview_id: ID of the dataview to update
            patch_data: List of patch operations (max 1, min 1)
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            Dict: Update operation result
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project(workspace_id=workspace_id)
            project_id = project['id']
        
        payload = {"patch": patch_data}
            
        response = self._client._request(
            "PATCH",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}",
            json=payload
        )
        return response
    
    def delete_dataview(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Delete dataview safely.
        
        Args:
            dataset_id: ID of the dataset
            dataview_id: ID of the dataview to delete
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            Dict: Delete operation result
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project(workspace_id=workspace_id)
            project_id = project['id']
            
        response = self._client._request(
            "DELETE",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}"
        )
        return response
    
    def delete_dataviews(
        self,
        dataset_id: int,
        dataview_ids: Union[List[int], str],
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Delete multiple dataviews.
        
        Args:
            dataset_id: ID of the dataset
            dataview_ids: List of dataview IDs or comma-separated string
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            Dict: Bulk delete operation result
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project(workspace_id=workspace_id)
            project_id = project['id']
        
        # Convert list to comma-separated string if needed
        if isinstance(dataview_ids, list):
            ids_str = ",".join(str(id) for id in dataview_ids)
        else:
            ids_str = str(dataview_ids)
        
        params = {
            "ids": ids_str
        }
            
        response = self._client._request(
            "DELETE",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews",
            params=params
        )
        return response
    
    def get_dataview_data(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get dataview data (GET method).
        
        Args:
            dataset_id: ID of the dataset
            dataview_id: ID of the dataview
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            Dict: Dataview data
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project(workspace_id=workspace_id)
            project_id = project['id']
            
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/data"
        )
        return response
    
    def get_dataview_data_post(
        self,
        dataset_id: int,
        dataview_id: int,
        sequence: int = 0,
        offset: int = 1,
        limit: int = 400,
        columns: Optional[List[str]] = None,
        condition: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get dataview data with filtering options (POST method).
        
        Args:
            dataset_id: ID of the dataset
            dataview_id: ID of the dataview
            sequence: Step in pipeline at which to fetch data (default: 0)
            offset: One-indexed starting position of rows (default: 1)
            limit: Number of rows to fetch (default: 400)
            columns: List of column names to fetch (optional)
            condition: JSON condition for filtering rows (optional)
            sort: Sort specification as string (optional)
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            Dict: Filtered dataview data
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project(workspace_id=workspace_id)
            project_id = project['id']
        
        payload = {
            "sequence": sequence,
            "offset": offset,
            "limit": limit
        }
        
        if columns is not None:
            payload["columns"] = columns
        if condition is not None:
            payload["condition"] = condition
        if sort is not None:
            payload["sort"] = sort
            
        response = self._client._request(
            "POST",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/data",
            json=payload
        )
        return response
    
    def get_active_users(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get list of active users on this dataview.
        
        Args:
            dataset_id: ID of the dataset
            dataview_id: ID of the dataview
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            Dict: List of active users
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project(workspace_id=workspace_id)
            project_id = project['id']
            
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/activities"
        )
        return response
    
    def mark_active_user(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Mark active user on this dataview.
        
        Args:
            dataset_id: ID of the dataset
            dataview_id: ID of the dataview
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            Dict: Updated active users list
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project(workspace_id=workspace_id)
            project_id = project['id']
            
        response = self._client._request(
            "POST",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/activities"
        )
        return response