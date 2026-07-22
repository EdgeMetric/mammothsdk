"""Data Apps API client for Mammoth."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

ERR_DATA_APP_ID_POSITIVE = "`data_app_id` must be a positive integer, got {0}."
ERR_JOB_ID_POSITIVE = "`job_id` must be a positive integer, got {0}."


class DataAppsAPI:
    """Client for data app operations.

    Data apps are standalone resources — endpoints are not workspace/project
    scoped (except for the optional ``workspace_id`` filter on :meth:`list`).

    Access via ``client.data_apps``::

        data_app = client.data_apps.create(body={"name": "My App"})
        client.data_apps.delete(data_app["id"])
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    @staticmethod
    def _check_data_app_id(data_app_id: int) -> None:
        if data_app_id <= 0:
            raise MammothValidationError(ERR_DATA_APP_ID_POSITIVE.format(data_app_id))

    @staticmethod
    def _check_job_id(job_id: int) -> None:
        if job_id <= 0:
            raise MammothValidationError(ERR_JOB_ID_POSITIVE.format(job_id))

    def list(self, workspace_id: int | None = None) -> dict[str, Any]:
        """List data apps.

        Args:
            workspace_id: Optional workspace ID to filter by.

        Returns:
            Dict with the data apps list.
        """
        params: dict[str, Any] = {}
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        return self._client._request_json("GET", "/data-apps", params=params or None)

    def get(self, data_app_id: int) -> dict[str, Any]:
        """Get details of a data app.

        Args:
            data_app_id: ID of the data app.

        Returns:
            Dict with data app details.

        Raises:
            MammothValidationError: If *data_app_id* is not a positive integer.
        """
        self._check_data_app_id(data_app_id)
        return self._client._request_json("GET", f"/data-apps/{data_app_id}")

    def create(self, body: dict[str, Any]) -> dict[str, Any]:
        """Create a new data app.

        Args:
            body: Data app creation payload (name, source dataview, etc.).

        Returns:
            Dict with the created data app.
        """
        return self._client._request_json("POST", "/data-apps", json=body)

    def update(self, data_app_id: int, body: dict[str, Any]) -> dict[str, Any]:
        """Update data app settings.

        Args:
            data_app_id: ID of the data app.
            body: Settings to update.

        Returns:
            Dict with the updated data app.

        Raises:
            MammothValidationError: If *data_app_id* is not a positive integer.
        """
        self._check_data_app_id(data_app_id)
        return self._client._request_json("POST", f"/data-apps/{data_app_id}/settings", json=body)

    def delete(self, data_app_id: int) -> dict[str, Any]:
        """Delete a data app.

        Args:
            data_app_id: ID of the data app.

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *data_app_id* is not a positive integer.
        """
        self._check_data_app_id(data_app_id)
        return self._client._request_json("DELETE", f"/data-apps/{data_app_id}")

    def active_job(self, data_app_id: int) -> dict[str, Any]:
        """Get the currently active job for a data app, if any.

        Args:
            data_app_id: ID of the data app.

        Returns:
            Dict with the active job info.

        Raises:
            MammothValidationError: If *data_app_id* is not a positive integer.
        """
        self._check_data_app_id(data_app_id)
        return self._client._request_json("GET", f"/data-apps/{data_app_id}/active-job")

    def job(self, data_app_id: int, job_id: int) -> dict[str, Any]:
        """Get a specific job for a data app.

        Args:
            data_app_id: ID of the data app.
            job_id: ID of the job.

        Returns:
            Dict with job details.

        Raises:
            MammothValidationError: If *data_app_id* or *job_id* is not a
                positive integer.
        """
        self._check_data_app_id(data_app_id)
        self._check_job_id(job_id)
        return self._client._request_json("GET", f"/data-apps/{data_app_id}/jobs/{job_id}")

    def pipeline_changes(self, data_app_id: int) -> dict[str, Any]:
        """Get pending pipeline changes for a data app's source dataview.

        Args:
            data_app_id: ID of the data app.

        Returns:
            Dict describing pipeline changes.

        Raises:
            MammothValidationError: If *data_app_id* is not a positive integer.
        """
        self._check_data_app_id(data_app_id)
        return self._client._request_json("GET", f"/data-apps/{data_app_id}/pipeline-changes")

    def share(self, data_app_id: int, body: dict[str, Any]) -> dict[str, Any]:
        """Share a data app with a user.

        Args:
            data_app_id: ID of the data app.
            body: Share spec (e.g. recipient email, role).

        Returns:
            Dict with the share result.

        Raises:
            MammothValidationError: If *data_app_id* is not a positive integer.
        """
        self._check_data_app_id(data_app_id)
        return self._client._request_json("POST", f"/data-apps/{data_app_id}/share", json=body)

    def upload(
        self,
        data_app_id: int,
        file: str | Path | BinaryIO,
        append_to_ds_id: int | None = None,
    ) -> dict[str, Any]:
        """Upload a file to a data app.

        Args:
            data_app_id: ID of the data app.
            file: File to upload — a file path, ``Path``, or file-like object.
            append_to_ds_id: Dataset ID to append the upload to, if appending.

        Returns:
            Dict with the upload/job result.

        Raises:
            MammothValidationError: If *data_app_id* is not a positive integer.
            ValueError: If *file* is a path that does not exist.
        """
        self._check_data_app_id(data_app_id)
        params: dict[str, Any] = {}
        if append_to_ds_id is not None:
            params["append_to_ds_id"] = append_to_ds_id

        opened_file: Any = None
        try:
            if isinstance(file, (str, Path)):
                file_path = Path(file)
                if not file_path.exists():
                    raise ValueError(f"File not found: {file_path}")
                opened_file = open(file_path, "rb")  # noqa: SIM115
                file_data: list[tuple[str, tuple[str, Any, str]]] = [
                    ("files", (file_path.name, opened_file, "application/octet-stream"))
                ]
            else:
                filename = getattr(file, "name", "uploaded_file")
                if hasattr(filename, "split"):
                    filename = os.path.basename(filename)
                file_data = [("files", (filename, file, "application/octet-stream"))]

            return self._client._request_json(
                "POST",
                f"/data-apps/{data_app_id}/files",
                params=params or None,
                files=file_data,
            )
        finally:
            if opened_file is not None:
                opened_file.close()

    def user_list(self, data_app_id: int) -> dict[str, Any]:
        """List users a data app is shared with.

        Args:
            data_app_id: ID of the data app.

        Returns:
            Dict with the shared users list.

        Raises:
            MammothValidationError: If *data_app_id* is not a positive integer.
        """
        self._check_data_app_id(data_app_id)
        return self._client._request_json("GET", f"/data-apps/{data_app_id}/users")

    def user_remove(self, data_app_id: int, email: str) -> dict[str, Any]:
        """Remove a shared user from a data app.

        Args:
            data_app_id: ID of the data app.
            email: Email address of the user to remove.

        Returns:
            Dict with the removal result.

        Raises:
            MammothValidationError: If *data_app_id* is not a positive integer.
        """
        self._check_data_app_id(data_app_id)
        return self._client._request_json(
            "DELETE", f"/data-apps/{data_app_id}/users", params={"email": email}
        )
