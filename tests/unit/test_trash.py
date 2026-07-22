"""Unit tests for the Trash API client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mammoth.api.trash import TrashAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[TrashAPI, MagicMock]:
    """Create a TrashAPI with a mocked client."""
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    mock_client.project_id = 100
    api = TrashAPI(mock_client)
    return api, mock_client


class TestTrashAPIList:
    def test_list_no_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"items": [], "limit": 50, "offset": 0, "total": 0}
        result = api.list()
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/projects/100/trash",
            params=None,
        )
        assert result["total"] == 0

    def test_list_with_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.list(
            type="dataview",
            sort="name",
            order="asc",
            limit=10,
            offset=5,
            q="report",
            trashed_by=3,
            trashed_after="2026-01-01",
            trashed_before="2026-06-01",
            expiring_within_days=7,
            folder_path="/reports",
            folder_root="root",
        )
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/projects/100/trash",
            params={
                "type": "dataview",
                "sort": "name",
                "order": "asc",
                "limit": 10,
                "offset": 5,
                "q": "report",
                "trashed_by": 3,
                "trashed_after": "2026-01-01",
                "trashed_before": "2026-06-01",
                "expiring_within_days": 7,
                "folder_path": "/reports",
                "folder_root": "root",
            },
        )

    def test_list_explicit_project_id(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.list(project_id=7)
        path = mock_client._request_json.call_args[0][1]
        assert path == "/workspaces/2/projects/7/trash"


class TestTrashAPIAdd:
    def test_add(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"job": {"id": 1}}
        items = [{"id": 42, "type": "dataview"}]
        result = api.add(items=items)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/projects/100/trash",
            json={"items": items},
        )
        assert result == {"job": {"id": 1}}

    def test_add_empty_items(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="items"):
            api.add(items=[])

    def test_add_missing_keys(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="items"):
            api.add(items=[{"id": 1}])

    def test_add_non_positive_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="id"):
            api.add(items=[{"id": 0, "type": "dataview"}])

    def test_add_invalid_type(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="type"):
            api.add(items=[{"id": 1, "type": "bogus"}])


class TestTrashAPIRestore:
    def test_restore(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"job": {"id": 2}}
        items = [{"id": 42, "type": "dataset"}]
        result = api.restore(items=items)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/projects/100/trash/restore",
            json={"items": items},
        )
        assert result == {"job": {"id": 2}}

    def test_restore_empty_items(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="items"):
            api.restore(items=[])


class TestTrashAPIProjectRequired:
    def test_list_requires_project(self):
        mock_client = MagicMock()
        mock_client.workspace_id = 2
        mock_client.project_id = None
        api = TrashAPI(mock_client)
        with pytest.raises(ValueError, match="project_id must be set"):
            api.list()
