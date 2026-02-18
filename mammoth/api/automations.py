"""
Automations API client for managing automations and schedules in Mammoth.
"""

from typing import Dict, Any


class AutomationsAPI:
    """Client for managing automations and schedules.

    Access via client.automations:
        automations = client.automations.list()
        automation = client.automations.create(config={...})
        schedules = client.automations.list_schedules()
        client.automations.create_schedule(config={...})
    """

    def __init__(self, client):
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    # ── Automations ──────────────────────────────────────────────

    def list(self) -> list:
        """List all automations.

        Returns:
            List of automation dicts.
        """
        response = self._client._request("GET", f"/workspaces/{self._ws()}/automations")
        return response.get("automations", response if isinstance(response, list) else [])

    def create(self, config: Dict[str, Any]) -> dict:
        """Create a new automation.

        Args:
            config: Automation configuration (name, triggers, actions, etc.).

        Returns:
            Dict with created automation info.
        """
        return self._client._request("POST", f"/workspaces/{self._ws()}/automations", json=config)

    def get(self, automation_id: int) -> dict:
        """Get automation details.

        Args:
            automation_id: ID of the automation.

        Returns:
            Dict with automation details.
        """
        return self._client._request("GET", f"/workspaces/{self._ws()}/automations/{automation_id}")

    def update(self, automation_id: int, config: Dict[str, Any]) -> dict:
        """Update an automation.

        Args:
            automation_id: ID of the automation.
            config: Updated automation configuration.

        Returns:
            Dict with updated automation info.
        """
        return self._client._request("PATCH", f"/workspaces/{self._ws()}/automations/{automation_id}", json=config)

    def delete(self, automation_id: int) -> dict:
        """Delete an automation.

        Args:
            automation_id: ID of the automation.

        Returns:
            Dict with deletion result.
        """
        return self._client._request("DELETE", f"/workspaces/{self._ws()}/automations/{automation_id}")

    # ── Schedules ────────────────────────────────────────────────

    def list_schedules(self) -> list:
        """List all schedules.

        Returns:
            List of schedule dicts.
        """
        response = self._client._request("GET", f"/workspaces/{self._ws()}/schedules")
        return response.get("schedules", response if isinstance(response, list) else [])

    def create_schedule(self, config: Dict[str, Any]) -> dict:
        """Create a new schedule.

        Args:
            config: Schedule configuration (cron, timezone, actions, etc.).

        Returns:
            Dict with created schedule info.
        """
        return self._client._request("POST", f"/workspaces/{self._ws()}/schedules", json=config)

    def update_schedule(self, schedule_id: int, config: Dict[str, Any]) -> dict:
        """Update a schedule.

        Args:
            schedule_id: ID of the schedule.
            config: Updated schedule configuration.

        Returns:
            Dict with updated schedule info.
        """
        return self._client._request("PATCH", f"/workspaces/{self._ws()}/schedules/{schedule_id}", json=config)

    def delete_schedule(self, schedule_id: int) -> dict:
        """Delete a schedule.

        Args:
            schedule_id: ID of the schedule.

        Returns:
            Dict with deletion result.
        """
        return self._client._request("DELETE", f"/workspaces/{self._ws()}/schedules/{schedule_id}")
