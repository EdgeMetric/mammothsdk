"""User Profile API client for managing user profiles in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient


class UserProfileAPI:
    """Client for managing user profile and settings.

    Access via client.user_profile::

        profile = client.user_profile.get()
        client.user_profile.update(name="New Name")
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def get(self) -> dict[str, Any]:
        """Get current user profile.

        Returns:
            Dict with user profile information.
        """
        return self._client._request_json("GET", "/user/profile")

    def update(self, **fields: Any) -> dict[str, Any]:
        """Update current user profile.

        Args:
            **fields: Profile fields to update (name, email, etc.).

        Returns:
            Dict with updated profile.
        """
        return self._client._request_json("PATCH", "/user/profile", json=fields)

    def change_password(self, current_password: str, new_password: str) -> dict[str, Any]:
        """Change user password.

        Args:
            current_password: Current password.
            new_password: New password.

        Returns:
            Dict with result.
        """
        return self._client._request_json(
            "POST",
            "/user/change_password",
            json={
                "current_password": current_password,
                "new_password": new_password,
            },
        )

    def get_preferences(self) -> dict[str, Any]:
        """Get user preferences.

        Returns:
            Dict with user preferences.
        """
        return self._client._request_json("GET", "/user/preferences")

    def update_preferences(self, **prefs: Any) -> dict[str, Any]:
        """Update user preferences.

        Args:
            **prefs: Preference fields to update.

        Returns:
            Dict with updated preferences.
        """
        return self._client._request_json("PATCH", "/user/preferences", json=prefs)
