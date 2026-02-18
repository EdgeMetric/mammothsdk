"""Activity Logs API client for querying activity logs in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient


class ActivityLogsAPI:
    """Client for querying and exporting activity logs.

    Access via client.activity_logs::

        logs = client.activity_logs.list()
        export = client.activity_logs.export(format="csv")
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        **filters: Any,
    ) -> dict[str, Any]:
        """List activity logs.

        Args:
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).
            sort: Sort specification.
            **filters: Additional filter parameters (user, action, resource, etc.).

        Returns:
            Dict with activity logs and pagination info.
        """
        ws = self._ws()
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if sort:
            params["sort"] = sort
        params.update(filters)
        return self._client._request_json("GET", f"/workspaces/{ws}/activity_logs", params=params)

    def export(self, format: str = "csv", **filters: Any) -> dict[str, Any]:
        """Export activity logs.

        Args:
            format: Export format (default "csv").
            **filters: Filter parameters for the export.

        Returns:
            Dict with export result (may include download URL or job ID).
        """
        ws = self._ws()
        params: dict[str, Any] = {"format": format}
        params.update(filters)
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/activity_logs/export", params=params
        )
