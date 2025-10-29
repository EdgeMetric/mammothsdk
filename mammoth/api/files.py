"""
Files API client for managing files and datasets in Mammoth.
"""

import os
from pathlib import Path
from typing import List, Optional, Union, BinaryIO
from ..models.files import (
    FilesList, FileDetails, FileSchema, FilePatchRequest, 
    FilePatchData, FilePatchOperation, FilePatchPath
)
from ..models.jobs import ObjectJobSchema


class FilesAPI:
    """Client for interacting with Mammoth Files API."""
    
    def __init__(self, client):
        self._client = client
    
    def list_files(
        self,
        fields: Optional[str] = None,
        file_ids: Optional[List[int]] = None,
        names: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort: Optional[str] = None
    ) -> FilesList:
        """
        List files in a project with optional filtering and pagination.
        
        Args:
            fields: Fields to return (e.g., "__standard", "__full", "__min", or comma-separated)
            file_ids: List of specific file IDs to retrieve
            names: List of file names to filter by
            statuses: List of statuses to filter by
            created_at: Date range filter for creation date (format: "(from:'YYYY-MM-DDTHH:MM:SSZ',to:'YYYY-MM-DDTHH:MM:SSZ')")
            updated_at: Date range filter for update date  
            limit: Maximum number of results (0-100, default: 50)
            offset: Number of results to skip (default: 0)
            sort: Sort specification (e.g., "(id:asc),(name:desc)")
            
        Returns:
            FilesList: List of files with pagination info
            
        Raises:
            MammothAPIError: If the API request fails
        """
        # Use client's workspace_id and project_id
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, 'project_id', None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        params = {}
        
        if fields:
            params["fields"] = fields
        if file_ids:
            params["id"] = ",".join(str(fid) for fid in file_ids)
        if names:
            params["name"] = ",".join(names)
        if statuses:
            params["status"] = ",".join(statuses)
        if created_at:
            params["created_at"] = created_at
        if updated_at:
            params["updated_at"] = updated_at
        if limit != 50:
            params["limit"] = limit
        if offset != 0:
            params["offset"] = offset
        if sort:
            params["sort"] = sort
            
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/projects/{project_id}/files",
            params=params
        )
        return FilesList(**response)
    
    def get_file_details(
        self,
        file_id: int,
        fields: Optional[str] = None
    ) -> FileSchema:
        """
        Get detailed information about a specific file.
        
        Args:
            file_id: ID of the file
            fields: Fields to return (default: "__standard")
            
        Returns:
            FileSchema: Detailed file information
            
        Raises:
            MammothAPIError: If the API request fails
        """
        # Use client's workspace_id and project_id
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, 'project_id', None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        params = {}
        if fields:
            params["fields"] = fields
            
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/projects/{project_id}/files/{file_id}",
            params=params
        )
        file_details = FileDetails(**response)
        return file_details.file
    
    def upload_files(
        self,
        files: Union[List[Union[str, Path, BinaryIO]], str, Path, BinaryIO] = None,
        folder_resource_id: Optional[str] = None,
        append_to_ds_id: Optional[int] = None,
        override_target_schema: Optional[bool] = None,
        wait_for_completion: bool = True,
        timeout: int = 300
    ) -> Union[List[int], int, None]:
        """
        Upload one or more files to create datasets. Each file will be treated as a
        separate dataset. If the file path contains a folder structure, that structure
        will be preserved, and the files will be placed in their respective folders.
        
        Args:
            files: File(s) to upload - can be file paths, Path objects, or file-like objects
            folder_resource_id: Resource ID of target folder. This is the resource ID of the Mammoth folder
            append_to_ds_id: Dataset ID to append to (if appending to existing dataset)
            override_target_schema: Whether to override target schema when appending
            wait_for_completion: Whether to wait for upload processing to complete
            timeout: Timeout in seconds when waiting for completion
            
        Returns:
            If wait_for_completion=False: Initial job ID for tracking
            If wait_for_completion=True: List of dataset IDs if multiple files uploaded, 
            single dataset ID if one file, or None if no datasets created
            
        Raises:
            MammothAPIError: If the API request fails
            ValueError: If job processing times out or fails
        """
        # Use client's workspace_id and project_id
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, 'project_id', None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        
        if files is None:
            raise ValueError("files parameter is required")
        # Normalize files to list
        if not isinstance(files, list):
            files = [files]
        
        # Prepare files for upload
        file_data = []
        opened_files = []
        
        try:
            for file_input in files:
                if isinstance(file_input, (str, Path)):
                    file_path = Path(file_input)
                    if not file_path.exists():
                        raise ValueError(f"File not found: {file_path}")
                    file_obj = open(file_path, 'rb')
                    opened_files.append(file_obj)
                    file_data.append(('files', (file_path.name, file_obj, 'application/octet-stream')))
                else:
                    # Assume it's a file-like object
                    filename = getattr(file_input, 'name', 'uploaded_file')
                    if hasattr(filename, 'split'):
                        filename = os.path.basename(filename)
                    file_data.append(('files', (filename, file_input, 'application/octet-stream')))
            
            # Prepare parameters
            params = {}
            if folder_resource_id:
                params["folder_resource_id"] = folder_resource_id
            if append_to_ds_id:
                params["append_to_ds_id"] = append_to_ds_id
            if override_target_schema is not None:
                params["override_target_schema"] = override_target_schema
            
            # Make upload request
            response = self._client._request(
                "POST",
                f"/workspaces/{workspace_id}/projects/{project_id}/files",
                params=params,
                files=file_data
            )
            
        finally:
            # Clean up opened files
            for file_obj in opened_files:
                file_obj.close()
        
        # Parse the new async job response format
        # Response format: {"id": 19264, "status": "processing", "response": {}, ...}
        initial_job_id = response.get("id")
        
        if not wait_for_completion:
            return initial_job_id
        
        # Wait for initial job to complete
        if initial_job_id:
            # Step 1: Wait for the initial validation/upload job
            completed_initial_job = self._client.jobs.wait_for_job(initial_job_id, timeout=timeout)
            
            # Step 2: Extract nested job_ids from the response
            # Format: {"response": {"job_ids": [{"job_id": 19265}]}}
            job_response = completed_initial_job.get('response', {})
            nested_job_ids = job_response.get('job_ids', [])
            
            if not nested_job_ids:
                return None
            
            # Step 3: Wait for the nested jobs (actual file processing) to complete
            dataset_ids = []
            for job_info in nested_job_ids:
                nested_job_id = job_info.get('job_id')
                if nested_job_id:
                    completed_nested_job = self._client.jobs.wait_for_job(nested_job_id, timeout=timeout)
                    
                    # Extract ds_id from the nested job response
                    # Format: {"response": {"ds_id": 1569, "status": "ready"}}
                    nested_response = completed_nested_job.get('response', {})
                    ds_id = nested_response.get('ds_id')
                    if ds_id:
                        dataset_ids.append(ds_id)
            
            # Return single dataset ID for single file, list for multiple files
            if len(files) == 1:
                return dataset_ids[0] if dataset_ids else None
            return dataset_ids
        
        return None
    
    def upload_folder(
        self,
        folder_path: Union[str, Path],
        folder_resource_id: Optional[str] = None,
        wait_for_completion: bool = True,
        timeout: int = 300
    ) -> Union[List[int], int, None]:
        """
        Upload all files in a folder to create datasets.
        
        Args:
            folder_path: Path to the folder containing files to upload
            folder_resource_id: Resource ID of target folder in Mammoth
            wait_for_completion: Whether to wait for upload processing to complete
            timeout: Timeout in seconds when waiting for completion
            
        Returns:
            If wait_for_completion=False: Initial job ID for tracking
            If wait_for_completion=True: List of dataset IDs
            
        Raises:
            MammothAPIError: If the API request fails
            ValueError: If folder doesn't exist or contains no files
        """
        folder_path = Path(folder_path)
        if not folder_path.exists() or not folder_path.is_dir():
            raise ValueError(f"Folder not found or not a directory: {folder_path}")
        
        # Find all files in the folder (non-recursive for now)
        files = [f for f in folder_path.iterdir() if f.is_file()]
        if not files:
            raise ValueError(f"No files found in folder: {folder_path}")
        
        # Use the existing upload_files method
        return self.upload_files(
            files=files,
            folder_resource_id=folder_resource_id,
            wait_for_completion=wait_for_completion,
            timeout=timeout
        )
    
    def delete_file(
        self,
        file_id: int
    ) -> None:
        """
        Delete a specific file.
        
        Args:
            file_id: ID of the file to delete
            
        Raises:
            MammothAPIError: If the API request fails
        """
        # Use client's workspace_id and project_id
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, 'project_id', None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        self._client._request(
            "DELETE",
            f"/workspaces/{workspace_id}/projects/{project_id}/files/{file_id}"
        )
    
    def delete_files(
        self,
        file_ids: List[int]
    ) -> None:
        """
        Delete multiple files.
        
        Args:
            file_ids: List of file IDs to delete
            
        Raises:
            MammothAPIError: If the API request fails
        """
        # Use client's workspace_id and project_id
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, 'project_id', None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        params = {"ids": ",".join(str(fid) for fid in file_ids)}
        self._client._request(
            "DELETE",
            f"/workspaces/{workspace_id}/projects/{project_id}/files",
            params=params
        )
    
    def update_file_config(
        self,
        file_id: int,
        patch_request: FilePatchRequest
    ) -> ObjectJobSchema:
        """
        Update file configuration (e.g., set password, extract sheets).
        
        Args:
            file_id: ID of the file to update
            patch_request: Configuration changes to apply
            
        Returns:
            ObjectJobSchema: Job information for the update operation
            
        Raises:
            MammothAPIError: If the API request fails
        """
        # Use client's workspace_id and project_id
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, 'project_id', None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        response = self._client._request(
            "PATCH",
            f"/workspaces/{workspace_id}/projects/{project_id}/files/{file_id}",
            json=patch_request.model_dump()
        )
        return ObjectJobSchema(**response)
    
    def set_file_password(
        self,
        file_id: int,
        password: str
    ) -> ObjectJobSchema:
        """
        Set password for a password-protected file.
        
        Args:
            file_id: ID of the file
            password: Password to set
            
        Returns:
            ObjectJobSchema: Job information for the update operation
        """
        patch_data = FilePatchData(
            op=FilePatchOperation.REPLACE,
            path=FilePatchPath.PASSWORD,
            value=password
        )
        patch_request = FilePatchRequest(patch=[patch_data])
        return self.update_file_config(file_id, patch_request)
    
    def extract_sheets(
        self,
        file_id: int,
        sheets: List[str],
        delete_file_after_extract: bool = True,
        combine_after_extract: bool = False
    ) -> ObjectJobSchema:
        """
        Extract specific sheets from an Excel file.
        
        Args:
            file_id: ID of the Excel file
            sheets: List of sheet names to extract
            delete_file_after_extract: Whether to delete main file after extraction
            combine_after_extract: Whether to combine sheets after extraction
            
        Returns:
            ObjectJobSchema: Job information for the extraction operation
        """
        from ..models.files import ExtractSheetsPatch
        
        extract_config = ExtractSheetsPatch(
            sheets=sheets,
            delete_file_after_extract=delete_file_after_extract,
            combine_after_extract=combine_after_extract
        )
        
        patch_data = FilePatchData(
            op=FilePatchOperation.REPLACE,
            path=FilePatchPath.EXTRACT_SHEETS,
            value=extract_config
        )
        patch_request = FilePatchRequest(patch=[patch_data])
        return self.update_file_config(file_id, patch_request)
