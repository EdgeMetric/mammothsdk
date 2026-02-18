"""
Automations API client for managing automations and schedules in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name


class AutomationsAPI:
    """Client for managing automations and schedules.

    Access via client.automations:
        automations = client.automations.list()
        automation = client.automations.create(config={...})
        schedules = client.automations.list_schedules()
        client.automations.create_schedule(config={...})
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

    # ── Automations ──────────────────────────────────────────────

    def list(self) -> _list[dict[str, Any]]:
        """List all automations.

        Returns:
            List of automation dicts.
        """
        response = self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/projects/{self._proj()}/automations"
        )
        return response.get("automations", response if isinstance(response, _list) else [])

    def create(self, config: dict[str, Any]) -> dict[str, Any]:
        """Create a new automation.

        Args:
            config: Automation configuration (name, triggers, actions, etc.).

        Returns:
            Dict with created automation info.
        """
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/projects/{self._proj()}/automations", json=config
        )

    def get(self, automation_id: int) -> dict[str, Any]:
        """Get automation details.

        Args:
            automation_id: ID of the automation.

        Returns:
            Dict with automation details.
        """
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/projects/{self._proj()}/automations/{automation_id}"
        )

    def update(self, automation_id: int, config: dict[str, Any]) -> dict[str, Any]:
        """Update an automation.

        Args:
            automation_id: ID of the automation.
            config: Updated automation configuration.

        Returns:
            Dict with updated automation info.
        """
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/automations/{automation_id}",
            json=config,
        )

    def delete(self, automation_id: int) -> dict[str, Any]:
        """Delete an automation.

        Args:
            automation_id: ID of the automation.

        Returns:
            Dict with deletion result.
        """
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/automations/{automation_id}",
        )

    # ── Schedules ────────────────────────────────────────────────

    def list_schedules(self) -> _list[dict[str, Any]]:
        """List all schedules.

        Returns:
            List of schedule dicts.
        """
        response = self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/projects/{self._proj()}/schedules"
        )
        return response.get("schedules", response if isinstance(response, _list) else [])

    def create_schedule(self, config: dict[str, Any]) -> dict[str, Any]:
        """Create a new schedule.

        Args:
            config: Schedule configuration (cron, timezone, actions, etc.).

        Returns:
            Dict with created schedule info.
        """
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/projects/{self._proj()}/schedules", json=config
        )

    def update_schedule(self, schedule_id: int, config: dict[str, Any]) -> dict[str, Any]:
        """Update a schedule.

        Args:
            schedule_id: ID of the schedule.
            config: Updated schedule configuration.

        Returns:
            Dict with updated schedule info.
        """
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{self._ws()}/projects/{self._proj()}/schedules/{schedule_id}",
            json=config,
        )

    def delete_schedule(self, schedule_id: int) -> dict[str, Any]:
        """Delete a schedule.

        Args:
            schedule_id: ID of the schedule.

        Returns:
            Dict with deletion result.
        """
        return self._client._request_json(
            "DELETE", f"/workspaces/{self._ws()}/projects/{self._proj()}/schedules/{schedule_id}"
        )
