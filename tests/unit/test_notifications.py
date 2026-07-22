"""Unit tests for the Notifications API client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mammoth.api.notifications import NotificationsAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[NotificationsAPI, MagicMock]:
    """Create a NotificationsAPI with a mocked client."""
    mock_client = MagicMock()
    api = NotificationsAPI(mock_client)
    return api, mock_client


class TestNotificationsAPIList:
    def test_list_no_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"notifications": []}
        result = api.list()
        mock_client._request_json.assert_called_once_with("GET", "/notifications", params=None)
        assert result == {"notifications": []}

    def test_list_with_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"notifications": []}
        api.list(
            fields="__standard",
            workspace_id=2,
            project_id=100,
            last_updated_at__gte="2026-01-01",
            status="active",
            is_read=False,
            notification_scope="workspace",
            limit=10,
            offset=5,
            sort="(id:desc)",
        )
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/notifications",
            params={
                "fields": "__standard",
                "workspace_id": 2,
                "project_id": 100,
                "last_updated_at__gte": "2026-01-01",
                "status": "active",
                "is_read": False,
                "notification_scope": "workspace",
                "limit": 10,
                "offset": 5,
                "sort": "(id:desc)",
            },
        )


class TestNotificationsAPIDelete:
    def test_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.delete(5)
        mock_client._request_json.assert_called_once_with("DELETE", "/notifications/5")

    def test_delete_non_positive_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="notification_id"):
            api.delete(0)


class TestNotificationsAPIDeleteBatch:
    def test_delete_batch_no_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.delete_batch()
        mock_client._request_json.assert_called_once_with("DELETE", "/notifications", params=None)

    def test_delete_batch_with_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.delete_batch(
            workspace_id=2,
            ids=[1, 2, 3],
            last_updated_at__lt="2026-01-01",
            is_read=True,
        )
        mock_client._request_json.assert_called_once_with(
            "DELETE",
            "/notifications",
            params={
                "workspace_id": 2,
                "ids": "1,2,3",
                "last_updated_at__lt": "2026-01-01",
                "is_read": True,
            },
        )


class TestNotificationsAPIUpdate:
    def test_update(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 5, "is_read": True}
        patch = [{"op": "replace", "path": "isRead", "value": True}]
        result = api.update(5, patch=patch)
        mock_client._request_json.assert_called_once_with(
            "PATCH", "/notifications/5", json={"patch": patch}
        )
        assert result["is_read"] is True

    def test_update_non_positive_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="notification_id"):
            api.update(0, patch=[{"op": "replace", "path": "isRead", "value": True}])

    def test_update_empty_patch(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="patch"):
            api.update(5, patch=[])

    def test_update_invalid_path(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="path"):
            api.update(5, patch=[{"op": "replace", "path": "bogus", "value": True}])

    def test_update_invalid_op(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="op"):
            api.update(5, patch=[{"op": "add", "path": "isRead", "value": True}])

    def test_update_missing_keys(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="patch"):
            api.update(5, patch=[{"op": "replace", "path": "isRead"}])


class TestNotificationsAPIUpdateBatch:
    def test_update_batch(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        patch = [{"op": "replace", "path": "isReadMultiple", "value": True}]
        api.update_batch(patch=patch, workspace_id=2)
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/notifications",
            params={"workspace_id": 2},
            json={"patch": patch},
        )

    def test_update_batch_no_workspace(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        patch = [{"op": "replace", "path": "isReadMultiple", "value": True}]
        api.update_batch(patch=patch)
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/notifications",
            params=None,
            json={"patch": patch},
        )

    def test_update_batch_empty_patch(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="patch"):
            api.update_batch(patch=[])
