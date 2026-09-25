"""Unit tests for the WorkspacesAPI client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.workspaces import WorkspacesAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[WorkspacesAPI, MagicMock]:
    """Create a WorkspacesAPI with a mocked client."""
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    api = WorkspacesAPI(mock_client)
    return api, mock_client


class TestAcceptInvite:
    async def test_accept_invite(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"status": "accepted"})
        result = await api.accept_invite("invite_token")
        mock_client._request_json.assert_called_once_with(
            "POST", "/accept-invite", json={"token": "invite_token"}
        )
        assert result == {"status": "accepted"}

    async def test_accept_invite_empty_token_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="token"):
            await api.accept_invite("")


class TestCreate:
    async def test_create(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 5, "name": "New workspace"})
        result = await api.create({"name": "New workspace"})
        mock_client._request_json.assert_called_once_with(
            "POST", "/workspaces", json={"name": "New workspace"}
        )
        assert result == {"id": 5, "name": "New workspace"}


class TestCheckExpression:
    async def test_check_expression(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"valid": True})
        body = {"expression": "1 + 1"}
        result = await api.check_expression(body)
        mock_client._request_json.assert_called_once_with(
            "POST", "/workspaces/2/ai/check-expression", json=body
        )
        assert result == {"valid": True}


class TestLlmTask:
    async def test_llm_task(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"job": {"id": 1}})
        params = {"object_id": 245, "object_type": "dataview", "mode": "llm"}
        result = await api.llm_task("generate_summary", params)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/llm",
            json={"type": "generate_summary", "params": params},
        )
        assert result == {"job": {"id": 1}}

    async def test_llm_task_empty_type_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="task_type"):
            await api.llm_task("", {})


class TestAppUsage:
    async def test_app_usage_no_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"used": 10})
        await api.app_usage()
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/app-usage", params=None
        )

    async def test_app_usage_with_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"used": 10})
        await api.app_usage(fields="storage,rows")
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/app-usage", params={"fields": "storage,rows"}
        )


class TestStorageBreakdown:
    async def test_storage_breakdown_no_params(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"items": []})
        await api.storage_breakdown()
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/storage-breakdown", params=None
        )

    async def test_storage_breakdown_with_params(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"items": []})
        await api.storage_breakdown(limit=10, offset=5)
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/storage-breakdown",
            params={"limit": 10, "offset": 5},
        )


class TestSegments:
    async def test_segment_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"segments": ["Alpha"]})
        result = await api.segment_list()
        mock_client._request_json.assert_called_once_with("GET", "/workspaces/2/split-segments")
        assert result == {"segments": ["Alpha"]}

    async def test_segment_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"segments": ["Beta"]})
        patch = [{"op": "add", "path": "segments", "value": "Beta"}]
        await api.segment_update(patch)
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/split-segments",
            json={"patch": patch},
        )

    async def test_segment_update_empty_patch_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="patch"):
            await api.segment_update([])


class TestWorkspaceUsers:
    async def test_user_add_minimal(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"invited": ["a@example.com"]})
        await api.user_add(["a@example.com"])
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/users",
            json={"invite": {"email_ids": ["a@example.com"]}},
        )

    async def test_user_add_with_projects(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"invited": ["a@example.com"]})
        projects = [{"project_id": 1, "role": "project_analyst"}]
        await api.user_add(["a@example.com"], projects=projects)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/users",
            json={"invite": {"email_ids": ["a@example.com"], "projects": projects}},
        )

    async def test_user_add_empty_email_ids_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="email_ids"):
            await api.user_add([])

    async def test_user_remove(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.user_remove(7)
        mock_client._request_json.assert_called_once_with("DELETE", "/workspaces/2/users/7")

    async def test_user_remove_non_positive_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="user_id"):
            await api.user_remove(0)

    async def test_user_remove_batch_no_params(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.user_remove_batch()
        mock_client._request_json.assert_called_once_with(
            "DELETE", "/workspaces/2/users", params=None
        )

    async def test_user_remove_batch_with_params(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.user_remove_batch(ids="1,2", invite_ids="3,4")
        mock_client._request_json.assert_called_once_with(
            "DELETE",
            "/workspaces/2/users",
            params={"ids": "1,2", "invite_ids": "3,4"},
        )

    async def test_user_update_batch(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"updated": True})
        patches = [{"op": "replace", "path": "role", "value": "1,workspace_member"}]
        await api.user_update_batch(patches)
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/users",
            json={"patches": patches},
        )

    async def test_user_update_batch_empty_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="patches"):
            await api.user_update_batch([])
