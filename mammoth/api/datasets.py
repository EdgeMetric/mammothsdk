"""
Datasets API client for managing datasets in Mammoth.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

from mammoth.api._pagination import collect_offset_pages
from mammoth.exceptions import (
    MammothAPIError,
    MammothDeletionVerificationError,
    MammothValidationError,
)
from mammoth.models.datasets import DataAdditionMode

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

ERR_DATASET_ID_POSITIVE = "`dataset_id` must be a positive integer, got {0}."
ERR_FOLLOW_BOOL = "`follow` must be true or false, got {0!r}."
ERR_FILE_OBJECT_ID_POSITIVE = "`file_object_id` must be a positive integer, got {0}."
_INTERPRETATION_MODES = ("interpreted", "original")
ERR_TOOL_CLAIM_TOKEN = "`token` must be 1 to 300 characters, got {0} characters."
ERR_FILE_SETTINGS_UNKNOWN = "The dataset's current {0} could not be read; pass it explicitly."
ERR_DATA_ADDITION_MODE = "`mode` must be 'replace' or 'combine', got {0!r}."
#: The fields of the backend's ``SchemaSettings`` (mvc-service apiv2 datasets schema),
#: which the ``replace schema_settings`` patch stores whole.
_SCHEMA_SETTINGS_FIELDS = (
    "data_addition_mode",
    "strict_data_type_check",
    "strict_column_length_check",
    "convert_columns_to_text",
    "convert_incompatible_data_to_null",
    "delete_after_append",
    "match_existing_target_schema",
    "schema_mapping",
    "unique_sequence_column",
    "ignored_source_columns",
    "optional_destination_columns",
)
#: What the platform stores for a dataset that has no settings yet: mvc-service
#: ``api/api/ds/schema.py`` ``SchemaPropertiesDefaultValues`` (origin/release).
#: The PATCH handler (``apiv2/apiv2/datasets/utils.py``
#: ``update_schema_settings_for_dataset``) stores ``SchemaSettings.model_dump()``
#: whole, and that model's own field defaults differ again (``data_addition_mode``
#: defaults to "replace", ``apiv2/apiv2/datasets/schema.py``), so every field must
#: be sent: one left out is stored as the model default, not as the dataset had it.
#: ``ignored_source_columns`` and ``optional_destination_columns`` are not defaulted: they
#: are read back with the other stored settings (``_SCHEMA_SETTINGS_FIELDS``), so
#: ``set_update_method`` sends the dataset's own choices again and echoes them as stored.
#: A dataset that holds none sends none, and the backend then keeps its remembered choices
#: when the matching keys are unchanged (``_with_remembered_column_choices``).
_STORED_DEFAULTS: dict[str, Any] = {
    "data_addition_mode": "combine",
    "delete_after_append": True,
    "strict_data_type_check": True,
    "convert_columns_to_text": False,
    "strict_column_length_check": False,
    "match_existing_target_schema": True,
    "convert_incompatible_data_to_null": False,
}
#: The server's length limit on an Open tables link's token.
TOOL_CLAIM_TOKEN_MAX = 300


def _check_tool_claim_token(token: str) -> None:
    """Reject a token the server would refuse (empty, or over its length limit)."""
    if not isinstance(token, str) or not 1 <= len(token) <= TOOL_CLAIM_TOKEN_MAX:
        raise MammothValidationError(
            ERR_TOOL_CLAIM_TOKEN.format(len(token) if isinstance(token, str) else 0)
        )


class DatasetsAPI:
    """Client for interacting with Mammoth Datasets API.

    Access via client.datasets:
        datasets = client.datasets.list()
        dataset = client.datasets.get(123)
        data = client.datasets.get_data(123)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self, project_id: int | None = None) -> int:
        if project_id is not None:
            return project_id
        proj = getattr(self._client, "project_id", None)
        if proj is not None:
            return proj
        raise ValueError("project_id must be set on the client using client.set_project_id()")

    async def list(
        self,
        workspace_id: int | None = None,
        project_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
        sort: str = "(created_at:desc)",
        fields: str = "id,name",
        ids: _list[int] | None = None,
    ) -> dict[str, Any]:
        """Get list of datasets in a project.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            limit: Maximum number of results (default 100).
            offset: Number of results to skip (default 0).
            sort: Sort order (default "(created_at:desc)").
            fields: Comma-separated dataset fields to return, or "__min" /
                "__standard" / "__full" (default "id,name"). ``stats`` carries
                the row/column counts, ``data_schema`` the column names and types,
                ``sources`` how the dataset was made, plus ``created_at`` and
                ``updated_at``.
            ids: Only these dataset ids (sent as the server's comma-separated ``id``
                filter); omitted lists every dataset.

        Returns:
            Dict containing datasets list with the requested fields.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        params: dict[str, Any] = {"fields": fields, "limit": limit, "offset": offset, "sort": sort}
        if ids:
            params["id"] = ",".join(str(int(item)) for item in ids)
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets", params=params
        )

    async def list_all(
        self,
        workspace_id: int | None = None,
        project_id: int | None = None,
        limit: int = 100,
        sort: str = "(created_at:desc)",
        max_pages: int = 1000,
        fields: str = "id,name",
        ids: _list[int] | None = None,
    ) -> dict[str, Any]:
        """List all datasets with bounded, progress-checked pagination.

        The server's supported ``offset``/``next`` contract is used directly.
        Repeated pages, empty pages carrying ``next``, non-advancing hints and
        unbounded continuation raise :class:`MammothPaginationError` instead
        of silently claiming complete inventory coverage.
        """
        return await collect_offset_pages(
            lambda offset: self.list(
                workspace_id=workspace_id,
                project_id=project_id,
                limit=limit,
                offset=offset,
                sort=sort,
                fields=fields,
                ids=ids,
            ),
            item_key="datasets",
            limit=limit,
            max_pages=max_pages,
            full_page_continues=True,
        )

    async def search(
        self,
        term: str,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Find the project's datasets whose name, column names or sampled values hold ``term``.

        Sampled values are the per-column samples the profiler keeps, so a dataset that was
        never profiled matches on its name and column names only.

        Args:
            term: Text to look for (case-insensitive substring, at least 2 characters).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``datasets``: ``{id, name, matches}``, each match naming where it was
            found (``found_in`` is ``name``, ``column`` or ``value``) with its ``column`` and
            ``value``.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/search", params={"q": term}
        )

    async def column_stats(
        self,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Read every column's blank count, type and distinct count for the project's datasets.

        One call for the whole project. The figures come from the stats the platform stored
        at the last load or pipeline run, so nothing is profiled or run.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``datasets``, newest first: ``{id, name, rows, columns}``, each column
            ``{name, type, blank_count, blank_pct, distinct}`` (``blank_pct`` is 0-100).
            ``rows`` and ``distinct`` are ``None`` when the platform has not stored them.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/column-stats"
        )

    async def list_definitions(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """List what terms mean for a dataset, as saved by its users.

        A definition is shared by every chat on the dataset; the in-app agent reads
        the project's definitions in each turn.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``dataset_id`` and ``definitions``: ``{id, term, definition,
            created_by, created_at}`` each, oldest first.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/definitions"
        )

    async def tool_claim_get(self, token: str) -> dict[str, Any]:
        """Say what an emailed Open tables link opens.

        A table-extraction tool emails a link whose token stands for the tables it found in
        a file. The answer never contains the address the link was sent to.

        Args:
            token: Token from the emailed link (up to 300 characters).

        Returns:
            Dict with ``file_name``, ``table_count``, ``expired``, ``signed_in``,
            ``for_this_account`` (the link was sent to the caller's address) and
            ``redeemed`` (``{workspace_id, project_id, folder_id}`` once added, shown to the
            link's owner only).

        Raises:
            MammothValidationError: If *token* is empty or longer than 300 characters.
        """
        _check_tool_claim_token(token)
        return await self._client._request_json("GET", "/tool-claims", params={"token": token})

    async def tool_claim_redeem(
        self,
        token: str,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Add the tables of an emailed Open tables link to a project, in a new folder.

        The link must have been sent to the caller's address. Redeeming the same link again
        returns where the tables already are and adds nothing.

        Args:
            token: Token from the emailed link (up to 300 characters).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``workspace_id``, ``project_id`` and ``folder_id`` (the new folder).

        Raises:
            MammothValidationError: If *token* is empty or longer than 300 characters.
        """
        _check_tool_claim_token(token)
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/tool-claims", json={"token": token}
        )

    async def add_definition(
        self,
        dataset_id: int,
        term: str,
        definition: str,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Save what *term* means for a dataset; a definition of the same term is replaced.

        The term matches case-insensitively. A dataset holds at most 20 definitions;
        over that the server answers ``4DSET076``.

        Args:
            dataset_id: ID of the dataset.
            term: The term, 1-60 characters (for example ``late``).
            definition: What it means for this data, 1-300 characters.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``dataset_id`` and the dataset's ``definitions`` after the save.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/definitions",
            json={"term": term, "definition": definition},
        )

    async def remove_definition(
        self,
        dataset_id: int,
        definition_id: str,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Remove one definition from a dataset by its id.

        An id the dataset does not hold is answered with ``4DSET077``.

        Args:
            dataset_id: ID of the dataset.
            definition_id: The definition's ``id`` from :meth:`list_definitions`.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``dataset_id`` and the dataset's remaining ``definitions``.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/definitions/{definition_id}",
        )

    async def get(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """Get dataset details by ID.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            fields: Comma-separated fields to return, or "__min" / "__standard" /
                "__full" (default: the standard set).

        Returns:
            Dict with complete dataset information.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        path = f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}"
        if fields:
            return await self._client._request_json("GET", path, params={"fields": fields})
        return await self._client._request_json("GET", path)

    async def get_data(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
        timeout: int = 300,
        poll_interval: float | None = None,
    ) -> dict[str, Any]:
        """Get the actual data from a dataset. Polls the job until completion.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            timeout: Maximum wait time in seconds (default 300).
            poll_interval: Seconds between job polls (default:
                client.job_poll_seconds).

        Returns:
            Dict with dataset data.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)

        response = await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/data"
        )
        return await self._client._wait_if_job(
            response, timeout=timeout, poll_interval=poll_interval
        )

    async def create(
        self,
        dataset_spec: dict[str, Any],
        ds_creation_type: str,
        folder_resource_id: str | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new dataset.

        Args:
            dataset_spec: Dataset specification (varies by creation type).
            ds_creation_type: Type of creation: "clone", "cloud", "sketch", "weburl".
            folder_resource_id: Optional folder resource ID.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with created dataset information.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)

        payload: dict[str, Any] = {
            "dataset_spec": dataset_spec,
            "ds_creation_type": ds_creation_type,
        }
        if folder_resource_id is not None:
            payload["folder_resource_id"] = folder_resource_id

        return await self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/datasets", json=payload
        )

    async def update(
        self,
        patch_data: _list[dict[str, Any]],
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Send raw patch operations to the plural ``/datasets`` endpoint.

        This is a low-level passthrough; the payload is sent as
        ``{"patch": patch_data}`` without validation. The current OpenAPI
        contract for this route (``DatasetsPatchOperation``) accepts a single
        ``{"op": "replace", "path": "name", "value": {"<dataset_id>": "<new
        name>"}}`` object, so most callers want :meth:`rename` (one dataset)
        or :meth:`bulk_update` (several datasets) instead.

        Args:
            patch_data: Patch payload, passed through unchanged.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with update result.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets",
            json={"patch": patch_data},
        )

    async def rename(
        self,
        dataset_id: int,
        name: str,
        workspace_id: int | None = None,
        project_id: int | None = None,
        unique: bool = False,
    ) -> dict[str, Any]:
        """Rename a dataset.

        Sends ``PATCH /datasets/{dataset_id}`` with the OpenAPI
        ``DatasetPatchOperation`` ``{"op": "replace", "path": "name",
        "value": name}``.

        Args:
            dataset_id: ID of the dataset to rename.
            name: New name for the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            unique: When true the server picks a free name (``name 2``, ``name 3``...)
                if ``name`` is taken, as dataset creation does. The result's ``name``
                is the name applied.

        Returns:
            Dict with update result.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}",
            json={"patch": {"op": "replace", "path": "name", "value": name}},
            **({"params": {"unique": "true"}} if unique else {}),
        )

    async def get_update_method(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Read what new rows do to a dataset, and how they are matched to its columns.

        The settings live in the dataset's ``configurations.schema_properties``; the web
        app calls ``data_addition_mode`` the dataset's "Update Method".

        Args:
            dataset_id: ID of the dataset (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            The stored settings, keyed as the ``schema_settings`` patch takes them
            (``data_addition_mode``, ``schema_mapping``, ``delete_after_append``, ...).
            Empty when the dataset has none stored yet; the platform then treats it as
            ``combine`` (new rows are added).

        Raises:
            MammothValidationError: If *dataset_id* ≤ 0.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        response = await self.get(
            dataset_id,
            workspace_id=workspace_id,
            project_id=project_id,
            fields="id,configurations",
        )
        dataset = response.get("dataset", response) if isinstance(response, dict) else {}
        configurations = dataset.get("configurations") if isinstance(dataset, dict) else None
        stored = (configurations or {}).get("schema_properties") or {}
        return {key: stored[key] for key in _SCHEMA_SETTINGS_FIELDS if key in stored}

    async def set_update_method(
        self,
        dataset_id: int,
        mode: str,
        schema_mapping: dict[str, _list[str]] | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Set whether a new file or pull replaces a dataset's rows or adds to them.

        The ``replace schema_settings`` patch stores the whole settings object, so a
        field it is not sent goes back to its default. This reads the stored settings
        first and sends them back with only ``mode`` (and ``schema_mapping``) changed;
        a field the dataset does not hold yet is sent as the platform stores it by
        default (see ``_STORED_DEFAULTS``).

        The read and the write are two requests and the backend has no partial update,
        so an edit to the dataset's settings made by someone else between them is
        overwritten.

        The mode stays on the dataset: every later upload into it and every folder
        automation feeding it follows it.

        Args:
            dataset_id: ID of the dataset (must be > 0).
            mode: ``replace`` or ``combine`` (add).
            schema_mapping: Optional ``{"dataset column": ["file column", ...]}`` used to
                match a new file's columns to the dataset's.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            ``{"dataset_id", "data_addition_mode", "previous_data_addition_mode",
            "schema_settings"}``, read back after the change.

        Raises:
            MammothValidationError: If *dataset_id* ≤ 0 or *mode* is not a known mode.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        try:
            new_mode = DataAdditionMode(mode)
        except ValueError as exc:
            raise MammothValidationError(ERR_DATA_ADDITION_MODE.format(mode)) from exc
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        current = await self.get_update_method(dataset_id, workspace_id=ws, project_id=proj)
        settings = {**_STORED_DEFAULTS, **current, "data_addition_mode": new_mode.value}
        if schema_mapping is not None:
            settings["schema_mapping"] = schema_mapping
        await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}",
            json={"patch": {"op": "replace", "path": "schema_settings", "value": settings}},
        )
        stored = await self.get_update_method(dataset_id, workspace_id=ws, project_id=proj)
        return {
            "dataset_id": dataset_id,
            "data_addition_mode": stored.get("data_addition_mode"),
            "previous_data_addition_mode": current.get("data_addition_mode"),
            "schema_settings": stored,
        }

    async def refresh_from_url(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Fetch a fetch-from-URL dataset's link again, into the same dataset.

        Sends ``PATCH /datasets/{dataset_id}`` with the OpenAPI ``DatasetPatchOperation``
        ``{"op": "command", "path": "data_refresh", "value": {"refresh_source_type":
        "weburl", "source_id": dataset_id}}``. The server refuses a dataset that was not
        made from a URL, and a URL that serves JSON (a sketch dataset).

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            The job handle (``job_id``); wait on it before reading the dataset.

        Raises:
            MammothValidationError: If *dataset_id* <= 0.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        patch = {
            "op": "command",
            "path": "data_refresh",
            "value": {"refresh_source_type": "weburl", "source_id": dataset_id},
        }
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}",
            json={"patch": patch},
        )

    async def follow_link(
        self,
        dataset_id: int,
        follow: bool = True,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Make a dataset made from a link follow it again, or turn it into a copy.

        Sends ``PATCH /datasets/{dataset_id}`` with ``{"op": "replace", "path":
        "follow_link", "value": follow}``. A copy no longer refreshes from its link.

        Args:
            dataset_id: ID of the dataset.
            follow: ``True`` to follow the link (refresh from it), ``False`` for a copy.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``follow_link``, the setting after the change.

        Raises:
            MammothValidationError: If *dataset_id* <= 0 or *follow* is not a bool.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        if not isinstance(follow, bool):
            raise MammothValidationError(ERR_FOLLOW_BOOL.format(follow))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        patch = {"op": "replace", "path": "follow_link", "value": follow}
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}",
            json={"patch": patch},
        )

    async def links(
        self,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Show which of the project's datasets follow a link, with their last fetch.

        Copies (datasets that stopped following their link), JSON sketches and Mammoth's
        sample datasets are left out.

        Args:
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``datasets``, oldest first: ``{id, name, url, last_fetched_at,
            failure, refresh_automation_ids}``. ``failure`` (``at``, ``status``, ``reason``,
            ``unreachable``) is set while the last fetch failed.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/links"
        )

    async def delete(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete a dataset.

        Args:
            dataset_id: ID of the dataset to delete.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}"
        )

    async def delete_and_verify(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
        *,
        timeout: int | None = None,
        poll_interval: float = 2.0,
        dependencies: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Delete one dataset and verify its supported GET readback is absent.

        ``dependencies`` is an optional caller-supplied dependency record. It
        is deliberately not inferred from arbitrary inventory differences. If
        known dependents are supplied, the operation is blocked before DELETE;
        callers must explicitly remove owned dependents first.
        """
        if dependencies:
            raise MammothDeletionVerificationError(
                "Dataset deletion is blocked by known dependent resources.",
                {"dataset_id": dataset_id, "dependencies": list(dependencies)},
            )
        ack = await self.delete(dataset_id, workspace_id=workspace_id, project_id=project_id)
        settled = await self._client._wait_if_job(ack)
        deadline = time.monotonic() + (
            timeout if timeout is not None else int(getattr(self._client, "job_timeout", 60))
        )
        while True:
            try:
                current = await self.get(
                    dataset_id, workspace_id=workspace_id, project_id=project_id
                )
            except MammothAPIError as exc:
                if exc.status_code == 404:
                    return {
                        "dataset_id": dataset_id,
                        "status": "deleted",
                        "verified": True,
                        "ack": settled,
                    }
                raise
            state = str(current.get("status", "")).lower() if isinstance(current, dict) else ""
            if state in {"deleted", "absent", "not_found"}:
                return {
                    "dataset_id": dataset_id,
                    "status": "deleted",
                    "verified": True,
                    "ack": settled,
                    "readback": current,
                }
            if time.monotonic() >= deadline:
                raise MammothDeletionVerificationError(
                    "Dataset delete was acknowledged but absence was not verified.",
                    {
                        "dataset_id": dataset_id,
                        "status": "pending",
                        "verified": False,
                        "ack": settled,
                        "readback": current,
                    },
                )
            await asyncio.sleep(poll_interval)

    async def bulk_update(
        self,
        patch_data: dict[str, Any],
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update multiple datasets (bulk operation).

        The plural route accepts one ``DatasetsPatchOperation``; to rename
        several datasets at once pass
        ``{"op": "replace", "path": "name", "value": {"12": "a", "13": "b"}}``.

        Args:
            patch_data: One patch operation object, sent as ``{"patch": patch_data}``.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with bulk update result.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "PATCH", f"/workspaces/{ws}/projects/{proj}/datasets", json={"patch": patch_data}
        )

    async def bulk_delete(
        self,
        dataset_ids: _list[int] | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> None:
        """Delete several datasets by id (bulk operation).

        Args:
            dataset_ids: Ids of the datasets to delete (sent as the ``ids``
                query parameter). Required: the route has no delete-all form
                and rejects an empty id list.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
        """
        if not dataset_ids:
            raise MammothValidationError("bulk_delete requires a non-empty `dataset_ids` list.")
        ids = ",".join(str(int(item)) for item in dataset_ids)
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        await self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/datasets", params={"ids": ids}
        )

    async def preview_interpretation(
        self,
        dataset_id: int,
        instruction: str,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Show how a file would be read differently, without changing it.

        A file that has more than one plausible reading — a title above the
        header, say, or two rows of headers — is read one way and left waiting.
        This asks for another reading in words and shows what it would give.

        Args:
            dataset_id: ID of the dataset.
            instruction: How to read the file, in plain words.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict describing the reading: the columns it would give and a sample.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/interpretation/preview",
            json={"user_instruction": instruction},
        )

    async def confirm_interpretation(
        self,
        dataset_id: int,
        instruction: str,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Apply the reading last previewed for this instruction.

        The plan itself is never sent: it carries SQL, which would then run
        unchecked. An empty ``structure_map`` is what tells the route to re-read
        the plan its own preview saved, rather than working the instruction out
        again and possibly answering differently.

        Args:
            dataset_id: ID of the dataset.
            instruction: The same instruction the preview was asked for.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/interpretation",
            json={"user_instruction": instruction, "structure_map": {}},
        )

    async def get_unstructured_rows(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get the lines of a file that did not fit the dataset built from it.

        A file whose rows are ragged is read as far as it can be, and the lines
        that did not fit are set aside. The dataset then holds data and still
        waits, because nobody has said what to do about them.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``unstructured_rows`` (each with its line, line number and
            the reason it did not fit) and ``row_count``.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/unstructured_rows"
        )

    async def resolve_unstructured_rows(
        self,
        dataset_id: int,
        op: Literal["add", "remove"],
        batch_id: int,
        rows: list[dict[str, Any]],  # type: ignore[valid-type]
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Take corrected set-aside lines into the dataset, or discard them.

        Runs as a job; once no set-aside line remains the dataset is finished.
        Discarded lines do not come back: a line worth keeping has to be
        corrected (``add``) or fixed in the source file and uploaded again.

        Args:
            dataset_id: ID of the dataset.
            op: ``"add"`` to take the corrected lines in, ``"remove"`` to discard them.
            batch_id: Upload the lines came from (``batch_id`` of each row from
                :meth:`get_unstructured_rows`).
            rows: ``{"line_num": int, "line": str}`` entries. ``line`` is the
                corrected text for ``add`` and is ignored for ``remove``.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            The job record (``id``, ``status``, ...); wait on it before reading the dataset.

        Raises:
            MammothValidationError: If *dataset_id* <= 0 or *rows* is empty.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        if not rows:
            raise MammothValidationError("rows must name at least one line")
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        patch = {
            "op": op,
            "path": "unstructured_rows",
            "value": {"batch_id": batch_id, "data": rows},
        }
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/unstructured_rows",
            json={"patch": patch},
        )

    async def list_batches(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> _list[dict[str, Any]]:
        """List batches for a dataset.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            List of batch dicts.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        response = await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches"
        )
        return response.get("batches", response if isinstance(response, _list) else [])

    async def get_batch(
        self,
        dataset_id: int,
        batch_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get details of a specific batch.

        Args:
            dataset_id: ID of the dataset.
            batch_id: ID of the batch.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with batch details.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches/{batch_id}"
        )

    async def get_batch_data(
        self,
        dataset_id: int,
        batch_id: int,
        columns: str | _list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
        workspace_id: int | None = None,
        project_id: int | None = None,
        timeout: int | None = None,
        poll_interval: float | None = None,
    ) -> dict[str, Any]:
        """Get data for a batch; the API returns an asynchronous job.

        ``columns`` are column ids (``c_id`` of the dataset schema), a list or one
        comma-separated string; the route refuses display names.
        """
        if limit < 0 or limit > 100:
            raise MammothValidationError("limit must be between 0 and 100.")
        if offset < 0:
            raise MammothValidationError("offset must be non-negative.")
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if columns is not None:
            params["columns"] = columns if isinstance(columns, str) else ",".join(columns)
        response = await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches/{batch_id}/data",
            params=params,
        )
        return await self._client._wait_if_job(
            response, timeout=timeout, poll_interval=poll_interval
        )

    async def get_file_settings(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get file settings for a dataset.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with file settings.
        """
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/file_settings"
        )

    async def create_from_pdf(
        self,
        file_object_id: int,
        file_name: str,
        file_id: str | None = None,
        table_list: _list[int] | None = None,
        delete_file_after_extract: bool = False,
        is_preview_needed: bool | None = None,
        user_instruction: str | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create one or more datasets from tables extracted out of a PDF file.

        Args:
            file_object_id: Internal ID of the uploaded PDF file object (must be > 0).
            file_name: Original name of the uploaded PDF file.
            file_id: Unique identifier for the uploaded PDF file in pdf2csv (optional).
            table_list: Indices of the tables to extract and convert into datasets
                (exactly one of table_list and is_preview_needed is required).
            delete_file_after_extract: Delete the file from storage after
                extraction completes (default False).
            is_preview_needed: Whether a preview is required before dataset
                creation (optional).
            user_instruction: User-provided instruction for custom extraction
                logic (optional).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with created dataset(s) information (may include a job ID for
            async extraction).

        Raises:
            MammothValidationError: If *file_object_id* ≤ 0, or table_list and
                is_preview_needed are both given or both missing.
        """
        if file_object_id <= 0:
            raise MammothValidationError(ERR_FILE_OBJECT_ID_POSITIVE.format(file_object_id))
        if table_list is None and is_preview_needed is None:
            raise MammothValidationError(
                "Give table_list (the table indices to extract) or is_preview_needed=True "
                "(to preview the tables first); the API needs exactly one of them."
            )
        if table_list is not None and is_preview_needed is not None:
            raise MammothValidationError("Give table_list or is_preview_needed, not both.")
        if table_list is not None and user_instruction is not None:
            raise MammothValidationError("user_instruction cannot be combined with table_list.")
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)

        payload: dict[str, Any] = {
            "file_object_id": file_object_id,
            "file_name": file_name,
            "delete_file_after_extract": delete_file_after_extract,
        }
        if file_id is not None:
            payload["file_id"] = file_id
        if table_list is not None:
            payload["table_list"] = table_list
        if is_preview_needed is not None:
            payload["is_preview_needed"] = is_preview_needed
        if user_instruction is not None:
            payload["user_instruction"] = user_instruction

        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets-from-pdf",
            json=payload,
        )

    async def file_settings_update(
        self,
        dataset_id: int,
        delimiter: str | None = None,
        has_header: bool | None = None,
        initial_skip_count: int | None = None,
        quotechar: str | None = None,
        date_format: str | None = None,
        preview_mode: bool = False,
        skip_auto_process_check: bool = True,
        date_formats: dict[str, str] | None = None,
        set_project_level_date_format: bool = False,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update file data settings for a dataset (delimiter, header, dates, ...).

        The route needs all four of ``delimiter``, ``has_header``, ``initial_skip_count``
        and ``quotechar``. Any of them left out is taken from :meth:`get_file_settings`,
        so one setting can be changed on its own.

        Args:
            dataset_id: ID of the dataset (must be > 0).
            delimiter: Delimiter used in the file (one of ``,``, ``\\t``, ``|``, ``;``);
                the current one if not provided.
            has_header: Whether the file has a header row; the current setting if not
                provided.
            initial_skip_count: Number of initial rows to skip in the file; the current
                count if not provided.
            quotechar: Quote character used in the file (one of ``'``, ``"``, ``""``);
                the current one if not provided.
            date_format: Default date format used in the source file, e.g. "US"
                or "UK" (optional).
            preview_mode: Whether to preview the changes before applying (default False).
            skip_auto_process_check: Whether to skip the automatic processing
                check (default True).
            date_formats: Per-column date format overrides, e.g.
                ``{"column_3": "UK"}`` (optional).
            set_project_level_date_format: Whether to set the date format at the
                project level (default False).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with updated file settings.

        Raises:
            MammothValidationError: If *dataset_id* ≤ 0, or a setting left out cannot be
                read from the dataset.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        reading: dict[str, Any] = {
            "delimiter": delimiter,
            "has_header": has_header,
            "initial_skip_count": initial_skip_count,
            "quotechar": quotechar,
        }
        if any(value is None for value in reading.values()):
            current = await self.get_file_settings(dataset_id, workspace_id=ws, project_id=proj)
            detected = current.get("info", current) if isinstance(current, dict) else {}
            for key, value in reading.items():
                if value is None:
                    reading[key] = detected.get(key) if isinstance(detected, dict) else None
            missing = [key for key, value in reading.items() if value is None]
            if missing:
                raise MammothValidationError(ERR_FILE_SETTINGS_UNKNOWN.format(", ".join(missing)))

        payload: dict[str, Any] = {
            **reading,
            "preview_mode": preview_mode,
            "skip_auto_process_check": skip_auto_process_check,
            "set_project_level_date_format": set_project_level_date_format,
        }
        if date_format is not None:
            payload["date_format"] = date_format
        if date_formats is not None:
            payload["date_formats"] = date_formats

        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/file_settings",
            json=payload,
        )

    async def file_settings_undo(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Undo the last file data settings change for a dataset.

        Args:
            dataset_id: ID of the dataset (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with the restored file settings.

        Raises:
            MammothValidationError: If *dataset_id* ≤ 0.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "DELETE", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/file_settings"
        )

    async def interpretation_preview(
        self,
        dataset_id: int,
        user_instruction: str | None = None,
        structure_map: dict[str, Any] | None = None,
        destination_dataset_id: int | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Preview how a file that could be read several ways would look once interpreted.

        Applies a plain-English instruction (for example one of the dataset's stored
        suggestions, "Skip preamble rows, row 5 is the header") or a ready structure
        map to the cached sample rows. Nothing is finalised; the dataset stays as it is.

        Args:
            dataset_id: ID of the dataset (must be > 0).
            user_instruction: Plain-English description of how to read the file.
            structure_map: A SheetStructureMap from an earlier preview; no model call.
            destination_dataset_id: Replay the saved recipe of this destination dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``preview_rows``, ``total_row_count``, ``structure_map`` and
            ``header_types``.

        Raises:
            MammothValidationError: If *dataset_id* ≤ 0.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/interpretation/preview",
            json=self._interpretation_body(user_instruction, structure_map, destination_dataset_id),
        )

    async def interpretation_confirm(
        self,
        dataset_id: int,
        user_instruction: str | None = None,
        structure_map: dict[str, Any] | None = None,
        destination_dataset_id: int | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        """Apply an interpretation to the whole file and finalise the dataset.

        Moves the dataset out of the state where its file has more than one plausible
        reading. Pass the ``structure_map`` a preview returned, or the same
        ``user_instruction``; or ``mode="original"`` to keep the file in the layout
        it was uploaded in (later files for the dataset are then ingested the same
        way, without review).

        Args:
            dataset_id: ID of the dataset (must be > 0).
            user_instruction: Plain-English description of how to read the file.
            structure_map: The confirmed SheetStructureMap.
            destination_dataset_id: Replay the saved recipe of this destination dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            mode: ``"interpreted"`` (the default: apply the reviewed reshape) or
                ``"original"`` (keep the uploaded layout; takes no reshape inputs).

        Returns:
            Dict, empty when the backend answers with no body.

        Raises:
            MammothValidationError: If *dataset_id* ≤ 0, *mode* is not one of the
                two, or ``mode="original"`` comes with a reshape input.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        body = self._interpretation_body(user_instruction, structure_map, destination_dataset_id)
        if mode is not None:
            if mode not in _INTERPRETATION_MODES:
                raise MammothValidationError(
                    f"`mode` must be one of {', '.join(_INTERPRETATION_MODES)}, got {mode!r}."
                )
            if mode == "original" and body:
                raise MammothValidationError(
                    "`mode` 'original' keeps the uploaded layout and takes no "
                    f"{', '.join(body)}; drop it or use mode 'interpreted'."
                )
            body["mode"] = mode
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/interpretation",
            json=body,
        )

    @staticmethod
    def _interpretation_body(
        user_instruction: str | None,
        structure_map: dict[str, Any] | None,
        destination_dataset_id: int | None,
    ) -> dict[str, Any]:
        fields = {
            "user_instruction": user_instruction,
            "structure_map": structure_map,
            "destination_dataset_id": destination_dataset_id,
        }
        return {name: value for name, value in fields.items() if value is not None}

    async def restore(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Restore a trashed dataset.

        Args:
            dataset_id: ID of the dataset (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with restore result.

        Raises:
            MammothValidationError: If *dataset_id* ≤ 0.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/restore"
        )

    async def trash(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Move a dataset to trash.

        Args:
            dataset_id: ID of the dataset (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with trash result.

        Raises:
            MammothValidationError: If *dataset_id* ≤ 0.
        """
        if dataset_id <= 0:
            raise MammothValidationError(ERR_DATASET_ID_POSITIVE.format(dataset_id))
        ws = workspace_id or self._ws()
        proj = self._proj(project_id)
        return await self._client._request_json(
            "POST", f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/trash"
        )
