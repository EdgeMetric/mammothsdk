from unittest.mock import MagicMock

from mammoth.api.dashboards import DashboardsAPI
from mammoth.models.dashboards import UseTemplateSpec


def test_take_pending_template_posts_exact_route() -> None:
    client = MagicMock()
    client._request_json.return_value = {"slug": "starter"}
    assert DashboardsAPI(client).take_pending_template() == {"slug": "starter"}
    client._request_json.assert_called_once_with("POST", "/dashboards/v3/templates/pending")


def test_use_template_posts_exact_route() -> None:
    client = MagicMock()
    client._request_json.return_value = {
        "job": {
                "id": 3, "status": "processing", "response": {},
                "last_updated_at": "2026-01-01T00:00:00Z", "created_at": "2026-01-01T00:00:00Z",
                "path": "/jobs/3", "operation": "use-template",
        }
    }
    body = UseTemplateSpec.model_validate({"params": {"project_id": 9, "mode": "dark"}})
    assert DashboardsAPI(client).use_template("starter", body).job.id == 3
    client._request_json.assert_called_once_with(
        "POST", "/dashboards/v3/templates/starter/use",
        json={"params": {"project_id": 9, "style_id": "", "mode": "dark"}},
    )
