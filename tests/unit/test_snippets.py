"""Unit tests for the SnippetsAPI client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.snippets import SnippetsAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[SnippetsAPI, MagicMock]:
    """Create a SnippetsAPI with a mocked client."""
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    api = SnippetsAPI(mock_client)
    return api, mock_client


class TestSnippetsAPIList:
    async def test_list_default(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"snippets": []})
        await api.list()
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/snippets", params=None
        )

    async def test_list_with_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"snippets": []})
        await api.list(
            limit=10, offset=5, search="revenue", group_id=3, sort="name:asc", project_id=1
        )
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/snippets",
            params={
                "limit": 10,
                "offset": 5,
                "search": "revenue",
                "group_id": 3,
                "sort": "name:asc",
                "project_id": 1,
            },
        )


class TestSnippetsAPICreate:
    async def test_create_minimal(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        await api.create(
            name="my_snippet",
            code="SELECT * FROM table",
            language="sql",
            project_id=1,
        )
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/snippets",
            json={
                "name": "my_snippet",
                "code": "SELECT * FROM table",
                "language": "sql",
                "scope": "project",
                "project_id": 1,
            },
        )

    async def test_create_with_description_and_group(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 2})
        await api.create(
            name="my_snippet",
            code="SELECT 1",
            language="sql",
            description="Aggregates revenue by region",
            group_id=4,
            project_id=1,
        )
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["description"] == "Aggregates revenue by region"
        assert call_json["group_id"] == 4

    async def test_create_invalid_project_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.create(name="x", code="y", language="sql", project_id=0)


class TestSnippetsAPIGetUpdateDelete:
    async def test_get(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 5})
        await api.get(5)
        mock_client._request_json.assert_called_once_with("GET", "/workspaces/2/snippets/5")

    async def test_get_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.get(0)

    async def test_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.update(5, name="renamed_snippet", code="SELECT id, name FROM table")
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/snippets/5",
            json={"name": "renamed_snippet", "code": "SELECT id, name FROM table"},
        )

    async def test_update_no_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.update(5)
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json == {}

    async def test_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.delete(5)
        mock_client._request_json.assert_called_once_with("DELETE", "/workspaces/2/snippets/5")


class TestSnippetsAPIDependenciesDuplicateRerun:
    async def test_dependencies(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"depends_on": []})
        await api.dependencies(5)
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/snippets/5/dependencies"
        )

    async def test_duplicate(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 6})
        await api.duplicate(5)
        mock_client._request_json.assert_called_once_with(
            "POST", "/workspaces/2/snippets/5/duplicate"
        )

    async def test_rerun(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.rerun(5)
        mock_client._request_json.assert_called_once_with("POST", "/workspaces/2/snippets/5/rerun")
