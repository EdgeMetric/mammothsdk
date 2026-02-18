"""Reports API client for listing reports in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient


class ReportsAPI:
    """Client for listing workspace reports.

    Access via client.reports::

        reports = client.reports.list()
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List all reports.

        Args:
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).

        Returns:
            Dict with reports list and pagination info.
        """
        ws = self._ws()
        params: dict[str, Any] = {}
        if limit != 50:
            params["limit"] = limit
        if offset != 0:
            params["offset"] = offset
        return self._client._request_json("GET", f"/workspaces/{ws}/reports", params=params or None)
