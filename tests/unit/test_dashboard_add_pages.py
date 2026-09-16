"""Offline contract tests for the release dashboard add-pages binding."""

from unittest.mock import MagicMock

import pytest

from mammoth.api.dashboards import DashboardsAPI
from mammoth.exceptions import MammothValidationError


def _api() -> tuple[DashboardsAPI, MagicMock]:
    client = MagicMock()
    client._request_json.return_value = {"sequence": 4, "bake_job_id": 99}
    return DashboardsAPI(client), client


def test_add_pages_posts_exact_release_shape() -> None:
    api, client = _api()
    result = api.add_pages(
        7,
        {
            "params": {
                "pages": [{"title": "Revenue", "type": "summary"}],
                "base_sequence": 3,
                "activity": {"kind": "manual"},
            }
        },
    )
    assert result.sequence == 4
    client._request_json.assert_called_once_with(
        "POST",
        "/dashboards/7/pages",
        json={
            "params": {
                "pages": [{"title": "Revenue", "type": "summary"}],
                "base_sequence": 3,
                "activity": {"kind": "manual"},
            }
        },
    )


@pytest.mark.parametrize("dashboard_id", [0, -1, True, "7"])
def test_add_pages_rejects_invalid_dashboard_id(dashboard_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="dashboard_id"):
        api.add_pages(dashboard_id, {"params": {"pages": [{}]}})  # type: ignore[arg-type]
    client._request_json.assert_not_called()


@pytest.mark.parametrize(
    "body",
    [
        {"params": {"pages": []}},
        {"params": {"pages": [{}], "unexpected": True}},
        {"unexpected": True},
    ],
)
def test_add_pages_rejects_invalid_request_shape(body: dict[str, object]) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError):
        api.add_pages(7, body)  # type: ignore[arg-type]
    client._request_json.assert_not_called()
