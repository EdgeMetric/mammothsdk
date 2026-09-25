from unittest.mock import AsyncMock, MagicMock

from mammoth.api.dashboards import DashboardsAPI
from mammoth.models.dashboards import SwapDataSpec


async def test_swap_data_posts_literal_release_route_and_body() -> None:
    client = MagicMock()
    client._request_json = AsyncMock(return_value={"job_id": 4})
    result = await DashboardsAPI(client).swap_data(
        7, SwapDataSpec.model_validate({"params": {"dataview_id": 9, "mapping": {"a": "b"}}})
    )
    assert result.job_id == 4
    client._request_json.assert_called_once_with(
        "POST",
        "/dashboards/v3/7/swap-data",
        json={"params": {"dataview_id": 9, "mapping": {"a": "b"}}},
    )
