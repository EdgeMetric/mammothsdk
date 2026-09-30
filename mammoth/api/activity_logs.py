"""Activity Logs API client for querying activity logs in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient


class ActivityLogsAPI:
    """Client for querying and exporting activity logs.

    Access via client.activity_logs::

        logs = await client.activity_logs.list()
        export = await client.activity_logs.export(format="csv")
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    async def list(
        self,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        project_id: int | None = None,
        categories: list[Any] | None = None,
        activities: list[Any] | None = None,
        resource_id: str | None = None,
        result: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        origin: str | None = None,
        user_ids: list[Any] | None = None,
        parent_id: int | None = None,
        search_text: str | None = None,
    ) -> dict[str, Any]:
        """List activity logs.

        Args:
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).
            sort: Sort specification.
            project_id: Filter to one project's activity.
            categories: Filter by activity categories (e.g. "Project", "Dataview").
            activities: Filter by activity names (e.g. "create_project").
            resource_id: Filter to one resource's activity.
            result: Filter by outcome (e.g. "success").
            start_time: Filter to activity at or after this time.
            end_time: Filter to activity at or before this time.
            origin: Filter by request origin (e.g. "user").
            user_ids: Filter by the ids of the users who performed the activity.
            parent_id: Filter by the parent resource id.
            search_text: Free-text search across activity log entries.

        Returns:
            Dict with activity logs and pagination info.
        """
        ws = self._ws()
        body: dict[str, Any] = {"limit": limit, "offset": offset}
        if sort:
            body["sort"] = sort
        for name, value in (
            ("project_id", project_id),
            ("categories", categories),
            ("activities", activities),
            ("resource_id", resource_id),
            ("result", result),
            ("start_time", start_time),
            ("end_time", end_time),
            ("origin", origin),
            ("user_ids", user_ids),
            ("parent_id", parent_id),
            ("search_text", search_text),
        ):
            if value is not None:
                body[name] = value
        return await self._client._request_json("POST", f"/workspaces/{ws}/activity_log", json=body)

    async def export(self, format: str = "csv", **filters: Any) -> dict[str, Any]:
        """Export activity logs.

        Args:
            format: Export format (default "csv").
            **filters: Filter parameters for the export.

        Returns:
            Dict with export result (may include download URL or job ID).
        """
        ws = self._ws()
        body: dict[str, Any] = {"format": format}
        body.update(filters)
        return await self._client._request_json(
            "POST", f"/workspaces/{ws}/activity_log/export", json=body
        )
