"""Unit tests for the DataAppsAPI client."""

from __future__ import annotations

import io
from unittest.mock import MagicMock

import pytest

from mammoth.api.data_apps import DataAppsAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[DataAppsAPI, MagicMock]:
    mock_client = MagicMock()
    api = DataAppsAPI(mock_client)
    return api, mock_client


class TestDataAppsAPIList:
    def test_list_no_filter(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"data_apps": []}
        result = api.list()
        mock_client._request_json.assert_called_once_with("GET", "/data-apps", params=None)
        assert result == {"data_apps": []}

    def test_list_with_workspace_id(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"data_apps": []}
        api.list(workspace_id=2)
        mock_client._request_json.assert_called_once_with(
            "GET", "/data-apps", params={"workspace_id": 2}
        )


class TestDataAppsAPIGet:
    def test_get(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 5}
        result = api.get(5)
        mock_client._request_json.assert_called_once_with("GET", "/data-apps/5")
        assert result == {"id": 5}

    def test_get_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="data_app_id"):
            api.get(0)


class TestDataAppsAPICreate:
    def test_create(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 1}
        result = api.create(body={"name": "My App"})
        mock_client._request_json.assert_called_once_with(
            "POST", "/data-apps", json={"name": "My App"}
        )
        assert result == {"id": 1}


class TestDataAppsAPIUpdate:
    def test_update(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.update(5, body={"name": "Renamed"})
        mock_client._request_json.assert_called_once_with(
            "POST", "/data-apps/5/settings", json={"name": "Renamed"}
        )


class TestDataAppsAPIDelete:
    def test_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.delete(5)
        mock_client._request_json.assert_called_once_with("DELETE", "/data-apps/5")

    def test_delete_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            api.delete(-1)


class TestDataAppsAPIActiveJob:
    def test_active_job(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"job_id": 9}
        result = api.active_job(5)
        mock_client._request_json.assert_called_once_with("GET", "/data-apps/5/active-job")
        assert result == {"job_id": 9}


class TestDataAppsAPIJob:
    def test_job(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 9, "status": "done"}
        result = api.job(5, 9)
        mock_client._request_json.assert_called_once_with("GET", "/data-apps/5/jobs/9")
        assert result == {"id": 9, "status": "done"}

    def test_job_invalid_job_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="job_id"):
            api.job(5, 0)


class TestDataAppsAPIPipelineChanges:
    def test_pipeline_changes(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"changes": []}
        api.pipeline_changes(5)
        mock_client._request_json.assert_called_once_with("GET", "/data-apps/5/pipeline-changes")


class TestDataAppsAPIShare:
    def test_share(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.share(5, body={"email": "user@example.com"})
        mock_client._request_json.assert_called_once_with(
            "POST", "/data-apps/5/share", json={"email": "user@example.com"}
        )


class TestDataAppsAPIUpload:
    def test_upload_file_like(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 1}
        file_obj = io.BytesIO(b"col1,col2\n1,2\n")
        file_obj.name = "data.csv"
        api.upload(5, file_obj)
        mock_client._request_json.assert_called_once()
        args, kwargs = mock_client._request_json.call_args
        assert args == ("POST", "/data-apps/5/files")
        assert kwargs["params"] is None
        assert kwargs["files"][0][0] == "files"
        assert kwargs["files"][0][1][0] == "data.csv"

    def test_upload_with_append(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 1}
        file_obj = io.BytesIO(b"data")
        api.upload(5, file_obj, append_to_ds_id=42)
        kwargs = mock_client._request_json.call_args[1]
        assert kwargs["params"] == {"append_to_ds_id": 42}

    def test_upload_missing_path_raises(self):
        api, _ = _make_api()
        with pytest.raises(ValueError, match="File not found"):
            api.upload(5, "/nonexistent/path/to/file.csv")


class TestDataAppsAPIUsers:
    def test_user_list(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"users": []}
        api.user_list(5)
        mock_client._request_json.assert_called_once_with("GET", "/data-apps/5/users")

    def test_user_remove(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.user_remove(5, email="user@example.com")
        mock_client._request_json.assert_called_once_with(
            "DELETE",
            "/data-apps/5/users",
            params={"email": "user@example.com"},
        )
