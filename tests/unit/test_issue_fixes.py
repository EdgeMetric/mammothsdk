"""Unit tests for SDK issue fixes.

Tests:
- Fix 1: connectors.active_connectors handles list and dict responses
- Fix 2: enter_draft_mode re-entry guard
- Fix 3: views.list() with dataset_id parameter
- Fix 4: dict coercion for copy_columns, convert_type, bulk_replace, split_column, pivot
- Fix 6a: datasets.browse removed
- Fix 6b: datasets.update uses plural endpoint; datasets.rename convenience
- Fix 8: addons.list
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mammoth.client import MammothClient
from mammoth.models.pipeline import (
    AggregateFunction,
    AggregationSpec,
    BulkReplaceMapping,
    ColumnType,
    ConversionSpec,
    CopySpec,
    SplitColumnSpec,
)
from mammoth.view import View

# ── Fixtures ──────────────────────────────────────────────

SAMPLE_COLUMNS = [
    {"display_name": "Sales", "internal_name": "column_aaa", "type": "NUMERIC"},
    {"display_name": "Region", "internal_name": "column_bbb", "type": "TEXT"},
    {"display_name": "Product", "internal_name": "column_ccc", "type": "TEXT"},
]

SAMPLE_VIEW_DATA = {
    "id": 100,
    "name": "Test",
    "properties": {"columns": SAMPLE_COLUMNS},
}


@pytest.fixture
def mock_client() -> MammothClient:
    with patch("mammoth.client.requests.Session"):
        client = MammothClient(api_key="k", api_secret="s", workspace_id=1)
    client.project_id = 10
    client._request = MagicMock(return_value={})
    client._request_json = MagicMock(return_value={})
    client.pipeline = MagicMock()
    client.pipeline.add_task = MagicMock(return_value={"id": 1})
    client.pipeline.wait_for_pipeline = MagicMock(return_value={})
    client.dataviews = MagicMock()
    client.dataviews.get = MagicMock(return_value=SAMPLE_VIEW_DATA)
    client.dataviews.list = MagicMock(return_value={"dataviews": [SAMPLE_VIEW_DATA]})
    return client


@pytest.fixture
def mock_view(mock_client: MammothClient) -> View:
    view = View(mock_client, SAMPLE_VIEW_DATA, 500)
    captured: list[dict[str, Any]] = []

    def fake_add_task(params: dict[str, Any]) -> dict[str, Any]:
        captured.append(params)
        return {"id": len(captured)}

    view._add_task = fake_add_task  # type: ignore[assignment]
    view._captured_payloads = captured  # type: ignore[attr-defined]
    return view


# ── Fix 1: connectors handles list response ─────────────


class TestConnectorsListResponse:
    def test_active_connectors_handles_list(self, mock_client: MammothClient):
        mock_client._request = MagicMock(return_value=[{"key": "postgres"}])
        result = mock_client.connectors.active_connectors()
        assert result == [{"key": "postgres"}]

    def test_active_connectors_handles_dict(self, mock_client: MammothClient):
        mock_client._request = MagicMock(return_value={"connectors": [{"key": "mysql"}]})
        result = mock_client.connectors.active_connectors()
        assert result == [{"key": "mysql"}]

    def test_list_handles_list(self, mock_client: MammothClient):
        mock_client._request = MagicMock(return_value=[{"key": "s3"}])
        result = mock_client.connectors.list()
        assert result == [{"key": "s3"}]

    def test_list_handles_dict(self, mock_client: MammothClient):
        mock_client._request = MagicMock(return_value={"connectors": [{"key": "s3"}]})
        result = mock_client.connectors.list()
        assert result == [{"key": "s3"}]


# ── Fix 2: draft mode re-entry guard ────────────────────


class TestDraftModeGuard:
    def test_guard_prevents_double_entry(self, mock_view: View):
        mock_view._draft_mode = True
        result = mock_view.enter_draft_mode()
        assert result == {"status": "already_in_draft_mode"}
        # No API call should have been made
        mock_view._client.pipeline.draft_mode.assert_not_called()

    def test_first_entry_calls_api(self, mock_view: View):
        mock_view._draft_mode = False
        mock_view._client.pipeline.draft_mode = MagicMock(return_value={"state": "draft"})
        result = mock_view.enter_draft_mode()
        assert result == {"state": "draft"}
        assert mock_view._draft_mode is True
        mock_view._client.pipeline.draft_mode.assert_called_once()


# ── Fix 3: views.list() with dataset_id ─────────────────


class TestViewsListDatasetId:
    def test_list_with_dataset_id(self, mock_client: MammothClient):
        views = mock_client.views.list(dataset_id=500)
        assert len(views) == 1
        assert views[0].id == 100
        mock_client.dataviews.list.assert_called_once_with(dataset_id=500)

    def test_list_requires_dataset_id(self, mock_client: MammothClient):
        with pytest.raises(TypeError):
            mock_client.views.list()  # type: ignore[call-arg]


# ── Fix 4: dict coercion ────────────────────────────────


class TestSpecInputs:
    """Transform methods take strictly-typed spec objects (no dict/str coercion)."""

    def test_copy_columns_accepts_specs(self, mock_view: View):
        mock_view.copy_columns([CopySpec(source="Sales", as_name="Sales Copy")])
        p = mock_view._captured_payloads[-1]  # type: ignore[attr-defined]
        assert "COPY" in p
        assert p["COPY"][0]["SOURCE"] == "column_aaa"

    def test_convert_type_accepts_specs(self, mock_view: View):
        mock_view.convert_type([ConversionSpec(column="Sales", to=ColumnType.NUMERIC)])
        p = mock_view._captured_payloads[-1]  # type: ignore[attr-defined]
        assert "CONVERT" in p
        assert p["CONVERT"][0]["SOURCE"] == "column_aaa"

    def test_bulk_replace_accepts_specs(self, mock_view: View):
        mock_view.bulk_replace(
            columns=["Region"],
            mapping=[BulkReplaceMapping(search=["West", "W"], replace="Western")],
        )
        p = mock_view._captured_payloads[-1]  # type: ignore[attr-defined]
        assert "REPLACE" in p
        assert p["REPLACE"]["MAPPING"][0]["SEARCH_VALUE"] == ["West", "W"]

    def test_split_column_accepts_specs(self, mock_view: View):
        mock_view.split_column(
            "Region",
            "-",
            [SplitColumnSpec("Part1"), SplitColumnSpec("Part2")],
        )
        p = mock_view._captured_payloads[-1]  # type: ignore[attr-defined]
        assert "SPLIT" in p
        assert len(p["SPLIT"]["AS"]) == 2

    def test_pivot_accepts_specs(self, mock_view: View):
        mock_view.pivot(
            group_by=["Region"],
            aggregations=[
                AggregationSpec(
                    column="Sales",
                    function=AggregateFunction.SUM,
                    as_name="Total",
                )
            ],
        )
        p = mock_view._captured_payloads[-1]  # type: ignore[attr-defined]
        assert "PIVOT" in p
        assert p["PIVOT"]["SELECT"][0]["FUNCTION"] == "SUM"


# ── Fix 6a: datasets.browse removed ─────────────────────


class TestDatasetsBrowseRemoved:
    def test_no_browse_method(self, mock_client: MammothClient):
        assert not hasattr(mock_client.datasets, "browse")


# ── Fix 6b: datasets.update and rename ──────────────────


class TestDatasetsUpdate:
    def test_update_uses_plural_endpoint(self, mock_client: MammothClient):
        mock_client.datasets.update(
            patch_data=[{"op": "rename_dataset", "path": "/123", "value": {"name": "X"}}]
        )
        mock_client._request_json.assert_called_once()
        args = mock_client._request_json.call_args
        assert args[0][0] == "PATCH"
        assert args[0][1].endswith("/datasets")

    def test_rename_convenience(self, mock_client: MammothClient):
        mock_client.datasets.rename(dataset_id=123, name="New Name")
        mock_client._request_json.assert_called_once()
        args = mock_client._request_json.call_args
        payload = args[1].get("json") or args[0][2] if len(args[0]) > 2 else None
        if payload is None:
            payload = args[1]["json"]
        assert payload["patch"][0]["op"] == "rename_dataset"
        assert payload["patch"][0]["path"] == "/123"


# ── Fix 8: addons.list ──────────────────────────────────


class TestAddonsList:
    def test_list_calls_get(self, mock_client: MammothClient):
        mock_client.addons.list()
        mock_client._request_json.assert_called_once()
        args = mock_client._request_json.call_args
        assert args[0][0] == "GET"
        assert "/addons" in args[0][1]
