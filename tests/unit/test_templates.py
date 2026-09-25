"""Unit tests for the TemplatesAPI client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.templates import TemplatesAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[TemplatesAPI, MagicMock]:
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    api = TemplatesAPI(mock_client)
    return api, mock_client


class TestTemplatesAPIList:
    async def test_list(self):
        api, mock_client = _make_api()
        # The route answers with a bare JSON array; the SDK wraps it.
        mock_client._request_list = AsyncMock(return_value=[])
        result = await api.list()
        mock_client._request_list.assert_called_once_with("GET", "/workspaces/2/templates")
        assert result == {"templates": []}


class TestTemplatesAPIGet:
    async def test_get(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 5})
        result = await api.get(5)
        mock_client._request_json.assert_called_once_with("GET", "/workspaces/2/templates/5")
        assert result == {"id": 5}

    async def test_get_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="template_id"):
            await api.get(0)


class TestTemplatesAPICreate:
    async def test_create(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        await api.create(body={"name": "Sales starter"})
        mock_client._request_json.assert_called_once_with(
            "POST", "/workspaces/2/templates", json={"name": "Sales starter"}
        )


class TestTemplatesAPIUpdate:
    async def test_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.update(5, body={"name": "renamed"})
        mock_client._request_json.assert_called_once_with(
            "PATCH", "/workspaces/2/templates/5", json={"name": "renamed"}
        )

    async def test_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.update(-1, body={})


class TestTemplatesAPIDelete:
    async def test_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.delete(5)
        mock_client._request_json.assert_called_once_with("DELETE", "/workspaces/2/templates/5")

    async def test_delete_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.delete(0)
