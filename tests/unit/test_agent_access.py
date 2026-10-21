"""Unit tests for the agent access methods of AgentsAPI."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.agents import AgentsAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[AgentsAPI, MagicMock]:
    """Create an AgentsAPI with a mocked client."""
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    mock_client._request_json = AsyncMock(return_value={})
    mock_client._request_list = AsyncMock(return_value=[])
    return AgentsAPI(mock_client), mock_client


class TestAccessReads:
    async def test_me_sends_no_params_by_default(self):
        api, client = _make_api()
        await api.access_me()
        client._request_json.assert_called_once_with("GET", "/agents/access/me", params=None)

    async def test_me_sends_project_and_preview_user(self):
        api, client = _make_api()
        await api.access_me(project_id=7, preview_user_id=9)
        client._request_json.assert_called_once_with(
            "GET", "/agents/access/me", params={"project_id": 7, "preview_user_id": 9}
        )

    async def test_settings_get(self):
        api, client = _make_api()
        await api.access_settings_get()
        client._request_json.assert_called_once_with("GET", "/agents/access/settings")

    async def test_grants_list_uses_list_transport(self):
        api, client = _make_api()
        client._request_list.return_value = [{"id": 1}]
        assert await api.access_grants_list() == [{"id": 1}]
        client._request_list.assert_called_once_with("GET", "/agents/access/grants")

    async def test_people_search(self):
        api, client = _make_api()
        await api.access_people("ana")
        client._request_list.assert_called_once_with(
            "GET", "/agents/access/people", params={"search": "ana"}
        )

    async def test_people_without_search_sends_no_params(self):
        api, client = _make_api()
        await api.access_people()
        client._request_list.assert_called_once_with("GET", "/agents/access/people", params=None)

    async def test_tree(self):
        api, client = _make_api()
        await api.access_tree()
        client._request_list.assert_called_once_with("GET", "/agents/access/tree")

    async def test_project_askers(self):
        api, client = _make_api()
        await api.access_project_askers(12)
        client._request_json.assert_called_once_with("GET", "/agents/access/projects/12/askers")

    async def test_reach_for_a_user(self):
        api, client = _make_api()
        await api.access_reach(user_id=5)
        client._request_list.assert_called_once_with(
            "GET", "/agents/access/reach", params={"user_id": 5}
        )

    async def test_requests_list_filters_by_status(self):
        api, client = _make_api()
        await api.access_requests_list("open")
        client._request_list.assert_called_once_with(
            "GET", "/agents/access/requests", params={"status": "open"}
        )

    async def test_requests_list_rejects_unknown_status(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="status"):
            await api.access_requests_list("pending")

    async def test_requests_mine_names_the_session(self):
        api, client = _make_api()
        await api.access_requests_mine("sess-1")
        client._request_list.assert_called_once_with(
            "GET", "/agents/access/requests/mine", params={"session_id": "sess-1"}
        )

    async def test_turn_feedback_list(self):
        api, client = _make_api()
        await api.turn_feedback_list("sess-1")
        client._request_list.assert_called_once_with("GET", "/agents/sessions/sess-1/feedback")


class TestAccessSettingsUpdate:
    async def test_sends_only_the_fields_given(self):
        api, client = _make_api()
        await api.access_settings_update(enabled=False, downloads=True)
        client._request_json.assert_called_once_with(
            "PATCH", "/agents/access/settings", json={"enabled": False, "downloads": True}
        )

    async def test_nothing_to_change_raises(self):
        api, client = _make_api()
        with pytest.raises(MammothValidationError):
            await api.access_settings_update()
        client._request_json.assert_not_called()


class TestAccessGrants:
    async def test_give(self):
        api, client = _make_api()
        await api.access_grant_give(["a@example.com"], "ask", [{"project_id": 1}])
        client._request_json.assert_called_once_with(
            "POST",
            "/agents/access/grants",
            json={"emails": ["a@example.com"], "level": "ask", "items": [{"project_id": 1}]},
        )

    @pytest.mark.parametrize(
        ("emails", "level", "items"),
        [
            ([], "ask", [{"project_id": 1}]),
            (["a@example.com"], "ask", []),
            (["a@example.com"], "admin", [{"project_id": 1}]),
        ],
    )
    async def test_give_validates_before_sending(self, emails, level, items):
        api, client = _make_api()
        with pytest.raises(MammothValidationError):
            await api.access_grant_give(emails, level, items)
        client._request_json.assert_not_called()

    async def test_update_sends_only_the_fields_given(self):
        api, client = _make_api()
        await api.access_grant_update(4, level="explore")
        client._request_json.assert_called_once_with(
            "PATCH", "/agents/access/grants/4", json={"level": "explore"}
        )

    async def test_update_with_nothing_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError):
            await api.access_grant_update(4)

    async def test_revoke(self):
        api, client = _make_api()
        await api.access_grant_revoke(4)
        client._request_json.assert_called_once_with("DELETE", "/agents/access/grants/4")


class TestAccessRequests:
    async def test_create(self):
        api, client = _make_api()
        await api.access_request_create("access", "Please share", project_id=3)
        client._request_json.assert_called_once_with(
            "POST",
            "/agents/access/requests",
            json={"kind": "access", "text": "Please share", "project_id": 3},
        )

    async def test_create_rejects_unknown_kind_and_long_text(self):
        api, client = _make_api()
        with pytest.raises(MammothValidationError, match="kind"):
            await api.access_request_create("wish", "x")
        with pytest.raises(MammothValidationError):
            await api.access_request_create("access", "x" * 2001)
        client._request_json.assert_not_called()

    async def test_resolve(self):
        api, client = _make_api()
        await api.access_request_resolve(8, "done")
        client._request_json.assert_called_once_with(
            "PATCH", "/agents/access/requests/8", json={"status": "done"}
        )

    async def test_resolve_cannot_reopen(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="status"):
            await api.access_request_resolve(8, "open")

    async def test_add_to_context(self):
        api, client = _make_api()
        await api.access_request_add_to_context(8)
        client._request_json.assert_called_once_with(
            "POST", "/agents/access/requests/8/project-context"
        )


class TestChartAndRating:
    async def test_chart_save_to_a_new_dashboard(self):
        api, client = _make_api()
        await api.access_chart_save("sess-1", "turn-1", new_dashboard_name="Revenue")
        client._request_json.assert_called_once_with(
            "POST",
            "/agents/access/saved-charts",
            json={"session_id": "sess-1", "turn_id": "turn-1", "new_dashboard_name": "Revenue"},
        )

    async def test_chart_save_needs_ids(self):
        api, client = _make_api()
        with pytest.raises(MammothValidationError):
            await api.access_chart_save("", "turn-1")
        client._request_json.assert_not_called()

    async def test_rate(self):
        api, client = _make_api()
        await api.turn_rate("sess-1", "turn-1", "down", comment="Wrong total")
        client._request_json.assert_called_once_with(
            "POST",
            "/agents/sessions/sess-1/turns/turn-1/feedback",
            json={"rating": "down", "comment": "Wrong total"},
        )

    async def test_rate_rejects_unknown_rating(self):
        api, client = _make_api()
        with pytest.raises(MammothValidationError, match="rating"):
            await api.turn_rate("sess-1", "turn-1", "meh")
        client._request_json.assert_not_called()
