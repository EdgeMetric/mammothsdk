"""
Files API client for managing files and datasets in Mammoth.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

if TYPE_CHECKING:
    from ..client import MammothClient

from ..models.files import (
    FileDetails,
    FilePatchData,
    FilePatchOperation,
    FilePatchPath,
    FilePatchRequest,
    FileSchema,
    FilesList,
)
from ..models.jobs import ObjectJobSchema

_list = list  # Alias to avoid shadowing by method name


class FilesAPI:
    """Client for interacting with Mammoth Files API.

    Access via client.files:
        files = client.files.list()
        file_info = client.files.get(file_id=123)
        ds_id = client.files.upload("data.csv")
        client.files.delete(123)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self) -> int:
        proj = getattr(self._client, "project_id", None)
        if proj is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        return proj

    def list(
        self,
        fields: str | None = None,
        file_ids: _list[int] | None = None,
        names: _list[str] | None = None,
        statuses: _list[str] | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> FilesList:
        """List files in a project with optional filtering and pagination.

        Args:
            fields: Fields to return (e.g., "__standard", "__full", "__min").
            file_ids: List of specific file IDs to retrieve.
            names: List of file names to filter by.
            statuses: List of statuses to filter by.
            created_at: Date range filter for creation date.
            updated_at: Date range filter for update date.
            limit: Maximum number of results (0-100, default 50).
            offset: Number of results to skip (default 0).
            sort: Sort specification (e.g., "(id:asc),(name:desc)").

        Returns:
            FilesList with files and pagination info.
        """
        ws = self._ws()
        proj = self._proj()
        params: dict[str, Any] = {}
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

        response = self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/files", params=params
        )
        return FilesList(**response)

    def get(
        self,
        file_id: int,
        fields: str | None = None,
    ) -> FileSchema:
        """Get detailed information about a specific file.

        Args:
            file_id: ID of the file.
            fields: Fields to return (default "__standard").

        Returns:
            FileSchema with detailed file information.
        """
        ws = self._ws()
        proj = self._proj()
        params: dict[str, Any] = {}
        if fields:
            params["fields"] = fields
        response = self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/files/{file_id}", params=params
        )
        file_details = FileDetails(**response)
        return file_details.file

    def upload(
        self,
        files: _list[str | Path | BinaryIO] | str | Path | BinaryIO | None = None,
        folder_resource_id: str | int | None = None,
        append_to_ds_id: int | None = None,
        override_target_schema: bool | None = None,
        wait_for_completion: bool = True,
        timeout: int = 300,
    ) -> _list[int] | int | None:
        """Upload one or more files to create datasets.

        Each file becomes a separate dataset. Folder structure is preserved.

        Args:
            files: File(s) to upload — file paths, Path objects, or file-like objects.
            folder_resource_id: Resource ID of target folder.
            append_to_ds_id: Dataset ID to append to (if appending).
            override_target_schema: Override target schema when appending.
            wait_for_completion: Wait for upload processing to complete.
            timeout: Timeout in seconds when waiting for completion.

        Returns:
            If wait_for_completion=False: Initial job ID.
            If wait_for_completion=True: List of dataset IDs (or single ID for one file).
        """
        ws = self._ws()
        proj = self._proj()

        if files is None:
            raise ValueError("files parameter is required")
        if not isinstance(files, _list):
            files = [files]

        file_data: _list[tuple[str, tuple[str, Any, str]]] = []
        opened_files: _list[Any] = []

        try:
            for file_input in files:
                if isinstance(file_input, (str, Path)):
                    file_path = Path(file_input)
                    if not file_path.exists():
                        raise ValueError(f"File not found: {file_path}")
                    file_obj = open(file_path, "rb")  # noqa: SIM115
                    opened_files.append(file_obj)
                    file_data.append(
                        ("files", (file_path.name, file_obj, "application/octet-stream"))
                    )
                else:
                    filename = getattr(file_input, "name", "uploaded_file")
                    if hasattr(filename, "split"):
                        filename = os.path.basename(filename)
                    file_data.append(("files", (filename, file_input, "application/octet-stream")))

            params: dict[str, Any] = {}
            if folder_resource_id:
                params["folder_resource_id"] = folder_resource_id
            if append_to_ds_id:
                params["append_to_ds_id"] = append_to_ds_id
            if override_target_schema is not None:
                params["override_target_schema"] = override_target_schema

            response = self._client._request_json(
                "POST",
                f"/workspaces/{ws}/projects/{proj}/files",
                params=params,
                files=file_data,
            )

        finally:
            for file_obj in opened_files:
                file_obj.close()

        initial_job_id = response.get("id")

        if not wait_for_completion:
            return initial_job_id

        if initial_job_id:
            completed_initial_job = self._client.jobs.wait_for_job(initial_job_id, timeout=timeout)
            job_response = completed_initial_job.get("response", {})
            nested_job_ids = job_response.get("job_ids", [])

            if not nested_job_ids:
                return None

            dataset_ids = []
            for job_info in nested_job_ids:
                nested_job_id = job_info.get("job_id")
                if nested_job_id:
                    completed_nested_job = self._client.jobs.wait_for_job(
                        nested_job_id, timeout=timeout
                    )
                    nested_response = completed_nested_job.get("response", {})
                    ds_id = nested_response.get("ds_id")
                    if ds_id:
                        dataset_ids.append(ds_id)

            if len(files) == 1:
                return dataset_ids[0] if dataset_ids else None
            return dataset_ids

        return None

    def upload_folder(
        self,
        folder_path: str | Path,
        folder_resource_id: str | None = None,
        wait_for_completion: bool = True,
        timeout: int = 300,
    ) -> _list[int] | int | None:
        """Upload all files in a folder to create datasets.

        Args:
            folder_path: Path to the folder containing files.
            folder_resource_id: Resource ID of target folder in Mammoth.
            wait_for_completion: Wait for upload processing to complete.
            timeout: Timeout in seconds when waiting for completion.

        Returns:
            List of dataset IDs (or single ID) if wait_for_completion=True.
        """
        folder_path = Path(folder_path)
        if not folder_path.exists() or not folder_path.is_dir():
            raise ValueError(f"Folder not found or not a directory: {folder_path}")

        files = [f for f in folder_path.iterdir() if f.is_file()]
        if not files:
            raise ValueError(f"No files found in folder: {folder_path}")

        return self.upload(
            files=files,
            folder_resource_id=folder_resource_id,
            wait_for_completion=wait_for_completion,
            timeout=timeout,
        )

    def delete(self, file_id: int) -> None:
        """Delete a specific file.

        Args:
            file_id: ID of the file to delete.
        """
        ws = self._ws()
        proj = self._proj()
        self._client._request_json("DELETE", f"/workspaces/{ws}/projects/{proj}/files/{file_id}")

    def bulk_delete(self, file_ids: _list[int]) -> None:
        """Delete multiple files.

        Args:
            file_ids: List of file IDs to delete.
        """
        ws = self._ws()
        proj = self._proj()
        params = {"ids": ",".join(str(fid) for fid in file_ids)}
        self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/files", params=params
        )

    def update(self, file_id: int, patch_request: FilePatchRequest) -> ObjectJobSchema:
        """Update file configuration (e.g., set password, extract sheets).

        Waits for the job to complete before returning.

        Args:
            file_id: ID of the file to update.
            patch_request: Configuration changes to apply.

        Returns:
            ObjectJobSchema with job information.
        """
        ws = self._ws()
        proj = self._proj()
        response = self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/files/{file_id}",
            json=patch_request.model_dump(),
        )
        self._client._wait_if_job(response)
        return ObjectJobSchema(**response)

    def set_password(self, file_id: int, password: str) -> ObjectJobSchema:
        """Set password for a password-protected file.

        Args:
            file_id: ID of the file.
            password: Password to set.

        Returns:
            ObjectJobSchema with job information.
        """
        patch_data = FilePatchData(
            op=FilePatchOperation.REPLACE,
            path=FilePatchPath.PASSWORD,
            value=password,
        )
        patch_request = FilePatchRequest(patch=[patch_data])
        return self.update(file_id, patch_request)

    def extract_sheets(
        self,
        file_id: int,
        sheets: _list[str],
        delete_file_after_extract: bool = True,
        combine_after_extract: bool = False,
    ) -> ObjectJobSchema:
        """Extract specific sheets from an Excel file.

        Args:
            file_id: ID of the Excel file.
            sheets: List of sheet names to extract.
            delete_file_after_extract: Delete main file after extraction.
            combine_after_extract: Combine sheets after extraction.

        Returns:
            ObjectJobSchema with job information.
        """
        from ..models.files import ExtractSheetsPatch

        extract_config = ExtractSheetsPatch(
            sheets=sheets,
            delete_file_after_extract=delete_file_after_extract,
            combine_after_extract=combine_after_extract,
        )
        patch_data = FilePatchData(
            op=FilePatchOperation.REPLACE,
            path=FilePatchPath.EXTRACT_SHEETS,
            value=extract_config,
        )
        patch_request = FilePatchRequest(patch=[patch_data])
        return self.update(file_id, patch_request)
