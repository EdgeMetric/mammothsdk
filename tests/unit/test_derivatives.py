"""Unit tests for the DerivativesAPI client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.derivatives import DerivativesAPI
from mammoth.exceptions import MammothValidationError

_BASE = "/workspaces/2/projects/100/datasets/1/dataviews/9/derivatives"


def _make_api() -> tuple[DerivativesAPI, MagicMock]:
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    mock_client.project_id = 100
    api = DerivativesAPI(mock_client)
    return api, mock_client


class TestDerivativesAPIList:
    async def test_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"derivatives": []})
        await api.list(dataset_id=1, dataview_id=9)
        mock_client._request_json.assert_called_once_with("GET", _BASE)

    async def test_list_invalid_dataset_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="dataset_id"):
            await api.list(dataset_id=0, dataview_id=9)


class TestDerivativesAPICreate:
    async def test_create(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 4})
        await api.create(dataset_id=1, dataview_id=9, body={"type": "summary"})
        mock_client._request_json.assert_called_once_with("POST", _BASE, json={"type": "summary"})

    async def test_create_invalid_dataview_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="dataview_id"):
            await api.create(dataset_id=1, dataview_id=-1, body={})


class TestDerivativesAPIData:
    async def test_data(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"rows": []})
        await api.data(dataset_id=1, dataview_id=9, derivative_id=4, body={"limit": 10})
        mock_client._request_json.assert_called_once_with(
            "POST", f"{_BASE}/4/data", json={"limit": 10}
        )

    async def test_data_invalid_derivative_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="derivative_id"):
            await api.data(dataset_id=1, dataview_id=9, derivative_id=0, body={})


class TestDerivativesAPIUpdate:
    async def test_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.update(dataset_id=1, dataview_id=9, derivative_id=4, body={"name": "renamed"})
        mock_client._request_json.assert_called_once_with(
            "PATCH", f"{_BASE}/4", json={"name": "renamed"}
        )


class TestDerivativesAPIDelete:
    async def test_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.delete(dataset_id=1, dataview_id=9, derivative_id=4)
        mock_client._request_json.assert_called_once_with("DELETE", f"{_BASE}/4")

    async def test_delete_invalid_project_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="project_id"):
            await api.delete(dataset_id=1, dataview_id=9, derivative_id=4, project_id=-5)


class TestDerivativesAPIProjectRequired:
    async def test_requires_project(self):
        mock_client = MagicMock()
        mock_client.workspace_id = 2
        mock_client.project_id = None
        api = DerivativesAPI(mock_client)
        with pytest.raises(ValueError, match="project_id must be set"):
            await api.list(dataset_id=1, dataview_id=9)
