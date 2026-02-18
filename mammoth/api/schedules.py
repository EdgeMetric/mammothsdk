"""Schedules API client for managing project schedules in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient


class SchedulesAPI:
    """Client for managing schedules under projects.

    Access via client.schedules::

        schedules = client.schedules.list()
        schedule = client.schedules.create(config={...})
        client.schedules.delete(schedule_id)
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
        project_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List schedules in a project.

        Args:
            project_id: Project ID (uses client default if not provided).
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).

        Returns:
            Dict with schedules list and pagination info.
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
            f"/workspaces/{ws}/projects/{proj}/schedules",
            params=params or None,
        )

    def get(self, schedule_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Get schedule details.

        Args:
            schedule_id: ID of the schedule.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with schedule details.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/schedules/{schedule_id}"
        )

    def create(self, config: dict[str, Any], project_id: int | None = None) -> dict[str, Any]:
        """Create a new schedule.

        Args:
            config: Schedule configuration.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with created schedule info.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/schedules",
            json=config,
        )

    def update(
        self,
        schedule_id: int,
        config: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a schedule.

        Args:
            schedule_id: ID of the schedule.
            config: Updated schedule configuration.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with updated schedule info.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/schedules/{schedule_id}",
            json=config,
        )

    def delete(self, schedule_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Delete a schedule.

        Args:
            schedule_id: ID of the schedule.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/schedules/{schedule_id}",
        )
