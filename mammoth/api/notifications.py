"""Notifications API client for managing user notifications in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method params named `list`.

ERR_NOTIFICATION_ID_POSITIVE = "`notification_id` must be a positive integer, got {0}."
ERR_PATCH_EMPTY = "`patch` must be a non-empty list."
ERR_PATCH_ITEM_MISSING_KEYS = '`patch` entries must have "op", "path", and "value" keys, got {0!r}.'
ERR_PATCH_OP_INVALID = '`patch` entry `op` must be "replace", got {0!r}.'
ERR_PATCH_PATH_INVALID = "`patch` entry `path` must be one of {valid}, got {value!r}."

VALID_PATCH_PATHS = frozenset(
    {
        "isReadMultiple",
        "isReadMultipleIds",
        "isRead",
        "hasPoppedUp",
        "isDismissed",
        "isDeleted",
        "markPersistent",
    }
)


def _validate_patch(patch: list[dict[str, Any]]) -> None:
    """Validate the shape of a notifications JSON-patch list."""
    if not patch:
        raise MammothValidationError(ERR_PATCH_EMPTY)
    for item in patch:
        if not {"op", "path", "value"}.issubset(item):
            raise MammothValidationError(ERR_PATCH_ITEM_MISSING_KEYS.format(item))
        if item["op"] != "replace":
            raise MammothValidationError(ERR_PATCH_OP_INVALID.format(item["op"]))
        if item["path"] not in VALID_PATCH_PATHS:
            raise MammothValidationError(
                ERR_PATCH_PATH_INVALID.format(valid=sorted(VALID_PATCH_PATHS), value=item["path"])
            )


class NotificationsAPI:
    """Client for managing user notifications.

    Access via ``client.notifications``::

        notifications = client.notifications.list()
        client.notifications.update(
            notification_id, patch=[{"op": "replace", "path": "isRead", "value": True}]
        )
        client.notifications.delete(notification_id)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def list(
        self,
        fields: str | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
        last_updated_at__gte: str | None = None,
        status: str | None = None,
        is_read: bool | None = None,
        notification_scope: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List notifications for the current user.

        Args:
            fields: Fields to return.
            workspace_id: Filter by workspace ID.
            project_id: Filter by project ID.
            last_updated_at__gte: Only notifications updated at or after this
                timestamp.
            status: Filter by notification status.
            is_read: Filter by read/unread state.
            notification_scope: Filter by notification scope.
            limit: Maximum number of results.
            offset: Number of results to skip.
            sort: Sort specification.

        Returns:
            Dict with the notifications list.
        """
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        if project_id is not None:
            params["project_id"] = project_id
        if last_updated_at__gte is not None:
            params["last_updated_at__gte"] = last_updated_at__gte
        if status is not None:
            params["status"] = status
        if is_read is not None:
            params["is_read"] = is_read
        if notification_scope is not None:
            params["notification_scope"] = notification_scope
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sort is not None:
            params["sort"] = sort
        return self._client._request_json("GET", "/notifications", params=params or None)

    def delete(self, notification_id: int) -> dict[str, Any]:
        """Delete a single notification.

        Args:
            notification_id: ID of the notification to delete (must be > 0).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *notification_id* is not positive.
        """
        if notification_id <= 0:
            raise MammothValidationError(ERR_NOTIFICATION_ID_POSITIVE.format(notification_id))
        return self._client._request_json("DELETE", f"/notifications/{notification_id}")

    def delete_batch(
        self,
        workspace_id: int | None = None,
        ids: _list[int] | None = None,
        last_updated_at__lt: str | None = None,
        is_read: bool | None = None,
    ) -> dict[str, Any]:
        """Delete multiple notifications matching the given filters.

        Args:
            workspace_id: Filter by workspace ID.
            ids: Specific notification IDs to delete.
            last_updated_at__lt: Only notifications updated before this
                timestamp.
            is_read: Filter by read/unread state.

        Returns:
            Dict with the deletion result.
        """
        params: dict[str, Any] = {}
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        if ids is not None:
            params["ids"] = ",".join(str(i) for i in ids)
        if last_updated_at__lt is not None:
            params["last_updated_at__lt"] = last_updated_at__lt
        if is_read is not None:
            params["is_read"] = is_read
        return self._client._request_json("DELETE", "/notifications", params=params or None)

    def update(self, notification_id: int, patch: _list[dict[str, Any]]) -> dict[str, Any]:
        """Update a single notification via JSON-patch operations.

        Args:
            notification_id: ID of the notification to update (must be > 0).
            patch: Non-empty list of ``{"op": "replace", "path": ..., "value": ...}``
                dicts. ``path`` must be one of: ``isReadMultiple``,
                ``isReadMultipleIds``, ``isRead``, ``hasPoppedUp``,
                ``isDismissed``, ``isDeleted``, ``markPersistent``.

        Returns:
            Dict with the updated notification.

        Raises:
            MammothValidationError: If *notification_id* is not positive, or
                *patch* is empty or malformed.
        """
        if notification_id <= 0:
            raise MammothValidationError(ERR_NOTIFICATION_ID_POSITIVE.format(notification_id))
        _validate_patch(patch)
        return self._client._request_json(
            "PATCH", f"/notifications/{notification_id}", json={"patch": patch}
        )

    def update_batch(
        self,
        patch: _list[dict[str, Any]],
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Update multiple notifications via JSON-patch operations.

        Args:
            patch: Non-empty list of ``{"op": "replace", "path": ..., "value": ...}``
                dicts. ``path`` must be one of: ``isReadMultiple``,
                ``isReadMultipleIds``, ``isRead``, ``hasPoppedUp``,
                ``isDismissed``, ``isDeleted``, ``markPersistent``.
            workspace_id: Filter by workspace ID.

        Returns:
            Dict with the update result.

        Raises:
            MammothValidationError: If *patch* is empty or malformed.
        """
        _validate_patch(patch)
        params: dict[str, Any] = {}
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        return self._client._request_json(
            "PATCH", "/notifications", params=params or None, json={"patch": patch}
        )
