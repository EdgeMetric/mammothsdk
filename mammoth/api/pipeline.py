"""
Pipeline tasks HTTP client for managing dataview transformations.

Internal module used by the View object to manage transformation pipeline tasks.
Not intended for direct use — use client.views.get(id) to get a View object instead.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

from ..exceptions import (
    MammothAPIError,
    MammothJobTimeoutError,
    MammothPaginationError,
    MammothTransformError,
    MammothValidationError,
)
from ._pagination import collect_offset_pages

_list = list  # Alias to avoid shadowing by method name

if TYPE_CHECKING:
    from ..client import MammothClient

logger = logging.getLogger(__name__)

PIPELINE_TERMINAL_STATES = frozenset({"ready", "runtime_error", "ref_error"})
# States emitted while a pipeline is settling after a mutation.  Keep this
# allow-list deliberately small: an unrecognised value is not evidence that a
# submit is safe to replay.
PIPELINE_RUNNING_STATES = frozenset({"modifying", "modified", "running"})

ERR_FROM_SEQUENCE_NON_NEGATIVE = "`from_sequence` must be >= 0, got {0}."

# Pipeline-item keys used to resolve the latest task sequence. Reads (data,
# metadata) are scoped to a sequence: sequence 0 is the original dataset, and
# each task adds one. Columns produced by a task exist only at that task's
# sequence and later, so reads must target the latest to see them.
_ITEMS_KEY = "items"
_ITEM_TYPE_KEY = "item_type"
_ITEM_TYPE_TASK = "task"
_ITEM_SEQUENCE_KEY = "sequence"
_ITEM_STATUS_KEY = "status"
_ITEM_STATUS_DELETED = "deleted"
_ITEMS_FIELDS_STANDARD = "__standard"

# OpenAPI `dataview_pipeline_consts_PipelineDraftMode` enum values (pinned in
# `mammoth-cli/spec/openapi/openapi.json`) for which the dataview IS in draft.
# "clean" = draft with no unsaved changes yet; "dirty" = unsaved changes
# pending. "off" (or the field being null/absent) means NOT in draft.
DRAFT_MODE_CLEAN = "clean"
DRAFT_MODE_DIRTY = "dirty"
DRAFT_MODE_ACTIVE_VALUES = frozenset({DRAFT_MODE_CLEAN, DRAFT_MODE_DIRTY})


class PipelineAPI:
    """Low-level HTTP client for pipeline task endpoints.

    Used internally by View objects. Access via client.pipeline.
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client
        # Cache dataview -> dataset resolutions. The browse-based lookup in
        # ``_find_dataset_for_dataview`` scans every dataset in the project, so
        # it is expensive; a dataview belongs to exactly one dataset for its
        # lifetime, so the mapping is stable and safe to memoize per client.
        # Keyed by (workspace_id, project_id, dataview_id) so a client that
        # switches project or workspace never returns a stale dataset.
        self._dataview_dataset_cache: dict[tuple[int, int, int], int] = {}

    def _resolve_ids(
        self, dataview_id: int, dataset_id: int | None = None
    ) -> tuple[int, int, int, int]:
        """Resolve workspace, project, dataset IDs for a dataview.

        Args:
            dataview_id: ID of the target dataview.
            dataset_id: Dataset ID if known (avoids lookup).

        Returns:
            Tuple of (workspace_id, project_id, dataset_id, dataview_id).
        """
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, "project_id", None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")

        if dataset_id is None:
            dataset_id = self._find_dataset_for_dataview(dataview_id)

        return workspace_id, project_id, dataset_id, dataview_id

    def find_dataset_for_dataview(self, dataview_id: int, dataset_id: int | None = None) -> int:
        """Public typed resolver: find the dataset that contains a dataview.

        This is the supported public seam for dataview-to-dataset resolution.
        Callers must not reach into the private ``_find_dataset_for_dataview``
        helper across sub-clients.

        Args:
            dataview_id: ID of the dataview to resolve.
            dataset_id: Known parent dataset ID. This is an identity hint,
                not a request to search: it is returned as-is so callers do
                not probe unrelated datasets.

        Returns:
            The dataset_id that contains this dataview.
        """
        if dataset_id is not None:
            return dataset_id
        return self._find_dataset_for_dataview(dataview_id)

    def _find_dataset_for_dataview(self, dataview_id: int) -> int:
        """Find which dataset contains the specified dataview.

        Uses the browse API to discover datasets (including those nested
        inside folders), then checks each dataset for the dataview.

        Args:
            dataview_id: ID of the dataview to search for.

        Returns:
            The dataset_id that contains this dataview.

        Raises:
            ValueError: If dataview is not found in any dataset.
        """
        workspace_id = self._client.workspace_id
        project_id = getattr(self._client, "project_id", None)
        if project_id is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")

        cache_key = (workspace_id, project_id, dataview_id)
        cached = self._dataview_dataset_cache.get(cache_key)
        if cached is not None:
            return cached

        # Use workspace browse to get project's children (datasets + folders)
        browse_response = self._client.browse.workspace_resources(
            workspace_id=workspace_id, level=2
        )
        project_children: _list[dict[str, Any]] = []
        for resource in browse_response.get("resources", []):
            if resource.get("id") == project_id:
                project_children = resource.get("children", [])
                break

        # DFS through folders to collect all dataset IDs
        dataset_ids = self._collect_dataset_ids(project_children, project_id, workspace_id)

        # Check each dataset for the dataview
        for dataset_id in dataset_ids:
            try:
                # This is an existence probe only (found vs 404), so pin
                # ``sequence=0`` to skip the latest-task-sequence resolution the
                # default would trigger — one saved round trip per dataset
                # scanned, which matters when a project holds many datasets.
                self._client.dataviews.get(
                    dataset_id=dataset_id,
                    dataview_id=dataview_id,
                    workspace_id=workspace_id,
                    project_id=project_id,
                    sequence=0,
                )
                self._dataview_dataset_cache[cache_key] = dataset_id
                return dataset_id
            except MammothAPIError as exc:
                # Some tenants return 403, not 404, when a view belongs to a
                # different dataset. Confirm non-membership with the parent
                # collection before moving on; never discard a genuine denial.
                if exc.status_code == 404:
                    continue
                if exc.status_code == 403:
                    listing = self._client.dataviews.list(
                        dataset_id=dataset_id,
                        workspace_id=workspace_id,
                        project_id=project_id,
                        limit=1000,
                    )
                    views = listing.get("dataviews")
                    # The backend emits a speculative `next` URL even for a
                    # short final page. A short page relative to the server's
                    # reported limit proves this dataset has no further views.
                    page_limit = listing.get("limit", 1000)
                    if (
                        isinstance(views, list)
                        and isinstance(page_limit, int)
                        and len(views) < page_limit
                    ):
                        listed_ids = {view.get("id") for view in views if isinstance(view, dict)}
                        if dataview_id not in listed_ids:
                            continue
                raise
            except KeyError:
                # A missing dict key while reading the response is a local
                # miss for this dataset; keep scanning the remaining datasets.
                continue

        raise ValueError(f"Dataview {dataview_id} not found in any dataset in project {project_id}")

    def _collect_dataset_ids(
        self,
        children: _list[dict[str, Any]],
        project_id: int,
        workspace_id: int,
    ) -> _list[int]:
        """Collect all dataset IDs from browse children, recursing into folders.

        Folder browsing is parallelized to avoid sequential latency when
        projects have many nested folders.

        Args:
            children: List of browse resource children.
            project_id: Current project ID.
            workspace_id: Current workspace ID.

        Returns:
            List of dataset IDs found.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        dataset_ids: _list[int] = []
        folders: _list[dict[str, Any]] = []

        for child in children:
            child_type = child.get("type", "")
            if child_type == "datasource":
                dataset_ids.append(child["id"])
            elif child_type == "label":
                folders.append(child)

        if not folders:
            return dataset_ids

        def _browse_folder(folder_id: int) -> _list[dict[str, Any]]:
            resp = self._client.browse.folder_resources(
                folder_id=folder_id,
                project_id=project_id,
                workspace_id=workspace_id,
                level=2,
            )
            all_children: _list[dict[str, Any]] = []
            for sub_resource in resp.get("resources", []):
                all_children.extend(sub_resource.get("children", []))
            return all_children

        with ThreadPoolExecutor(max_workers=min(len(folders), 8)) as pool:
            futures = {pool.submit(_browse_folder, folder["id"]): folder for folder in folders}
            for future in as_completed(futures):
                try:
                    sub_children = future.result()
                    dataset_ids.extend(
                        self._collect_dataset_ids(sub_children, project_id, workspace_id)
                    )
                except MammothAPIError as exc:
                    # A vanished or inaccessible-as-missing folder (404) is
                    # safely skippable. Auth, rate-limit, and server errors
                    # (401/403/429/5xx) must propagate so resolution is not
                    # silently narrowed and misreported as a not-found.
                    if exc.status_code == 404:
                        continue
                    raise

        return dataset_ids

    def _base_url(self, ws_id: int, proj_id: int, ds_id: int, dv_id: int) -> str:
        return f"/workspaces/{ws_id}/projects/{proj_id}/datasets/{ds_id}/dataviews/{dv_id}/pipeline"

    def _dv_url(self, ws_id: int, proj_id: int, ds_id: int, dv_id: int) -> str:
        return f"/workspaces/{ws_id}/projects/{proj_id}/datasets/{ds_id}/dataviews/{dv_id}"

    def get_pipeline(self, dataview_id: int, dataset_id: int | None = None) -> dict[str, Any]:
        """Get pipeline state for a dataview.

        Args:
            dataview_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Pipeline state dict.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        return self._client._request_json("GET", self._base_url(ws, proj, ds, dv))

    def list_tasks(self, dataview_id: int, dataset_id: int | None = None) -> dict[str, Any]:
        """List all pipeline tasks for a dataview.

        Requests ``__full`` fields: the server's default (``__standard``)
        omits ``transform_status`` and ``reference_errors``, so a task that
        failed at run time (a GEN_AI step hitting a workspace AI quota, for
        example) is otherwise invisible -- the pipeline still reads ready.

        Args:
            dataview_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Dict with tasks list.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        return self._client._request_json(
            "GET", f"{self._base_url(ws, proj, ds, dv)}/tasks", params={"fields": "__full"}
        )

    def add_task(
        self, dataview_id: int, task_spec: dict[str, Any], dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Add a new transformation task to the pipeline.

        Args:
            dataview_id: ID of the dataview.
            task_spec: Task specification dict (varies by task type).
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Dict with created task info or job info.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        payload = {"DATAVIEW_ID": dv, **task_spec}
        response = self._client._request_json(
            "POST", f"{self._base_url(ws, proj, ds, dv)}/tasks", json=payload
        )
        return self._client._wait_if_job(response)

    def get_task(
        self, dataview_id: int, task_id: int, dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Get a specific pipeline task.

        Requests ``__full`` fields; see :meth:`list_tasks` for why.

        Args:
            dataview_id: ID of the dataview.
            task_id: ID of the task.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Task details dict.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        return self._client._request_json(
            "GET",
            f"{self._base_url(ws, proj, ds, dv)}/tasks/{task_id}",
            params={"fields": "__full"},
        )

    def update_task(
        self,
        dataview_id: int,
        task_id: int,
        task_spec: dict[str, Any] | None = None,
        dataset_id: int | None = None,
        patches: list[dict[str, Any]] | None = None,
        skip_validation: bool | None = None,
    ) -> dict[str, Any]:
        """Update an existing pipeline task.

        The route takes ``{"patches": [{"op", "path", "value"}]}`` with ``op``
        ``replace`` or ``command`` and ``path`` one of ``params``,
        ``display_info``, ``suspend``, ``restore``, ``discard``. ``task_spec``
        is the shortcut for ``[{"op": "replace", "path": "params", "value":
        task_spec}]``.

        Args:
            dataview_id: ID of the dataview.
            task_id: ID of the task to update.
            task_spec: New task params (replaces the ``params`` path).
            dataset_id: Exact parent dataset id.
            patches: Explicit patch operations, used instead of ``task_spec``.
            skip_validation: Forwarded as the ``skip_validation`` query flag.

        Returns:
            Updated task dict.
        """
        operations = list(patches or [])
        if task_spec is not None:
            operations.append({"op": "replace", "path": "params", "value": task_spec})
        if not operations:
            raise MammothValidationError("Provide `task_spec` or `patches` to update a task.")
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        params = {"skip_validation": skip_validation} if skip_validation is not None else None
        response = self._client._request_json(
            "PATCH",
            f"{self._base_url(ws, proj, ds, dv)}/tasks/{task_id}",
            params=params,
            json={"patches": operations},
        )
        return self._client._wait_if_job(response)

    def delete_task(
        self, dataview_id: int, task_id: int, dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Delete a pipeline task.

        Args:
            dataview_id: ID of the dataview.
            task_id: ID of the task to delete.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Delete confirmation dict.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        response = self._client._request_json(
            "DELETE", f"{self._base_url(ws, proj, ds, dv)}/tasks/{task_id}"
        )
        return self._client._wait_if_job(response)

    def preview_task(
        self, dataview_id: int, task_spec: dict[str, Any], dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Preview task results without adding to pipeline.

        Args:
            dataview_id: ID of the dataview.
            task_spec: Task specification to preview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Preview result dict with sample data.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        response = self._client._request_json(
            "POST", f"{self._base_url(ws, proj, ds, dv)}/task_preview", json=task_spec
        )
        return self._client._wait_if_job(response)

    def draft_mode(
        self, dataview_id: int, command: str, dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Manage draft mode for a dataview pipeline.

        Args:
            dataview_id: ID of the dataview.
            command: Draft mode command ("enter", "exit", "submit", "discard").
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Draft mode state dict.
        """
        if command not in {"enter", "exit", "submit", "discard"}:
            raise ValueError("command must be one of: enter, exit, submit, discard")
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        response = self._client._request_json(
            "POST",
            f"{self._dv_url(ws, proj, ds, dv)}/draft-mode",
            json={"draft_operation": command},
        )
        return self._client._wait_if_job(response)

    def get_draft_status(self, dataview_id: int, dataset_id: int | None = None) -> dict[str, Any]:
        """Read server-backed draft state for a dataview pipeline.

        Draft state must be read from the server so it is consistent across
        separate processes. This reads the current pipeline and reports whether
        the dataview is in draft mode, using the server's own pipeline state
        rather than any process-local flag.

        Args:
            dataview_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            A dict with ``dataview_id``, ``is_draft``, and the raw pipeline
            ``draft`` section when the server provides one.
        """
        pipeline = self.get_pipeline(dataview_id, dataset_id)
        # Some API revisions wrap the pipeline resource in a top-level
        # ``pipeline`` object.  Normalize that shape once and use the same
        # resource for state and draft fields; reading state from the outer
        # envelope while reading draft mode from the nested resource makes a
        # committed draft look unknown and can replay SUBMIT.
        resource: Mapping[str, Any] = pipeline
        nested = pipeline.get("pipeline")
        if isinstance(nested, Mapping):
            resource = nested

        draft_section = resource.get("draft")
        if draft_section is None:
            draft_section = resource.get("draft_mode")
        if draft_section is None and resource is not pipeline:
            # Preserve compatibility with wrappers that keep the draft marker
            # on the envelope while nesting only the state resource.
            draft_section = pipeline.get("draft", pipeline.get("draft_mode"))

        mode: str | None = None
        if isinstance(draft_section, str):
            mode = draft_section.lower()
        elif isinstance(draft_section, dict):
            raw_mode = draft_section.get("mode", draft_section.get("status"))
            if isinstance(raw_mode, str):
                mode = raw_mode.lower()
        draft_flags = (
            resource.get("is_draft"),
            resource.get("in_draft_mode"),
            pipeline.get("is_draft"),
            pipeline.get("in_draft_mode"),
        )
        is_draft = bool(
            (mode in DRAFT_MODE_ACTIVE_VALUES)
            or (isinstance(draft_section, dict) and draft_section.get("active") is True)
            or (isinstance(draft_section, dict) and draft_section.get("is_draft") is True)
            or any(flag is True for flag in draft_flags)
        )
        raw_state = resource.get("state")
        if "state" not in resource and resource is not pipeline:
            raw_state = pipeline.get("state")
        state = raw_state.lower() if isinstance(raw_state, str) else None
        return {
            "dataview_id": dataview_id,
            "is_draft": is_draft,
            "mode": mode,
            "has_pending_changes": mode == DRAFT_MODE_DIRTY,
            "pipeline_state": state,
            "draft": draft_section,
            "pipeline": pipeline,
        }

    def reconcile_draft_submission(
        self, dataview_id: int, dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Read the server state after an interrupted draft submission.

        This performs no mutation. A caller can safely invoke it from a fresh
        process before deciding whether another SUBMIT is necessary.
        """
        status = self.get_draft_status(dataview_id, dataset_id)
        state = status.get("pipeline_state")
        mode = status.get("mode")
        is_draft = status.get("is_draft") is True
        if state == "ready":
            if is_draft and mode == DRAFT_MODE_DIRTY:
                outcome = "pending"
            elif (is_draft and mode == DRAFT_MODE_CLEAN) or not is_draft:
                outcome = "succeeded"
            else:
                # A draft flag without a valid mode is not enough evidence to
                # replay a write.
                outcome = "unknown"
        elif state in PIPELINE_TERMINAL_STATES:
            outcome = "failed"
        elif state in PIPELINE_RUNNING_STATES:
            outcome = "running"
        else:
            # Missing, non-string, or newly introduced server states must be
            # reconciled by a caller rather than guessed into a mutation.
            outcome = "unknown"
        result = {**status, "outcome": outcome}
        if outcome == "unknown":
            result.update(
                {
                    "operation_state": "outcome_unknown",
                    "mutation_blocked": True,
                    "recovery_action": "re-read draft status before replaying SUBMIT",
                }
            )
        return result

    def edit_pipeline(
        self,
        dataview_id: int,
        patches: _list[dict[str, Any]],
        dataset_id: int | None = None,
    ) -> dict[str, Any]:
        """PATCH pipeline with operations (auto_run, run, reset, etc.).

        Args:
            dataview_id: ID of the dataview.
            patches: List of patch operation dicts.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Updated pipeline state dict.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        return self._client._request_json(
            "PATCH", self._base_url(ws, proj, ds, dv), json={"patches": patches}
        )

    def wait_for_pipeline(
        self,
        dataview_id: int,
        dataset_id: int | None = None,
        timeout: float | None = None,
        poll_interval: float = 3,
    ) -> dict[str, Any]:
        """Poll pipeline state until it reaches a terminal state.

        After any pipeline mutation (add_task, delete_task, sql_generation),
        the pipeline transitions through transient states before data is ready:
        ``modifying → modified → running → ready``.

        This method blocks until the pipeline reaches a terminal state
        (``ready``, ``runtime_error``, ``ref_error``).

        Args:
            dataview_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).
            timeout: Max wait time in seconds (default: client.pipeline_timeout).
            poll_interval: Seconds between polls (default: 3).

        Returns:
            Final pipeline state dict.

        Raises:
            MammothTransformError: If pipeline reaches ``runtime_error`` or ``ref_error``.
            MammothJobTimeoutError: If timeout is exceeded.
        """
        effective_timeout = (
            timeout if timeout is not None else getattr(self._client, "pipeline_timeout", 3600)
        )

        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        url = self._base_url(ws, proj, ds, dv)
        deadline = time.monotonic() + effective_timeout

        while True:
            pipeline = self._client._request_json("GET", url)
            state = pipeline.get("state", "").lower()

            if state in PIPELINE_TERMINAL_STATES:
                if state in ("runtime_error", "ref_error"):
                    detail = pipeline.get("error", state)
                    raise MammothTransformError(
                        f"Pipeline failed with state '{state}': {detail}",
                        details={"pipeline_state": state, "pipeline": pipeline},
                    )
                logger.debug("Pipeline ready for dataview %d (state=%s)", dataview_id, state)
                return pipeline

            if time.monotonic() >= deadline:
                raise MammothJobTimeoutError(job_id=dataview_id, timeout_seconds=effective_timeout)

            logger.debug("Pipeline state for dataview %d: %s — waiting...", dataview_id, state)
            time.sleep(poll_interval)

    def command(
        self, dataview_id: int, command: str, dataset_id: int | None = None
    ) -> dict[str, Any]:
        """Execute a draft-mode command on a dataview's pipeline.

        This wraps the OpenAPI ``ExecutePipelineDraftCommand`` operation, which
        is the same ``.../draft-mode`` endpoint used by :meth:`draft_mode`.

        Args:
            dataview_id: ID of the dataview.
            command: Draft mode command ("enter", "exit", "submit", "discard").
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Draft mode state dict.
        """
        return self.draft_mode(dataview_id, command, dataset_id)

    def items(
        self,
        dataview_id: int,
        dataset_id: int | None = None,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
        sequence: int | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Get pipeline items (tasks and exports, interleaved) for a dataview.

        Args:
            dataview_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).
            fields: Fields to return (e.g., "__standard", "__full", "__min").
            limit: Maximum number of results.
            offset: Number of results to skip.
            sort: Sort specification.
            sequence: Filter to a specific pipeline task sequence number.
            status: Filter by item status.

        Returns:
            Dict with the pipeline items list.
        """
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sort is not None:
            params["sort"] = sort
        if sequence is not None:
            params["sequence"] = sequence
        if status is not None:
            params["status"] = status
        return self._client._request_json(
            "GET", f"{self._base_url(ws, proj, ds, dv)}/items", params=params or None
        )

    def items_all(
        self,
        dataview_id: int,
        dataset_id: int,
        fields: str | None = None,
        limit: int = 100,
        sort: str | None = None,
        sequence: int | None = None,
        status: str | None = None,
        max_pages: int = 1000,
    ) -> dict[str, Any]:
        """Read the complete bounded pipeline-item listing.

        ``items`` intentionally mirrors the CLI's single-page
        ``view.pipeline.items`` operation.  Use this method when a readback
        needs completeness: every page is requested through :meth:`items`,
        which re-resolves the same workspace/project/dataset/dataview parent,
        while the shared paginator rejects repeated pages, non-advancing
        offsets, empty pages with a continuation, and excessive page counts.
        No mutation or server-provided URL is followed directly.
        """
        if isinstance(dataview_id, bool) or not isinstance(dataview_id, int) or dataview_id <= 0:
            raise MammothValidationError("`dataview_id` must be a positive integer")
        if isinstance(dataset_id, bool) or not isinstance(dataset_id, int) or dataset_id <= 0:
            raise MammothValidationError("`dataset_id` must be a positive integer")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise MammothValidationError("`limit` must be an integer from 1 through 100")
        if (
            isinstance(max_pages, bool)
            or not isinstance(max_pages, int)
            or not 1 <= max_pages <= 1000
        ):
            raise MammothValidationError("`max_pages` must be an integer from 1 through 1000")
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        expected_path = f"{self._base_url(ws, proj, ds, dv)}/items"

        def fetch(offset: int) -> dict[str, Any]:
            page = self.items(
                dataview_id=dataview_id,
                dataset_id=dataset_id,
                fields=fields,
                limit=limit,
                offset=offset,
                sort=sort,
                sequence=sequence,
                status=status,
            )
            hint = page.get("next")
            if hint:
                parsed = urlparse(str(hint))
                # The paginator uses only the offset from ``next``; still
                # require the server's hint to identify this exact parent
                # route and to carry the documented offset cursor.
                if not parsed.path.endswith(expected_path) or "offset" not in parse_qs(
                    parsed.query
                ):
                    raise MammothPaginationError(
                        "The API returned an unsupported pipeline-items continuation URL.",
                        {"next": str(hint), "expected_path": expected_path},
                    )
            return page

        return collect_offset_pages(
            fetch,
            item_key=_ITEMS_KEY,
            limit=limit,
            max_pages=max_pages,
        )

    def latest_task_sequence(self, dataview_id: int, dataset_id: int | None = None) -> int:
        """Return the highest non-deleted task sequence in the pipeline.

        Data and metadata reads are scoped to a task *sequence*. Sequence 0 is
        the original dataset; each task adds a sequence, and the columns a task
        produces exist only from its sequence onward. Reading at the latest
        sequence is therefore what surfaces every pipeline-derived column
        (math, add_column, etc.).

        Args:
            dataview_id: ID of the dataview.
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            The highest task sequence, or ``0`` when the view has no tasks.
        """
        page = self.items(dataview_id, dataset_id, fields=_ITEMS_FIELDS_STANDARD)
        sequences = [
            item.get(_ITEM_SEQUENCE_KEY)
            for item in page.get(_ITEMS_KEY) or []
            if item.get(_ITEM_TYPE_KEY) == _ITEM_TYPE_TASK
            and isinstance(item.get(_ITEM_SEQUENCE_KEY), int)
            and item.get(_ITEM_STATUS_KEY) != _ITEM_STATUS_DELETED
        ]
        return max(sequences) if sequences else 0

    def rerun(
        self,
        dataview_id: int,
        from_sequence: int | None = None,
        dataset_id: int | None = None,
    ) -> dict[str, Any]:
        """Rerun the pipeline starting from a specific task sequence.

        Useful for rerunning a stale pipeline from the step where a parameter
        is used, instead of rerunning the whole pipeline from scratch.

        Args:
            dataview_id: ID of the dataview.
            from_sequence: Task sequence number to start the rerun from (>= 0).
                If not provided, the server reruns from step 0 (the full
                pipeline).
            dataset_id: Dataset ID (auto-detected if not provided).

        Returns:
            Dict with the rerun job info.

        Raises:
            MammothValidationError: If from_sequence is negative.
        """
        if from_sequence is not None and from_sequence < 0:
            raise MammothValidationError(ERR_FROM_SEQUENCE_NON_NEGATIVE.format(from_sequence))
        ws, proj, ds, dv = self._resolve_ids(dataview_id, dataset_id)
        body: dict[str, Any] = {}
        if from_sequence is not None:
            body["from_sequence"] = from_sequence
        response = self._client._request_json(
            "POST", f"{self._base_url(ws, proj, ds, dv)}/rerun", json=body
        )
        return self._client._wait_if_job(response)
