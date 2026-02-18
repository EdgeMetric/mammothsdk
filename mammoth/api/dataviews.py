"""
Dataviews API client for managing dataviews in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name


class DataviewsAPI:
    """Client for interacting with Mammoth Dataviews API.

    Access via client.dataviews:
        views = client.dataviews.list(dataset_id=123)
        view = client.dataviews.get(dataset_id=123, dataview_id=456)
        data = client.dataviews.get_data(dataset_id=123, dataview_id=456)

    For rich View objects with transformation methods, use client.views instead.
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
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
        limit: int = 100,
        sort: str = "(created_at:desc)",
    ) -> dict[str, Any]:
        """Get list of dataviews in a dataset.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            limit: Maximum number of results (default 100).
            sort: Sort order (default "(created_at:desc)").

        Returns:
            Dict containing dataviews list.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        params = {"limit": limit, "sort": sort}
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews",
            params=params,
        )

    def get(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get dataview information.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with complete dataview information.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
        )

    def create(
        self,
        dataset_id: int,
        name: str | None = "View",
        clone_config_from: int | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create or duplicate a dataview.

        Args:
            dataset_id: ID of the dataset.
            name: Name of the dataview (default "View").
            clone_config_from: ID of dataview to clone config from (optional).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with created dataview information.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        payload: dict[str, Any] = {"name": name}
        if clone_config_from is not None:
            payload["clone_config_from"] = clone_config_from
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews",
            json=payload,
        )

    def update(
        self,
        dataset_id: int,
        dataview_id: int,
        patch_data: _list[dict[str, Any]],
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update dataview properties.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview to update.
            patch_data: List of patch operations.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with update result.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}",
            json={"patch": patch_data},
        )

    def delete(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete a dataview.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview to delete.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}",
        )

    def bulk_delete(
        self,
        dataset_id: int,
        dataview_ids: _list[int] | str,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete multiple dataviews.

        Args:
            dataset_id: ID of the dataset.
            dataview_ids: List of dataview IDs or comma-separated string.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with bulk deletion result.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        if isinstance(dataview_ids, _list):
            ids_str = ",".join(str(id) for id in dataview_ids)
        else:
            ids_str = str(dataview_ids)
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews",
            params={"ids": ids_str},
        )

    def get_data(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get dataview data (GET method).

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with dataview data.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/data",
        )

    def query_data(
        self,
        dataset_id: int,
        dataview_id: int,
        sequence: int = 0,
        offset: int = 1,
        limit: int = 400,
        columns: _list[str] | None = None,
        condition: dict[str, Any] | None = None,
        sort: str | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get dataview data with filtering options (POST method).

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            sequence: Pipeline step to fetch data at (default 0).
            offset: One-indexed starting row (default 1).
            limit: Number of rows to fetch (default 400).
            columns: List of column names to fetch (optional).
            condition: Filter condition dict (optional).
            sort: Sort specification string (optional).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with filtered dataview data.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        payload: dict[str, Any] = {"sequence": sequence, "offset": offset, "limit": limit}
        if columns is not None:
            payload["columns"] = columns
        if condition is not None:
            payload["condition"] = condition
        if sort is not None:
            payload["sort"] = sort
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/data",
            json=payload,
        )

    def active_users(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get list of active users on this dataview.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with list of active users.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/activities",
        )

    def mark_active(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Mark current user as active on this dataview.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with updated active users.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/activities",
        )

    def conditional_format_list(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> _list[dict[str, Any]]:
        """List conditional formatting rules.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            List of conditional format rule dicts.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        response = self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional_format",
        )
        return response.get("rules", response if isinstance(response, _list) else [])

    def conditional_format_create(
        self,
        dataset_id: int,
        dataview_id: int,
        rule: dict[str, Any],
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a conditional formatting rule.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            rule: Conditional format rule specification.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with created rule.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional_format",
            json=rule,
        )

    def conditional_format_update(
        self,
        dataset_id: int,
        dataview_id: int,
        rule: dict[str, Any],
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a conditional formatting rule.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            rule: Updated conditional format rule.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with updated rule.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional_format",
            json=rule,
        )

    def conditional_format_delete(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete all conditional formatting rules.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional_format",
        )

    def draft_mode(
        self,
        dataset_id: int,
        dataview_id: int,
        command: str,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Manage draft mode for a dataview pipeline.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            command: Draft mode command: "enter", "commit", or "discard".
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with draft mode state.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/pipeline/draft",
            json={"command": command},
        )
