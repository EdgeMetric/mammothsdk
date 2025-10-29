"""
Exports API client for managing dataview pipeline exports in Mammoth.
"""

from typing import Optional, Union
from ..models.exports import (
    PipelineExportsPaginated, AddExportSpec, PipelineExportsModificationResp,
    HandlerType, TriggerType, ExportStatus
)
from ..models.jobs import JobResponse
from pathlib import Path
import requests
from .jobs import JobsAPI


class ExportsAPI:
    """Client for interacting with Mammoth Exports API."""
    
    def __init__(self, client):
        self._client = client
        self._jobs_api = JobsAPI(client)

    def _find_dataset_for_dataview(self, dataview_id: int) -> int:
        """
        Internal helper to find which dataset contains the specified dataview.
        
        Args:
            dataview_id: ID of the dataview to search for
            
        Returns:
            int: The dataset_id that contains this dataview
            
        Raises:
            ValueError: If dataview is not found in any dataset
        """
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, 'project_id', None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        
        # Get all datasets in the project
        datasets_response = self._client.datasets.list_datasets(
            workspace_id=workspace_id,
            project_id=project_id
        )
        
        # Search through each dataset's dataviews
        for dataset in datasets_response.get('datasets', []):
            dataset_id = dataset['id']
            try:
                # Get dataviews for this dataset
                dataviews_response = self._client.dataviews.list_dataviews(
                    dataset_id=dataset_id,
                    workspace_id=workspace_id,
                    project_id=project_id
                )
                
                # Check if our target dataview_id is in this dataset
                for dataview in dataviews_response.get('dataviews', []):
                    if dataview.get('id') == dataview_id:
                        return dataset_id
                        
            except Exception:
                # Skip datasets we can't access
                continue
        
        raise ValueError(f"Dataview {dataview_id} not found in any dataset in project {project_id}")
    
    
    def list_exports(
        self,
        dataview_id: int,
        fields: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort: Optional[str] = None,
        sequence: Optional[int] = None,
        status: Optional[ExportStatus] = None,
        reordered: Optional[bool] = None,
        handler_type: Optional[HandlerType] = None,
        end_of_pipeline: Optional[bool] = None,
        runnable: Optional[bool] = None
    ) -> PipelineExportsPaginated:
        """
        Get dataview pipeline exports information with optional filtering and pagination.
        
        Args:
            dataview_id: ID of the dataview
            fields: Fields to return (e.g., "__standard", "__full", "__min", or comma-separated)
            limit: Maximum number of results (0-100, default: 50)
            offset: Number of results to skip (default: 0)
            sort: Sort specification (e.g., "(id:asc),(name:desc)")
            sequence: Filter by sequence number
            status: Filter by export status
            reordered: Filter by reordered status
            handler_type: Filter by handler type
            end_of_pipeline: Filter by end of pipeline status
            runnable: Filter by runnable status
            
        Returns:
            PipelineExportsPaginated: Paginated list of exports
            
        Raises:
            MammothAPIError: If the API request fails
        """
        # Use client's workspace_id and project_id
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, 'project_id', None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        
        # Auto-detect dataset_id - completely internal
        dataset_id = self._find_dataset_for_dataview(dataview_id)
        params = {}
        
        if fields:
            params["fields"] = fields
        if limit != 50:
            params["limit"] = limit
        if offset != 0:
            params["offset"] = offset
        if sort:
            params["sort"] = sort
        if sequence is not None:
            params["sequence"] = sequence
        if status is not None:
            params["status"] = status.value
        if reordered is not None:
            params["reorderd"] = reordered  # Note: API uses "reorderd" (typo in API)
        if handler_type is not None:
            params["handler_type"] = handler_type.value
        if end_of_pipeline is not None:
            params["end_of_pipeline"] = end_of_pipeline
        if runnable is not None:
            params["runnable"] = runnable
            
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/exports",
            params=params
        )
        return PipelineExportsPaginated(**response)
    
    def add_export(
        self,
        dataview_id: int,
        export_spec: AddExportSpec,
        dataset_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Union[PipelineExportsModificationResp, JobResponse]:
        """
        Add a new export to the dataview pipeline.
        
        Args:
            dataview_id: ID of the dataview
            export_spec: Export specification defining the export configuration
            dataset_id: ID of the dataset (required for API call)
            project_id: ID of the project (uses client default if not provided)
            
        Returns:
            PipelineExportsModificationResp: If export is added/draft mode (201)
            JobResponse: If request succeeded and job is processing (202)
            
        Raises:
            MammothAPIError: If the API request fails
        """
        # Use client's workspace_id and project_id if not provided
        workspace_id = self._client.workspace_id
        if project_id is None:
            project_id = getattr(self._client, 'project_id', None)
            if project_id is None:
                raise ValueError("project_id must be provided either to the method or set on the client")
        
        if dataset_id is None:
            raise ValueError("dataset_id is required for adding exports")
        response = self._client._request(
            "POST",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/exports",
            json=export_spec.model_dump()
        )
        
        # Check if response contains job information (202 response)
        if "job" in response:
            return JobResponse(**response)
        else:
            # Assume it's a modification response (201)
            return PipelineExportsModificationResp(**response)
    
    def create_s3_export(
        self,
        dataview_id: int,
        file: Optional[str] = None,
        file_type: str = "csv",
        include_hidden: bool = False,
        is_format_set: bool = True,
        use_format: bool = True,
        sequence: Optional[int] = None,
        trigger_id: Optional[int] = None,
        end_of_pipeline: bool = True,
        trigger_type: TriggerType = TriggerType.PIPELINE,
        condition: Optional[dict] = None,
        run_immediately: bool = True,
        validate_only: bool = False,
        additional_properties: Optional[dict] = None,
        dataset_id: Optional[int] = None
    ) -> Union[PipelineExportsModificationResp, JobResponse, dict]:
        """
        Create an S3 export with simplified parameters.
        
        Args:
            dataview_id: ID of the dataview
            file: Output filename (default: auto-generated from dataview_id)
            file_type: File format type (default: "csv")
            include_hidden: Include hidden columns (default: False)
            is_format_set: Format explicitly set (default: True)
            use_format: Apply formatting (default: True)
            sequence: Position in pipeline (default: None - append to end)
            trigger_id: Trigger ID for editing existing export (default: None)
            end_of_pipeline: Execute at end of pipeline (default: True)
            trigger_type: Type of trigger (default: PIPELINE)
            condition: Export conditions (default: empty dict)
            run_immediately: Execute immediately (default: True)
            validate_only: Only validate config (default: False)
            additional_properties: Additional configuration (default: empty dict)
            dataset_id: ID of the dataset (optional, will auto-detect if not provided)
            
        Returns:
            Dict with URL and trigger_id if job completes, otherwise JobResponse
        """
        from ..models.exports import S3TargetProperties
        
        # Use client's workspace_id and project_id
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, 'project_id', None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        
        # Use provided dataset_id or auto-detect
        if dataset_id is None:
            dataset_id = self._find_dataset_for_dataview(dataview_id)
        
        # Generate default filename if not provided
        if file is None:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file = f"dataview_{dataview_id}_export_{timestamp}.{file_type}"
        
        target_properties = S3TargetProperties(
            file=file,
            file_type=file_type,
            include_hidden=include_hidden,
            is_format_set=is_format_set,
            use_format=use_format
        )
        
        export_spec = AddExportSpec(
            DATAVIEW_ID=dataview_id,
            sequence=sequence,
            TRIGGER_ID=trigger_id,
            end_of_pipeline=end_of_pipeline,
            handler_type=HandlerType.S3,
            trigger_type=trigger_type,
            target_properties=target_properties,
            additional_properties=additional_properties or {},
            condition=condition or {},
            run_immediately=run_immediately,
            validate_only=validate_only
        )
        
        export_result = self.add_export(dataview_id, export_spec, dataset_id, project_id)
        
        # Wait for job completion 
        if hasattr(export_result, 'job') and export_result.job and export_result.job.id:
            job_id = export_result.job.id
            print(f"Waiting for export job {job_id} to complete...")
            
            # Wait for job completion
            completed_job = self._jobs_api.wait_for_job(job_id, timeout=300)
            
            # Extract URL and trigger ID from completed job
            if completed_job.get('response', {}).get('url'):
                return {'url': completed_job['response']['url'], 'trigger_id': completed_job['response'].get('trigger_id')}
            
            return completed_job
        
        return export_result
    
    def create_internal_dataset_export(
        self,
        dataview_id: int,
        dataset_name: str,
        column_mapping: Optional[dict] = None,
        sequence: Optional[int] = None,
        trigger_id: Optional[int] = None,
        end_of_pipeline: bool = True,
        trigger_type: TriggerType = TriggerType.PIPELINE,
        condition: Optional[dict] = None,
        run_immediately: bool = True,
        validate_only: bool = False,
        additional_properties: Optional[dict] = None
    ) -> Union[PipelineExportsModificationResp, JobResponse]:
        """
        Create an internal dataset export with simplified parameters.
        
        Args:
            dataview_id: ID of the dataview
            dataset_name: Name for the created dataset
            dataset_id: ID of the dataset (required for API call)
            project_id: ID of the project (uses client default if not provided)
            column_mapping: Column mapping configuration (default: None)
            sequence: Position in pipeline (default: None - append to end)
            trigger_id: Trigger ID for editing existing export (default: None)
            end_of_pipeline: Execute at end of pipeline (default: True)
            trigger_type: Type of trigger (default: PIPELINE)
            condition: Export conditions (default: empty dict)
            run_immediately: Execute immediately (default: True)
            validate_only: Only validate config (default: False)
            additional_properties: Additional configuration (default: empty dict)
            
        Returns:
            PipelineExportsModificationResp or JobResponse: Result of the operation
        """
        # Use client's workspace_id and project_id
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, 'project_id', None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        
        # Auto-detect dataset_id - completely internal
        dataset_id = self._find_dataset_for_dataview(dataview_id)
        
        target_properties = {
            "dataset_name": dataset_name
        }
        if column_mapping:
            target_properties["COLUMN_MAPPING"] = column_mapping
        
        export_spec = AddExportSpec(
            DATAVIEW_ID=dataview_id,
            sequence=sequence,
            TRIGGER_ID=trigger_id,
            end_of_pipeline=end_of_pipeline,
            handler_type=HandlerType.INTERNAL_DATASET,
            trigger_type=trigger_type,
            target_properties=target_properties,
            additional_properties=additional_properties or {},
            condition=condition or {},
            run_immediately=run_immediately,
            validate_only=validate_only
        )
        
        return self.add_export(dataview_id, export_spec, dataset_id, project_id)

    def download_dataview_csv(
        self,
        dataview_id: int,
        output_path: Optional[Union[str, Path]] = None,
        timeout: int = 300,
        dataset_id: Optional[int] = None
    ) -> Path:
        """
        Download dataview data as a CSV file.
        
        This utility function creates a CSV export job, waits for completion, 
        and downloads the resulting CSV file from the provided URL.
        
        Args:
            dataview_id: ID of the dataview to export
            output_path: Path where to save the CSV file. If None, uses a default name
            timeout: Timeout in seconds to wait for export completion (default: 300)
            dataset_id: ID of the dataset (optional, will auto-detect if not provided)
            
        Returns:
            Path: Path to the downloaded CSV file
            
        Raises:
            MammothAPIError: If the API request fails
            MammothJobTimeoutError: If export job times out
            MammothJobFailedError: If export job fails
            ValueError: If dataview is not found or client configuration is missing
        """
        project_id = getattr(self._client, 'project_id', None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        
        # Use provided dataset_id or auto-detect
        if dataset_id is None:
            dataset_id = self._find_dataset_for_dataview(dataview_id)
        # Determine output file path
        if output_path is None:
            output_path = f"dataview_{dataset_id}_{dataview_id}_export.csv"
        
        output_path = Path(output_path)
        
        # Create export job using the existing add_export method
        export_spec = AddExportSpec(
            DATAVIEW_ID=dataview_id,
            handler_type=HandlerType.S3,
            trigger_type=TriggerType.NONE,
            target_properties={
                "file": f"temp_export_{dataset_id}_{dataview_id}.csv",
                "file_type": "csv",
                "include_hidden": False,
                "is_format_set": True,
                "use_format": True
            },
            additional_properties={},
            condition={},
            run_immediately=True,
            validate_only=False,
            end_of_pipeline=True
        )
        
        # Create the export job
        export_result = self.add_export(dataview_id, export_spec, dataset_id)
        
        # Wait for job completion and download the file
        if hasattr(export_result, 'job') and export_result.job and export_result.job.id:
            job_id = export_result.job.id
            print(f"Waiting for export job {job_id} to complete...")
            
            # Wait for job completion
            completed_job = self._jobs_api.wait_for_job(job_id, timeout)
            
            # Extract download URL from completed job
            if completed_job.get('response', {}).get('url'):
                download_url = completed_job['response']['url']
                print(f"Download URL: {download_url}")
                
                # Download the file
                downloaded_file = self._download_file(download_url, output_path)
                return downloaded_file
            else:
                raise ValueError(f"No download URL found in completed job {job_id}")
        else:
            raise ValueError("No job ID found in export result")

    
    def _download_file(self, url: str, output_path: Path) -> Path:
        """
        Download a file from the given URL.
        
        Args:
            url: URL to download from
            output_path: Path where to save the file
            
        Returns:
            str: Path to the downloaded file
            
        Raises:
            MammothAPIError: If download fails
        """
        try:
            # Use the client's session to maintain authentication if needed
            response = self._client.session.get(url, stream=True, timeout=self._client.timeout)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file in chunks
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return output_path
            
        except requests.exceptions.RequestException as e:
            from ..exceptions import MammothAPIError
            raise MammothAPIError(f"Failed to download file: {str(e)}")
        except IOError as e:
            from ..exceptions import MammothAPIError
            raise MammothAPIError(f"Failed to save file: {str(e)}")
