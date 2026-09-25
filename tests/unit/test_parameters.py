"""Unit tests for the ParametersAPI client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.parameters import ParametersAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[ParametersAPI, MagicMock]:
    """Create a ParametersAPI with a mocked client."""
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    api = ParametersAPI(mock_client)
    return api, mock_client


class TestParametersAPIList:
    async def test_list_default(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"parameters": []})
        await api.list()
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/parameters", params=None
        )

    async def test_list_with_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"parameters": []})
        await api.list(limit=10, offset=5, search="rate", group_id=3, sort="name:asc", project_id=1)
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/parameters",
            params={
                "limit": 10,
                "offset": 5,
                "search": "rate",
                "group_id": 3,
                "sort": "name:asc",
                "project_id": 1,
            },
        )


class TestParametersAPICreate:
    async def test_create_minimal(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        await api.create(name="start_date", param_type="DATE", value="2026-01-01", project_id=1)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/parameters",
            json={
                "name": "start_date",
                "param_type": "DATE",
                "value": "2026-01-01",
                "scope": "project",
                "project_id": 1,
            },
        )

    async def test_create_workspace_scope(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 2})
        await api.create(name="global_rate", param_type="NUMERIC", value=1.5, scope="workspace")
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json == {
            "name": "global_rate",
            "param_type": "NUMERIC",
            "value": 1.5,
            "scope": "workspace",
        }

    async def test_create_invalid_project_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.create(name="x", param_type="TEXT", value="y", project_id=0)


class TestParametersAPIGetUpdateDelete:
    async def test_get(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 5})
        await api.get(5)
        mock_client._request_json.assert_called_once_with("GET", "/workspaces/2/parameters/5")

    async def test_get_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.get(0)

    async def test_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.update(5, value="2026-06-01", description="Updated start date")
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/parameters/5",
            json={"value": "2026-06-01", "description": "Updated start date"},
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
        mock_client._request_json.assert_called_once_with("DELETE", "/workspaces/2/parameters/5")


class TestParametersAPIDependenciesDuplicateRerun:
    async def test_dependencies(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"depends_on": []})
        await api.dependencies(5)
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/parameters/5/dependencies"
        )

    async def test_duplicate(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 6})
        await api.duplicate(5)
        mock_client._request_json.assert_called_once_with(
            "POST", "/workspaces/2/parameters/5/duplicate"
        )

    async def test_rerun(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.rerun(5)
        mock_client._request_json.assert_called_once_with(
            "POST", "/workspaces/2/parameters/5/rerun"
        )

    async def test_rerun_all_stale(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.rerun_all_stale(project_id=1)
        mock_client._request_json.assert_called_once_with(
            "POST", "/workspaces/2/parameters/rerun-all-stale", params={"project_id": 1}
        )

    async def test_rerun_all_stale_invalid_project_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.rerun_all_stale(project_id=0)


class TestParametersAPIGroups:
    async def test_group_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"groups": []})
        await api.group_list(project_id=1, limit=10, offset=0, sort="name:asc")
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/parameters/groups",
            params={"project_id": 1, "limit": 10, "offset": 0, "sort": "name:asc"},
        )

    async def test_group_create(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        await api.group_create(name="Date Parameters", project_id=1)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/parameters/groups",
            params={"project_id": 1},
            json={"name": "Date Parameters", "color": "#3B82F6"},
        )

    async def test_group_create_no_project(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        await api.group_create(name="Date Parameters")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/parameters/groups",
            params=None,
            json={"name": "Date Parameters", "color": "#3B82F6"},
        )

    async def test_group_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.group_update(3, name="Renamed Group", color="#8B5CF6")
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/parameters/groups/3",
            params=None,
            json={"name": "Renamed Group", "color": "#8B5CF6"},
        )

    async def test_group_update_invalid_group_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.group_update(0, name="x")

    async def test_group_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.group_delete(3, project_id=1)
        mock_client._request_json.assert_called_once_with(
            "DELETE", "/workspaces/2/parameters/groups/3", params={"project_id": 1}
        )

    async def test_group_reorder(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.group_reorder(order=[3, 1, 2], project_id=1)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/parameters/groups/reorder",
            params={"project_id": 1},
            json={"order": [3, 1, 2]},
        )
