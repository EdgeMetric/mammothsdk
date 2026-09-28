"""The two actions the route grew after the SDK's action enum was written.

`restore` and `set-rls-config` are actions the route takes today, and each
carries a parameter the SDK had no way to send.
"""

from unittest.mock import AsyncMock, MagicMock

from mammoth.api.dashboards import DashboardsAPI
from mammoth.models.dashboards import DashboardActionType


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
