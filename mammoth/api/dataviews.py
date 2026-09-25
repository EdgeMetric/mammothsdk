"""
Dataviews API client for managing dataviews in Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

ERR_DATAVIEW_ID_POSITIVE = "`dataview_id` must be a positive integer, got {0}."

#: Aggregate functions supported by :meth:`DataviewsAPI.aggregate`. Deliberately
#: a small, exact-match subset of the backend's ``PivotAggregationFunction``
#: wire vocabulary (which also has PERCENTAGE, DISTINCT_COUNT, CONCAT) — the
#: five an agent needs for "total/count/average/min/max of a column".
_AGGREGATE_FUNCTIONS = frozenset({"SUM", "COUNT", "AVG", "MIN", "MAX"})
ERR_AGGREGATE_FUNCTION_UNSUPPORTED = (
    "`function` must be one of SUM, COUNT, AVG, MIN, MAX for a volatile aggregation query, "
    "got {0!r}."
)
ERR_AGGREGATE_COLUMN_REQUIRED = "`column` is required for {0} aggregation."
ERR_AGGREGATE_EXACTLY_ONE = (
    "Pass exactly one of `aggregations` (a PIVOT; `group_by` is optional) or `metric`."
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


def _build_pivot_param(
    aggregations: list[dict[str, Any]], group_by: list[str] | None
) -> dict[str, Any]:
    """Build a volatile-query PIVOT param (distinct from the pipeline PIVOT task).

    Raises:
        MammothValidationError: If *aggregations* is empty, or (from
            :func:`_build_aggregate_select_item`) an aggregation is invalid.
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
            {"COLUMN": column, "INTERNAL_NAME": f"group_{index}"}
            for index, column in enumerate(group_by)
        ]
    return pivot


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

    def list(
        self,
        dataset_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
        limit: int = 100,
        sort: str = "(created_at:desc)",
    ) -> dict[str, Any]:
        """Get list of dataviews in a dataset.

        Args:
            dataset_id: ID of the dataset.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            limit: Maximum number of results (default 100).
            sort: Sort order (default "(created_at:desc)").

        Returns:
            Dict containing dataviews list.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        params = {"limit": limit, "sort": sort}
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews",
            params=params,
        )

    def get(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
        sequence: int | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """Get dataview information.

        Metadata is scoped to a pipeline task *sequence*. When ``sequence`` is
        omitted it defaults to the latest task sequence, so the returned
        ``metadata`` reflects every pipeline-derived column (math, add_column,
        etc.). Pass ``sequence=0`` for the original dataset columns.

        Args:
            dataset_id: ID of the dataset.
            dataview_id: ID of the dataview.
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            sequence: Pipeline step to read metadata at (default: latest).
            fields: Field set to return (e.g. ``"__full"``); server default if omitted.

        Returns:
            Dict with complete dataview information.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        if sequence is None:
            sequence = self._client.pipeline.latest_task_sequence(dataview_id, dataset_id)
        params: dict[str, Any] = {"sequence": sequence}
        if fields is not None:
            params["fields"] = fields
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}",
            params=params,
        )

    def create(
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
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews",
            json=payload,
        )
        return self._client._wait_if_job(response)

    def update(
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

            client.dataviews.update(
                dataset_id=123, dataview_id=456,
                patch_data=[{"op": "replace", "path": "/name", "value": "Renamed"}],
            )
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}",
            json={"patch": patch_data},
        )

    def delete(
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
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}",
        )

    def bulk_delete(
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
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews",
            params={"ids": ids_str},
        )

    def get_data(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
        timeout: int | None = None,
        poll_interval: int = 2,
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
            poll_interval: Seconds between job polls (default: 2).
            sequence: Pipeline step to read data at (default: latest).

        Returns:
            Dict with dataview data.
        """
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        if sequence is None:
            sequence = self._client.pipeline.latest_task_sequence(dataview_id, dataset_id)
        response = self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/data",
            params={"sequence": sequence},
        )
        return self._client._wait_if_job(response, timeout=timeout, poll_interval=poll_interval)

    def query_data(
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
            sequence: Pipeline step to fetch data at (default: latest task
                sequence, so rows include every pipeline-derived column; pass
                ``0`` for the original dataset).
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
        if sequence is None:
            sequence = self._client.pipeline.latest_task_sequence(dataview_id, dataset_id)
        payload: dict[str, Any] = {"sequence": sequence, "offset": offset, "limit": limit}
        if columns is not None:
            payload["columns"] = columns
        if condition is not None:
            payload["condition"] = condition
        if sort is not None:
            payload["sort"] = sort
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/data",
            json=payload,
        )
        return self._client._wait_if_job(response)

    def aggregate(
        self,
        dataset_id: int,
        dataview_id: int,
        aggregations: _list[dict[str, Any]] | None = None,
        group_by: _list[str] | None = None,
        metric: dict[str, Any] | None = None,
        condition: dict[str, Any] | None = None,
        sequence: int | None = None,
        limit: int | None = None,
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
                ``group_by`` aggregates the whole view into one row).
            metric: A single ``{"column": ..., "function": ..., "as_name": ...}``
                dict for a METRIC query (mutually exclusive with
                *aggregations*/*group_by*), same shape as an *aggregations* entry.
            condition: Filter condition dict applied before aggregating (optional).
            sequence: Pipeline step to read data at (default: latest).
            limit: Maximum number of result rows to return (optional).
            workspace_id: ID of the workspace (uses client default if not provided).
            project_id: ID of the project (uses client default if not provided).
            timeout: Max job wait time in seconds (default: client.job_timeout).
            poll_interval: Seconds between job polls (default: 2).

        Returns:
            Dict with the aggregated result rows.

        Raises:
            MammothValidationError: If neither or both of *aggregations*/
                *group_by* and *metric* are given, if a *function* is not one
                of SUM, COUNT, AVG, MIN, MAX, or if *column* is missing for a
                non-COUNT aggregation.

        Example::

            client.dataviews.aggregate(
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
        if limit is not None:
            payload["display_properties"] = {"LIMIT": limit}
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/data/query",
            json=payload,
        )
        return self._client._wait_if_job(response, timeout=timeout, poll_interval=poll_interval)

    def get_exportable_config(
        self,
        dataset_id: int,
        dataview_id: int,
        workspace_id: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get the pipeline/export configuration for a dataview."""
        ws = workspace_id or self._ws()
        proj = project_id or self._proj()
        response = self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/exportable-config",
        )
        return self._client._wait_if_job(response)

    def apply_exportable_config(
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
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/exportable-config",
            json=payload,
        )
        return self._client._wait_if_job(response)

    def active_users(
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
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/activities",
        )

    def mark_active(
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
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/activities",
        )

    def conditional_format_list(
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
        response = self._client._request_json(
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

    def conditional_format_create(
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
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format",
            json=rule,
        )

    def conditional_format_update(
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
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format",
            json=rule,
        )

    def conditional_format_delete(
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
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/conditional-format",
            params={"rule_id": rule_id},
        )

    def draft_mode(
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
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}/draft-mode",
            json={"draft_operation": command},
        )

    def parameter_context(
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
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/parameter-context",
        )

    def preview(
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
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/preview",
            params=params or None,
        )

    def restore(
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
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/restore",
        )

    def trash(
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
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/dataviews/{dataview_id}"
            "/trash",
        )
