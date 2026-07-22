"""
Datasets API client for managing datasets in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

ERR_DATASET_ID_POSITIVE = "`dataset_id` must be a positive integer, got {0}."
ERR_FILE_OBJECT_ID_POSITIVE = "`file_object_id` must be a positive integer, got {0}."


class DatasetsAPI:
    """Client for interacting with Mammoth Datasets API.

    Access via client.datasets:
        datasets = client.datasets.list()
        dataset = client.datasets.get(123)
        data = client.datasets.get_data(123)
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
        limit: int = 100,
        sort: str = "(created_at:desc)",
    ) -> dict[str, Any]:
        """Get list of datasets in a project.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            limit: Maximum number of results (default 100).
            sort: Sort order (default "(created_at:desc)").

        Returns:
            Dict containing datasets list with id, name and other info.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        params = {"fields": "id,name", "limit": limit, "sort": sort}
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets", params=params
        )

    def get(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get dataset details by ID.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with complete dataset information.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}"
        )

    def get_data(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
        timeout: int = 300,
        poll_interval: int = 2,
    ) -> dict[str, Any]:
        """Get the actual data from a dataset. Polls the job until completion.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            timeout: Maximum wait time in seconds (default 300).
            poll_interval: Polling interval in seconds (default 2).

        Returns:
            Dict with dataset data.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)

        response = self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/data"
        )
        return self._client._wait_if_job(response, timeout=timeout, poll_interval=poll_interval)

    def create(
        self,
        dataset_spec: dict[str, Any],
        ds_creation_type: str,
        folder_resource_id: str | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new dataset.

        Args:
            dataset_spec: Dataset specification (varies by creation type).
            ds_creation_type: Type of creation: "clone", "cloud", "sketch", "weburl".
            folder_resource_id: Optional folder resource ID.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with created dataset information.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)

        payload: dict[str, Any] = {
            "dataset_spec": dataset_spec,
            "ds_creation_type": ds_creation_type,
        }
        if folder_resource_id is not None:
            payload["folder_resource_id"] = folder_resource_id

        return self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/datasets", json=payload
        )

    def update(
        self,
        patch_data: _list[dict[str, Any]],
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update datasets using JSON Patch operations.

        The server expects patch operations sent to the plural ``/datasets``
        endpoint. Each operation must include ``op``, ``path``, and ``value``.

        Supported operations (mapped via ``OP_PATCH_TO_FUNCTION_MAP`` on the
        backend): ``rename_dataset``, ``update_datasets``, ``delete_datasets``,
        ``change_ds_column_type``, ``add_columns``, ``remove_columns``,
        ``rename_column``, ``refresh_data``, ``reattach_connection``.

        Args:
            patch_data: List of patch operations.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with update result.

        Example::

            # Rename a dataset
            client.datasets.update([
                {"op": "rename_dataset", "path": "/123", "value": {"name": "New Name"}}
            ])
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets",
            json={"patch": patch_data},
        )

    def rename(
        self,
        dataset_id: int,
        name: str,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Rename a dataset.

        Convenience method wrapping :meth:`update` with a ``rename_dataset``
        patch operation.

        Args:
            dataset_id: ID of the dataset to rename.
            name: New name for the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with update result.
        """
        return self.update(
            [{"op": "rename_dataset", "path": f"/{dataset_id}", "value": {"name": name}}],
            workspace_id=workspace_id,
            project_id=project_id,
        )

    def delete(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> None:
        """Delete a dataset.

        Args:
            dataset_id: ID of the dataset to delete.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}"
        )

    def bulk_update(
        self,
        patch_data: dict[str, Any],
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update multiple datasets (bulk operation).

        Args:
            patch_data: Patch operation data for multiple datasets.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with bulk update result.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "PATCH", f"/workspaces/{ws}/projects/{proj}/datasets", json={"patch": patch_data}
        )

    def bulk_delete(
        self,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> None:
        """Delete multiple datasets (bulk operation).

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        self._client._request_json("DELETE", f"/workspaces/{ws}/projects/{proj}/datasets")

    def list_batches(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> _list[dict[str, Any]]:
        """List batches for a dataset.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            List of batch dicts.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        response = self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches"
        )
        return response.get("batches", response if isinstance(response, _list) else [])

    def get_batch(
        self,
        dataset_id: int,
        batch_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get details of a specific batch.

        Args:
            dataset_id: ID of the dataset.
            batch_id: ID of the batch.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with batch details.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches/{batch_id}"
        )

    def get_file_settings(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get file settings for a dataset.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with file settings.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/file_settings"
        )

    def create_from_pdf(
        self,
        file_object_id: int,
        file_name: str,
        file_id: str | None = None,
        table_list: _list[int] | None = None,
        delete_file_after_extract: bool = False,
        is_preview_needed: bool | None = None,
        user_instruction: str | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create one or more datasets from tables extracted out of a PDF file.

        Args:
            file_object_id: Internal ID of the uploaded PDF file object (must be > 0).
            file_name: Original name of the uploaded PDF file.
            file_id: Unique identifier for the uploaded PDF file in pdf2csv (optional).
            table_list: Indices of the tables to extract and convert into datasets
                (optional; all tables are extracted if not provided).
            delete_file_after_extract: Delete the file from storage after
                extraction completes (default False).
            is_preview_needed: Whether a preview is required before dataset
                creation (optional).
            user_instruction: User-provided instruction for custom extraction
                logic (optional).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with created dataset(s) information (may include a job ID for
            async extraction).

        Raises:
            MammothValidationError: If *file_object_id* ≤ 0.
        """
        if file_object_id <= 0:
            raise MammothValidationError(ERR_FILE_OBJECT_ID_POSITIVE.format(file_object_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)

        payload: dict[str, Any] = {
            "file_object_id": file_object_id,
            "file_name": file_name,
            "delete_file_after_extract": delete_file_after_extract,
        }
        if file_id is not None:
            payload["file_id"] = file_id
        if table_list is not None:
            payload["table_list"] = table_list
        if is_preview_needed is not None:
            payload["is_preview_needed"] = is_preview_needed
        if user_instruction is not None:
            payload["user_instruction"] = user_instruction

        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets-from-pdf",
            json=payload,
        )

    def file_settings_update(
        self,
        dataset_id: int,
        delimiter: str,
        has_header: bool,
        initial_skip_count: int,
        quotechar: str,
        date_format: str | None = None,
        preview_mode: bool = False,
        skip_auto_process_check: bool = True,
        date_formats: dict[str, str] | None = None,
        set_project_level_date_format: bool = False,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update file data settings for a dataset (delimiter, header, dates, ...).

        Args:
            dataset_id: ID of the dataset (must be > 0).
            delimiter: Delimiter used in the file (one of ``,``, ``\\t``, ``|``, ``;``).
            has_header: Whether the file has a header row.
            initial_skip_count: Number of initial rows to skip in the file.
            quotechar: Quote character used in the file (one of ``'``, ``"``, ``""``).
            date_format: Default date format used in the source file, e.g. "US"
                or "UK" (optional).
            preview_mode: Whether to preview the changes before applying (default False).
            skip_auto_process_check: Whether to skip the automatic processing
                check (default True).
            date_formats: Per-column date format overrides, e.g.
                ``{"column_3": "UK"}`` (optional).
            set_project_level_date_format: Whether to set the date format at the
                project level (default False).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with updated file settings.

        Raises:
            MammothValidationError: If *dataset_id* ≤ 0.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)

        payload: dict[str, Any] = {
            "delimiter": delimiter,
            "has_header": has_header,
            "initial_skip_count": initial_skip_count,
            "quotechar": quotechar,
            "preview_mode": preview_mode,
            "skip_auto_process_check": skip_auto_process_check,
            "set_project_level_date_format": set_project_level_date_format,
        }
        if date_format is not None:
            payload["date_format"] = date_format
        if date_formats is not None:
            payload["date_formats"] = date_formats

        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/file_settings",
            json=payload,
        )

    def file_settings_undo(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Undo the last file data settings change for a dataset.

        Args:
            dataset_id: ID of the dataset (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with the restored file settings.

        Raises:
            MammothValidationError: If *dataset_id* ≤ 0.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/file_settings"
        )

    def restore(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Restore a trashed dataset.

        Args:
            dataset_id: ID of the dataset (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with restore result.

        Raises:
            MammothValidationError: If *dataset_id* ≤ 0.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/restore"
        )

    def trash(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Move a dataset to trash.

        Args:
            dataset_id: ID of the dataset (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with trash result.

        Raises:
            MammothValidationError: If *dataset_id* ≤ 0.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/trash"
        )
