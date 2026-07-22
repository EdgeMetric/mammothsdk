"""
Exports API client for managing dataview pipeline exports in Mammoth.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
    from ..client import MammothClient

from ..exceptions import MammothValidationError
from ..models.exports import (
    AddExportSpec,
    ExportStatus,
    HandlerType,
    OdbcType,
    PipelineExportsModificationResp,
    PipelineExportsPaginated,
    TriggerType,
)
from ..models.jobs import JobResponse
from .jobs import JobsAPI

ERR_DATAVIEW_ID_POSITIVE = "`dataview_id` must be a positive integer, got {0}."
ERR_EXPORT_ID_POSITIVE = "`export_id` must be a positive integer, got {0}."

_list = list  # Alias to avoid shadowing by method name


class ExportsAPI:
    """Client for interacting with Mammoth Exports API.

    Access via client.exports:
        exports = client.exports.list(dataview_id=456)
        client.exports.create(dataview_id=456, export_spec=spec, dataset_id=123)
        client.exports.to_csv(dataview_id=456, output_path="output.csv")
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client
        self._jobs_api = JobsAPI(client)

    def _find_dataset_for_dataview(self, dataview_id: int) -> int:
        """Find which dataset contains the specified dataview.

        Delegates to the public PipelineAPI.find_dataset_for_dataview to avoid
        duplicating the dataset-scanning logic.
        """
        return self._client.pipeline.find_dataset_for_dataview(dataview_id)

    def list(
        self,
        dataview_id: int,
        fields: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        sequence: int | None = None,
        status: ExportStatus | None = None,
        reordered: bool | None = None,
        handler_type: HandlerType | None = None,
        end_of_pipeline: bool | None = None,
        runnable: bool | None = None,
    ) -> PipelineExportsPaginated:
        """Get dataview pipeline exports with optional filtering and pagination.

        Args:
            dataview_id: ID of the dataview.
            fields: Fields to return.
            limit: Maximum number of results (0-100, default 50).
            offset: Number of results to skip (default 0).
            sort: Sort specification.
            sequence: Filter by sequence number.
            status: Filter by export status.
            reordered: Filter by reordered status.
            handler_type: Filter by handler type.
            end_of_pipeline: Filter by end of pipeline status.
            runnable: Filter by runnable status.

        Returns:
            PipelineExportsPaginated with paginated list of exports.
        """
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, "project_id", None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")

        dataset_id = self._find_dataset_for_dataview(dataview_id)
        params: dict[str, Any] = {}

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

        response = self._client._request_json(
            "GET",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/exports",
            params=params,
        )
        return PipelineExportsPaginated(**response)

    def create(
        self,
        dataview_id: int,
        export_spec: AddExportSpec,
        dataset_id: int | None = None,
        project_id: int | None = None,
    ) -> PipelineExportsModificationResp | JobResponse:
        """Add a new export to the dataview pipeline.

        Args:
            dataview_id: ID of the dataview.
            export_spec: Export specification.
            dataset_id: ID of the dataset (required).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            PipelineExportsModificationResp or JobResponse.
        """
        workspace_id = self._client.workspace_id
        if project_id is None:
            project_id = getattr(self._client, "project_id", None)
            if project_id is None:
                raise ValueError(
                    "project_id must be provided either to the method or set on the client"
                )

        if dataset_id is None:
            dataset_id = self._client.pipeline.find_dataset_for_dataview(dataview_id)

        response = self._client._request_json(
            "POST",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/exports",
            json=export_spec.model_dump(),
        )

        if "job" in response:
            return JobResponse(**response)
        return PipelineExportsModificationResp(**response)

    def get(
        self,
        dataview_id: int,
        export_id: int,
        fields: str | None = None,
        dataset_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get a single pipeline export.

        Args:
            dataview_id: ID of the dataview (must be > 0).
            export_id: ID of the export (must be > 0).
            fields: Comma-separated fields to return, or one of the presets
                ``"__full"``, ``"__standard"``, ``"__min"`` (optional).
            dataset_id: ID of the dataset (auto-detected if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with export details.

        Raises:
            MammothValidationError: If *dataview_id* or *export_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))
        if export_id <= 0:
            raise MammothValidationError(ERR_EXPORT_ID_POSITIVE.format(export_id))

        workspace_id = self._client.workspace_id
        if project_id is None:
            project_id = getattr(self._client, "project_id", None)
            if project_id is None:
                raise ValueError(
                    "project_id must be provided either to the method or set on the client"
                )
        if dataset_id is None:
            dataset_id = self._find_dataset_for_dataview(dataview_id)

        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields

        return self._client._request_json(
            "GET",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}"
            f"/dataviews/{dataview_id}/pipeline/exports/{export_id}",
            params=params or None,
        )

    def update(
        self,
        dataview_id: int,
        export_id: int,
        patches: _list[dict[str, Any]],
        skip_validation: bool | None = None,
        dataset_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Edit a pipeline export via patch operations.

        Args:
            dataview_id: ID of the dataview (must be > 0).
            export_id: ID of the export (must be > 0).
            patches: List of patch operation dicts, e.g.
                ``[{"op": "command", "path": "suspend", "value": None}]``.
            skip_validation: Skip server-side validation of the patch (optional).
            dataset_id: ID of the dataset (auto-detected if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with the updated export, or an empty dict if the server
            returns no content.

        Raises:
            MammothValidationError: If *dataview_id* or *export_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))
        if export_id <= 0:
            raise MammothValidationError(ERR_EXPORT_ID_POSITIVE.format(export_id))

        workspace_id = self._client.workspace_id
        if project_id is None:
            project_id = getattr(self._client, "project_id", None)
            if project_id is None:
                raise ValueError(
                    "project_id must be provided either to the method or set on the client"
                )
        if dataset_id is None:
            dataset_id = self._find_dataset_for_dataview(dataview_id)

        params: dict[str, Any] = {}
        if skip_validation is not None:
            params["skip_validation"] = skip_validation

        return self._client._request_json(
            "PATCH",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}"
            f"/dataviews/{dataview_id}/pipeline/exports/{export_id}",
            json={"patches": patches},
            params=params or None,
        )

    def delete(
        self,
        dataview_id: int,
        export_id: int,
        skip_validation: bool | None = None,
        dataset_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete a pipeline export.

        Args:
            dataview_id: ID of the dataview (must be > 0).
            export_id: ID of the export (must be > 0).
            skip_validation: Skip server-side validation of the deletion (optional).
            dataset_id: ID of the dataset (auto-detected if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with the deletion result, or an empty dict if the server
            returns no content.

        Raises:
            MammothValidationError: If *dataview_id* or *export_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))
        if export_id <= 0:
            raise MammothValidationError(ERR_EXPORT_ID_POSITIVE.format(export_id))

        workspace_id = self._client.workspace_id
        if project_id is None:
            project_id = getattr(self._client, "project_id", None)
            if project_id is None:
                raise ValueError(
                    "project_id must be provided either to the method or set on the client"
                )
        if dataset_id is None:
            dataset_id = self._find_dataset_for_dataview(dataview_id)

        params: dict[str, Any] = {}
        if skip_validation is not None:
            params["skip_validation"] = skip_validation

        return self._client._request_json(
            "DELETE",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}"
            f"/dataviews/{dataview_id}/pipeline/exports/{export_id}",
            params=params or None,
        )

    def publish_db(
        self,
        dataview_id: int,
        odbc_type: OdbcType,
        target_properties: dict[str, Any],
        dataset_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a publish-to-database subscription for a dataview.

        Args:
            dataview_id: ID of the dataview (must be > 0).
            odbc_type: Managed-connection type of the destination database.
            target_properties: Destination properties, e.g. ``{"table": "my_table"}``.
            dataset_id: ID of the dataset (auto-detected if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with the created publish-to-db job/result.

        Raises:
            MammothValidationError: If *dataview_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))

        workspace_id = self._client.workspace_id
        if project_id is None:
            project_id = getattr(self._client, "project_id", None)
            if project_id is None:
                raise ValueError(
                    "project_id must be provided either to the method or set on the client"
                )
        if dataset_id is None:
            dataset_id = self._find_dataset_for_dataview(dataview_id)

        body: dict[str, Any] = {
            "odbc_type": odbc_type.value,
            "target_properties": target_properties,
        }
        return self._client._request_json(
            "POST",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}"
            f"/dataviews/{dataview_id}/publish-to-db",
            json=body,
        )

    def publish_db_update(
        self,
        dataview_id: int,
        patch: _list[dict[str, Any]],
        dataset_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a dataview's publish-to-database subscription via patch operations.

        Args:
            dataview_id: ID of the dataview (must be > 0).
            patch: List of patch operation dicts, e.g.
                ``[{"op": "replace", "path": "credentials",
                "value": {"odbc_type": "postgres"}}]``.
            dataset_id: ID of the dataset (auto-detected if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with the updated publish-to-db job/result.

        Raises:
            MammothValidationError: If *dataview_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))

        workspace_id = self._client.workspace_id
        if project_id is None:
            project_id = getattr(self._client, "project_id", None)
            if project_id is None:
                raise ValueError(
                    "project_id must be provided either to the method or set on the client"
                )
        if dataset_id is None:
            dataset_id = self._find_dataset_for_dataview(dataview_id)

        return self._client._request_json(
            "PATCH",
            f"/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}"
            f"/dataviews/{dataview_id}/publish-to-db",
            json={"patch": patch},
        )

    def to_s3(
        self,
        dataview_id: int,
        file: str | None = None,
        file_type: str = "csv",
        include_hidden: bool = False,
        is_format_set: bool = True,
        use_format: bool = True,
        sequence: int | None = None,
        trigger_id: int | None = None,
        end_of_pipeline: bool = True,
        trigger_type: TriggerType = TriggerType.PIPELINE,
        condition: dict[str, Any] | None = None,
        run_immediately: bool = True,
        validate_only: bool = False,
        additional_properties: dict[str, Any] | None = None,
        dataset_id: int | None = None,
    ) -> PipelineExportsModificationResp | JobResponse | dict[str, Any]:
        """Create an S3 export with simplified parameters.

        Args:
            dataview_id: ID of the dataview.
            file: Output filename (auto-generated if not provided).
            file_type: File format type (default "csv").
            include_hidden: Include hidden columns (default False).
            is_format_set: Format explicitly set (default True).
            use_format: Apply formatting (default True).
            sequence: Position in pipeline.
            trigger_id: Trigger ID for editing existing export.
            end_of_pipeline: Execute at end of pipeline (default True).
            trigger_type: Type of trigger (default PIPELINE).
            condition: Export conditions.
            run_immediately: Execute immediately (default True).
            validate_only: Only validate config (default False).
            additional_properties: Additional configuration.
            dataset_id: ID of the dataset (auto-detected if not provided).

        Returns:
            Dict with URL and trigger_id if job completes.
        """
        from ..models.exports import S3TargetProperties

        project_id = getattr(self._client, "project_id", None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")

        if dataset_id is None:
            dataset_id = self._find_dataset_for_dataview(dataview_id)

        if file is None:
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file = f"dataview_{dataview_id}_export_{timestamp}.{file_type}"

        target_properties = S3TargetProperties(
            file=file,
            file_type=file_type,
            include_hidden=include_hidden,
            is_format_set=is_format_set,
            use_format=use_format,
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
            validate_only=validate_only,
        )

        export_result = self.create(dataview_id, export_spec, dataset_id, project_id)

        if isinstance(export_result, JobResponse) and export_result.job and export_result.job.id:
            job_id = export_result.job.id
            completed_job = self._jobs_api.wait_for_job(job_id, timeout=300)
            if completed_job.get("response", {}).get("url"):
                return {
                    "url": completed_job["response"]["url"],
                    "trigger_id": completed_job["response"].get("trigger_id"),
                }
            return completed_job

        return export_result

    def to_dataset(
        self,
        dataview_id: int,
        dataset_name: str,
        column_mapping: dict[str, Any] | None = None,
        sequence: int | None = None,
        trigger_id: int | None = None,
        end_of_pipeline: bool = True,
        trigger_type: TriggerType = TriggerType.PIPELINE,
        condition: dict[str, Any] | None = None,
        run_immediately: bool = True,
        validate_only: bool = False,
        additional_properties: dict[str, Any] | None = None,
    ) -> PipelineExportsModificationResp | JobResponse:
        """Create an internal dataset export.

        Args:
            dataview_id: ID of the dataview.
            dataset_name: Name for the created dataset.
            column_mapping: Column mapping configuration.
            sequence: Position in pipeline.
            trigger_id: Trigger ID for editing existing export.
            end_of_pipeline: Execute at end of pipeline (default True).
            trigger_type: Type of trigger (default PIPELINE).
            condition: Export conditions.
            run_immediately: Execute immediately (default True).
            validate_only: Only validate config (default False).
            additional_properties: Additional configuration.

        Returns:
            PipelineExportsModificationResp or JobResponse.
        """
        project_id = getattr(self._client, "project_id", None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")

        dataset_id = self._find_dataset_for_dataview(dataview_id)

        target_properties: dict[str, Any] = {"dataset_name": dataset_name}
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
            validate_only=validate_only,
        )

        return self.create(dataview_id, export_spec, dataset_id, project_id)

    def to_csv(
        self,
        dataview_id: int,
        output_path: str | Path | None = None,
        timeout: int = 300,
        dataset_id: int | None = None,
    ) -> Path:
        """Download dataview data as a CSV file.

        Creates a CSV export job, waits for completion, and downloads the result.

        Args:
            dataview_id: ID of the dataview to export.
            output_path: Path for the CSV file (auto-generated if not provided).
            timeout: Timeout in seconds (default 300).
            dataset_id: ID of the dataset (auto-detected if not provided).

        Returns:
            Path to the downloaded CSV file.
        """
        project_id = getattr(self._client, "project_id", None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")

        if dataset_id is None:
            dataset_id = self._find_dataset_for_dataview(dataview_id)

        if output_path is None:
            output_path = f"dataview_{dataset_id}_{dataview_id}_export.csv"

        output_path = Path(output_path)

        export_spec = AddExportSpec(
            DATAVIEW_ID=dataview_id,
            handler_type=HandlerType.S3,
            trigger_type=TriggerType.NONE,
            target_properties={
                "file": f"temp_export_{dataset_id}_{dataview_id}.csv",
                "file_type": "csv",
                "include_hidden": False,
                "is_format_set": True,
                "use_format": True,
            },
            additional_properties={},
            condition={},
            run_immediately=True,
            validate_only=False,
            end_of_pipeline=True,
        )

        export_result = self.create(dataview_id, export_spec, dataset_id)

        if isinstance(export_result, JobResponse) and export_result.job and export_result.job.id:
            job_id = export_result.job.id
            completed_job = self._jobs_api.wait_for_job(job_id, timeout)
            if completed_job.get("response", {}).get("url"):
                download_url = completed_job["response"]["url"]
                return self._download_file(download_url, output_path)
            raise ValueError(f"No download URL found in completed job {job_id}")
        raise ValueError("No job ID found in export result")

    def _download_file(self, url: str, output_path: Path) -> Path:
        """Download a file from the given URL.

        Args:
            url: URL to download from.
            output_path: Path where to save the file.

        Returns:
            Path to the downloaded file.
        """
        try:
            response = self._client.session.get(url, stream=True, timeout=self._client.timeout)
            response.raise_for_status()

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return output_path

        except requests.exceptions.RequestException as e:
            from ..exceptions import MammothAPIError

            raise MammothAPIError(f"Failed to download file: {e}") from e
        except OSError as e:
            from ..exceptions import MammothAPIError

            raise MammothAPIError(f"Failed to save file: {e}") from e
