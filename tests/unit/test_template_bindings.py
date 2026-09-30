from unittest.mock import AsyncMock, MagicMock

from mammoth.api.dashboards import DashboardsAPI
from mammoth.models.dashboards import UseTemplateSpec


async def test_take_pending_template_posts_exact_route() -> None:
    client = MagicMock()
    client._request_json = AsyncMock(return_value={"slug": "starter"})
    assert await DashboardsAPI(client).take_pending_template() == {"slug": "starter"}
    client._request_json.assert_called_once_with("POST", "/dashboards/v3/templates/pending")


async def test_use_template_posts_exact_route() -> None:
    client = MagicMock()
    client._request_json = AsyncMock(
        return_value={
            "job": {
                "id": 3,
                "status": "processing",
                "response": {},
                "last_updated_at": "2026-01-01T00:00:00Z",
                "created_at": "2026-01-01T00:00:00Z",
                "path": "/jobs/3",
                "operation": "use-template",
            }
        }
    )
    body = UseTemplateSpec.model_validate({"params": {"project_id": 9, "mode": "dark"}})
    assert (await DashboardsAPI(client).use_template("starter", body)).job.id == 3
    client._request_json.assert_called_once_with(
        "POST",
        "/dashboards/v3/templates/starter/use",
        json={"params": {"project_id": 9, "style_id": "", "mode": "dark"}},
    )
