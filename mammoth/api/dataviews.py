"""
Dataviews API client for managing dataviews in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

ERR_DATAVIEW_ID_POSITIVE = "`dataview_id` must be a positive integer, got {0}."


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
            Dict with ``"dataview_id"`` key containing the new dataview's ID.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        payload: dict[str, Any] = {"name": name}
        if clone_config_from is not None:
            payload["clone_config_from"] = clone_config_from
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews",
            json=payload,
        )
        return self._client._wait_if_job(response)

    def update(
        self,
        dataset_id: int,
        dataview_id: int,
        patch_data: _list[dict[str, Any]],
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update dataview properties using JSON Patch operations.

        Each operation in ``patch_data`` should have ``op``, ``path``, and
        ``value`` keys following JSON Patch conventions.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview to update.
            patch_data: List of patch operations.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with update result.

        Example::

            client.dataviews.update(
                dataset_id=123, dataview_id=456,
                patch_data=[{"op": "replace", "path": "/name", "value": "Renamed"}],
            )
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
        timeout: int | None = None,
        poll_interval: int = 2,
    ) -> dict[str, Any]:
        """Get dataview data (GET method).

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            timeout: Max job wait time in seconds (default: client.job_timeout).
            poll_interval: Seconds between job polls (default: 2).

        Returns:
            Dict with dataview data.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        response = self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/data",
        )
        return self._client._wait_if_job(response, timeout=timeout, poll_interval=poll_interval)

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
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/data",
            json=payload,
        )
        return self._client._wait_if_job(response)

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
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format",
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
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format",
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
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format",
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
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format",
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
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/draft-mode",
            json={"draft_operation": command},
        )

    def parameter_context(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get the parameter context available to a dataview's pipeline.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with the available parameter context.

        Raises:
            MammothValidationError: If *dataview_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/parameter-context",
        )

    def preview(
        self,
        dataset_id: int,
        dataview_id: int,
        rows: int | None = None,
        cols: int | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get a lightweight preview of a dataview's data.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview (must be > 0).
            rows: Maximum number of rows to include in the preview (optional).
            cols: Maximum number of columns to include in the preview (optional).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with the preview data.

        Raises:
            MammothValidationError: If *dataview_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        params: dict[str, Any] = {}
        if rows is not None:
            params["rows"] = rows
        if cols is not None:
            params["cols"] = cols
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/preview",
            params=params or None,
        )

    def restore(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Restore a trashed dataview.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with restore result.

        Raises:
            MammothValidationError: If *dataview_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/restore",
        )

    def trash(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Move a dataview to trash.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with trash result.

        Raises:
            MammothValidationError: If *dataview_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/trash",
        )
