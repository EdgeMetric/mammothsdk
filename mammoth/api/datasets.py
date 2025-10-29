"""
Datasets API client for managing datasets in Mammoth.
"""

import time
from typing import Optional, Dict, Any


class DatasetsAPI:
    """Client for interacting with Mammoth Datasets API."""
    
    def __init__(self, client):
        self._client = client
    
    def list_datasets(
        self,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        limit: int = 100,
        sort: str = "(created_at:desc)"
    ) -> Dict[str, Any]:
        """
        Get list of datasets in a project.
        
        Args:
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            limit: Maximum number of results (default: 100)
            sort: Sort order (default: "(created_at:desc)")
            
        Returns:
            Dict containing datasets list with id, name and other dataset info
            
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
            "fields": "id,name",
            "limit": limit,
            "sort": sort
        }
        
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets",
            params=params
        )
        return response
    
    def get_dataset(
        self,
        dataset_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get dataset details by ID.
        
        Args:
            dataset_id: ID of the dataset
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            Dict: Complete dataset information
            
        Raises:
            ValueError: If dataset cannot be found
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
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}"
        )
        return response
    
    def get_dataset_data(
        self,
        dataset_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        timeout: int = 300,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Get the actual data from a dataset. This method polls the job until completion.
        
        Args:
            dataset_id: ID of the dataset
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            timeout: Maximum time to wait for job completion in seconds (default: 300)
            poll_interval: Time to wait between polling attempts in seconds (default: 2)
            
        Returns:
            Dict: Dataset data
            
        Raises:
            ValueError: If dataset cannot be found or job times out
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        if project_id is None:
            project = self._client.projects.get_project(workspace_id=workspace_id)
            project_id = project['id']
            
        # Start the data export job
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/data"
        )
        
        # If response contains job_id, poll for completion
        if isinstance(response, dict) and 'job_id' in response:
            job_id = response['job_id']
            
            # Wait for job completion using the jobs API with workspace_id
            completed_job = self._client.jobs.wait_for_job(
                job_id=job_id,
                workspace_id=workspace_id,
                timeout=timeout,
                poll_interval=poll_interval
            )
            
            # Return the job response data
            if 'response' in completed_job:
                return completed_job['response']
            else:
                return completed_job
        
        # If no job_id, return the response directly (synchronous response)
        return response
    
    def create_dataset(
        self,
        dataset_spec: Dict[str, Any],
        ds_creation_type: str,
        folder_resource_id: Optional[str] = None,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new dataset.
        
        Args:
            dataset_spec: Dataset specification (varies by creation type)
            ds_creation_type: Type of dataset creation ("clone", "cloud", "sketch", "weburl")
            folder_resource_id: Optional folder resource ID
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            Dict: Created dataset information
            
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
            "dataset_spec": dataset_spec,
            "ds_creation_type": ds_creation_type
        }
        
        if folder_resource_id is not None:
            payload["folder_resource_id"] = folder_resource_id
            
        response = self._client._request(
            "POST",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets",
            json=payload
        )
        return response
    
    def update_dataset(
        self,
        dataset_id: int,
        patch_data: Dict[str, Any],
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update a dataset.
        
        Args:
            dataset_id: ID of the dataset to update
            patch_data: Patch operation data
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
        Returns:
            Dict: Updated dataset information
            
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
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}",
            json=payload
        )
        return response
    
    def delete_dataset(
        self,
        dataset_id: int,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> None:
        """
        Delete a dataset.
        
        Args:
            dataset_id: ID of the dataset to delete
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
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
            
        self._client._request(
            "DELETE",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}"
        )
    
    def update_datasets(
        self,
        patch_data: Dict[str, Any],
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update multiple datasets (bulk operation).
        
        Args:
            patch_data: Patch operation data for multiple datasets
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
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets",
            json=payload
        )
        return response
    
    def delete_datasets(
        self,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> None:
        """
        Delete multiple datasets (bulk operation).
        
        Args:
            workspace_id: ID of the workspace (auto-detected if not provided)
            project_id: ID of the project (auto-detected if not provided)
            
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
            
        self._client._request(
            "DELETE",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets"
        )