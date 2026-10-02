"""Dashboards API client for managing dashboards in Mammoth."""

from __future__ import annotations

import asyncio
import base64
import builtins
import os
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import quote

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
    EmbedConfigParams,
    EmbedConfigResponse,
    EmbedKeyResponse,
    EmbedLifetimeResponse,
    EmbedPreviewTokenResponse,
    EmbedSecretResponse,
    EmbedUsageResponse,
    ExemplarExtractResponse,
    ExemplarExtractSpec,
    GenerateV3Params,
    ImportDatasetResponse,
    PbixAssessResponse,
    PendingTemplateResponse,
    PowerBiPreflightResponse,
    SwapDataSpec,
    TableauPreflightResponse,
    TagMergeParams,
    TagRenameParams,
    TwbAssessResponse,
    UseTemplateSpec,
)
from mammoth.models.jobs import JobResponse, ObjectJobSchema

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

# ── Validation error constants ────────────────────────────────────────────────

ERR_DASHBOARD_ID_POSITIVE = "`dashboard_id` must be a positive integer, got {0}."
ERR_DASHBOARD_IDS_EMPTY = "`dashboard_ids` must be a non-empty list of dashboard ids."
ERR_STYLE_EMPTY = "`style` must be a non-empty string."
ERR_TEMPLATE_ID_EMPTY = "`template_id` must be a non-empty template slug."
ERR_SLUG_EMPTY = "`slug` must be a non-empty template slug."
ERR_SWAP_FIT_TARGETS = "`target_dataview_ids` must hold 1 to 60 positive dataview ids."
ERR_SWAP_FIT_SECONDS = "`seconds_budget` must be between 0 and 30, got {0}."
ERR_WINDOW_DAYS = "`days` must be 7, 30 or 90, got {0!r}."
ERR_DIGEST_ENABLED = "`enabled` must be true, false or null, got {0!r}."
ERR_CONTEXT_NOTE_LONG = "`note` must be at most 1000 characters, got {0}."
ERR_REVIEW_ID_EMPTY = "`review_id` must be a non-empty string."
_SWAP_FIT_MAX_TARGETS = 60
_SWAP_FIT_MAX_SECONDS = 30
_AUDIENCE_WINDOWS = frozenset({7, 30, 90})
_CONTEXT_NOTE_MAX = 1000
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
ERR_WORKSPACE_ID_POSITIVE = "`workspace_id` must be a positive integer, got {0}."
ERR_EMBED_ORIGIN_EMPTY = "`origin` must be a non-empty string."
ERR_EMBED_TOKEN_TTL_RANGE = "`token_ttl` must be between 60 and 3600 seconds, got {0}."

_INTENT_MIN_LEN = 10

# Local filename extension for each BI export target's downloaded artifact.
_BI_EXPORT_EXTENSIONS: dict[Literal["powerbi", "tableau"], str] = {
    "powerbi": "zip",
    "tableau": "twbx",
}


class DashboardsAPI:
    """Client for managing Mammoth dashboards.

    Access via ``client.dashboards``::

        dashboards = await client.dashboards.list()
        dashboard = await client.dashboards.create_blank(
            CreateBlankParams(dataview_id=101, title="Revenue by region"),
        )
        await client.dashboards.share(
            dashboard_id=5,
            type_of_auth=DashboardAuthType.PUBLIC,
        )
        await client.dashboards.delete(dashboard_id=5)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    async def list(self, project_id: int | None = None) -> _list[dict[str, Any]]:
        """List all dashboards.

        Returns:
            List of dashboard dicts.
        """
        params = {"project_id": project_id} if project_id is not None else None
        response = await self._client._request_json("GET", "/dashboards", params=params)
        return response.get("dashboards", response if isinstance(response, _list) else [])

    async def list_tags(self) -> dict[str, Any]:
        """List the workspace dashboard-tag vocabulary."""
        return await self._client._request_json("GET", "/dashboards/tags")

    async def rename_tag(self, tag_id: int, name: str) -> dict[str, Any]:
        """Rename one workspace dashboard tag using the release request shape."""
        if isinstance(tag_id, bool) or not isinstance(tag_id, int) or tag_id <= 0:
            raise MammothValidationError(f"`tag_id` must be a positive integer, got {tag_id}.")
        try:
            typed = TagRenameParams(name=name)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid tag rename parameters: {exc}") from exc
        if not typed.name.strip():
            raise MammothValidationError("`name` must be non-blank.")
        return await self._client._request_json(
            "PATCH", f"/dashboards/tags/{tag_id}", json=typed.model_dump(mode="json")
        )

    async def set_tags(self, dashboard_id: int, tags: builtins.list[str]) -> dict[str, Any]:
        """Replace a dashboard's complete tag set using the release request shape."""
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(
                f"`dashboard_id` must be a positive integer, got {dashboard_id}."
            )
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            raise MammothValidationError("`tags` must be a list of strings.")
        try:
            typed = DashboardTagsParams(tags=tags)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid dashboard tags parameters: {exc}") from exc
        return await self._client._request_json(
            "PUT", f"/dashboards/{dashboard_id}/tags", json=typed.model_dump(mode="json")
        )

    async def delete_tag(self, tag_id: int) -> dict[str, Any] | None:
        """Delete a tag from the workspace vocabulary."""
        if isinstance(tag_id, bool) or not isinstance(tag_id, int) or tag_id <= 0:
            raise MammothValidationError(f"`tag_id` must be a positive integer, got {tag_id}.")
        return await self._client._request_json("DELETE", f"/dashboards/tags/{tag_id}")

    async def merge_tag(self, tag_id: int, target_id: int) -> dict[str, Any]:
        """Merge one workspace tag into another using the release request shape."""
        for name, value in (("tag_id", tag_id), ("target_id", target_id)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise MammothValidationError(f"`{name}` must be a positive integer, got {value}.")
        if tag_id == target_id:
            raise MammothValidationError("`tag_id` and `target_id` must differ.")
        try:
            typed = TagMergeParams(target_id=target_id)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid tag merge parameters: {exc}") from exc
        return await self._client._request_json(
            "POST", f"/dashboards/tags/{tag_id}/merge", json=typed.model_dump(mode="json")
        )

    async def create_blank(self, params: CreateBlankParams) -> dict[str, Any]:
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
        return await self._client._request_json(
            "POST",
            "/dashboards/v3/blank",
            json={"params": typed.model_dump(mode="json", exclude_unset=True)},
        )

    async def generate_v3(self, params: GenerateV3Params | dict[str, Any]) -> dict[str, Any]:
        """Have Mammoth build a v3 dashboard on a dataview from a brief.

        The route answers with the id of the job that builds it.

        Args:
            params: What to build, as
                :class:`~mammoth.models.dashboards.GenerateV3Params` or the
                same fields as a dict. ``format="qa"`` opens a
                question-and-answer notebook, which needs no ``intent``.

        Returns:
            Dict carrying the build job.

        Raises:
            MammothValidationError: If the brief is not one the route takes.
        """
        try:
            typed = (
                params
                if isinstance(params, GenerateV3Params)
                else GenerateV3Params.model_validate(params)
            )
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid dashboard generation parameters: {exc}") from exc
        return await self._client._request_json(
            "POST",
            "/dashboards/v3/generate",
            json={"params": typed.model_dump(mode="json", exclude_unset=True)},
        )

    async def get(self, dashboard_id: int) -> dict[str, Any]:
        """Get dashboard details.

        Args:
            dashboard_id: ID of the dashboard.

        Returns:
            Dict with dashboard details.
        """
        return await self._client._request_json("GET", f"/dashboards/{dashboard_id}")

    async def add_pages(self, dashboard_id: int, body: AddPagesSpec) -> AddPagesResponse:
        """Append structural pages and start the asynchronous dashboard bake."""
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        try:
            typed = body if isinstance(body, AddPagesSpec) else AddPagesSpec.model_validate(body)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid add-pages parameters: {exc}") from exc
        response = await self._client._request_json(
            "POST",
            f"/dashboards/{dashboard_id}/pages",
            json=typed.model_dump(mode="json", exclude_none=True),
        )
        try:
            return AddPagesResponse.model_validate(response)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid add-pages response: {exc}") from exc

    async def extract_context(self, body: ContextExtractSpec) -> dict[str, Any]:
        """Extract a context file into slot suggestions (release route)."""
        try:
            typed = (
                body
                if isinstance(body, ContextExtractSpec)
                else ContextExtractSpec.model_validate(body)
            )
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid context-extract parameters: {exc}") from exc
        response = await self._client._request_json(
            "POST",
            "/dashboards/v3/contexts/extract",
            json=typed.model_dump(mode="json", exclude_none=True),
        )
        try:
            return ContextExtractResponse.model_validate(response).model_dump(mode="json")
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid context-extract response: {exc}") from exc

    async def extract_exemplar(self, body: ExemplarExtractSpec) -> dict[str, Any]:
        """Extract an example report into an editable dashboard spec."""
        try:
            typed = (
                body
                if isinstance(body, ExemplarExtractSpec)
                else ExemplarExtractSpec.model_validate(body)
            )
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid exemplar-extract parameters: {exc}") from exc
        response = await self._client._request_json(
            "POST",
            "/dashboards/v3/exemplar/extract",
            json=typed.model_dump(mode="json", exclude_none=True),
        )
        try:
            return ExemplarExtractResponse.model_validate(response).model_dump(mode="json")
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid exemplar-extract response: {exc}") from exc

    async def swap_data(self, dashboard_id: int, body: SwapDataSpec) -> ObjectJobSchema:
        """Re-point a v3 dashboard at a different dataset."""
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        try:
            typed = body if isinstance(body, SwapDataSpec) else SwapDataSpec.model_validate(body)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid swap-data parameters: {exc}") from exc
        response = await self._client._request_json(
            "POST",
            f"/dashboards/v3/{dashboard_id}/swap-data",
            json=typed.model_dump(mode="json", exclude_none=True),
        )
        try:
            return ObjectJobSchema.model_validate(response)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid swap-data response: {exc}") from exc

    async def take_pending_template(self) -> dict[str, Any]:
        """Claim the pending dashboard template for the workspace."""
        response = await self._client._request_json("POST", "/dashboards/v3/templates/pending")
        try:
            return PendingTemplateResponse.model_validate(response).model_dump(mode="json")
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid pending-template response: {exc}") from exc

    async def use_template(self, slug: str, body: UseTemplateSpec) -> ObjectJobSchema | JobResponse:
        """Instantiate a dashboard template on its sample data."""
        if not isinstance(slug, str) or not slug:
            raise MammothValidationError("`slug` must be a non-empty string.")
        try:
            typed = (
                body if isinstance(body, UseTemplateSpec) else UseTemplateSpec.model_validate(body)
            )
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid use-template parameters: {exc}") from exc
        response = await self._client._request_json(
            "POST",
            f"/dashboards/v3/templates/{quote(slug, safe='')}/use",
            json=typed.model_dump(mode="json", exclude_none=True),
        )
        try:
            if isinstance(response, dict) and "job" in response:
                return JobResponse.model_validate(response)
            return ObjectJobSchema.model_validate(response)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid use-template response: {exc}") from exc

    async def assess_twb(self, file: str | Path) -> TwbAssessResponse:
        """Assess a Tableau workbook without importing it."""
        return await self._assess_upload(file, "/dashboards/v3/twb/assess", TwbAssessResponse)

    async def assess_pbix(self, file: str | Path) -> PbixAssessResponse:
        """Assess a Power BI workbook without importing it."""
        return await self._assess_upload(file, "/dashboards/v3/pbix/assess", PbixAssessResponse)

    async def import_workbook(
        self, file: str | Path, project_id: int | None = None
    ) -> ImportDatasetResponse:
        """Import a workbook into a project-scoped dataset."""
        if isinstance(project_id, bool) or (
            project_id is not None and not isinstance(project_id, int)
        ):
            raise MammothValidationError("`project_id` must be an integer or None.")
        try:
            path = Path(file)
        except (TypeError, ValueError) as exc:
            raise MammothValidationError("`file` must be a valid local path.") from exc
        if not path.is_file():
            raise MammothValidationError(f"File not found: {path}")
        try:
            opened = path.open("rb")
        except OSError as exc:
            raise MammothValidationError(f"File cannot be opened: {path}") from exc
        try:
            response = await self._client._request_json(
                "POST",
                "/dashboards/v3/import/dataset",
                data={"project_id": str(project_id)} if project_id is not None else None,
                files=[("file", (os.path.basename(path), opened, "application/octet-stream"))],
            )
        finally:
            opened.close()
        try:
            return ImportDatasetResponse.model_validate(response)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid workbook import response: {exc}") from exc

    async def _assess_upload(self, file: str | Path, endpoint: str, model: Any) -> Any:
        try:
            path = Path(file)
        except (TypeError, ValueError) as exc:
            raise MammothValidationError("`file` must be a valid local path.") from exc
        if not path.is_file():
            raise MammothValidationError(f"File not found: {path}")
        try:
            opened = path.open("rb")
        except OSError as exc:
            raise MammothValidationError(f"File cannot be opened: {path}") from exc
        try:
            response = await self._client._request_json(
                "POST",
                endpoint,
                files=[("file", (os.path.basename(path), opened, "application/octet-stream"))],
            )
        finally:
            opened.close()
        try:
            return model.model_validate(response)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid workbook assessment response: {exc}") from exc

    async def powerbi_preflight(self, dashboard_id: int) -> PowerBiPreflightResponse:
        """What a Power BI export of this dashboard would carry (release route)."""
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        response = await self._client._request_json("GET", f"/dashboards/{dashboard_id}/powerbi")
        try:
            return PowerBiPreflightResponse.model_validate(response)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid Power BI preflight response: {exc}") from exc

    async def tableau_preflight(self, dashboard_id: int) -> TableauPreflightResponse:
        """What a Tableau export of this dashboard would carry (release route)."""
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        response = await self._client._request_json("GET", f"/dashboards/{dashboard_id}/tableau")
        try:
            return TableauPreflightResponse.model_validate(response)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid Tableau preflight response: {exc}") from exc

    async def powerbi_export_artifact(self, dashboard_id: int) -> dict[str, Any]:
        """Fetch the raw Power BI export artifact (release route).

        SDK-only: :meth:`export_powerbi` decodes ``content_base64`` and writes
        the result to disk; that is the reviewed CLI command.
        """
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        return await self._client._request_binary(
            "GET", f"/dashboards/{dashboard_id}/powerbi/export"
        )

    async def tableau_export_artifact(self, dashboard_id: int) -> dict[str, Any]:
        """Fetch the raw Tableau export artifact (release route).

        SDK-only: :meth:`export_tableau` decodes ``content_base64`` and writes
        the result to disk; that is the reviewed CLI command.
        """
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        return await self._client._request_binary(
            "GET", f"/dashboards/{dashboard_id}/tableau/export"
        )

    async def export_powerbi(
        self, dashboard_id: int, output_path: str | Path | None = None
    ) -> Path:
        """Download this dashboard as a Power BI project (.zip) to a local file.

        The zip holds the PBIP project, a CSV snapshot of the data, and a
        readme written for someone who has never seen the Mammoth original.
        See :meth:`powerbi_preflight` for what will convert before committing
        to the download.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            output_path: Path for the .zip file (auto-generated if not provided).

        Returns:
            Path to the downloaded file.
        """
        return await self._download_bi_export(dashboard_id, "powerbi", output_path)

    async def export_tableau(
        self, dashboard_id: int, output_path: str | Path | None = None
    ) -> Path:
        """Download this dashboard as a Tableau workbook (.twbx) to a local file.

        One file, no refresh step and no gateway -- a .twbx carries its own
        data. See :meth:`tableau_preflight` for what will convert before
        committing to the download.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            output_path: Path for the .twbx file (auto-generated if not provided).

        Returns:
            Path to the downloaded file.
        """
        return await self._download_bi_export(dashboard_id, "tableau", output_path)

    async def _download_bi_export(
        self,
        dashboard_id: int,
        target: Literal["powerbi", "tableau"],
        output_path: str | Path | None,
    ) -> Path:
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        artifact = (
            await self.powerbi_export_artifact(dashboard_id)
            if target == "powerbi"
            else await self.tableau_export_artifact(dashboard_id)
        )
        try:
            content = base64.b64decode(artifact["content_base64"])
        except (KeyError, ValueError) as exc:
            raise MammothValidationError(f"Invalid {target} export artifact response.") from exc
        path = (
            Path(output_path)
            if output_path
            else Path(f"dashboard_{dashboard_id}_{target}.{_BI_EXPORT_EXTENSIONS[target]}")
        )
        return await asyncio.to_thread(_write_bytes_atomic, content, path)

    async def update(
        self,
        dashboard_id: int,
        patch: _list[DashboardPatchItem],
    ) -> dict[str, Any]:
        """Update a dashboard with patch operations.

        The patch items look like RFC 6902 JSON Patch but ``path`` is a bare
        field name from :class:`~mammoth.models.dashboards.DashboardPatchPath`
        (``"title"``, ``"intent"``, ``"theme"``, ``"pages"``, ``"filters"``),
        not a JSON pointer: ``"/title"`` is rejected.

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
        return await self._client._request_json("PATCH", f"/dashboards/{dashboard_id}", json=body)

    async def delete(self, dashboard_id: int) -> dict[str, Any]:
        """Delete a dashboard.

        Args:
            dashboard_id: ID of the dashboard.

        Returns:
            Dict with deletion result.
        """
        return await self._client._request_json("DELETE", f"/dashboards/{dashboard_id}")

    async def archive(self, dashboard_id: int, archived: bool) -> Any:
        """Set whether a dashboard is archived.

        ``archived=True`` archives the dashboard and ``archived=False``
        restores it. The API declares no response body schema and the live
        server answers with a non-object JSON value, so any 2xx JSON body is
        accepted and returned unchanged instead of being rejected as a
        response-contract violation on a write that already committed.
        """
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        if not isinstance(archived, bool):
            raise MammothValidationError("`archived` must be a boolean.")
        return await self._client._request(
            "POST", f"/dashboards/{dashboard_id}/archive", json={"archived": archived}
        )

    async def get_sources(self) -> _list[dict[str, Any]]:
        """Get available dashboard data sources.

        .. note::

            This endpoint may return HTTP 500 on some server configurations.

        Returns:
            List of source dicts.
        """
        response = await self._client._request_json("GET", "/dashboards/sources")
        return response.get("sources", response if isinstance(response, _list) else [])

    async def get_analytics(self, dashboard_id: int) -> dict[str, Any]:
        """Get dashboard analytics (views, users).

        Args:
            dashboard_id: ID of the dashboard.

        Returns:
            Dict with analytics data.
        """
        return await self._client._request_json("GET", f"/dashboards/{dashboard_id}/analytics")

    async def share(
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
        # Like ``archive``, the share route declares no response body schema;
        # accept whatever JSON the server returns for the committed write.
        return await self._client._request("POST", f"/dashboards/{dashboard_id}/share", json=body)

    async def action(
        self,
        dashboard_id: int,
        action: DashboardActionType,
        params_enabled: bool | None = None,
        params_view_id: int | None = None,
        params_sequence: int | None = None,
        params_filter_column: str | None = None,
    ) -> dict[str, Any]:
        """Perform an action on a dashboard.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            action: The action to execute.
            params_enabled: Required for ``auto-sync`` and ``auto-publish``;
                enables or disables the behaviour.
            params_view_id: Required (> 0) for ``delete-source``;
                optional for ``sync`` and ``auto-sync`` to scope to one source.
            params_sequence: The version to rewind to; required for ``restore``.
            params_filter_column: The column rows are filtered on; required
                when ``set-rls-config`` turns row-level security on.

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
        if params_sequence is not None:
            params["sequence"] = params_sequence
        if params_filter_column is not None:
            params["filter_column"] = params_filter_column
        if params:
            body["params"] = params

        return await self._client._request_json(
            "POST", f"/dashboards/{dashboard_id}/action", json=body
        )

    async def get_by_url(self, url: str) -> dict[str, Any]:
        """Get dashboard by URL slug.

        Args:
            url: Dashboard URL slug.

        Returns:
            Dict with dashboard details.
        """
        return await self._client._request_json("GET", f"/dashboards/url/{url}")

    @staticmethod
    def _widget_data_params(
        widget_id: str,
        global_filters: dict[str, Any] | None,
        drilldown_filters: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not isinstance(widget_id, str) or not widget_id.strip():
            raise MammothValidationError("`widget_id` must be a non-empty string (widget UUID).")
        params: dict[str, Any] = {"widget_id": widget_id}
        if global_filters is not None:
            params["global_filters"] = global_filters
        if drilldown_filters is not None:
            params["drilldown_filters"] = drilldown_filters
        return params

    async def get_draft_data(
        self,
        dashboard_id: int,
        widget_id: str,
        global_filters: dict[str, Any] | None = None,
        drilldown_filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get one widget's rows from a dashboard's draft (unpublished) state.

        The route is historically named ``GetDraftDataFromSql`` but the API
        contract takes a ``WidgetDataSpec``: ``{"params": {"widget_id", ...}}``.
        A top-level ``sql`` body is rejected with HTTP 400 ``params: Field
        required``.

        Args:
            dashboard_id: ID of the dashboard.
            widget_id: UUID of the widget whose data to fetch.
            global_filters: Sidebar filters, ``{column: value}``.
            drilldown_filters: Chart-click filters, ``{column: value}``
                (always exact match).

        Returns:
            Dict with a ``data`` list of row dicts.
        """
        params = self._widget_data_params(widget_id, global_filters, drilldown_filters)
        return await self._client._request_json(
            "POST", f"/dashboards/{dashboard_id}/getDraftData", json={"params": params}
        )

    async def get_publish_data(
        self,
        dashboard_id: int,
        widget_id: str,
        global_filters: dict[str, Any] | None = None,
        drilldown_filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get one widget's rows from a dashboard's published state.

        Same ``WidgetDataSpec`` contract as :meth:`get_draft_data`.

        Args:
            dashboard_id: ID of the dashboard.
            widget_id: UUID of the widget whose data to fetch.
            global_filters: Sidebar filters, ``{column: value}``.
            drilldown_filters: Chart-click filters, ``{column: value}``.

        Returns:
            Dict with a ``data`` list of row dicts.
        """
        params = self._widget_data_params(widget_id, global_filters, drilldown_filters)
        return await self._client._request_json(
            "POST", f"/dashboards/{dashboard_id}/getPublishData", json={"params": params}
        )

    async def cancel_generation(self, dashboard_id: int) -> dict[str, Any]:
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
        return await self._client._request_json(
            "POST", f"/dashboards/{dashboard_id}/cancel-generation"
        )

    async def job_by_url(self, url: str, job_id: int) -> dict[str, Any]:
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
        return await self._client._request_json("GET", f"/dashboards/url/{url}/jobs/{job_id}")

    async def wait_for_job_by_url(
        self,
        url: str,
        job_id: int,
        timeout: float | None = None,
        poll_interval: float | None = None,
    ) -> dict[str, Any]:
        """Wait for a published-dashboard job through the URL-scoped job route.

        Jobs dispatched by the ``/dashboards/url/{url}/...`` routes are not
        readable through ``GET /jobs/{id}`` (the server answers ``4PERM002``),
        so poll :meth:`job_by_url` with the same timeout and failure semantics
        as :meth:`~mammoth.api.jobs.JobsAPI.wait_for_job`.
        """
        return await self._client.jobs.wait_for_job(
            job_id,
            timeout=timeout,
            poll_interval=poll_interval,
            fetch=lambda jid, _remaining: self.job_by_url(url, jid),
        )

    async def published_data_by_url(self, url: str, body: dict[str, Any]) -> dict[str, Any]:
        """Get published dashboard widget data via SQL, addressed by URL slug.

        Args:
            url: Dashboard URL slug.
            body: Widget data request payload (``WidgetDataSpec``), e.g.
                ``{"params": {"widget_id": ..., "global_filters": {...},
                "drilldown_filters": {...}}}``.

        Returns:
            Dict with query results (may include a job ID for async execution).
        """
        return await self._client._request_json(
            "POST", f"/dashboards/url/{url}/getPublishData", json=body
        )

    async def restore(self, dashboard_id: int) -> dict[str, Any]:
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
        return await self._client._request_json("POST", f"/dashboards/{dashboard_id}/restore")

    async def trash(self, dashboard_id: int) -> dict[str, Any]:
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
        return await self._client._request_json("POST", f"/dashboards/{dashboard_id}/trash")

    async def widget_data(self, dashboard_id: int, body: dict[str, Any]) -> dict[str, Any]:
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
        return await self._client._request_json(
            "POST", f"/dashboards/{dashboard_id}/widgets/data", json=body
        )

    async def widget_data_by_url(self, url: str, body: dict[str, Any]) -> dict[str, Any]:
        """Get data for multiple dashboard widgets in bulk, addressed by URL slug.

        Args:
            url: Dashboard URL slug.
            body: Bulk widget data request payload (``BulkWidgetDataSpec``).

        Returns:
            Dict with per-widget data results.
        """
        return await self._client._request_json(
            "POST", f"/dashboards/url/{url}/widgets/data", json=body
        )

    # ── embed: config / key / usage / preview-token / workspace secret ──────

    async def embed_config_get(self, dashboard_id: int) -> EmbedConfigResponse:
        """Read a board's embed settings.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).

        Returns:
            The board's embed settings plus the URLs a snippet needs.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0.
        """
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        response = await self._client._request_json(
            "GET", f"/dashboards/{dashboard_id}/embed/config"
        )
        return EmbedConfigResponse.model_validate(response)

    async def embed_config_set(
        self,
        dashboard_id: int,
        mode: Literal["key", "signed"] = "key",
        allow_any_origin: bool = True,
        allowed_origins: _list[str] | None = None,
        appearance: dict[str, Any] | None = None,
        snippet: dict[str, Any] | None = None,
    ) -> EmbedConfigResponse:
        """Save a board's embed settings (mode, origin allowlist, appearance).

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            mode: ``key`` (the board's embed key) or ``signed`` (a host-signed
                token). Ignored while the board is public.
            allow_any_origin: Any site may frame the board. Set false to
                restrict framing to *allowed_origins*.
            allowed_origins: Origin patterns allowed to frame the board while
                *allow_any_origin* is false. At most 20.
            appearance: The board's saved embed look (theme, filters, tile, ...).
            snippet: How the embed snippet is shaped (``height`` etc.).

        Returns:
            The board's updated embed settings.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0 or the parameters
                fail validation (e.g. more than 20 *allowed_origins*).
        """
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        try:
            typed = EmbedConfigParams(
                mode=mode,
                allow_any_origin=allow_any_origin,
                allowed_origins=allowed_origins or [],
                appearance=appearance or {},
                snippet=snippet or {},
            )
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid embed config parameters: {exc}") from exc
        response = await self._client._request_json(
            "PUT",
            f"/dashboards/{dashboard_id}/embed/config",
            json={"params": typed.model_dump(mode="json")},
        )
        return EmbedConfigResponse.model_validate(response)

    async def embed_key_rotate(
        self, dashboard_id: int, keep_previous: bool = True
    ) -> EmbedKeyResponse:
        """Create or rotate a board's embed key (Basic embeds).

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            keep_previous: Keep the replaced key usable for 24h (the default,
                for a planned rotation). Pass ``False`` to end it at once,
                for a leaked key.

        Returns:
            The board's new embed key (shown once here; readable again via
            :meth:`embed_config_get`).

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0.
        """
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        response = await self._client._request_json(
            "POST",
            f"/dashboards/{dashboard_id}/embed/key",
            json={"params": {"keep_previous": keep_previous}},
        )
        return EmbedKeyResponse.model_validate(response)

    async def embed_usage_get(self, dashboard_id: int) -> EmbedUsageResponse:
        """Get one board's embed registry: origins, tiles and render counts.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).

        Returns:
            Per-origin render/health counts and the active-origin total.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0.
        """
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        response = await self._client._request_json(
            "GET", f"/dashboards/{dashboard_id}/embed/usage"
        )
        return EmbedUsageResponse.model_validate(response)

    async def embed_usage_summary(self, dashboard_ids: _list[int]) -> dict[str, Any]:
        """Count the active embed origins of several boards in one call.

        The dashboard library's "embedded on N sites" figure. Boards outside
        the workspace are ignored by the route.

        Args:
            dashboard_ids: Non-empty list of dashboard ids (each > 0).

        Returns:
            Dict with ``counts`` (origins that loaded each board in the last
            90 days) and ``refused`` (origins refused per board).

        Raises:
            MammothValidationError: If *dashboard_ids* is empty or holds an id ≤ 0.
        """
        if not dashboard_ids:
            raise MammothValidationError(ERR_DASHBOARD_IDS_EMPTY)
        for dashboard_id in dashboard_ids:
            if (
                isinstance(dashboard_id, bool)
                or not isinstance(dashboard_id, int)
                or dashboard_id <= 0
            ):
                raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        return await self._client._request_json(
            "GET",
            f"/workspaces/{self._client.workspace_id}/dashboards/embed-usage",
            params={"ids": ",".join(str(i) for i in dashboard_ids)},
        )

    async def format_preview(self, dashboard_id: int, style: str) -> dict[str, Any]:
        """Dry-run a format switch: what carries over, what is added, what is lost.

        Computed by the server on a copy of the canvas; nothing is persisted.

        Args:
            dashboard_id: ID of the v3 dashboard (must be > 0).
            style: Target format/style name (non-empty), as ``dashboard style
                preset list`` names them.

        Returns:
            Dict with the carried and added counts and the ``not_shown`` ledger.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0 or *style* is empty.
        """
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        if not style:
            raise MammothValidationError(ERR_STYLE_EMPTY)
        return await self._client._request_json(
            "GET", f"/dashboards/{dashboard_id}/format-preview", params={"style": style}
        )

    async def swap_fit(
        self,
        source_dashboard_id: int,
        target_dataview_ids: _list[int],
        include_over_budget: bool = False,
        seconds_budget: float | None = None,
    ) -> dict[str, Any]:
        """Score one board against candidate datasets before ``swap_data`` (no writes).

        Pure computation over dataset profiles: no model call, nothing persisted.

        Args:
            source_dashboard_id: The v3 board that would be re-pointed (must be > 0).
            target_dataview_ids: Candidate dataview ids, 1 to 60, returned in this order.
            include_over_budget: Score even datasets past the cost budget (an explicit
                per-dataset check).
            seconds_budget: Seconds of cold profile building the request may spend
                (0 to 30); the server default when omitted. 0 scores cached datasets only.

        Returns:
            Dict with ``fits`` (one entry per dataview: a grade with matched, total and
            reasons, or a ``skipped`` reason), ``cell_budget``, ``sample_dataview_ids``,
            ``seconds_spent`` and ``seconds_budget``.

        Raises:
            MammothValidationError: If an id is ≤ 0, the list is empty or over 60, or
                *seconds_budget* is outside 0 to 30.
        """
        _require_dashboard_id(source_dashboard_id)
        if not target_dataview_ids or len(target_dataview_ids) > _SWAP_FIT_MAX_TARGETS:
            raise MammothValidationError(ERR_SWAP_FIT_TARGETS)
        for dataview_id in target_dataview_ids:
            if isinstance(dataview_id, bool) or not isinstance(dataview_id, int) or dataview_id < 1:
                raise MammothValidationError(ERR_SWAP_FIT_TARGETS)
        if seconds_budget is not None and not 0 <= seconds_budget <= _SWAP_FIT_MAX_SECONDS:
            raise MammothValidationError(ERR_SWAP_FIT_SECONDS.format(seconds_budget))
        params: dict[str, Any] = {
            "source_dashboard_id": source_dashboard_id,
            "target_dataview_ids": _list(target_dataview_ids),
            "include_over_budget": include_over_budget,
        }
        if seconds_budget is not None:
            params["seconds_budget"] = seconds_budget
        return await self._client._request_json(
            "POST", "/dashboards/v3/swap/fit", json={"params": params}, operation_effect="read"
        )

    async def audience(self, dashboard_id: int, days: int = 7) -> dict[str, Any]:
        """Get who read a board: totals, daily series, viewers, reach and actions.

        Editors only. The route never returns an IP or a city and never counts the
        editors' own visits.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            days: Window length: 7, 30 or 90.

        Returns:
            Dict with totals against the window before, a 30-day daily series, named
            workspace viewers, anonymous counts, country / device / viewport coverage,
            people it was shared with who never opened it, page and tile reach, and
            outward actions.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0 or *days* is not 7, 30 or 90.
        """
        _require_dashboard_id(dashboard_id)
        _require_window_days(days)
        return await self._client._request_json(
            "GET", f"/dashboards/{dashboard_id}/audience", params={"days": days}
        )

    async def audience_digest_get(self, dashboard_id: int) -> dict[str, Any]:
        """Get the caller's weekly audience email setting for one board.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).

        Returns:
            Dict with ``enabled`` (the effective answer), ``explicit`` (the stored
            choice, null when never chosen) and ``default_on``. Editors only.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0.
        """
        _require_dashboard_id(dashboard_id)
        return await self._client._request_json(
            "GET", f"/dashboards/{dashboard_id}/audience/digest"
        )

    async def audience_digest_set(self, dashboard_id: int, enabled: bool | None) -> dict[str, Any]:
        """Store the caller's choice for one board's weekly audience email.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            enabled: ``True`` or ``False`` to choose; ``None`` clears the choice, which
                returns to the default (on once the board has more than 5 viewers a week).

        Returns:
            Dict with ``enabled``, ``explicit`` and ``default_on`` after the change.
            Editors only.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0 or *enabled* is not a bool or None.
        """
        _require_dashboard_id(dashboard_id)
        if enabled is not None and not isinstance(enabled, bool):
            raise MammothValidationError(ERR_DIGEST_ENABLED.format(enabled))
        return await self._client._request_json(
            "PUT", f"/dashboards/{dashboard_id}/audience/digest", json={"enabled": enabled}
        )

    async def audience_summary(self, dashboard_ids: _list[int]) -> dict[str, Any]:
        """Get views per board for the dashboard library: several boards in one call.

        Args:
            dashboard_ids: Non-empty list of dashboard ids (each > 0, 200 at most are read).

        Returns:
            Dict ``{"items": {dashboard_id: {...}}}`` with views and people over 7 days,
            views over 30 days, the last view and a 14-day daily series. A board never
            viewed is absent; boards outside the workspace or that the caller cannot
            edit are ignored.

        Raises:
            MammothValidationError: If *dashboard_ids* is empty or holds an id ≤ 0.
        """
        if not dashboard_ids:
            raise MammothValidationError(ERR_DASHBOARD_IDS_EMPTY)
        for dashboard_id in dashboard_ids:
            _require_dashboard_id(dashboard_id)
        return await self._client._request_json(
            "GET",
            f"/workspaces/{self._client.workspace_id}/dashboards/audience-summary",
            params={"ids": ",".join(str(i) for i in dashboard_ids)},
        )

    async def column_roster(self, dashboard_id: int) -> dict[str, Any]:
        """Get every column of a board's source dataset with its profile.

        Served from the cached dataset profile: value samples, measure ranges and
        aggregates, date spans and the profiler's identifier and protected-attribute
        verdicts (the Data panel).

        Args:
            dashboard_id: ID of the dashboard (must be > 0).

        Returns:
            Dict with ``columns``, ``on_board_count``, ``row_count`` and ``signals``.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0.
        """
        _require_dashboard_id(dashboard_id)
        return await self._client._request_json("GET", f"/dashboards/{dashboard_id}/columns")

    async def context_review(
        self,
        dashboard_id: int,
        scope: str | None = None,
        note: str | None = None,
        fresh: bool = False,
    ) -> ObjectJobSchema:
        """Dry-run what applying a board's current context would change.

        Nothing is written: not the canvas, not the transcript, not the bake. The
        planner runs under the grounding limit and the candidate is held server side.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            scope: How much prose to touch: ``summary`` (default), ``insights`` or ``all``.
            note: Free text to steer the review (1000 characters at most).
            fresh: Work the review out again instead of reusing a pending one.

        Returns:
            The job handle; its result holds the item-level change set and a
            ``review_id`` (null when the context changes nothing).

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0 or *note* is over 1000 characters.
        """
        _require_dashboard_id(dashboard_id)
        if note is not None and len(note) > _CONTEXT_NOTE_MAX:
            raise MammothValidationError(ERR_CONTEXT_NOTE_LONG.format(len(note)))
        params: dict[str, Any] = {"fresh": fresh}
        if scope is not None:
            params["scope"] = scope
        if note is not None:
            params["note"] = note
        response = await self._client._request_json(
            "POST",
            f"/dashboards/{dashboard_id}/context-review",
            json={"params": params},
            operation_effect="read",
        )
        try:
            return ObjectJobSchema.model_validate(response)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid context-review response: {exc}") from exc

    async def context_apply(
        self,
        dashboard_id: int,
        review_id: str,
        keep: _list[str] | None = None,
        base_sequence: int | None = None,
    ) -> ObjectJobSchema:
        """Write the candidate a context review proposed, as a new canvas version.

        The change lands like a chat edit, so undo, revert and the version timeline
        reach it. The server rejects it when the candidate expired or was superseded,
        and when the board's head moved since the review.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            review_id: ``review_id`` from the ``context_review`` job result (non-empty).
            keep: Roster keys whose hand-typed text to keep over the proposal.
            base_sequence: The head the review was computed against; 409 if it moved.

        Returns:
            The job handle; its result holds ``sequence``, ``canvas``, ``version_before``
            and ``bake_ok``.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0 or *review_id* is empty.
        """
        _require_dashboard_id(dashboard_id)
        if not review_id:
            raise MammothValidationError(ERR_REVIEW_ID_EMPTY)
        params: dict[str, Any] = {"keep": _list(keep or [])}
        if base_sequence is not None:
            params["base_sequence"] = base_sequence
        response = await self._client._request_json(
            "POST",
            f"/dashboards/{dashboard_id}/context-review/{quote(review_id, safe='')}/apply",
            json={"params": params},
        )
        try:
            return ObjectJobSchema.model_validate(response)
        except ValidationError as exc:
            raise MammothValidationError(f"Invalid context-apply response: {exc}") from exc

    async def qa_insights(self, dashboard_id: int, days: int = 7) -> dict[str, Any]:
        """Get the questions viewers asked on a board, grouped by their text.

        Editors only. Nobody is named: no user, session or name is returned, and the
        editors' own questions are left out.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            days: Window length: 7, 30 or 90.

        Returns:
            Dict with ``groups`` (feedback and unanswered counts, the measure and
            dimension each answer was about), ``feedback``, ``questions_total`` and
            ``range_days``.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0 or *days* is not 7, 30 or 90.
        """
        _require_dashboard_id(dashboard_id)
        _require_window_days(days)
        return await self._client._request_json(
            "GET", f"/dashboards/{dashboard_id}/qa/insights", params={"days": days}
        )

    async def template_thumbnail_get(self, template_id: str) -> dict[str, Any]:
        """Download the picture a template's card shows.

        Args:
            template_id: Template slug (non-empty).

        Returns:
            Dict with ``content_type``, ``size_bytes``, ``sha256`` and
            ``content_base64``. The route answers 404 when the template has no
            picture; the card then falls back to its og-card.

        Raises:
            MammothValidationError: If *template_id* is empty.
        """
        return await self._client._request_binary("GET", _thumbnail_path(template_id))

    async def template_thumbnail_set(self, template_id: str, file: str | Path) -> dict[str, Any]:
        """Replace the picture of a saved workspace template.

        Owner or workspace admin only; curated templates are not writable.
        The server accepts PNG, JPEG or WebP (by content) up to 1 MB.

        Args:
            template_id: Template slug (non-empty).
            file: Path to a local image file.

        Returns:
            Dict ``{"ok": True}``.

        Raises:
            MammothValidationError: If *template_id* is empty or *file* is not
                a readable local file.
        """
        endpoint = _thumbnail_path(template_id)
        path = Path(file)
        if not path.is_file():
            raise MammothValidationError(f"File not found: {path}")
        with path.open("rb") as opened:
            return await self._client._request_json(
                "PUT",
                endpoint,
                files=[("data", (path.name, opened, "application/octet-stream"))],
            )

    async def template_thumbnail_clear(self, template_id: str) -> dict[str, Any]:
        """Remove a saved template's picture; its card falls back to the og-card.

        Owner or workspace admin only.

        Args:
            template_id: Template slug (non-empty).

        Returns:
            Dict ``{"ok": bool}``: ``False`` when the template had no picture.

        Raises:
            MammothValidationError: If *template_id* is empty.
        """
        return await self._client._request_json("DELETE", _thumbnail_path(template_id))

    async def gallery_list(
        self, function: str | None = None, industry: str | None = None
    ) -> dict[str, Any]:
        """List the public template gallery: curated, live templates only.

        The anonymous catalog (no internal ids). Each card carries its copy,
        taxonomy labels, ``thumbnail_ref`` and ``viewer_url``.

        Args:
            function: Keep only templates for this business function.
            industry: Keep only templates for this industry.

        Returns:
            Dict with the template cards and the facet lists with counts. The
            route answers 404 for an unknown facet or one with nothing under it.
        """
        params = {
            key: value
            for key, value in (("function", function), ("industry", industry))
            if value is not None
        }
        return await self._client._request_json(
            "GET", "/dashboards/public/templates", params=params or None
        )

    async def gallery_get(self, slug: str) -> dict[str, Any]:
        """Get one template card from the public gallery.

        Args:
            slug: Template slug (non-empty).

        Returns:
            Dict ``{"template": {...}}``. The route answers 404 for an unknown
            slug, a user-saved template, or a curated one that is not live.

        Raises:
            MammothValidationError: If *slug* is empty.
        """
        if not slug:
            raise MammothValidationError(ERR_SLUG_EMPTY)
        return await self._client._request_json(
            "GET", f"/dashboards/public/templates/{quote(slug, safe='')}"
        )

    async def embed_origin_revoke(self, dashboard_id: int, origin: str) -> EmbedConfigResponse:
        """Remove one origin from a board's embed allowlist.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            origin: The origin to remove (non-empty).

        Returns:
            The board's embed settings after the origin is removed.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0 or *origin* is empty.
        """
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        if not origin:
            raise MammothValidationError(ERR_EMBED_ORIGIN_EMPTY)
        response = await self._client._request_json(
            "DELETE",
            f"/dashboards/{dashboard_id}/embed/origin",
            json={"params": {"origin": origin}},
        )
        return EmbedConfigResponse.model_validate(response)

    async def embed_preview_token_create(
        self, dashboard_id: int, claims: dict[str, Any] | None = None
    ) -> EmbedPreviewTokenResponse:
        """Mint a preview token for the embed simulator (editor-only).

        Args:
            dashboard_id: ID of the dashboard (must be > 0).
            claims: Row-level-security claims, keyed by the board's RLS
                column name, exactly as a host's token would carry them.

        Returns:
            A short-lived token, its expiry, and the embed URL to use it with.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0.
        """
        if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
            raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))
        response = await self._client._request_json(
            "POST",
            f"/dashboards/{dashboard_id}/embed/preview-token",
            json={"params": {"claims": claims or {}}},
        )
        return EmbedPreviewTokenResponse.model_validate(response)

    async def embed_secret_rotate(self, workspace_id: int) -> EmbedSecretResponse:
        """Create or rotate the workspace's embed signing secret (owners/admins).

        The plaintext secret is returned once, here, and never by a read route.
        Rotating keeps the previous secret valid for 24 hours.

        Args:
            workspace_id: ID of the workspace (must be > 0).

        Returns:
            The new plaintext secret, its session token TTL, and rotation time.

        Raises:
            MammothValidationError: If *workspace_id* ≤ 0.
        """
        if isinstance(workspace_id, bool) or not isinstance(workspace_id, int) or workspace_id <= 0:
            raise MammothValidationError(ERR_WORKSPACE_ID_POSITIVE.format(workspace_id))
        response = await self._client._request_json(
            "POST", f"/workspaces/{workspace_id}/embed/secret"
        )
        return EmbedSecretResponse.model_validate(response)

    async def embed_lifetime_set(self, workspace_id: int, token_ttl: int) -> EmbedLifetimeResponse:
        """Set how long an embed viewer session lives for a workspace.

        Args:
            workspace_id: ID of the workspace (must be > 0).
            token_ttl: Session lifetime in seconds, 60 to 3600 inclusive.

        Returns:
            The saved session lifetime.

        Raises:
            MammothValidationError: If *workspace_id* ≤ 0 or *token_ttl* is
                outside [60, 3600].
        """
        if isinstance(workspace_id, bool) or not isinstance(workspace_id, int) or workspace_id <= 0:
            raise MammothValidationError(ERR_WORKSPACE_ID_POSITIVE.format(workspace_id))
        if not (60 <= token_ttl <= 3600):
            raise MammothValidationError(ERR_EMBED_TOKEN_TTL_RANGE.format(token_ttl))
        response = await self._client._request_json(
            "PUT",
            f"/workspaces/{workspace_id}/embed/lifetime",
            json={"params": {"token_ttl": token_ttl}},
        )
        return EmbedLifetimeResponse.model_validate(response)


# ── Private helpers ───────────────────────────────────────────────────────────


def _require_dashboard_id(dashboard_id: int) -> None:
    """Reject a dashboard id that is not a positive integer."""
    if isinstance(dashboard_id, bool) or not isinstance(dashboard_id, int) or dashboard_id <= 0:
        raise MammothValidationError(ERR_DASHBOARD_ID_POSITIVE.format(dashboard_id))


def _require_window_days(days: int) -> None:
    """Reject an audience window the server does not serve."""
    if isinstance(days, bool) or days not in _AUDIENCE_WINDOWS:
        raise MammothValidationError(ERR_WINDOW_DAYS.format(days))


def _thumbnail_path(template_id: str) -> str:
    """The in-product thumbnail route of one template, its slug path-encoded."""
    if not template_id:
        raise MammothValidationError(ERR_TEMPLATE_ID_EMPTY)
    return f"/dashboards/v3/templates/{quote(template_id, safe='')}/thumbnail"


def _write_bytes_atomic(content: bytes, output_path: Path) -> Path:
    """Write ``content`` to ``output_path``, publishing it only once complete.

    Uses a same-directory temporary file so the final ``os.replace`` is atomic
    even when the destination is on a different filesystem from the process
    temp dir; the destination is never opened for writing until the full
    content has been flushed and fsynced.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_temp_path = tempfile.mkstemp(
        prefix=f".{output_path.name}.", suffix=".part", dir=output_path.parent
    )
    temp_path = Path(raw_temp_path)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, output_path)
    except OSError:
        with suppress(OSError):
            temp_path.unlink()
        raise
    return output_path


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
