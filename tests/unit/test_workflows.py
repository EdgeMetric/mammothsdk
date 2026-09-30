"""Unit tests for the WorkflowsAPI client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.workflows import WorkflowsAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[WorkflowsAPI, MagicMock]:
    """Create a WorkflowsAPI with a mocked client."""
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    mock_client.project_id = 100
    api = WorkflowsAPI(mock_client)
    return api, mock_client


class TestWorkflowsAPIList:
    async def test_list(self):
        api, mock_client = _make_api()
        mock_client._request_list = AsyncMock(return_value=[{"id": 1}])
        result = await api.list()
        mock_client._request_list.assert_called_once_with(
            "GET", "/workspaces/2/projects/100/workflows"
        )
        assert result == [{"id": 1}]

    async def test_list_explicit_project_id(self):
        api, mock_client = _make_api()
        mock_client._request_list = AsyncMock(return_value=[])
        await api.list(project_id=7)
        mock_client._request_list.assert_called_once_with(
            "GET", "/workspaces/2/projects/7/workflows"
        )

    async def test_list_invalid_project_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.list(project_id=0)


class TestWorkflowsAPICreate:
    async def test_create_defaults(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        await api.create(name="Sales pipeline")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/projects/100/workflows",
            json={"name": "Sales pipeline", "shape": "blank"},
        )

    async def test_create_with_options(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 2})
        await api.create(
            name="Merge flow",
            shape="merge",
            purpose="Combine two sources",
            seed_datasource_id=42,
        )
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json == {
            "name": "Merge flow",
            "shape": "merge",
            "purpose": "Combine two sources",
            "seed_datasource_id": 42,
        }


class TestWorkflowsAPIGetUpdateDelete:
    async def test_get(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 5})
        result = await api.get(5)
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/projects/100/workflows/5"
        )
        assert result == {"id": 5}

    async def test_get_invalid_workflow_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.get(0)

    async def test_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.update(5, name="Renamed", notes="Some notes")
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/projects/100/workflows/5",
            json={"name": "Renamed", "notes": "Some notes"},
        )

    async def test_update_no_fields_sends_empty_body(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.update(5)
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json == {}

    async def test_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.delete(5)
        mock_client._request_json.assert_called_once_with(
            "DELETE", "/workspaces/2/projects/100/workflows/5"
        )


class TestWorkflowsAPIGraphCleanup:
    async def test_graph(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"nodes": []})
        await api.graph()
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/projects/100/workflows/graph"
        )

    async def test_cleanup(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"removed": 0})
        await api.cleanup()
        mock_client._request_json.assert_called_once_with(
            "POST", "/workspaces/2/projects/100/workflows/cleanup"
        )


class TestWorkflowsAPIFromTemplate:
    async def test_from_template(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 9})
        await api.from_template(template_id=3, workflow_name="Cloned flow")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/projects/100/workflows/from-template",
            json={"template_id": 3, "workflow_name": "Cloned flow"},
        )


class TestWorkflowsAPIWorkspaceLists:
    async def test_workspace_datasets(self):
        api, mock_client = _make_api()
        mock_client._request_list = AsyncMock(return_value=[{"id": 1}])
        result = await api.workspace_datasets()
        mock_client._request_list.assert_called_once_with(
            "GET", "/workspaces/2/projects/100/workflows/workspace-datasets"
        )
        assert result == [{"id": 1}]

    async def test_workspace_exports(self):
        api, mock_client = _make_api()
        mock_client._request_list = AsyncMock(return_value=[])
        await api.workspace_exports()
        mock_client._request_list.assert_called_once_with(
            "GET", "/workspaces/2/projects/100/workflows/workspace-exports"
        )

    async def test_workspace_sources(self):
        api, mock_client = _make_api()
        mock_client._request_list = AsyncMock(return_value=[])
        await api.workspace_sources()
        mock_client._request_list.assert_called_once_with(
            "GET", "/workspaces/2/projects/100/workflows/workspace-sources"
        )


class TestWorkflowsAPIBlocks:
    async def test_block_add(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        await api.block_add(5, block_type="source", display_name="My source")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/projects/100/workflows/5/blocks",
            json={"block_type": "source", "display_name": "My source"},
        )

    async def test_block_add_invalid_block_id_via_workflow(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.block_add(0, block_type="source")

    async def test_block_auth(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.block_auth(5, 9, auth_data={"token": "abc"})
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/projects/100/workflows/5/blocks/9/auth",
            json={"auth_data": {"token": "abc"}},
        )

    async def test_block_auth_invalid_block_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.block_auth(5, 0, auth_data={})

    async def test_block_type(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.block_type(5, 9, connection_type="postgres")
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/projects/100/workflows/5/blocks/9/type",
            json={"connection_type": "postgres"},
        )

    async def test_block_config(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.block_config(5, 9)
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/projects/100/workflows/5/blocks/9/config",
        )

    async def test_canvas(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.canvas(5, canvas_state={"nodes": []})
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/projects/100/workflows/5/canvas",
            json={"canvas_state": {"nodes": []}},
        )


class TestWorkflowsAPIProjectRequired:
    async def test_list_requires_project(self):
        mock_client = MagicMock()
        mock_client.workspace_id = 2
        mock_client.project_id = None
        api = WorkflowsAPI(mock_client)
        with pytest.raises(ValueError, match="project_id must be set"):
            await api.list()
