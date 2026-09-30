"""Unit tests for the DataAppsAPI client."""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.data_apps import DataAppsAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[DataAppsAPI, MagicMock]:
    mock_client = MagicMock()
    api = DataAppsAPI(mock_client)
    return api, mock_client


class TestDataAppsAPIList:
    async def test_list_no_filter(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"data_apps": []})
        result = await api.list()
        mock_client._request_json.assert_called_once_with("GET", "/data-apps", params=None)
        assert result == {"data_apps": []}

    async def test_list_with_workspace_id(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"data_apps": []})
        await api.list(workspace_id=2)
        mock_client._request_json.assert_called_once_with(
            "GET", "/data-apps", params={"workspace_id": 2}
        )


class TestDataAppsAPIGet:
    async def test_get(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 5})
        result = await api.get(5)
        mock_client._request_json.assert_called_once_with("GET", "/data-apps/5")
        assert result == {"id": 5}

    async def test_get_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="data_app_id"):
            await api.get(0)


class TestDataAppsAPICreate:
    async def test_create(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        result = await api.create(body={"name": "My App"})
        mock_client._request_json.assert_called_once_with(
            "POST", "/data-apps", json={"name": "My App"}
        )
        assert result == {"id": 1}


class TestDataAppsAPIUpdate:
    async def test_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.update(5, body={"name": "Renamed"})
        mock_client._request_json.assert_called_once_with(
            "POST", "/data-apps/5/settings", json={"name": "Renamed"}
        )


class TestDataAppsAPIDelete:
    async def test_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.delete(5)
        mock_client._request_json.assert_called_once_with("DELETE", "/data-apps/5")

    async def test_delete_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.delete(-1)


class TestDataAppsAPIActiveJob:
    async def test_active_job(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"job_id": 9})
        result = await api.active_job(5)
        mock_client._request_json.assert_called_once_with("GET", "/data-apps/5/active-job")
        assert result == {"job_id": 9}


class TestDataAppsAPIJob:
    async def test_job(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 9, "status": "done"})
        result = await api.job(5, 9)
        mock_client._request_json.assert_called_once_with("GET", "/data-apps/5/jobs/9")
        assert result == {"id": 9, "status": "done"}

    async def test_job_invalid_job_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="job_id"):
            await api.job(5, 0)


class TestDataAppsAPIPipelineChanges:
    async def test_pipeline_changes(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"changes": []})
        await api.pipeline_changes(5)
        mock_client._request_json.assert_called_once_with("GET", "/data-apps/5/pipeline-changes")


class TestDataAppsAPIShare:
    async def test_share(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.share(5, body={"email": "user@example.com"})
        mock_client._request_json.assert_called_once_with(
            "POST", "/data-apps/5/share", json={"email": "user@example.com"}
        )


class TestDataAppsAPIUpload:
    async def test_upload_file_like(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        file_obj = io.BytesIO(b"col1,col2\n1,2\n")
        file_obj.name = "data.csv"
        await api.upload(5, file_obj)
        mock_client._request_json.assert_called_once()
        args, kwargs = mock_client._request_json.call_args
        assert args == ("POST", "/data-apps/5/files")
        assert kwargs["params"] is None
        assert kwargs["files"][0][0] == "files"
        assert kwargs["files"][0][1][0] == "data.csv"

    async def test_upload_with_append(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        file_obj = io.BytesIO(b"data")
        await api.upload(5, file_obj, append_to_ds_id=42)
        kwargs = mock_client._request_json.call_args[1]
        assert kwargs["params"] == {"append_to_ds_id": 42}

    async def test_upload_missing_path_raises(self):
        api, _ = _make_api()
        with pytest.raises(ValueError, match="File not found"):
            await api.upload(5, "/nonexistent/path/to/file.csv")


class TestDataAppsAPIUsers:
    async def test_user_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"users": []})
        await api.user_list(5)
        mock_client._request_json.assert_called_once_with("GET", "/data-apps/5/users")

    async def test_user_remove(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.user_remove(5, email="user@example.com")
        mock_client._request_json.assert_called_once_with(
            "DELETE",
            "/data-apps/5/users",
            params={"email": "user@example.com"},
        )
