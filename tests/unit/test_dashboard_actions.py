"""The actions and parameters the route grew after the SDK's action enum was written.

`restore` and `set-rls-config` are actions the route takes today, and each
carries a parameter the SDK had no way to send.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.dashboards import DashboardsAPI
from mammoth.exceptions import MammothValidationError
from mammoth.models.dashboards import DashboardActionType, DashboardPublishRooms


def _api() -> tuple[DashboardsAPI, MagicMock]:
    client = MagicMock()
    client._request_json = AsyncMock(return_value={"job": {"id": 3}})
    return DashboardsAPI(client), client


async def test_a_dashboard_is_restored_to_one_of_its_versions() -> None:
    api, client = _api()

    await api.action(7, DashboardActionType.RESTORE, params_sequence=4)

    client._request_json.assert_called_once_with(
        "POST", "/dashboards/7/action", json={"action": "restore", "params": {"sequence": 4}}
    )


async def test_row_level_security_is_switched_on_for_a_column() -> None:
    api, client = _api()

    await api.action(
        7, DashboardActionType.SET_RLS_CONFIG, params_enabled=True, params_filter_column="region"
    )

    assert client._request_json.call_args.kwargs["json"] == {
        "action": "set-rls-config",
        "params": {"enabled": True, "filter_column": "region"},
    }


async def test_a_publish_says_what_to_do_about_the_ask_rooms_it_would_hide_the_board_in() -> None:
    api, client = _api()

    await api.action(
        7, DashboardActionType.PUBLISH_PRESENTATION, params_rooms=DashboardPublishRooms.ADD
    )

    client._request_json.assert_called_once_with(
        "POST",
        "/dashboards/7/action",
        json={"action": "publish-presentation", "params": {"rooms": "add"}},
    )


async def test_the_rooms_choice_is_taken_as_its_word() -> None:
    api, client = _api()

    await api.action(7, DashboardActionType.PUBLISH_PRESENTATION, params_rooms="hide")  # type: ignore[arg-type]

    assert client._request_json.call_args.kwargs["json"]["params"] == {"rooms": "hide"}


@pytest.mark.parametrize(
    ("action", "rooms", "message"),
    [
        (DashboardActionType.PUBLISH_PRESENTATION, "maybe", "'add' or 'hide'"),
        (DashboardActionType.SYNC, DashboardPublishRooms.ADD, "publish-presentation"),
    ],
)
async def test_a_rooms_choice_the_route_cannot_take_is_refused_before_a_request(
    action: DashboardActionType, rooms: str, message: str
) -> None:
    api, client = _api()

    with pytest.raises(MammothValidationError, match=message):
        await api.action(7, action, params_rooms=rooms)  # type: ignore[arg-type]

    client._request_json.assert_not_called()
