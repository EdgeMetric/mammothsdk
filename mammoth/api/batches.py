"""Batches API client for managing dataset batches in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient


class BatchesAPI:
    """Client for managing dataset batch operations.

    Access via client.batches::

        batches = client.batches.list(dataset_id=123)
        batch = client.batches.get(dataset_id=123, batch_id=1)
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
        dataset_id: int,
        project_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List batches for a dataset.

        Args:
            dataset_id: ID of the dataset.
            project_id: Project ID (uses client default if not provided).
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).

        Returns:
            Dict with batches list and pagination info.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        params: dict[str, Any] = {}
        if limit != 50:
            params["limit"] = limit
        if offset != 0:
            params["offset"] = offset
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches",
            params=params or None,
        )

    def get(
        self,
        dataset_id: int,
        batch_id: int,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get batch details.

        Args:
            dataset_id: ID of the dataset.
            batch_id: ID of the batch.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with batch details.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches/{batch_id}",
        )

    def create(
        self,
        dataset_id: int,
        config: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new batch for a dataset.

        Args:
            dataset_id: ID of the dataset.
            config: Batch configuration.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with created batch info.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches",
            json=config,
        )

    def update(
        self,
        dataset_id: int,
        config: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update batches for a dataset.

        Args:
            dataset_id: ID of the dataset.
            config: Updated batch configuration.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with updated batch info.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches",
            json=config,
        )

    def delete(
        self,
        dataset_id: int,
        batch_id: int,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete a batch.

        Args:
            dataset_id: ID of the dataset.
            batch_id: ID of the batch.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches/{batch_id}",
        )
