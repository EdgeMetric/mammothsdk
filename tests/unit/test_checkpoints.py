"""Unit tests for the CheckpointsAPI client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.checkpoints import CheckpointsAPI
from mammoth.exceptions import MammothValidationError

_BASE = "/workspaces/2/projects/100/datasets/1/dataviews/9/pipeline/checkpoints"


def _make_api() -> tuple[CheckpointsAPI, MagicMock]:
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    mock_client.project_id = 100
    api = CheckpointsAPI(mock_client)
    return api, mock_client


class TestCheckpointsAPIList:
    async def test_list_no_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"checkpoints": []})
        await api.list(dataset_id=1, dataview_id=9)
        mock_client._request_json.assert_called_once_with("GET", _BASE, params=None)

    async def test_list_with_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"checkpoints": []})
        await api.list(
            dataset_id=1,
            dataview_id=9,
            fields="__standard",
            sort="(id:asc)",
            sequence="1",
            status="ready",
        )
        mock_client._request_json.assert_called_once_with(
            "GET",
            _BASE,
            params={
                "fields": "__standard",
                "sort": "(id:asc)",
                "sequence": "1",
                "status": "ready",
            },
        )

    async def test_list_invalid_dataset_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="dataset_id"):
            await api.list(dataset_id=0, dataview_id=9)


class TestCheckpointsAPIGet:
    async def test_get(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 3})
        result = await api.get(dataset_id=1, dataview_id=9, checkpoint_id=3)
        mock_client._request_json.assert_called_once_with("GET", f"{_BASE}/3", params=None)
        assert result == {"id": 3}

    async def test_get_invalid_checkpoint_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="checkpoint_id"):
            await api.get(dataset_id=1, dataview_id=9, checkpoint_id=0)


class TestCheckpointsAPICreate:
    async def test_create(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 4})
        await api.create(dataset_id=1, dataview_id=9, body={"name": "cp1"})
        mock_client._request_json.assert_called_once_with("POST", _BASE, json={"name": "cp1"})

    async def test_create_invalid_dataview_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="dataview_id"):
            await api.create(dataset_id=1, dataview_id=-1, body={})


class TestCheckpointsAPIUpdate:
    async def test_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.update(dataset_id=1, dataview_id=9, checkpoint_id=3, body={"name": "renamed"})
        mock_client._request_json.assert_called_once_with(
            "PATCH", f"{_BASE}/3", json={"name": "renamed"}
        )


class TestCheckpointsAPIDelete:
    async def test_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.delete(dataset_id=1, dataview_id=9, checkpoint_id=3)
        mock_client._request_json.assert_called_once_with("DELETE", f"{_BASE}/3")

    async def test_delete_invalid_project_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="project_id"):
            await api.delete(dataset_id=1, dataview_id=9, checkpoint_id=3, project_id=-5)


class TestCheckpointsAPIProjectRequired:
    async def test_requires_project(self):
        mock_client = MagicMock()
        mock_client.workspace_id = 2
        mock_client.project_id = None
        api = CheckpointsAPI(mock_client)
        with pytest.raises(ValueError, match="project_id must be set"):
            await api.list(dataset_id=1, dataview_id=9)
