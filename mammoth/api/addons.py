"""Addons API client for managing workspace addons in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias: the AddonsAPI.list method shadows the builtin in annotations.

# Argument validation messages (raised before any API call).
ERR_CONNECTOR_ONE_REQUIRED = "Provide exactly one of `connector_id` or `connector_ids`."
ERR_CONNECTOR_IDS_EMPTY = "`connector_ids` must be a non-empty list."
ERR_CONNECTOR_ID_POSITIVE = "Connector ids must be positive integers (got {value})."
ERR_STORAGE_GB_POSITIVE = "`{field}` must be a positive integer (got {value})."
ERR_USER_COUNT_POSITIVE = "`user_count` must be a positive integer (got {value})."


def _connector_body(connector_id: int | None, connector_ids: list[int] | None) -> dict[str, Any]:
    """Validate and build the connector-addon request body.

    Exactly one of *connector_id* (single) or *connector_ids* (bulk) must be
    given; all ids must be positive.
    """
    if (connector_id is None) == (connector_ids is None):
        raise MammothValidationError(ERR_CONNECTOR_ONE_REQUIRED)
    if connector_ids is not None:
        if not connector_ids:
            raise MammothValidationError(ERR_CONNECTOR_IDS_EMPTY)
        bad = next((i for i in connector_ids if i <= 0), None)
        if bad is not None:
            raise MammothValidationError(ERR_CONNECTOR_ID_POSITIVE.format(value=bad))
        return {"connector_ids": connector_ids}
    if connector_id <= 0:  # type: ignore[operator]
        raise MammothValidationError(ERR_CONNECTOR_ID_POSITIVE.format(value=connector_id))
    return {"connector_id": connector_id}


class AddonsAPI:
    """Client for managing workspace addons (connectors, storage, users).

    Access via client.addons::

        client.addons.add_connector(connector_id=42)
        client.addons.add_connector(connector_ids=[42, 43])
        client.addons.add_storage(additional_storage_gb=50)
        client.addons.add_users(user_count=5)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(self) -> dict[str, Any]:
        """List active addons for the workspace.

        Returns:
            Dict with addon information.
        """
        ws = self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}/addons")

    def add_connector(
        self,
        connector_id: int | None = None,
        connector_ids: _list[int] | None = None,
    ) -> dict[str, Any]:
        """Add one or more connector addons to the workspace.

        Provide exactly one of *connector_id* (single) or *connector_ids* (bulk).

        Args:
            connector_id: A single connector id to add.
            connector_ids: A non-empty list of connector ids to add.

        Returns:
            Dict with addon result.

        Raises:
            MammothValidationError: If neither or both arguments are given, or
                any id is not a positive integer.
        """
        ws = self._ws()
        body = _connector_body(connector_id, connector_ids)
        return self._client._request_json("POST", f"/workspaces/{ws}/addons/connectors", json=body)

    def remove_connector(
        self,
        connector_id: int | None = None,
        connector_ids: _list[int] | None = None,
    ) -> dict[str, Any]:
        """Remove one or more connector addons from the workspace.

        Provide exactly one of *connector_id* (single) or *connector_ids* (bulk).

        Args:
            connector_id: A single connector id to remove.
            connector_ids: A non-empty list of connector ids to remove.

        Returns:
            Dict with removal result.

        Raises:
            MammothValidationError: If neither or both arguments are given, or
                any id is not a positive integer.
        """
        ws = self._ws()
        body = _connector_body(connector_id, connector_ids)
        return self._client._request_json(
            "DELETE", f"/workspaces/{ws}/addons/connectors", json=body
        )

    def add_storage(self, additional_storage_gb: int) -> dict[str, Any]:
        """Add storage capacity to the workspace.

        Args:
            additional_storage_gb: GB of storage to add (positive integer).

        Returns:
            Dict with addon result.

        Raises:
            MammothValidationError: If *additional_storage_gb* is not positive.
        """
        if additional_storage_gb <= 0:
            raise MammothValidationError(
                ERR_STORAGE_GB_POSITIVE.format(
                    field="additional_storage_gb", value=additional_storage_gb
                )
            )
        ws = self._ws()
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/addons/storage",
            json={"additional_storage_gb": additional_storage_gb},
        )

    def remove_storage(self, removal_storage_gb: int) -> dict[str, Any]:
        """Remove storage capacity from the workspace.

        Args:
            removal_storage_gb: GB of storage to remove (positive integer).

        Returns:
            Dict with removal result.

        Raises:
            MammothValidationError: If *removal_storage_gb* is not positive.
        """
        if removal_storage_gb <= 0:
            raise MammothValidationError(
                ERR_STORAGE_GB_POSITIVE.format(field="removal_storage_gb", value=removal_storage_gb)
            )
        ws = self._ws()
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/addons/storage",
            json={"removal_storage_gb": removal_storage_gb},
        )

    def add_users(self, user_count: int = 1) -> dict[str, Any]:
        """Add user seats to the workspace.

        Args:
            user_count: Number of seats to add (positive integer, default 1).

        Returns:
            Dict with addon result.

        Raises:
            MammothValidationError: If *user_count* is not positive.
        """
        if user_count <= 0:
            raise MammothValidationError(ERR_USER_COUNT_POSITIVE.format(value=user_count))
        ws = self._ws()
        return self._client._request_json(
            "POST", f"/workspaces/{ws}/addons/users", json={"user_count": user_count}
        )

    def remove_users(self, user_count: int) -> dict[str, Any]:
        """Remove user seats from the workspace.

        Args:
            user_count: Number of seats to remove (positive integer).

        Returns:
            Dict with removal result.

        Raises:
            MammothValidationError: If *user_count* is not positive.
        """
        if user_count <= 0:
            raise MammothValidationError(ERR_USER_COUNT_POSITIVE.format(value=user_count))
        ws = self._ws()
        return self._client._request_json(
            "DELETE", f"/workspaces/{ws}/addons/users", json={"user_count": user_count}
        )
