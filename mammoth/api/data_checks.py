"""Pipeline data checks API client for Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."
ERR_DATASET_ID_POSITIVE = "`dataset_id` must be a positive integer, got {0}."
ERR_DATAVIEW_ID_POSITIVE = "`dataview_id` must be a positive integer, got {0}."
ERR_DATA_CHECK_ID_POSITIVE = "`data_check_id` must be a positive integer, got {0}."


class DataChecksAPI:
    """Client for pipeline data check operations.

    Data checks are validations attached to a dataview's pipeline that flag
    rows or values failing configured rules.

    Access via ``client.data_checks``::

        check = client.data_checks.create(
            dataset_id=1, dataview_id=2, body={"name": "No nulls in Amount"}
        )
        client.data_checks.delete(dataset_id=1, dataview_id=2, data_check_id=check["id"])
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

    def _check_ids(self, dataset_id: int, dataview_id: int, project_id: int | None) -> None:
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))
        if project_id is not None and project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))

    def _url(self, dataset_id: int, dataview_id: int, project_id: int | None = None) -> str:
        ws = self._ws()
        proj = self._proj(project_id)
        return (
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}"
            f"/dataviews/{dataview_id}/pipeline/data-checks"
        )

    def list(
        self,
        dataset_id: int,
        dataview_id: int,
        project_id: int | None = None,
        fields: str | None = None,
        sort: str | None = None,
        sequence: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """List pipeline data checks for a dataview.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            project_id: Project ID (uses client default if not provided).
            fields: Fields to return.
            sort: Sort specification.
            sequence: Sequence filter.
            status: Status filter.

        Returns:
            Dict with the data checks list.

        Raises:
            MammothValidationError: If *dataset_id*, *dataview_id*, or
                *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        if sort is not None:
            params["sort"] = sort
        if sequence is not None:
            params["sequence"] = sequence
        if status is not None:
            params["status"] = status
        return self._client._request_json(
            "GET",
            self._url(dataset_id, dataview_id, project_id),
            params=params or None,
        )

    def get(
        self,
        dataset_id: int,
        dataview_id: int,
        data_check_id: int,
        project_id: int | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """Get a specific pipeline data check.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            data_check_id: ID of the data check.
            project_id: Project ID (uses client default if not provided).
            fields: Fields to return.

        Returns:
            Dict with data check details.

        Raises:
            MammothValidationError: If any of *dataset_id*, *dataview_id*,
                *data_check_id*, or *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        if data_check_id <= 0:
            raise MammothValidationError(ERR_DATA_CHECK_ID_POSITIVE.format(data_check_id))
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        return self._client._request_json(
            "GET",
            f"{self._url(dataset_id, dataview_id, project_id)}/{data_check_id}",
            params=params or None,
        )

    def create(
        self,
        dataset_id: int,
        dataview_id: int,
        body: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new pipeline data check.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            body: Data check creation payload.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the created data check.

        Raises:
            MammothValidationError: If *dataset_id*, *dataview_id*, or
                *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        return self._client._request_json(
            "POST",
            self._url(dataset_id, dataview_id, project_id),
            json=body,
        )

    def update(
        self,
        dataset_id: int,
        dataview_id: int,
        data_check_id: int,
        body: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a pipeline data check via patch operations.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            data_check_id: ID of the data check.
            body: Patch operations payload.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the updated data check.

        Raises:
            MammothValidationError: If any of *dataset_id*, *dataview_id*,
                *data_check_id*, or *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        if data_check_id <= 0:
            raise MammothValidationError(ERR_DATA_CHECK_ID_POSITIVE.format(data_check_id))
        return self._client._request_json(
            "PATCH",
            f"{self._url(dataset_id, dataview_id, project_id)}/{data_check_id}",
            json=body,
        )

    def delete(
        self,
        dataset_id: int,
        dataview_id: int,
        data_check_id: int,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete a pipeline data check.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            data_check_id: ID of the data check.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If any of *dataset_id*, *dataview_id*,
                *data_check_id*, or *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        if data_check_id <= 0:
            raise MammothValidationError(ERR_DATA_CHECK_ID_POSITIVE.format(data_check_id))
        return self._client._request_json(
            "DELETE",
            f"{self._url(dataset_id, dataview_id, project_id)}/{data_check_id}",
        )
