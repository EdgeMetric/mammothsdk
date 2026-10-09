"""
Files API client for managing files and datasets in Mammoth.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

if TYPE_CHECKING:
    from ..client import MammothClient

from ..exceptions import MammothValidationError
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

    async def list(
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

        response = await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/files", params=params
        )
        return FilesList(**response)

    async def get(
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
        response = await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/files/{file_id}", params=params
        )
        file_details = FileDetails(**response)
        return file_details.file

    async def upload(
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

        Raises:
            MammothValidationError: The server refused files (``errors`` on the
                upload job, e.g. ``unsupported_files``) and no dataset was made.
        """
        outcome = await self.upload_result(
            files,
            folder_resource_id=folder_resource_id,
            append_to_ds_id=append_to_ds_id,
            override_target_schema=override_target_schema,
            wait_for_completion=wait_for_completion,
            timeout=timeout,
        )
        if not wait_for_completion:
            return outcome["job_id"]
        dataset_ids: _list[int] = outcome["dataset_ids"]
        errors: dict[str, Any] = outcome["errors"]
        if errors and not dataset_ids:
            raise MammothValidationError(
                f"The server refused the upload and created no dataset: {errors}",
                details={"errors": errors},
            )
        if not outcome["job_id"] or not outcome["nested_job_ids"]:
            return None
        if not isinstance(files, _list) or len(files) == 1:
            return dataset_ids[0] if dataset_ids else None
        return dataset_ids

    async def upload_result(
        self,
        files: _list[str | Path | BinaryIO] | str | Path | BinaryIO | None = None,
        folder_resource_id: str | int | None = None,
        append_to_ds_id: int | None = None,
        override_target_schema: bool | None = None,
        wait_for_completion: bool = True,
        timeout: int = 300,
    ) -> dict[str, Any]:
        """Upload files and report the created datasets AND any server refusals.

        Like :meth:`upload`, but returns ``{"job_id", "dataset_ids", "errors", "nested_job_ids"}``.
        ``errors`` is the upload job's own ``errors`` map (for example
        ``{"unsupported_files": ["X.pbix"]}``), empty when nothing was refused.

        Each file becomes a separate dataset. Folder structure is preserved.

        Args:
            files: File(s) to upload — file paths, Path objects, or file-like objects.
            folder_resource_id: Resource ID of target folder.
            append_to_ds_id: Dataset ID to append to (if appending).
            override_target_schema: Override target schema when appending.
            wait_for_completion: Wait for upload processing to complete.
            timeout: Timeout in seconds when waiting for completion.

        Returns:
            ``job_id`` is the initial job; with wait_for_completion=False the
            other two are empty.
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

            response = await self._client._request_json(
                "POST",
                f"/workspaces/{ws}/projects/{proj}/files",
                params=params,
                files=file_data,
            )

        finally:
            for file_obj in opened_files:
                file_obj.close()

        initial_job_id = response.get("id")

        outcome: dict[str, Any] = {
            "job_id": initial_job_id,
            "dataset_ids": [],
            "errors": {},
            "nested_job_ids": [],
        }
        if not wait_for_completion:
            return outcome

        if initial_job_id:
            completed_initial_job = await self._client.jobs.wait_for_job(
                initial_job_id, timeout=timeout
            )
            job_response = completed_initial_job.get("response", {})
            errors = job_response.get("errors")
            outcome["errors"] = errors if isinstance(errors, dict) else {}
            nested_job_ids = job_response.get("job_ids", [])

            if not nested_job_ids:
                return outcome

            outcome["nested_job_ids"] = nested_job_ids
            nested = [job_info["job_id"] for job_info in nested_job_ids if job_info.get("job_id")]
            # One batched poll for every nested job, not one poll loop per file.
            finished = (
                await self._client.jobs.wait_for_jobs(nested, timeout=timeout) if nested else {}
            )
            outcome["dataset_ids"] = [
                ds_id
                for job in finished.get("jobs", [])
                if (ds_id := (job.get("response") or {}).get("ds_id"))
            ]

        return outcome

    async def upload_folder(
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

        files: _list[str | Path | BinaryIO] = [f for f in folder_path.iterdir() if f.is_file()]
        if not files:
            raise ValueError(f"No files found in folder: {folder_path}")

        return await self.upload(
            files=files,
            folder_resource_id=folder_resource_id,
            wait_for_completion=wait_for_completion,
            timeout=timeout,
        )

    async def delete(self, file_id: int) -> None:
        """Delete a specific file.

        Args:
            file_id: ID of the file to delete.
        """
        ws = self._ws()
        proj = self._proj()
        await self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/files/{file_id}"
        )

    async def bulk_delete(self, file_ids: _list[int]) -> None:
        """Delete multiple files.

        Args:
            file_ids: List of file IDs to delete.
        """
        ws = self._ws()
        proj = self._proj()
        params = {"ids": ",".join(str(fid) for fid in file_ids)}
        await self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/files", params=params
        )

    async def update(self, file_id: int, patch_request: FilePatchRequest) -> ObjectJobSchema:
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
        response = await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/files/{file_id}",
            json=patch_request.model_dump(),
        )
        # Wait for the kicked-off job, then build the result from the completed
        # payload so a terminal ``status_code``/``failure_reason`` is surfaced
        # rather than the enqueue-time handle. The original response is kept as a
        # base so ``job_id`` survives when the completed payload omits it.
        completed = await self._client._wait_if_job(response)
        merged = {**response, **completed} if isinstance(completed, dict) else response
        return ObjectJobSchema(**merged)

    async def set_password(self, file_id: int, password: str) -> ObjectJobSchema:
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
        return await self.update(file_id, patch_request)

    async def extract_sheets(
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
        return await self.update(file_id, patch_request)

    async def preview_multi_sheet(
        self,
        file_id: int,
        sheet_name: str,
        block_id: str | None = None,
        user_instruction: str | None = None,
        structure_map: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Preview how one sheet of a multi-sheet file reads, before any dataset exists.

        Args:
            file_id: ID of the file.
            sheet_name: The sheet to preview, exactly as it is named in the workbook.
            block_id: Which detected block to resolve, on a multi-table sheet.
            user_instruction: Plain-English description of how to read the sheet
                or block. Omitted: the detected header row and its data.
            structure_map: A structure map already known to be correct; skips the
                LLM call.

        Returns:
            Dict with the sheet's read preview.
        """
        ws = self._ws()
        proj = self._proj()
        body: dict[str, Any] = {
            "sheet_name": sheet_name,
            "block_id": block_id,
            "user_instruction": user_instruction,
            "structure_map": structure_map,
        }
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/files/{file_id}/sheets/interpretation/preview",
            json={name: value for name, value in body.items() if value is not None},
        )

    async def create_datasets_from_multi_sheet(
        self,
        file_id: int,
        tables: _list[dict[str, Any]],
        delete_file_after_extract: bool = True,
    ) -> ObjectJobSchema:
        """Create datasets from accepted sheet and table reads of a multi-sheet file.

        Args:
            file_id: ID of the file.
            tables: Every accepted sheet/block read to create datasets from (1 to 100),
                each with ``sheet_name``, ``dataset_name`` and ``structure_map``.
            delete_file_after_extract: Delete the file once its datasets are created.

        Returns:
            ObjectJobSchema with job information, after the job completes.
        """
        ws = self._ws()
        proj = self._proj()
        body = {"tables": tables, "delete_file_after_extract": delete_file_after_extract}
        response = await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/files/{file_id}/multi-sheet-extraction",
            json=body,
        )
        completed = await self._client._wait_if_job(response)
        merged = {**response, **completed} if isinstance(completed, dict) else response
        return ObjectJobSchema(**merged)
