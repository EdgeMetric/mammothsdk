"""Dataview derivatives API client for Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."
ERR_DATASET_ID_POSITIVE = "`dataset_id` must be a positive integer, got {0}."
ERR_DATAVIEW_ID_POSITIVE = "`dataview_id` must be a positive integer, got {0}."
ERR_DERIVATIVE_ID_POSITIVE = "`derivative_id` must be a positive integer, got {0}."


class DerivativesAPI:
    """Client for dataview derivative operations.

    Derivatives are computed views (e.g. aggregations, samples) derived from
    a dataview's pipeline output.

    Access via ``client.derivatives``::

        derivative = client.derivatives.create(
            dataset_id=1, dataview_id=2, body={"type": "summary"}
        )
        data = client.derivatives.data(
            dataset_id=1, dataview_id=2, derivative_id=derivative["id"], body={}
        )
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
            f"/dataviews/{dataview_id}/derivatives"
        )

    def list(
        self,
        dataset_id: int,
        dataview_id: int,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """List derivatives for a dataview.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the derivatives list.

        Raises:
            MammothValidationError: If *dataset_id*, *dataview_id*, or
                *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        return self._client._request_json("GET", self._url(dataset_id, dataview_id, project_id))

    def create(
        self,
        dataset_id: int,
        dataview_id: int,
        body: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new derivative for a dataview.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            body: Derivative creation payload.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the created derivative.

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

    def data(
        self,
        dataset_id: int,
        dataview_id: int,
        derivative_id: int,
        body: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Fetch data for a derivative.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            derivative_id: ID of the derivative.
            body: Fetch request payload (e.g. pagination, filters).
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the fetched derivative data.

        Raises:
            MammothValidationError: If any of *dataset_id*, *dataview_id*,
                *derivative_id*, or *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        if derivative_id <= 0:
            raise MammothValidationError(ERR_DERIVATIVE_ID_POSITIVE.format(derivative_id))
        return self._client._request_json(
            "POST",
            f"{self._url(dataset_id, dataview_id, project_id)}/{derivative_id}/data",
            json=body,
        )

    def update(
        self,
        dataset_id: int,
        dataview_id: int,
        derivative_id: int,
        body: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a derivative.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            derivative_id: ID of the derivative.
            body: Fields to update.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the updated derivative.

        Raises:
            MammothValidationError: If any of *dataset_id*, *dataview_id*,
                *derivative_id*, or *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        if derivative_id <= 0:
            raise MammothValidationError(ERR_DERIVATIVE_ID_POSITIVE.format(derivative_id))
        return self._client._request_json(
            "PATCH",
            f"{self._url(dataset_id, dataview_id, project_id)}/{derivative_id}",
            json=body,
        )

    def delete(
        self,
        dataset_id: int,
        dataview_id: int,
        derivative_id: int,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete a derivative.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            derivative_id: ID of the derivative.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If any of *dataset_id*, *dataview_id*,
                *derivative_id*, or *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        if derivative_id <= 0:
            raise MammothValidationError(ERR_DERIVATIVE_ID_POSITIVE.format(derivative_id))
        return self._client._request_json(
            "DELETE",
            f"{self._url(dataset_id, dataview_id, project_id)}/{derivative_id}",
        )
