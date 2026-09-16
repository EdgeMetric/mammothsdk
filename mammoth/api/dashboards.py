"""Dashboards API client for managing dashboards in Mammoth."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from mammoth.exceptions import MammothValidationError
from mammoth.models.dashboards import (
    AddPagesResponse,
    AddPagesSpec,
    ContextExtractResponse,
    ContextExtractSpec,
    CreateBlankParams,
    DashboardActionType,
    DashboardAuthType,
    DashboardPatchItem,
    DashboardPatchPath,
    DashboardShareUser,
    DashboardTagsParams,
    TagMergeParams,
    TagRenameParams,
)

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

# ── Validation error constants ────────────────────────────────────────────────

ERR_DASHBOARD_ID_POSITIVE = "`dashboard_id` must be a positive integer, got {0}."
ERR_INTENT_TOO_SHORT = "`intent` must be at least 10 characters, got {0!r}."
ERR_SOURCE_EMPTY = "`source` must be a non-empty list of dataview IDs."
ERR_SOURCE_IDS_POSITIVE = "All `source` IDs must be positive integers; got invalid ID {0}."
ERR_PATCH_EMPTY = "`patch` must be a non-empty list of patch operations."
ERR_INTENT_VALUE_TOO_SHORT = "Patch value for `intent` must be at least 10 characters, got {0!r}."
ERR_INTENT_VALUE_NOT_STR = "Patch value for `intent` must be a string."
ERR_TITLE_VALUE_NOT_STR = "Patch value for `title` must be a string."
ERR_THEME_VALUE_NOT_STR = "Patch value for `theme` must be a string."
ERR_SHARE_USER_EMAIL_EMPTY = "Each shared user must have a non-empty `email`."
ERR_AUTO_SYNC_NEEDS_ENABLED = "`auto-sync` action requires `params_enabled` (bool)."
ERR_AUTO_PUBLISH_NEEDS_ENABLED = "`auto-publish` action requires `params_enabled` (bool)."
ERR_DELETE_SOURCE_NEEDS_VIEW_ID = "`delete-source` action requires `params_view_id` (int > 0)."
ERR_VIEW_ID_POSITIVE = "`params_view_id` must be a positive integer, got {0}."
ERR_JOB_ID_POSITIVE = "`job_id` must be a positive integer, got {0}."

_INTENT_MIN_LEN = 10


class DashboardsAPI:
    """Client for managing Mammoth dashboards.

    Access via ``client.dashboards``::

        dashboards = client.dashboards.list()
        dashboard = client.dashboards.create(
            intent="Show quarterly revenue by region",
            source=[101, 102],
        )
        client.dashboards.share(
            dashboard_id=5,
            type_of_auth=DashboardAuthType.PUBLIC,
        )
        client.dashboards.delete(dashboard_id=5)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def list(self, project_id: int | None = None) -> _list[dict[str, Any]]:
        """List all dashboards.

        Returns:
            List of dashboard dicts.
        """
        params = {"project_id": project_id} if project_id is not None else None
        response = self._client._request_json("GET", "/dashboards", params=params)
        return response.get("dashboards", response if isinstance(response, _list) else [])

    def list_tags(self) -> dict[str, Any]:
        """List the workspace dashboard-tag vocabulary."""
        return self._client._request_json("GET", "/dashboards/tags")

    def rename_tag(self, tag_id: int, name: str) -> dict[str, Any]:
        """Rename one workspace dashboard tag using the release request shape."""
        if isinstance(tag_id, bool) or not isinstance(tag_id, int) or tag_id <= 0:
            raise MammothValidationError(
                f"`tag_id` must be a positive integer, got {tag_id}."
            )
        try:
            typed = TagRenameParams(name=name)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid tag rename parameters: {exc}") from exc
        if not typed.name.strip():
            raise MammothValidationError("`name` must be non-blank.")
        return self._client._request_json(
            "PATCH", f"/dashboards/tags/{tag_id}", json=typed.model_dump(mode="json")
        )

    def set_tags(self, dashboard_id: int, tags: builtins.list[str]) -> dict[str, Any]:
        """Replace a dashboard's complete tag set using the release request shape."""
        if (
            isinstance(dashboard_id, bool)
            or not isinstance(dashboard_id, int)
            or dashboard_id <= 0
        ):
            raise MammothValidationError(
                f"`dashboard_id` must be a positive integer, got {dashboard_id}."
            )
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            raise MammothValidationError("`tags` must be a list of strings.")
        if len(tags) != len(set(tags)):
            raise MammothValidationError("`tags` must not contain duplicates.")
        try:
            typed = DashboardTagsParams(tags=tags)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid dashboard tags parameters: {exc}") from exc
        return self._client._request_json(
            "PUT", f"/dashboards/{dashboard_id}/tags", json=typed.model_dump(mode="json")
        )

    def delete_tag(self, tag_id: int) -> dict[str, Any] | None:
        """Delete a tag from the workspace vocabulary."""
        if isinstance(tag_id, bool) or not isinstance(tag_id, int) or tag_id <= 0:
            raise MammothValidationError(
                f"`tag_id` must be a positive integer, got {tag_id}."
            )
        return self._client._request_json("DELETE", f"/dashboards/tags/{tag_id}")

    def merge_tag(self, tag_id: int, target_id: int) -> dict[str, Any]:
        """Merge one workspace tag into another using the release request shape."""
        for name, value in (("tag_id", tag_id), ("target_id", target_id)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise MammothValidationError(
                    f"`{name}` must be a positive integer, got {value}."
                )
        if tag_id == target_id:
            raise MammothValidationError("`tag_id` and `target_id` must differ.")
        try:
            typed = TagMergeParams(target_id=target_id)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid tag merge parameters: {exc}") from exc
        return self._client._request_json(
            "POST", f"/dashboards/tags/{tag_id}/merge", json=typed.model_dump(mode="json")
        )

    def create(
        self,
        intent: str,
        source: _list[int],
        enable_filters: bool = True,
        enable_pages: bool = False,
    ) -> dict[str, Any]:
        """Create a new AI-generated dashboard.

        Args:
            intent: Natural-language description of what the dashboard should
                show (minimum 10 characters).
            source: Non-empty list of dataview IDs to use as the data source.
                All IDs must be positive integers; existence is validated
                server-side.
            enable_filters: Whether to include filter widgets (default ``True``).
            enable_pages: Whether to generate multiple pages (default ``False``).

        Returns:
            Dict with created dashboard info (may include a job ID for async
            creation).

        Raises:
            MammothValidationError: If *intent* is shorter than 10 characters,
                *source* is empty, or any source ID is not a positive integer.
        """
        if len(intent) < _INTENT_MIN_LEN:
            raise MammothValidationError(ERR_INTENT_TOO_SHORT.format(intent))
        if not source:
            raise MammothValidationError(ERR_SOURCE_EMPTY)
        for sid in source:
            if sid <= 0:
                raise MammothValidationError(ERR_SOURCE_IDS_POSITIVE.format(sid))

        body: dict[str, Any] = {
            "params": {
                "intent": intent,
                "source": source,
                "enable_filters": enable_filters,
                "enable_pages": enable_pages,
            }
        }
        return self._client._request_json("POST", "/dashboards", json=body)

    def create_blank(self, params: CreateBlankParams) -> dict[str, Any]:
        """Create an empty v3 dashboard bound to a dataview.

        The release endpoint returns the created dashboard ``id`` and seeded
        canvas ``sequence``. Style is an unrestricted release string with a
        default of ``dashboard``; the server owns any further style policy.
        """
        try:
            typed = (
                params
                if isinstance(params, CreateBlankParams)
                else CreateBlankParams.model_validate(params)
            )
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid blank dashboard parameters: {exc}") from exc
        if typed.dataview_id <= 0:
            raise MammothValidationError(
                f"`dataview_id` must be a positive integer, got {typed.dataview_id}."
            )
        return self._client._request_json(
            "POST",
            "/dashboards/v3/blank",
            json={"params": typed.model_dump(mode="json", exclude_unset=True)},
        )

    def get(self, dashboard_id: int) -> dict[str, Any]:
        """Get dashboard details.

        Args:
            dashboard_id: ID of the dashboard.

        Returns:
            Dict with dashboard details.
        """
        return self._client._request_json("GET", f"/dashboards/{dashboard_id}")

    def add_pages(self, dashboard_id: int, body: AddPagesSpec) -> AddPagesResponse:
        """Append structural pages and start the asynchronous dashboard bake."""
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        try:
            typed = body if isinstance(body, AddPagesSpec) else AddPagesSpec.model_validate(body)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid add-pages parameters: {exc}") from exc
        response = self._client._request_json(
            "POST",
            f"/dashboards/{dashboard_id}/pages",
            json=typed.model_dump(mode="json", exclude_none=True),
        )
        try:
            return AddPagesResponse.model_validate(response)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid add-pages response: {exc}") from exc

    def extract_context(self, body: ContextExtractSpec) -> dict[str, Any]:
        """Extract a context file into slot suggestions (release route)."""
        try:
            typed = (
                body
                if isinstance(body, ContextExtractSpec)
                else ContextExtractSpec.model_validate(body)
            )
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid context-extract parameters: {exc}") from exc
        response = self._client._request_json(
            "POST", "/dashboards/v3/contexts/extract",
            json=typed.model_dump(mode="json", exclude_none=True),
        )
        try:
            return ContextExtractResponse.model_validate(response).model_dump(mode="json")
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid context-extract response: {exc}") from exc

    def update(
        self,
        dashboard_id: int,
        patch: _list[DashboardPatchItem],
    ) -> dict[str, Any]:
        """Update a dashboard via JSON-patch operations.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            patch: Non-empty list of :class:`~mammoth.models.dashboards.DashboardPatchItem`
                describing the operations to apply.

                Supported combos:

                * ``op=add, path=intent`` — trigger AI edit; value must be str ≥ 10 chars.
                * ``op=replace, path=title`` — rename dashboard; value must be str.
                * ``op=replace, path=theme`` — change theme; value must be str.

        Returns:
            Dict with updated dashboard info.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0, *patch* is empty, or
                an ``intent`` value is too short / a ``title``/``theme`` value is
                not a string.
        """
        if dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        if not patch:
            raise MammothValidationError(ERR_PATCH_EMPTY)
        for item in patch:
            _validate_patch_item(item)

        body: dict[str, Any] = {
            "patch": [
                {"op": item.op.value, "path": item.path.value, "value": item.value}
                for item in patch
            ]
        }
        return self._client._request_json("PATCH", f"/dashboards/{dashboard_id}", json=body)

    def delete(self, dashboard_id: int) -> dict[str, Any]:
        """Delete a dashboard.

        Args:
            dashboard_id: ID of the dashboard.

        Returns:
            Dict with deletion result.
        """
        return self._client._request_json("DELETE", f"/dashboards/{dashboard_id}")

    def archive(self, dashboard_id: int, archived: bool) -> Any:
        """Set whether a dashboard is archived.

        ``archived=True`` archives the dashboard and ``archived=False``
        restores it. The API declares no response body schema, so the raw
        response is returned unchanged.
        """
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        if not isinstance(archived, bool):
            raise MammothValidationError("`archived` must be a boolean.")
        return self._client._request_json(
            "POST", f"/dashboards/{dashboard_id}/archive", json={"archived": archived}
        )

    def get_sources(self) -> _list[dict[str, Any]]:
        """Get available dashboard data sources.

        .. note::

            This endpoint may return HTTP 500 on some server configurations.

        Returns:
            List of source dicts.
        """
        response = self._client._request_json("GET", "/dashboards/sources")
        return response.get("sources", response if isinstance(response, _list) else [])

    def get_analytics(self, dashboard_id: int) -> dict[str, Any]:
        """Get dashboard analytics (views, users).

        Args:
            dashboard_id: ID of the dashboard.

        Returns:
            Dict with analytics data.
        """
        return self._client._request_json("GET", f"/dashboards/{dashboard_id}/analytics")

    def share(
        self,
        dashboard_id: int,
        type_of_auth: DashboardAuthType,
        users: _list[DashboardShareUser] | None = None,
    ) -> dict[str, Any]:
        """Share a dashboard.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            type_of_auth: Authentication model for the shared link.
            users: Optional list of :class:`~mammoth.models.dashboards.DashboardShareUser`
                granting per-user access.  Only used when *type_of_auth* is
                :attr:`~mammoth.models.dashboards.DashboardAuthType.MAMMOTH`;
                ignored for ``public`` / ``password``.  Each user must have a
                non-empty ``email``.

        Returns:
            Dict with sharing result.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0 or any user has an
                empty ``email``.
        """
        if dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        if users is not None:
            for user in users:
                if not user.email:
                    raise MammothValidationError(ERR_SHARE_USER_EMAIL_EMPTY)

        auth_dict: dict[str, Any] = {"type_of_auth": type_of_auth.value}
        if users is not None and type_of_auth is DashboardAuthType.MAMMOTH:
            auth_dict["options"] = {
                "users": [
                    {"email": u.email, "role": u.role.value, "shared": u.shared} for u in users
                ]
            }

        body: dict[str, Any] = {"params": {"auth": auth_dict}}
        return self._client._request_json("POST", f"/dashboards/{dashboard_id}/share", json=body)

    def action(
        self,
        dashboard_id: int,
        action: DashboardActionType,
        params_enabled: bool | None = None,
        params_view_id: int | None = None,
    ) -> dict[str, Any]:
        """Perform an action on a dashboard.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            action: The action to execute.
            params_enabled: Required for ``auto-sync`` and ``auto-publish``;
                enables or disables the behaviour.
            params_view_id: Required (> 0) for ``delete-source``;
                optional for ``sync`` and ``auto-sync`` to scope to one source.

        Returns:
            Dict with action result.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0, ``auto-sync`` /
                ``auto-publish`` are called without *params_enabled*, or
                ``delete-source`` is called without a positive *params_view_id*.
        """
        if dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        if action is DashboardActionType.AUTO_SYNC and params_enabled is None:
            raise MammothValidationError(ERR_AUTO_SYNC_NEEDS_ENABLED)
        if action is DashboardActionType.AUTO_PUBLISH and params_enabled is None:
            raise MammothValidationError(ERR_AUTO_PUBLISH_NEEDS_ENABLED)
        if action is DashboardActionType.DELETE_SOURCE:
            if params_view_id is None:
                raise MammothValidationError(ERR_DELETE_SOURCE_NEEDS_VIEW_ID)
            if params_view_id <= 0:
                raise MammothValidationError(ERR_VIEW_ID_POSITIVE.format(params_view_id))
        if params_view_id is not None and params_view_id <= 0:
            raise MammothValidationError(ERR_VIEW_ID_POSITIVE.format(params_view_id))

        body: dict[str, Any] = {"action": action.value}
        params: dict[str, Any] = {}
        if params_enabled is not None:
            params["enabled"] = params_enabled
        if params_view_id is not None:
            params["view_id"] = params_view_id
        if params:
            body["params"] = params

        return self._client._request_json("POST", f"/dashboards/{dashboard_id}/action", json=body)

    def get_by_url(self, url: str) -> dict[str, Any]:
        """Get dashboard by URL slug.

        Args:
            url: Dashboard URL slug.

        Returns:
            Dict with dashboard details.
        """
        return self._client._request_json("GET", f"/dashboards/url/{url}")

    def get_draft_data(self, dashboard_id: int, sql: str) -> dict[str, Any]:
        """Get draft data using SQL query.

        Args:
            dashboard_id: ID of the dashboard.
            sql: SQL query to execute against draft data.

        Returns:
            Dict with query results.
        """
        return self._client._request_json(
            "POST",
            f"/dashboards/{dashboard_id}/getDraftData",
            json={"sql": sql},
        )

    def get_publish_data(self, dashboard_id: int, sql: str) -> dict[str, Any]:
        """Get published data using SQL query.

        Args:
            dashboard_id: ID of the dashboard.
            sql: SQL query to execute against published data.

        Returns:
            Dict with query results.
        """
        return self._client._request_json(
            "POST",
            f"/dashboards/{dashboard_id}/getPublishData",
            json={"sql": sql},
        )

    def cancel_generation(self, dashboard_id: int) -> dict[str, Any]:
        """Cancel an in-progress AI dashboard generation.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).

        Returns:
            Dict with cancellation result.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0.
        """
        if dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        return self._client._request_json("POST", f"/dashboards/{dashboard_id}/cancel-generation")

    def job_by_url(self, url: str, job_id: int) -> dict[str, Any]:
        """Get the status/result of an async dashboard job, addressed by URL slug.

        Args:
            url: Dashboard URL slug.
            job_id: ID of the job (must be > 0).

        Returns:
            Dict with job status/result.

        Raises:
            MammothValidationError: If *job_id* ≤ 0.
        """
        if job_id <= 0:
            raise MammothValidationError(ERR_JOB_ID_POSITIVE.format(job_id))
        return self._client._request_json("GET", f"/dashboards/url/{url}/jobs/{job_id}")

    def published_data_by_url(self, url: str, body: dict[str, Any]) -> dict[str, Any]:
        """Get published dashboard widget data via SQL, addressed by URL slug.

        Args:
            url: Dashboard URL slug.
            body: Widget data request payload (``WidgetDataSpec``), e.g.
                ``{"params": {"widget_id": ..., "global_filters": {...},
                "drilldown_filters": {...}}}``.

        Returns:
            Dict with query results (may include a job ID for async execution).
        """
        return self._client._request_json(
            "POST", f"/dashboards/url/{url}/getPublishData", json=body
        )

    def restore(self, dashboard_id: int) -> dict[str, Any]:
        """Restore a trashed dashboard.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).

        Returns:
            Dict with restore result.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0.
        """
        if dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        return self._client._request_json("POST", f"/dashboards/{dashboard_id}/restore")

    def trash(self, dashboard_id: int) -> dict[str, Any]:
        """Move a dashboard to trash.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).

        Returns:
            Dict with trash result.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0.
        """
        if dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        return self._client._request_json("POST", f"/dashboards/{dashboard_id}/trash")

    def widget_data(self, dashboard_id: int, body: dict[str, Any]) -> dict[str, Any]:
        """Get data for multiple dashboard widgets in bulk.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            body: Bulk widget data request payload (``BulkWidgetDataSpec``).

        Returns:
            Dict with per-widget data results.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0.
        """
        if dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        return self._client._request_json(
            "POST", f"/dashboards/{dashboard_id}/widgets/data", json=body
        )

    def widget_data_by_url(self, url: str, body: dict[str, Any]) -> dict[str, Any]:
        """Get data for multiple dashboard widgets in bulk, addressed by URL slug.

        Args:
            url: Dashboard URL slug.
            body: Bulk widget data request payload (``BulkWidgetDataSpec``).

        Returns:
            Dict with per-widget data results.
        """
        return self._client._request_json("POST", f"/dashboards/url/{url}/widgets/data", json=body)


# ── Private helpers ───────────────────────────────────────────────────────────


def _validate_patch_item(item: DashboardPatchItem) -> None:
    """Raise MammothValidationError if the patch item's value constraints fail."""
    if item.path is DashboardPatchPath.INTENT:
        if not isinstance(item.value, str):
            raise MammothValidationError(ERR_INTENT_VALUE_NOT_STR)
        if len(item.value) < _INTENT_MIN_LEN:
            raise MammothValidationError(ERR_INTENT_VALUE_TOO_SHORT.format(item.value))
    elif item.path is DashboardPatchPath.TITLE:
        if not isinstance(item.value, str):
            raise MammothValidationError(ERR_TITLE_VALUE_NOT_STR)
    elif item.path is DashboardPatchPath.THEME:
        if not isinstance(item.value, str):
            raise MammothValidationError(ERR_THEME_VALUE_NOT_STR)


# Generated from the pinned production OpenAPI operation inventory. Keeping
# these as ordinary functions preserves inspectable typed signatures for SDK
# users and the CLI schema builder while avoiding hand-maintained route drift.
from mammoth.api import dashboard_generated as _generated  # noqa: E402

for _method_name in _generated.GENERATED_METHODS:
    setattr(DashboardsAPI, _method_name, getattr(_generated, _method_name))
