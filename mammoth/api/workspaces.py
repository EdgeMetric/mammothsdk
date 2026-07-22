"""Workspaces API client for cross-workspace operations in Mammoth.

Covers workspace creation, invite acceptance, AI/LLM helpers scoped to a
workspace (expression checking, unified LLM tasks), split-testing segments,
app usage / storage breakdown reporting, and workspace-user management
(invite, remove, update role). This is a thin typed wrapper over the REST
endpoints — no confirmation prompts or business logic live here; that
belongs to callers (e.g. the CLI).

.. note::

    An existing, distinct sub-client ``mammoth.api.workspace.WorkspaceAPI``
    (singular) already covers single-workspace CRUD (get/update/delete/
    reactivate) and per-user detail lookups. This module is a separate,
    additional surface and does not replace it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

_list = list  # Alias to avoid shadowing by method name

# ── Validation error constants ────────────────────────────────────────────────

ERR_TOKEN_EMPTY = "`token` must be a non-empty string."
ERR_TASK_TYPE_EMPTY = "`task_type` must be a non-empty string."
ERR_USER_ID_POSITIVE = "`user_id` must be a positive integer, got {0}."
ERR_EMAIL_IDS_EMPTY = "`email_ids` must be a non-empty list of email addresses."
ERR_SEGMENT_PATCH_EMPTY = "`patch` must be a non-empty list of patch operations."
ERR_USER_PATCHES_EMPTY = "`patches` must be a non-empty list of patch operations."


class WorkspacesAPI:
    """Client for cross-workspace operations (invites, LLM tasks, usage
    reporting, split-test segments, and workspace-user management).

    Wired onto :class:`~mammoth.client.MammothClient` by the client itself;
    see the client's attribute docs for the exact access name.

    Example (assuming an ``api`` instance bound to a client)::

        api.accept_invite("invite_token")
        api.create({"name": "New workspace"})
        usage = api.app_usage()
        api.user_add(["a@example.com"])
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    # ── Invites & creation ───────────────────────────────────────────────────

    def accept_invite(self, token: str) -> dict[str, Any]:
        """Accept a pending workspace invite.

        Args:
            token: Non-empty invite token.

        Returns:
            Dict with the acceptance result.

        Raises:
            MammothValidationError: If ``token`` is empty.
        """
        if not token:
            raise MammothValidationError(ERR_TOKEN_EMPTY)
        return self._client._request_json("POST", "/accept-invite", json={"token": token})

    def create(self, body: dict[str, Any]) -> dict[str, Any]:
        """Create a new workspace.

        Args:
            body: Workspace creation payload (e.g. ``{"name": "..."}``).

        Returns:
            Dict with the created workspace info.
        """
        return self._client._request_json("POST", "/workspaces", json=body)

    # ── AI / LLM helpers ─────────────────────────────────────────────────────

    def check_expression(self, body: dict[str, Any]) -> dict[str, Any]:
        """Ask the AI assistant to check/validate an expression.

        Args:
            body: Check-expression request payload.

        Returns:
            Dict with the check result.
        """
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/ai/check-expression", json=body
        )

    def llm_task(self, task_type: str, params: dict[str, Any]) -> dict[str, Any]:
        """Submit a unified LLM task (rename columns, generate dataset, generate summary).

        Args:
            task_type: Task type — one of ``"rename_columns"``,
                ``"generate_dataset"``, ``"generate_summary"``.
            params: Task-specific parameter dict (shape depends on ``task_type``).

        Returns:
            Dict with the job response for the submitted LLM task.

        Raises:
            MammothValidationError: If ``task_type`` is empty.
        """
        if not task_type:
            raise MammothValidationError(ERR_TASK_TYPE_EMPTY)
        body = {"type": task_type, "params": params}
        return self._client._request_json("POST", f"/workspaces/{self._ws()}/llm", json=body)

    # ── Reporting ────────────────────────────────────────────────────────────

    def app_usage(self, fields: str | None = None) -> dict[str, Any]:
        """Get app usage stats for the workspace.

        Args:
            fields: Comma-separated list of fields to include.

        Returns:
            Dict with app usage details.
        """
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/app-usage", params=params or None
        )

    def storage_breakdown(
        self, limit: int | None = None, offset: int | None = None
    ) -> dict[str, Any]:
        """Get a breakdown of storage usage for the workspace.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            Dict with the storage breakdown.
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/storage-breakdown", params=params or None
        )

    # ── Split-test segments ──────────────────────────────────────────────────

    def segment_list(self) -> dict[str, Any]:
        """List split-test segments for the workspace.

        Returns:
            Dict with the segments list.
        """
        return self._client._request_json("GET", f"/workspaces/{self._ws()}/split-segments")

    def segment_update(self, patch: _list[dict[str, Any]]) -> dict[str, Any]:
        """Update split-test segments via JSON-patch operations.

        Args:
            patch: Non-empty list of patch ops, each shaped like
                ``{"op": "add", "path": "segments", "value": "Beta"}``.

        Returns:
            Dict with the updated segments.

        Raises:
            MammothValidationError: If ``patch`` is empty.
        """
        if not patch:
            raise MammothValidationError(ERR_SEGMENT_PATCH_EMPTY)
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{self._ws()}/split-segments",
            json={"patch": patch},
        )

    # ── Workspace users ──────────────────────────────────────────────────────

    def user_add(
        self,
        email_ids: _list[str],
        projects: _list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Invite one or more users to the workspace.

        Args:
            email_ids: Non-empty list of email addresses to invite.
            projects: Optional list of ``{"project_id": int, "role": str}``
                dicts granting project-level roles to the invited users.

        Returns:
            Dict with the invite result.

        Raises:
            MammothValidationError: If ``email_ids`` is empty.
        """
        if not email_ids:
            raise MammothValidationError(ERR_EMAIL_IDS_EMPTY)
        invite: dict[str, Any] = {"email_ids": email_ids}
        if projects is not None:
            invite["projects"] = projects
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/users",
            json={"invite": invite},
        )

    def user_remove(self, user_id: int) -> dict[str, Any]:
        """Remove a single user from the workspace.

        Args:
            user_id: ID of the user (must be > 0).

        Returns:
            Dict with the removal result.

        Raises:
            MammothValidationError: If ``user_id`` is not a positive integer.
        """
        if user_id <= 0:
            raise MammothValidationError(ERR_USER_ID_POSITIVE.format(user_id))
        return self._client._request_json("DELETE", f"/workspaces/{self._ws()}/users/{user_id}")

    def user_remove_batch(
        self,
        ids: str | None = None,
        invite_ids: str | None = None,
    ) -> dict[str, Any]:
        """Remove multiple users and/or pending invites from the workspace.

        Args:
            ids: Comma-separated list of user IDs to remove.
            invite_ids: Comma-separated list of invite IDs to remove.

        Returns:
            Dict with the removal result.
        """
        params: dict[str, Any] = {}
        if ids is not None:
            params["ids"] = ids
        if invite_ids is not None:
            params["invite_ids"] = invite_ids
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{self._ws()}/users",
            params=params or None,
        )

    def user_update_batch(self, patches: _list[dict[str, Any]]) -> dict[str, Any]:
        """Update workspace users via JSON-patch operations.

        Supports role changes, invite resend, and invite role removal, e.g.
        ``{"op": "replace", "path": "role", "value": "1,workspace_member"}``.

        Args:
            patches: Non-empty list of patch ops.

        Returns:
            Dict with the update result.

        Raises:
            MammothValidationError: If ``patches`` is empty.
        """
        if not patches:
            raise MammothValidationError(ERR_USER_PATCHES_EMPTY)
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{self._ws()}/users",
            json={"patches": patches},
        )
