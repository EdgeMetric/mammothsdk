"""
Dataviews API client for managing dataviews in Mammoth.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

ERR_DATAVIEW_ID_POSITIVE = "`dataview_id` must be a positive integer, got {0}."
ERR_IMPACT_SCOPE = '`scope` must be "task" or "view", got {0!r}.'
ERR_IMPACT_TASK_ID = '`task_id` is required when `scope` is "task".'
_IMPACT_SCOPES = frozenset({"task", "view"})
ERR_OPTIMIZE_RULE = (
    "`apply_rules` entries must be drop_suspended, drop_duplicate, drop_noop_filter or "
    "hoist_filter, got {0}."
)
ERR_COMPARE_PAIRS = "`pairs` must hold 1 to 20 [view_a, view_b] pairs of positive dataview ids."
_OPTIMIZE_RULES = frozenset(
    {"drop_suspended", "drop_duplicate", "drop_noop_filter", "hoist_filter"}
)
_COMPARE_MAX_PAIRS = 20

#: Aggregate functions supported by :meth:`DataviewsAPI.aggregate`. Deliberately
#: a small, exact-match subset of the backend's ``PivotAggregationFunction``
#: wire vocabulary (which also has PERCENTAGE, CONCAT) — what an agent needs for
#: "total/count/average/min/max/spread/distinct values of a column", and every
#: aggregation the web app's Explore card offers (COUNT, SUM, AVG, MIN, MAX, STDDEV).
_AGGREGATE_FUNCTIONS = frozenset({"SUM", "COUNT", "AVG", "MIN", "MAX", "STDDEV", "DISTINCT_COUNT"})
ERR_AGGREGATE_FUNCTION_UNSUPPORTED = (
    "`function` must be one of SUM, COUNT, AVG, MIN, MAX, STDDEV, DISTINCT_COUNT for a volatile "
    "aggregation query, "
    "got {0!r}."
)
ERR_AGGREGATE_COLUMN_REQUIRED = "`column` is required for {0} aggregation."
ERR_AGGREGATE_EXACTLY_ONE = (
    "Pass exactly one of `aggregations` (a PIVOT; `group_by` is optional) or `metric`."
)

#: Date-truncation levels the backend's PIVOT GROUP_BY ``TRUNCATE`` accepts
#: (``apiv2.dataview.consts.DateTruncUnit``).
_DATE_TRUNCATE_LEVELS = frozenset(
    {
        "SECOND",
        "MINUTE",
        "HOUR",
        "DAY",
        "WEEK",
        "MONTH",
        "QUARTER",
        "YEAR",
        "DECADE",
        "CENTURY",
        "MILLENNIUM",
        "AUTO",
    }
)
ERR_GROUP_BY_COLUMN_REQUIRED = "`column` is required for a PIVOT `group_by` entry."
ERR_GROUP_BY_TRUNCATE_UNSUPPORTED = (
    "`truncate` must be one of SECOND, MINUTE, HOUR, DAY, WEEK, MONTH, QUARTER, YEAR, DECADE, "
    "CENTURY, MILLENNIUM, AUTO for a PIVOT `group_by` entry, got {0!r}."
)


def _build_aggregate_select_item(agg: dict[str, Any], internal_name: str) -> dict[str, Any]:
    """Build one volatile-query PIVOT/METRIC aggregate item from ``{column, function, as_name}``.

    Raises:
        MammothValidationError: If *agg*'s function is not one of SUM, COUNT,
            AVG, MIN, MAX, or its column is missing for a non-COUNT function.
    """
    function = str(agg.get("function") or "").upper()
    if function not in _AGGREGATE_FUNCTIONS:
        raise MammothValidationError(ERR_AGGREGATE_FUNCTION_UNSUPPORTED.format(agg.get("function")))
    column = agg.get("column")
    if not column and function != "COUNT":
        raise MammothValidationError(ERR_AGGREGATE_COLUMN_REQUIRED.format(function))
    as_name = agg.get("as_name") or (f"{function}_{column}" if column else function)
    item: dict[str, Any] = {"FUNCTION": function, "AS": as_name, "INTERNAL_NAME": internal_name}
    if column:
        item["COLUMN"] = column
    return item


def _build_pivot_group_by_item(entry: str | dict[str, Any], index: int) -> dict[str, Any]:
    """Build one volatile-query PIVOT GROUP_BY item.

    *entry* is either a plain column name (a TEXT-style group, unchanged
    behaviour), or a ``{"column": ..., "truncate": ...}`` / ``{"column": ...,
    "resolution": ...}`` dict bucketing a DATE column by truncation level or a
    NUMERIC column by resolution level, mirroring the web app's Explore card
    (``getPivotGroupByParam``).

    Raises:
        MammothValidationError: If *entry* is a dict without ``column``, or its
            ``truncate`` is not one of the backend's allowed date-truncation
            levels.
    """
    if isinstance(entry, str):
        return {"COLUMN": entry, "INTERNAL_NAME": f"group_{index}"}
    column = entry.get("column")
    if not column:
        raise MammothValidationError(ERR_GROUP_BY_COLUMN_REQUIRED)
    item: dict[str, Any] = {"COLUMN": column, "INTERNAL_NAME": f"group_{index}"}
    truncate = entry.get("truncate")
    if truncate is not None:
        truncate = str(truncate).upper()
        if truncate not in _DATE_TRUNCATE_LEVELS:
            raise MammothValidationError(
                ERR_GROUP_BY_TRUNCATE_UNSUPPORTED.format(entry.get("truncate"))
            )
        item["TRUNCATE"] = truncate
    resolution = entry.get("resolution")
    if resolution is not None:
        item["RESOLUTION"] = resolution
    return item


def _build_pivot_param(
    aggregations: list[dict[str, Any]], group_by: list[str | dict[str, Any]] | None
) -> dict[str, Any]:
    """Build a volatile-query PIVOT param (distinct from the pipeline PIVOT task).

    Raises:
        MammothValidationError: If *aggregations* is empty, or (from
            :func:`_build_aggregate_select_item` or
            :func:`_build_pivot_group_by_item`) an aggregation or group_by
            entry is invalid.
    """
    if not aggregations:
        raise MammothValidationError("`aggregations` must be a non-empty list.")
    pivot: dict[str, Any] = {
        "SELECT": [
            _build_aggregate_select_item(agg, f"agg_{index}")
            for index, agg in enumerate(aggregations)
        ]
    }
    if group_by:
        pivot["GROUP_BY"] = [
            _build_pivot_group_by_item(entry, index) for index, entry in enumerate(group_by)
        ]
    return pivot


ERR_AGGREGATE_SORT_INVALID = (
    "`sort` must be at most three [result_column, 'ASC'|'DESC'] pairs, got {0!r}."
)


def _build_query_display_properties(
    limit: int | None, sort: _list[_list[str]] | None
) -> dict[str, Any]:
    """Build a volatile query's ``display_properties`` (LIMIT and SORT)."""
    display: dict[str, Any] = {}
    if limit is not None:
        display["LIMIT"] = limit
    if sort:
        valid = len(sort) <= 3 and all(
            len(pair) == 2 and str(pair[1]).upper() in ("ASC", "DESC") for pair in sort
        )
        if not valid:
            raise MammothValidationError(ERR_AGGREGATE_SORT_INVALID.format(sort))
        display["SORT"] = [[str(pair[0]), str(pair[1]).upper()] for pair in sort]
    return display


def _build_metric_param(metric: dict[str, Any]) -> dict[str, Any]:
    """Build a volatile-query METRIC param from a single ``{column, function, as_name}`` dict."""
    item = _build_aggregate_select_item(metric, "metric")
    value: dict[str, Any] = {"FUNCTION": item["FUNCTION"]}
    if "COLUMN" in item:
        value["ARGUMENT"] = item["COLUMN"]
    return {
        "EXPRESSION": [{"TYPE": "FUNCTION", "VALUE": value}],
        "AS": item["AS"],
        "INTERNAL_NAME": item["INTERNAL_NAME"],
    }


#: Rows a TEXT :meth:`DataviewsAPI.explore` returns unless ``limit`` says
#: otherwise -- the same default the web app's Explore card top-values list
#: uses.
_EXPLORE_DEFAULT_TEXT_LIMIT = 20


def _add_explore_percentages(rows: list[dict[str, Any]]) -> None:
    """Add a local ``percentage`` (of the total count across every bucket) to each row.

    Mirrors the Explore card's PERCENTAGE(AGGREGATION=COUNT) select item
    without asking the backend for it (:func:`_build_aggregate_select_item`
    sends no PERCENTAGE), so the percentage is always against
    every bucket the query returned, never just a page truncated by ``limit``.
    """
    total = sum(row.get("agg_0") or 0 for row in rows)
    for row in rows:
        row["percentage"] = round((row.get("agg_0") or 0) / total * 100, 2) if total else 0.0


def _add_explore_cumulative(rows: list[dict[str, Any]]) -> None:
    """Add a ``cumulative`` running total to each row, in bucket order.

    The running total is of the per-bucket metric (``agg_1``) when the explore
    carries one, else of the bucket count (``agg_0``). It always runs over every
    bucket the query returned, in ascending bucket order, whatever display order
    or page the caller then asks for. A blank bucket has no place in the order, so
    it gets ``None``.
    """
    field = "agg_1" if any("agg_1" in row for row in rows) else "agg_0"
    running = Decimal(0)
    for row in sorted(rows, key=lambda r: (r.get("group_0") is None, r.get("group_0") or 0)):
        if row.get("group_0") is None:
            row["cumulative"] = None
            continue
        running += Decimal(str(row.get(field) or 0))
        row["cumulative"] = float(running)


#: ``sort`` values :meth:`DataviewsAPI.explore` accepts: by count or by bucket value.
_EXPLORE_SORTS = frozenset({"count_desc", "count_asc", "value_asc", "value_desc"})
ERR_EXPLORE_SORT_UNSUPPORTED = (
    "`sort` must be one of count_desc, count_asc, value_asc, value_desc, got {0!r}."
)


def _explore_sort_and_limit(
    rows: list[dict[str, Any]],
    column_type: str,
    sort: str | None,
    page: tuple[int | None, int | None],
) -> list[dict[str, Any]]:
    """Order explore rows the way the Explore card does, then page by ``(offset, limit)``.

    Default order: a DATE/NUMERIC bucket ascending by value (a trend or
    distribution reads left to right); a TEXT top-values list by count
    descending, defaulting to the top 20 when no ``limit`` is given. ``sort``
    overrides it (the card's sort menu). Blanks sort last either way.
    """
    order = sort or ("count_desc" if column_type not in ("DATE", "NUMERIC") else "value_asc")
    if order not in _EXPLORE_SORTS:
        raise MammothValidationError(ERR_EXPLORE_SORT_UNSUPPORTED.format(sort))
    field = "agg_0" if order.startswith("count") else "group_0"
    present = [row for row in rows if row.get(field) is not None]
    blank = [row for row in rows if row.get(field) is None]
    ordered = sorted(present, key=lambda row: row[field], reverse=order.endswith("desc")) + blank
    offset, limit = page
    if limit is None and column_type not in ("DATE", "NUMERIC"):
        limit = _EXPLORE_DEFAULT_TEXT_LIMIT
    start = offset or 0
    return ordered[start : start + limit] if limit else ordered[start:]


class DataviewsAPI:
    """Client for interacting with Mammoth Dataviews API.

    Access via client.dataviews:
        views = client.dataviews.list(dataset_id=123)
        view = client.dataviews.get(dataset_id=123, dataview_id=456)
        data = client.dataviews.get_data(dataset_id=123, dataview_id=456)

    For rich View objects with transformation methods, use client.views instead.
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self) -> int:
        proj = getattr(self._client, "project_id", None)
        if proj is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        return proj

    async def list(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
        limit: int = 100,
        sort: str = "(created_at:desc)",
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get list of dataviews in a dataset.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            limit: Maximum number of results (default 100).
            sort: Sort order (default "(created_at:desc)").
            offset: Number of dataviews to skip (default 0).

        Returns:
            Dict containing dataviews list.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        params: dict[str, Any] = {"limit": limit, "sort": sort}
        if offset:
            params["offset"] = offset
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews",
            params=params,
        )

    async def get(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
        sequence: int | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """Get dataview information.

        Metadata is scoped to a pipeline task *sequence*. Omitting it leaves
        the choice to the API, which reads the last task in the pipeline, so
        the returned ``metadata`` reflects every pipeline-derived column (math,
        add_column, etc.). Pass ``sequence=0`` for the original dataset columns.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            sequence: Pipeline step to read metadata at. Omit to let the
                API read the last task in the pipeline.
            fields: Field set to return (e.g. ``"__full"``); server default if omitted.

        Returns:
            Dict with complete dataview information.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        # No sequence means "the last task in the pipeline" to the API itself.
        # Working it out here cost a request and got it wrong while a draft was
        # open, where the highest task is the staged one that never ran.
        params: dict[str, Any] = {}
        if sequence is not None:
            params["sequence"] = sequence
        if fields is not None:
            params["fields"] = fields
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}",
            params=params or None,
        )

    async def create(
        self,
        dataset_id: int,
        name: str | None = "View",
        clone_config_from: int | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create or duplicate a dataview.

        Args:
            dataset_id: ID of the dataset.
            name: Name of the dataview (default "View").
            clone_config_from: ID of dataview to clone config from (optional).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``"dataview_id"`` key containing the new dataview's ID.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        payload: dict[str, Any] = {"name": name}
        if clone_config_from is not None:
            payload["clone_config_from"] = clone_config_from
        response = await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews",
            json=payload,
        )
        return await self._client._wait_if_job(response)

    async def update(
        self,
        dataset_id: int,
        dataview_id: int,
        patch_data: _list[dict[str, Any]],
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update dataview properties using JSON Patch operations.

        Each operation in ``patch_data`` should have ``op``, ``path``, and
        ``value`` keys following JSON Patch conventions.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview to update.
            patch_data: List of patch operations.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with update result.

        Example::

            await client.dataviews.update(
                dataset_id=123, dataview_id=456,
                patch_data=[{"op": "replace", "path": "name", "value": "Renamed"}],
            )
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}",
            json={"patch": patch_data},
        )

    async def delete(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete a dataview.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview to delete.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}",
        )

    async def delete_impact(
        self,
        dataset_id: int,
        dataview_id: int,
        scope: str,
        task_id: int | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """List what deleting a pipeline task or a whole view would affect (read only).

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            scope: ``"task"`` for one pipeline task (then *task_id* is required) or
                ``"view"`` for the whole view.
            task_id: ID of the task, for ``scope="task"``.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with the affected ``dashboards``, ``exports``, ``views`` (dependent
            dataviews) and ``automations``, plus ``dependencies`` when the scope is a task.

        Raises:
            MammothValidationError: If *scope* is not ``task`` or ``view``, or a task
                scope has no *task_id*.
        """
        if scope not in _IMPACT_SCOPES:
            raise MammothValidationError(ERR_IMPACT_SCOPE.format(scope))
        if scope == "task" and task_id is None:
            raise MammothValidationError(ERR_IMPACT_TASK_ID)
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        params: dict[str, Any] = {"scope": scope}
        if task_id is not None:
            params["task_id"] = task_id
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/impact",
            params=params,
        )

    async def analysis(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """List pipeline steps that can be dropped or moved without changing the result.

        Read only. Each finding says whether the change provably preserves results.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``findings``: a list of ``{rule, seqs, detail, proposed_order, safe}``.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/analysis",
        )

    async def optimize(
        self,
        dataset_id: int,
        dataview_id: int,
        apply_rules: _list[str] | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Apply the safe pipeline findings of :meth:`analysis` (a write; reruns the pipeline).

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            apply_rules: Rules to apply (``drop_suspended``, ``drop_duplicate``,
                ``drop_noop_filter``, ``hoist_filter``); ``None`` applies every safe finding.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with ``applied``, ``skipped`` (``{rule, seqs, reason}``), ``before_steps``,
            ``after_steps`` and ``job_id`` (the rerun, when one was queued).

        Raises:
            MammothValidationError: If a rule is not one of the four known rules.
        """
        if apply_rules is not None:
            unknown = [rule for rule in apply_rules if rule not in _OPTIMIZE_RULES]
            if unknown:
                raise MammothValidationError(ERR_OPTIMIZE_RULE.format(unknown))
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/optimize",
            json={"apply_rules": None if apply_rules is None else _list(apply_rules)},
        )

    async def compare(
        self, pairs: _list[_list[int]], workspace_id: int | None = None
    ) -> dict[str, Any]:
        """Compare dataviews pairwise: row counts, column differences and checksums (read only).

        Args:
            pairs: 1 to 20 ``[view_a, view_b]`` pairs of dataview ids.
            workspace_id: ID of the workspace (uses client default if not provided).

        Returns:
            Dict with ``results``, one entry per pair in request order: ``view_a``,
            ``view_b``, ``status`` (``ok``, ``not_ready`` or ``not_comparable``),
            ``problem_views``, ``rows_a``, ``rows_b``, ``columns_only_in_a``,
            ``columns_only_in_b``, ``checksum_a``, ``checksum_b``, ``equal`` and
            ``mismatched_columns``.

        Raises:
            MammothValidationError: If *pairs* is empty, has over 20 entries, or an entry
                is not two positive ids.
        """
        if not pairs or len(pairs) > _COMPARE_MAX_PAIRS:
            raise MammothValidationError(ERR_COMPARE_PAIRS)
        for pair in pairs:
            if len(pair) != 2 or any(
                isinstance(view, bool) or not isinstance(view, int) or view <= 0 for view in pair
            ):
                raise MammothValidationError(ERR_COMPARE_PAIRS)
        ws = workspace_id or self._ws()
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/dataviews/compare",
            json={"pairs": [_list(pair) for pair in pairs]},
            operation_effect="read",
        )

    async def bulk_delete(
        self,
        dataset_id: int,
        dataview_ids: _list[int] | str,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete multiple dataviews.

        Args:
            dataset_id: ID of the dataset.
            dataview_ids: List of dataview IDs or comma-separated string.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with bulk deletion result.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        if isinstance(dataview_ids, _list):
            ids_str = ",".join(str(id) for id in dataview_ids)
        else:
            ids_str = str(dataview_ids)
        return await self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews",
            params={"ids": ids_str},
        )

    async def get_data(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
        timeout: int | None = None,
        poll_interval: float | None = None,
        sequence: int | None = None,
    ) -> dict[str, Any]:
        """Get dataview data (GET method).

        Data is scoped to a pipeline task *sequence*. When ``sequence`` is
        omitted it defaults to the latest task sequence, so rows include every
        pipeline-derived column. Pass ``sequence=0`` for the original dataset.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            timeout: Max job wait time in seconds (default: client.job_timeout).
            poll_interval: Seconds between job polls (default:
                client.job_poll_seconds).
            sequence: Pipeline step to read data at (default: latest).

        Returns:
            Dict with dataview data.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        if sequence is None:
            sequence = await self._client.pipeline.latest_task_sequence(dataview_id, dataset_id)
        response = await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/data",
            params={"sequence": sequence},
        )
        return await self._client._wait_if_job(
            response, timeout=timeout, poll_interval=poll_interval
        )

    async def query_data(
        self,
        dataset_id: int,
        dataview_id: int,
        sequence: int | None = None,
        offset: int = 1,
        limit: int = 400,
        columns: _list[str] | None = None,
        condition: dict[str, Any] | None = None,
        sort: str | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get dataview data with filtering options (POST method).

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            sequence: Pipeline step to fetch data at. Omit to let the API
                read the last task in the pipeline; pass ``0`` for the
                original dataset.
            offset: One-indexed starting row (default 1).
            limit: Number of rows to fetch (default 400).
            columns: List of column names to fetch (optional).
            condition: Filter condition dict (optional).
            sort: Sort specification string (optional).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with filtered dataview data.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        # As in `get`: the API reads the last task in the pipeline when asked
        # for no sequence, and is right about it while a draft is open.
        payload: dict[str, Any] = {"offset": offset, "limit": limit}
        if sequence is not None:
            payload["sequence"] = sequence
        if columns is not None:
            payload["columns"] = columns
        if condition is not None:
            payload["condition"] = condition
        if sort is not None:
            payload["sort"] = sort
        response = await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/data",
            json=payload,
        )
        return await self._client._wait_if_job(response)

    async def aggregate(
        self,
        dataset_id: int,
        dataview_id: int,
        aggregations: _list[dict[str, Any]] | None = None,
        group_by: _list[str | dict[str, Any]] | None = None,
        metric: dict[str, Any] | None = None,
        condition: dict[str, Any] | None = None,
        sequence: int | None = None,
        limit: int | None = None,
        sort: _list[_list[str]] | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
        timeout: int | None = None,
        poll_interval: int = 2,
    ) -> dict[str, Any]:
        """Run a read-only aggregation query against a dataview (POST .../data/query).

        This is a volatile query: it computes and returns an aggregated result
        (a PIVOT group-by, or a single METRIC value) without adding a task to
        the view's pipeline or otherwise changing it — unlike :meth:`View.pivot`,
        which adds a PIVOT task. Exactly one of *aggregations* or *metric* is
        required.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            aggregations: One or more ``{"column": ..., "function": ...,
                "as_name": ...}`` dicts for a PIVOT query (mutually exclusive
                with *metric*). ``function`` is one of SUM, COUNT, AVG, MIN,
                MAX; ``column`` is required unless ``function`` is COUNT;
                ``as_name`` defaults to ``f"{function}_{column}"``.
            group_by: Columns to group the PIVOT by (optional; a PIVOT with no
                ``group_by`` aggregates the whole view into one row). Each
                entry is either a plain column name, or a ``{"column": ...,
                "truncate": ...}`` dict bucketing a DATE column by truncation
                level (one of SECOND, MINUTE, HOUR, DAY, WEEK, MONTH, QUARTER,
                YEAR, DECADE, CENTURY, MILLENNIUM, AUTO), or a ``{"column":
                ..., "resolution": ...}`` dict bucketing a NUMERIC column by
                resolution level.
            metric: A single ``{"column": ..., "function": ..., "as_name": ...}``
                dict for a METRIC query (mutually exclusive with
                *aggregations*/*group_by*), same shape as an *aggregations* entry.
            condition: Filter condition dict applied before aggregating (optional).
            sequence: Pipeline step to read data at (default: latest).
            limit: Maximum number of result rows to return (optional). Without
                *sort* the rows kept are arbitrary, not the top ones.
            sort: Up to three ``[result_column, "ASC"|"DESC"]`` pairs, applied by
                the backend before *limit*. ``result_column`` is the internal name
                of a result column: ``agg_<n>`` for the n-th aggregation, ``group_<n>``
                for the n-th group_by entry, ``metric`` for a METRIC.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            timeout: Max job wait time in seconds (default: client.job_timeout).
            poll_interval: Seconds between job polls (default: 2).

        Returns:
            Dict with the aggregated result rows.

        Raises:
            MammothValidationError: If neither or both of *aggregations*/
                *group_by* and *metric* are given, if a *function* is not one
                of SUM, COUNT, AVG, MIN, MAX, STDDEV, DISTINCT_COUNT, or if *column* is missing
                for a non-COUNT aggregation.

        Example::

            await client.dataviews.aggregate(
                dataset_id=500, dataview_id=42,
                group_by=["Channel"],
                aggregations=[{"column": "Spend", "function": "SUM", "as_name": "Total Spend"}],
            )
        """
        if (aggregations is not None or group_by is not None) == (metric is not None):
            raise MammothValidationError(ERR_AGGREGATE_EXACTLY_ONE)
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        param: dict[str, Any] = (
            {"METRIC": _build_metric_param(metric)}
            if metric is not None
            else {"PIVOT": _build_pivot_param(aggregations or [], group_by)}
        )
        if condition is not None:
            param["CONDITION"] = condition
        if sequence is not None:
            param["SEQUENCE_NUMBER"] = sequence
        payload: dict[str, Any] = {"param": param}
        display_properties = _build_query_display_properties(limit, sort)
        if display_properties:
            payload["display_properties"] = display_properties
        response = await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/data/query",
            json=payload,
        )
        return await self._client._wait_if_job(
            response, timeout=timeout, poll_interval=poll_interval
        )

    async def explore(
        self,
        dataset_id: int,
        dataview_id: int,
        column: str,
        column_type: str | None = None,
        level: str | None = None,
        metric: dict[str, Any] | None = None,
        condition: dict[str, Any] | None = None,
        sequence: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
        cumulative: bool = False,
        workspace_id: int | None = None,
        project_id: int | None = None,
        timeout: int | None = None,
        poll_interval: int = 2,
    ) -> dict[str, Any]:
        """Explore one column: trend/distribution/top values (a PIVOT convenience).

        A read-only wrapper over :meth:`aggregate` that buckets *column* by its
        type the way the web app's Explore card does: a DATE column by
        ``level`` truncation (default "AUTO"), a NUMERIC column by ``level``
        resolution (default "AUTO"), and any other column (TEXT) by its own
        distinct values. Every bucket carries a ``count`` and a ``percentage``
        of the column's total (computed locally, against every bucket the
        query returns, never just a page truncated by *limit*). An optional
        *metric* adds a second aggregation over another column.

        Buckets are ordered the way the Explore card orders them: a DATE or
        NUMERIC bucket ascending (a trend or distribution reads left to
        right); a TEXT top-values list by ``count`` descending, defaulting to
        the top 20 when no *limit* is given. A DATE/NUMERIC result returns
        every bucket unless *limit* is given.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            column: Column to explore (internal name).
            column_type: The column's type ("DATE", "NUMERIC", or "TEXT"/None);
                selects the bucketing and ordering strategy.
            level: Truncation level (DATE) or resolution level (NUMERIC);
                ignored for other column types. Defaults to "AUTO".
            metric: An optional ``{"column": ..., "function": ..., "as_name":
                ...}`` dict (SUM, COUNT, AVG, MIN, MAX, STDDEV or DISTINCT_COUNT) computed per
                bucket in addition to the COUNT.
            condition: Filter condition dict applied before exploring (optional).
            sequence: Pipeline step to read data at (default: latest).
            limit: Maximum number of buckets to return (default: 20 for TEXT,
                unlimited for DATE/NUMERIC).
            offset: Buckets to skip first ("load more"; default 0).
            sort: count_desc, count_asc, value_asc or value_desc (default:
                count_desc for TEXT, value_asc for DATE/NUMERIC).
            cumulative: Add a ``cumulative`` running total per bucket (of the
                *metric* when given, else of the count), over every bucket in
                ascending bucket order, before any *sort*/*limit* is applied.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            timeout: Max job wait time in seconds (default: client.job_timeout).
            poll_interval: Seconds between job polls (default: 2).

        Returns:
            Dict with one result row per bucket.

        Raises:
            MammothValidationError: If *level* is not one of the backend's
                allowed date-truncation levels, or (from :meth:`aggregate`) if
                *metric*'s function is unsupported.

        Example::

            await client.dataviews.explore(
                dataset_id=500, dataview_id=42,
                column="column_3", column_type="DATE", level="MONTH",
            )
        """
        group_by: dict[str, Any] = {"column": column}
        normalized_type = str(column_type or "").upper()
        if normalized_type == "DATE":
            group_by["truncate"] = level or "AUTO"
        elif normalized_type == "NUMERIC":
            group_by["resolution"] = level or "AUTO"
        aggregations: list[dict[str, Any]] = [{"function": "COUNT", "as_name": "count"}]
        if metric is not None:
            aggregations.append(metric)
        response = await self.aggregate(
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            aggregations=aggregations,
            group_by=[group_by],
            condition=condition,
            sequence=sequence,
            workspace_id=workspace_id,
            project_id=project_id,
            timeout=timeout,
            poll_interval=poll_interval,
        )
        rows = response.get("data")
        if isinstance(rows, list):
            typed_rows = [row for row in rows if isinstance(row, dict)]
            _add_explore_percentages(typed_rows)
            if cumulative:
                _add_explore_cumulative(typed_rows)
            typed_rows = _explore_sort_and_limit(typed_rows, normalized_type, sort, (offset, limit))
            response = {**response, "data": typed_rows}
        return response

    async def get_exportable_config(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get the pipeline/export configuration for a dataview."""
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        response = await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/exportable-config",
        )
        return await self._client._wait_if_job(response)

    async def apply_exportable_config(
        self,
        dataset_id: int,
        dataview_id: int,
        *,
        items: _list[dict[str, Any]] | None = None,
        config: dict[str, Any] | None = None,
        insert_after_sequence: int | None = None,
        is_paste_mode: bool = False,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Apply exactly one of items or full config."""
        if (items is None) == (config is None):
            raise MammothValidationError("Exactly one of items or config is required.")
        payload: dict[str, Any] = {"items": items} if items is not None else {"config": config}
        if insert_after_sequence is not None:
            payload["insert_after_sequence"] = insert_after_sequence
        if is_paste_mode:
            payload["is_paste_mode"] = True
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        response = await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/exportable-config",
            json=payload,
        )
        return await self._client._wait_if_job(response)

    async def active_users(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get list of active users on this dataview.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with list of active users.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/activities",
        )

    async def mark_active(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Mark current user as active on this dataview.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with updated active users.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/activities",
        )

    async def conditional_format_list(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> _list[dict[str, Any]]:
        """List conditional formatting rules.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            List of conditional format rule dicts. The release route returns
            the rules as a mapping keyed by rule id; each returned dict
            carries that key as ``rule_id`` (the value
            :meth:`conditional_format_delete` needs).
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        response = await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format",
        )
        if isinstance(response, _list):
            return response
        if not isinstance(response, dict):
            return []
        if isinstance(response.get("rules"), _list):
            return response["rules"]
        return [
            {"rule_id": rule_id, **rule}
            for rule_id, rule in response.items()
            if isinstance(rule, dict) and "cf_type" in rule
        ]

    async def conditional_format_create(
        self,
        dataset_id: int,
        dataview_id: int,
        rule: dict[str, Any],
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a conditional formatting rule.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            rule: Conditional format rule specification.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with created rule.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format",
            json=rule,
        )

    async def conditional_format_update(
        self,
        dataset_id: int,
        dataview_id: int,
        rule: dict[str, Any],
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a conditional formatting rule.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            rule: Updated conditional format rule.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with updated rule.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format",
            json=rule,
        )

    async def conditional_format_delete(
        self,
        dataset_id: int,
        dataview_id: int,
        rule_id: str | int | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete one conditional formatting rule.

        The route requires the ``rule_id`` query parameter (from
        :meth:`conditional_format_list`); there is no delete-all form.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            rule_id: ID of the rule to delete.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        if rule_id is None or rule_id == "":
            raise MammothValidationError(
                "conditional_format_delete requires `rule_id`; list rules first."
            )
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format",
            params={"rule_id": rule_id},
        )

    async def draft_mode(
        self,
        dataset_id: int,
        dataview_id: int,
        command: str,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Manage draft mode for a dataview pipeline.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            command: Draft mode command: "enter", "commit", or "discard".
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with draft mode state.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/draft-mode",
            json={"draft_operation": command},
        )

    async def parameter_context(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get the parameter context available to a dataview's pipeline.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with the available parameter context.

        Raises:
            MammothValidationError: If *dataview_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/parameter-context",
        )

    async def preview(
        self,
        dataset_id: int,
        dataview_id: int,
        rows: int | None = None,
        cols: int | None = None,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get a lightweight preview of a dataview's data.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview (must be > 0).
            rows: Maximum number of rows to include in the preview (optional).
            cols: Maximum number of columns to include in the preview (optional).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with the preview data.

        Raises:
            MammothValidationError: If *dataview_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        params: dict[str, Any] = {}
        if rows is not None:
            params["rows"] = rows
        if cols is not None:
            params["cols"] = cols
        return await self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/preview",
            params=params or None,
        )

    async def restore(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Restore a trashed dataview.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with restore result.

        Raises:
            MammothValidationError: If *dataview_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/restore",
        )

    async def trash(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Move a dataview to trash.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview (must be > 0).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Dict with trash result.

        Raises:
            MammothValidationError: If *dataview_id* ≤ 0.
        """
        if dataview_id <= 0:
            raise MammothValidationError(ERR_DATAVIEW_ID_POSITIVE.format(dataview_id))
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return await self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/trash",
        )
