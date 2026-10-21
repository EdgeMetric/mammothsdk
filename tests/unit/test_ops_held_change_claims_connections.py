"""Unit tests for the held plan change, entitlement edit, tool claim, connection overview,
task preview cancel and dashboard chat attachment / unpublished-changes SDK methods."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.billing import BillingAPI
from mammoth.api.connectors import ConnectorsAPI
from mammoth.api.dashboards import DashboardsAPI
from mammoth.api.datasets import DatasetsAPI
from mammoth.api.pipeline import PipelineAPI
from mammoth.api.support import SupportAPI
from mammoth.exceptions import MammothValidationError


def _client() -> MagicMock:
    client = MagicMock()
    client.workspace_id = 2
    client.project_id = 100
    client._request_json = AsyncMock(return_value={})
    client._request_list = AsyncMock(return_value=[])
    return client


class TestHeldChange:
    async def test_get(self):
        client = _client()
        await BillingAPI(client).stripe_held_change_get()
        client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/subscription/held-change"
        )

    async def test_cancel(self):
        client = _client()
        await BillingAPI(client).stripe_held_change_cancel()
        client._request_json.assert_called_once_with(
            "POST", "/workspaces/2/subscription/held-change/cancel"
        )


class TestPlanEntitlements:
    async def test_update_sends_the_values_body(self):
        client = _client()
        await SupportAPI(client).plan_update_entitlements(3, {"max_users": 10, "sso": True})
        client._request_json.assert_called_once_with(
            "PUT",
            "/subscription/plans/3/entitlements",
            json={"values": {"max_users": 10, "sso": True}},
        )

    async def test_empty_values_raise(self):
        client = _client()
        with pytest.raises(MammothValidationError):
            await SupportAPI(client).plan_update_entitlements(3, {})
        client._request_json.assert_not_called()

    async def test_plan_id_must_be_positive(self):
        client = _client()
        with pytest.raises(MammothValidationError):
            await SupportAPI(client).plan_update_entitlements(0, {"sso": True})
        client._request_json.assert_not_called()


class TestToolClaims:
    async def test_get_sends_the_token_as_a_query_param(self):
        client = _client()
        await DatasetsAPI(client).tool_claim_get("tok")
        client._request_json.assert_called_once_with("GET", "/tool-claims", params={"token": "tok"})

    async def test_redeem_defaults_to_the_client_workspace_and_project(self):
        client = _client()
        await DatasetsAPI(client).tool_claim_redeem("tok")
        client._request_json.assert_called_once_with(
            "POST", "/workspaces/2/projects/100/tool-claims", json={"token": "tok"}
        )

    async def test_redeem_into_a_named_project(self):
        client = _client()
        await DatasetsAPI(client).tool_claim_redeem("tok", workspace_id=5, project_id=6)
        client._request_json.assert_called_once_with(
            "POST", "/workspaces/5/projects/6/tool-claims", json={"token": "tok"}
        )

    @pytest.mark.parametrize("token", ["", "x" * 301])
    async def test_token_length_is_checked_before_sending(self, token):
        client = _client()
        api = DatasetsAPI(client)
        with pytest.raises(MammothValidationError):
            await api.tool_claim_get(token)
        with pytest.raises(MammothValidationError):
            await api.tool_claim_redeem(token)
        client._request_json.assert_not_called()


class TestConnections:
    async def test_list_all_sends_no_params_by_default(self):
        client = _client()
        await ConnectorsAPI(client).list_all_connections()
        client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/projects/100/connections", params=None
        )

    async def test_list_all_pages_and_keeps_a_zero_offset(self):
        client = _client()
        await ConnectorsAPI(client).list_all_connections(limit=10, offset=0, project_id=7)
        client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/projects/7/connections",
            params={"limit": 10, "offset": 0},
        )

    @pytest.mark.parametrize("kwargs", [{"limit": -1}, {"limit": 101}, {"offset": -1}])
    async def test_list_all_rejects_bad_paging(self, kwargs):
        client = _client()
        with pytest.raises(MammothValidationError):
            await ConnectorsAPI(client).list_all_connections(**kwargs)
        client._request_json.assert_not_called()

    async def test_test_connection_uses_the_raw_key(self):
        client = _client()
        await ConnectorsAPI(client).test_connection("prod-warehouse")
        client._request_json.assert_called_once_with(
            "PATCH", "/workspaces/2/projects/100/connections/prod-warehouse/test"
        )

    async def test_test_connection_needs_a_key(self):
        client = _client()
        with pytest.raises(MammothValidationError):
            await ConnectorsAPI(client).test_connection("")
        client._request_json.assert_not_called()


class TestPreviewCancel:
    async def test_cancel_deletes_the_preview_job(self):
        client = _client()
        api = PipelineAPI(client)
        api._resolve_ids = AsyncMock(return_value=(2, 100, 5, 9))  # type: ignore[method-assign]
        await api.preview_cancel(9, 44)
        client._request_json.assert_called_once_with(
            "DELETE", f"{api._base_url(2, 100, 5, 9)}/task_preview/44"
        )

    @pytest.mark.parametrize("job_id", [0, -1, True])
    async def test_job_id_must_be_a_positive_integer(self, job_id):
        client = _client()
        with pytest.raises(MammothValidationError):
            await PipelineAPI(client).preview_cancel(9, job_id)
        client._request_json.assert_not_called()


class TestDashboardChatAttachment:
    async def test_upload_posts_the_file_to_the_chat(self, tmp_path):
        client = _client()
        client._request_json.return_value = {"ref": "att:abc", "name": "notes.txt"}
        api = DashboardsAPI(client)
        api._post_workbook = AsyncMock(return_value={"ref": "att:abc"})  # type: ignore[method-assign]
        path = tmp_path / "notes.txt"
        path.write_text("hello")
        result = await api.chat_attachment_upload(12, path)
        api._post_workbook.assert_called_once_with(path, "/dashboards/12/chat/attachments")
        assert result == {"ref": "att:abc"}

    @pytest.mark.parametrize("dashboard_id", [0, -3, True])
    async def test_dashboard_id_must_be_positive(self, dashboard_id, tmp_path):
        client = _client()
        with pytest.raises(MammothValidationError):
            await DashboardsAPI(client).chat_attachment_upload(dashboard_id, tmp_path / "a.txt")
        client._request_json.assert_not_called()


class TestUnpublishedChanges:
    async def test_unpublished_reads_the_draft_summary(self):
        client = _client()
        client._request_json.return_value = {
            "published_sequence": 3,
            "head_sequence": 5,
            "count": 2,
            "changes": [],
        }
        result = await DashboardsAPI(client).unpublished(12)
        client._request_json.assert_called_once_with(
            "GET", "/dashboards/12/unpublished", params=None
        )
        assert result.count == 2
        assert result.head_sequence == 5
