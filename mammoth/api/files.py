"""
Files API client for managing files and datasets in Mammoth.
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

if TYPE_CHECKING:
    from ..client import MammothClient

from ..exceptions import MammothAPIError, MammothValidationError
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

#: The project resource type of an uploaded file.
_FILE_RESOURCE = "file_object"
#: File statuses that mean the file is done with (its dataset was made).
_FINISHED_FILE_STATUSES = frozenset({"processed", "extracted"})
#: File statuses of a file still being read, before it says what it waits on.
_BUSY_FILE_STATUSES = frozenset({"processing", "extracting"})
#: How long to wait for a file to say what it waits on, and how often to look.
_SETTLE_S = 60.0
_SETTLE_POLL_S = 1.0
#: How many of the project's newest files to read for an upload's own.
_NEWEST_FILES = 50
#: Allowance for the gap between this machine's clock and the server's.
_CLOCK_SKEW = timedelta(minutes=5)


def _created_at(stamp: Any) -> datetime | None:
    """Read a resource's ``created_at`` (naive UTC, sometimes with a ``Z``) as UTC."""
    try:
        read = datetime.fromisoformat(str(stamp).removesuffix("Z"))
    except ValueError:
        return None
    return read if read.tzinfo else read.replace(tzinfo=UTC)


def _waiting_file(item: dict[str, Any]) -> dict[str, Any]:
    """One uploaded file and what it waits on, from its project resource row."""
    properties = item.get("object_properties")
    action = properties.get("user_action_required") if isinstance(properties, dict) else None
    entry: dict[str, Any] = {
        "file_id": item.get("object_id"),
        "name": item.get("name"),
        "status": item.get("status"),
        "action_needed": None,
    }
    if isinstance(action, dict):
        entry["action_needed"] = action.get("type")
        if action.get("message"):
            entry["message"] = action["message"]
        if isinstance(action.get("sheet_info"), _list):
            entry["sheets_info"] = action["sheet_info"]
    return entry


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

        Like :meth:`upload`, but returns ``{"job_id", "dataset_ids", "errors", "nested_job_ids",
        "files"}`` (plus ``files_error`` when the project's file list could not be read).
        ``errors`` is the upload job's own ``errors`` map (for example
        ``{"unsupported_files": ["X.pbix"]}``), empty when nothing was refused. ``files``
        lists each uploaded file that made no dataset and what it waits on:
        ``{"file_id", "name", "status", "action_needed"}``, where ``action_needed`` is
        Mammoth's own ``user_action_required`` type (``sheet_selection_required`` with
        ``sheets_info`` for a workbook, ``password_required``, ...) or ``None``.

        A file is matched to this upload by its name
        among the project's 50 newest files, made no earlier than 5 minutes before the
        upload was sent: the file listing carries no job or batch id (only ``created_by``,
        a user name). A same-named file uploaded within those 5 minutes can be taken for
        this one, and a file pushed out by more than 50 newer ones is not found. When the
        listing could not be read, ``files`` stays empty and ``files_error`` holds the
        message.

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
            other fields are empty.
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

            sent_at = datetime.now(UTC)
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
            "files": [],
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
            if len(outcome["dataset_ids"]) < len(nested):
                # A file that stops for the user (a workbook's sheets, a password)
                # ends its job with no ``ds_id`` and no file id: the project's
                # resource list is where it says what it waits on.
                try:
                    outcome["files"] = await self._waiting_files(
                        [part[0] for _, part in file_data],
                        sent_at,
                        min(float(timeout), _SETTLE_S),
                    )
                except MammothAPIError as exc:
                    outcome["files_error"] = str(exc)

        return outcome

    async def _waiting_files(
        self, names: _list[str], sent_at: datetime, timeout: float
    ) -> _list[dict[str, Any]]:
        """The newest file of each uploaded name, made since the upload, that made no dataset.

        A workbook's job ends before its sheets are read, so this waits (up to
        ``timeout``) until no such file is still being read.

        Args:
            names: The names the files were uploaded under.
            sent_at: When the upload was sent.
            timeout: Longest wait, in seconds, for the files to settle.

        Returns:
            One ``{"file_id", "name", "status", "action_needed", ...}`` per such file.
        """
        deadline = asyncio.get_running_loop().time() + timeout
        while True:
            found = await self._uploaded_files(names, sent_at)
            busy = any(
                entry["status"] in _BUSY_FILE_STATUSES and not entry["action_needed"]
                for entry in found
            )
            if not busy or asyncio.get_running_loop().time() >= deadline:
                break
            await asyncio.sleep(_SETTLE_POLL_S)
        return [
            entry
            for entry in found
            if entry["action_needed"] or entry["status"] not in _FINISHED_FILE_STATUSES
        ]

    async def _uploaded_files(self, names: _list[str], sent_at: datetime) -> _list[dict[str, Any]]:
        """The newest project file of each name in ``names`` made since ``sent_at``.

        Raises:
            MammothAPIError: If the project's file list cannot be read; the caller
                reports it, since the upload itself went through.
        """
        listed = await self._client.browse.resources_list(
            resource_type=_FILE_RESOURCE,
            sort="created_at:desc",
            limit=_NEWEST_FILES,
            fields="full",
        )
        wanted = set(names)
        found: _list[dict[str, Any]] = []
        for item in listed.get("resources") or []:
            if not isinstance(item, dict) or item.get("name") not in wanted:
                continue
            created = _created_at(item.get("created_at"))
            if created is None or created < sent_at - _CLOCK_SKEW:
                continue
            wanted.discard(item["name"])
            found.append(_waiting_file(item))
        return found

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
    ) -> dict[str, Any]:
        """Create datasets from accepted sheet and table reads of a multi-sheet file.

        Args:
            file_id: ID of the file.
            tables: Every accepted sheet/block read to create datasets from (1 to 100),
                each with ``sheet_name``, ``dataset_name`` and ``structure_map``.
            delete_file_after_extract: Delete the file once its datasets are created.

        Returns:
            Dict with the finished ``job_id`` and ``status``, and ``resource_ids``: the
            resource ids of the files the job created, one per new dataset (not the
            dataset ids; each dataset starts processing and becomes ready on its own).
        """
        ws = self._ws()
        proj = self._proj()
        body = {"tables": tables, "delete_file_after_extract": delete_file_after_extract}
        response = await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/files/{file_id}/multi-sheet-extraction",
            json=body,
        )
        # A failed job raises here, so a return is a finished one; the wait hands back
        # the job's own result, which names the files it created.
        outcome = await self._client._wait_if_job(response)
        return {
            "job_id": (response.get("job") or {}).get("id"),
            "status": "success",
            "resource_ids": list(outcome.get("resource_ids") or []),
        }
