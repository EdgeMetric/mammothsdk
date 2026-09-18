"""User Profile API client for managing user profiles in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..exceptions import MammothValidationError

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
        return self._client._request_json("GET", "/self")

    def update(self, **fields: Any) -> dict[str, Any]:
        """Update current user profile.

        Args:
            **fields: Profile fields to update (name, email, etc.).

        Returns:
            Dict with updated profile.
        """
        return self._client._request_json("PATCH", "/self", json=fields)

    def change_password(self, current_password: str, new_password: str) -> dict[str, Any]:
        """Change user password.

        Note: This endpoint is not documented in the public OpenAPI spec.

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
        return self._client._request_json("GET", "/preferences")

    def update_preferences(
        self, patch: list[dict[str, Any]] | None = None, **prefs: Any
    ) -> dict[str, Any]:
        """Update user preferences.

        The route takes ``{"patch": [{"op": "replace", "path": ..., "value": ...}]}``
        where ``path`` is a dot-separated preference path rooted at ``GLOBAL``
        or ``WORKSPACE_PREFERENCES`` (for example
        ``GLOBAL.PREFERENCES.TOP_TABS``). Keyword arguments are turned into
        ``replace`` operations on the given path.

        Args:
            patch: Explicit patch operations.
            **prefs: ``path=value`` shortcuts, each becoming a ``replace``.

        Returns:
            Dict with updated preferences.
        """
        operations = list(patch or [])
        operations.extend(
            {"op": "replace", "path": path, "value": value} for path, value in prefs.items()
        )
        if not operations:
            raise MammothValidationError("Provide `patch` operations or path=value preferences.")
        return self._client._request_json("PATCH", "/preferences", json={"patch": operations})
