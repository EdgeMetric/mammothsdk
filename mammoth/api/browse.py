"""Browse API client for resource discovery in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient


class BrowseAPI:
    """Client for browsing and discovering resources.

    Access via client.browse::

        resources = client.browse.workspaces()
        resources = client.browse.projects()
        resources = client.browse.datasets(project_id=10)
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

    def workspaces(self) -> dict[str, Any]:
        """Browse available workspaces.

        Returns:
            Dict with workspace resources.
        """
        return self._client._request_json("GET", "/workspaces")

    def projects(self, workspace_id: int | None = None) -> dict[str, Any]:
        """Browse projects in a workspace.

        Args:
            workspace_id: Workspace ID (uses client default if not provided).

        Returns:
            Dict with project resources.
        """
        ws = workspace_id or self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}/projects")

    def datasets(
        self,
        project_id: int | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Browse datasets in a project.

        Args:
            project_id: Project ID (uses client default if not provided).
            workspace_id: Workspace ID (uses client default if not provided).

        Returns:
            Dict with dataset resources.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request_json("GET", f"/workspaces/{ws}/projects/{proj}/datasets")

    def dataviews(
        self,
        dataset_id: int,
        project_id: int | None = None,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Browse dataviews in a dataset.

        Args:
            dataset_id: ID of the dataset.
            project_id: Project ID (uses client default if not provided).
            workspace_id: Workspace ID (uses client default if not provided).

        Returns:
            Dict with dataview resources.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews",
        )

    def workspace_resources(
        self,
        workspace_id: int | None = None,
        level: int = 2,
        fields: str = "__min",
        limit: int = 100,
    ) -> dict[str, Any]:
        """Browse all resources in a workspace (projects, datasets, folders).

        Args:
            workspace_id: Workspace ID (uses client default if not provided).
            level: Depth of children to include (1 or 2, default 2).
            fields: Fields to return (default "__min").
            limit: Max resources to return (default 100).

        Returns:
            Dict with hierarchical resource list.
        """
        ws = workspace_id or self._ws()
        params: dict[str, Any] = {"level": level, "fields": fields, "limit": limit}
        return self._client._request_json("GET", f"/workspaces/{ws}/browse", params=params)

    def folder_resources(
        self,
        folder_id: int,
        project_id: int | None = None,
        workspace_id: int | None = None,
        level: int = 2,
        fields: str = "__min",
    ) -> dict[str, Any]:
        """Browse resources inside a folder.

        Args:
            folder_id: ID of the folder (label).
            project_id: Project ID (uses client default if not provided).
            workspace_id: Workspace ID (uses client default if not provided).
            level: Depth of children to include (1 or 2, default 2).
            fields: Fields to return (default "__min").

        Returns:
            Dict with folder's child resources.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        params: dict[str, Any] = {"level": level, "fields": fields}
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/folders/{folder_id}/browse",
            params=params,
        )
