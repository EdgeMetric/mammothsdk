"""Workspace API client for managing workspaces in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothAPIError, MammothValidationError
from mammoth.models.workspaces import CurrentWorkspace, UserRolePatchOp, WorkspacePatchOp

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

# ── Validation error constants ────────────────────────────────────────────────

_USERS_PAGE_LIMIT = 100  # server cap on /users page size

ERR_WORKSPACE_PATCHES_EMPTY = "`patches` must be a non-empty list of patch operations."
ERR_WORKSPACE_USER_ID_EMPTY = "`user_id` must be a non-empty string."
ERR_WORKSPACE_USER_PATCHES_EMPTY = "`patches` must be a non-empty list of patch operations."


class WorkspaceAPI:
    """Client for interacting with Mammoth Workspace API.

    Access via client.workspaces:
        workspaces = client.workspaces.list()
        workspace = client.workspaces.get()
        users = client.workspaces.list_users()
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    async def list(self, limit: int = 100) -> dict[str, Any]:
        """List all accessible workspaces.

        Args:
            limit: Maximum number of results (default 100).

        Returns:
            Dict containing workspaces list with id and name.
        """
        params = {"fields": "id,name", "limit": limit}
        return await self._client._request_json("GET", "/workspaces", params=params)

    async def current(self) -> CurrentWorkspace:
        """Ask which workspace this client's token acts in.

        Returns:
            The workspace's ``id``, and the ``resource`` (RFC 8707) an OAuth
            token was issued for: the URI of the one server the user let it
            reach. ``resource`` is None for a token made by hand, and for a
            token issued for no server.
        """
        answer = await self._client._request_json("GET", "/workspaces/current")
        return CurrentWorkspace.model_validate(answer)

    async def get(self, workspace_id: int | None = None) -> dict[str, Any]:
        """Get details of a specific workspace.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with workspace details.
        """
        ws = workspace_id or self._ws()
        return await self._client._request_json("GET", f"/workspaces/{ws}")

    async def update(
        self,
        patches: _list[WorkspacePatchOp],
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Update workspace settings via JSON-patch operations.

        The backend expects ``{"patches": [<ops>]}``.  Each op has:

        - ``op``: ``"replace"`` (only supported op).
        - ``path``: one of ``name``, ``metadata``, ``plan_id``, ``billing_cycle``.
        - ``value``: type depends on path:

          - ``name`` → ``str`` 1–50 chars
          - ``metadata`` → ``dict``
          - ``plan_id`` → ``int``
          - ``billing_cycle`` → ``"monthly"``, ``"yearly"``, or ``"annual"``

        Args:
            patches: Non-empty list of
                :class:`~mammoth.models.workspaces.WorkspacePatchOp` instances.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with updated workspace info.

        Raises:
            MammothValidationError: If ``patches`` is empty.
        """
        if not patches:
            raise MammothValidationError(ERR_WORKSPACE_PATCHES_EMPTY)
        ws = workspace_id or self._ws()
        body = {"patches": [{"op": p.op, "path": p.path.value, "value": p.value} for p in patches]}
        return await self._client._request_json("PATCH", f"/workspaces/{ws}", json=body)

    async def delete(self, workspace_id: int | None = None) -> dict[str, Any]:
        """Delete a workspace.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = workspace_id or self._ws()
        return await self._client._request_json("DELETE", f"/workspaces/{ws}")

    async def reactivate(self, workspace_id: int | None = None) -> dict[str, Any]:
        """Reactivate a deactivated workspace.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with reactivation result.
        """
        ws = workspace_id or self._ws()
        return await self._client._request_json("POST", f"/workspaces/{ws}/reactivate")

    async def list_users(
        self,
        workspace_id: int | None = None,
        fields: str | None = None,
        project_id: int | None = None,
    ) -> _list[dict[str, Any]]:
        """List all users in a workspace (or the members of one project).

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            fields: Field set to return (e.g. ``"__full"`` adds ``user_roles`` and
                ``status``); server default if omitted.
            project_id: Keep only members of this project.

        Returns:
            List of user dicts. Pending invites are not included; see
            ``WorkspacesAPI.invite_list``.
        """
        ws = workspace_id or self._ws()
        base_params: dict[str, Any] = {
            key: value
            for key, value in (("fields", fields), ("project_id", project_id))
            if value is not None
        }
        # The endpoint pages (server default 10, cap 100): read every page so
        # "all users" and get_user() do not stop at the first one.
        users: _list[dict[str, Any]] = []
        offset = 0
        while True:
            response = await self._client._request_json(
                "GET",
                f"/workspaces/{ws}/users",
                params={**base_params, "limit": _USERS_PAGE_LIMIT, "offset": offset},
            )
            if isinstance(response, _list):
                return response
            page = response.get("users", [])
            users.extend(page)
            if len(page) < _USERS_PAGE_LIMIT:
                return users
            offset += _USERS_PAGE_LIMIT

    async def get_user(self, user_id: str, workspace_id: int | None = None) -> dict[str, Any]:
        """Get one workspace user, with roles and status.

        The API has no GET for a single workspace user, so this reads the
        member list (``__full`` fields) and returns the matching entry.

        Args:
            user_id: ID of the user.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with user details.

        Raises:
            MammothAPIError: 404 when the user is not in the workspace.
        """
        for user in await self.list_users(workspace_id=workspace_id, fields="__full"):
            if str(user.get("id")) == str(user_id):
                return user
        raise MammothAPIError(f"User {user_id} is not in this workspace.", status_code=404)

    async def update_user(
        self,
        user_id: str,
        patches: _list[UserRolePatchOp],
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a user's role in the workspace via JSON-patch operations.

        The backend expects ``{"patches": [{"op": "replace", "path": "role",
        "value": "<role>"}]}``.

        Allowed role values (:class:`~mammoth.models.workspaces.WorkspaceRoleType`):
        ``workspace_member``, ``workspace_admin``, ``workspace_owner``,
        ``workspace_guest``.

        Args:
            user_id: Non-empty ID of the user to update.
            patches: Non-empty list of
                :class:`~mammoth.models.workspaces.UserRolePatchOp` instances.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with updated user info.

        Raises:
            MammothValidationError: If ``user_id`` is empty or ``patches`` is empty.
        """
        if not user_id:
            raise MammothValidationError(ERR_WORKSPACE_USER_ID_EMPTY)
        if not patches:
            raise MammothValidationError(ERR_WORKSPACE_USER_PATCHES_EMPTY)
        ws = workspace_id or self._ws()
        body = {"patches": [{"op": p.op, "path": p.path, "value": p.value.value} for p in patches]}
        return await self._client._request_json(
            "PATCH", f"/workspaces/{ws}/users/{user_id}", json=body
        )
