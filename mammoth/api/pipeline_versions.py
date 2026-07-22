"""Pipeline versions API client for Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."
ERR_DATASET_ID_POSITIVE = "`dataset_id` must be a positive integer, got {0}."
ERR_DATAVIEW_ID_POSITIVE = "`dataview_id` must be a positive integer, got {0}."
ERR_VERSION_ID_POSITIVE = "`version_id` must be a positive integer, got {0}."


class PipelineVersionsAPI:
    """Client for pipeline version operations.

    Pipeline versions are named snapshots of a dataview's pipeline that can
    be listed, inspected, edited, or re-applied.

    Access via ``client.pipeline_versions``::

        versions = client.pipeline_versions.list(dataset_id=1, dataview_id=2)
        client.pipeline_versions.apply(dataset_id=1, dataview_id=2, version_id=versions[0]["id"])
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
            f"/dataviews/{dataview_id}/pipeline/versions"
        )

    def list(
        self,
        dataset_id: int,
        dataview_id: int,
        project_id: int | None = None,
        fields: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """List pipeline versions for a dataview.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            project_id: Project ID (uses client default if not provided).
            fields: Fields to return.
            sort: Sort specification.
            limit: Maximum number of results.
            offset: Number of results to skip.
            name: Filter by version name.

        Returns:
            Dict with the pipeline versions list.

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
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if name is not None:
            params["name"] = name
        return self._client._request_json(
            "GET",
            self._url(dataset_id, dataview_id, project_id),
            params=params or None,
        )

    def get(
        self,
        dataset_id: int,
        dataview_id: int,
        version_id: int,
        project_id: int | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """Get a specific pipeline version.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            version_id: ID of the pipeline version.
            project_id: Project ID (uses client default if not provided).
            fields: Fields to return.

        Returns:
            Dict with pipeline version details.

        Raises:
            MammothValidationError: If any of *dataset_id*, *dataview_id*,
                *version_id*, or *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        if version_id <= 0:
            raise MammothValidationError(ERR_VERSION_ID_POSITIVE.format(version_id))
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        return self._client._request_json(
            "GET",
            f"{self._url(dataset_id, dataview_id, project_id)}/{version_id}",
            params=params or None,
        )

    def apply(
        self,
        dataset_id: int,
        dataview_id: int,
        version_id: int,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Re-apply a pipeline version to its dataview.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            version_id: ID of the pipeline version to apply.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the resulting pipeline state.

        Raises:
            MammothValidationError: If any of *dataset_id*, *dataview_id*,
                *version_id*, or *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        if version_id <= 0:
            raise MammothValidationError(ERR_VERSION_ID_POSITIVE.format(version_id))
        return self._client._request_json(
            "POST",
            f"{self._url(dataset_id, dataview_id, project_id)}/{version_id}",
        )

    def update(
        self,
        dataset_id: int,
        dataview_id: int,
        version_id: int,
        body: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a pipeline version via patch operations.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            version_id: ID of the pipeline version.
            body: Patch operations payload.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the updated pipeline version.

        Raises:
            MammothValidationError: If any of *dataset_id*, *dataview_id*,
                *version_id*, or *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        if version_id <= 0:
            raise MammothValidationError(ERR_VERSION_ID_POSITIVE.format(version_id))
        return self._client._request_json(
            "PATCH",
            f"{self._url(dataset_id, dataview_id, project_id)}/{version_id}",
            json=body,
        )

    def delete(
        self,
        dataset_id: int,
        dataview_id: int,
        version_id: int,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete a pipeline version.

        Args:
            dataset_id: ID of the dataset containing the dataview.
            dataview_id: ID of the dataview.
            version_id: ID of the pipeline version.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If any of *dataset_id*, *dataview_id*,
                *version_id*, or *project_id* is not a positive integer.
        """
        self._check_ids(dataset_id, dataview_id, project_id)
        if version_id <= 0:
            raise MammothValidationError(ERR_VERSION_ID_POSITIVE.format(version_id))
        return self._client._request_json(
            "DELETE",
            f"{self._url(dataset_id, dataview_id, project_id)}/{version_id}",
        )
