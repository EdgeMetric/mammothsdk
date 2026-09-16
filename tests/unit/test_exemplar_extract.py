"""Independent exact-wire checks for the release exemplar extract route."""

from unittest.mock import MagicMock

from mammoth.api.dashboards import DashboardsAPI
from mammoth.models.dashboards import ExemplarExtractSpec


def test_exemplar_extract_posts_literal_release_route_and_body() -> None:
    client = MagicMock()
    client._request_json.return_value = {"palette": ["blue"], "source": {"kind": "upload"}}
    result = DashboardsAPI(client).extract_exemplar(
        ExemplarExtractSpec.model_validate(
            {
                "params": {
                    "name": "example.pdf",
                    "size": 42,
                    "type": "application/pdf",
                    "content": "encoded-content",
                    "dataview_id": 9,
                }
            }
        )
    )
    assert result["palette"] == ["blue"]
    assert result["source"] == {"kind": "upload"}
    client._request_json.assert_called_once_with(
        "POST",
        "/dashboards/v3/exemplar/extract",
        json={
            "params": {
                "name": "example.pdf",
                "size": 42,
                "type": "application/pdf",
                "content": "encoded-content",
                "dataview_id": 9,
            }
        },
    )
