"""Independent exact-wire checks for the release-only context extract route."""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from mammoth.api.dashboards import DashboardsAPI
from mammoth.models.dashboards import ContextExtractSpec


def test_context_extract_posts_literal_release_route_and_body() -> None:
    client = MagicMock()
    client._request_json.return_value = {"suggestions": {"tone": "concise"}}
    result = DashboardsAPI(client).extract_context(
        ContextExtractSpec.model_validate(
            {"params": {"name": "context.txt", "size": 12, "type": "text/plain", "text": "Revenue"}}
        )
    )
    assert result == {
        "file": None,
        "rejected": None,
        "shape": None,
        "figureHeavy": [],
        "suggestions": {"tone": "concise"},
        "condensed": {},
        "skipped": None,
    }
    client._request_json.assert_called_once_with(
        "POST",
        "/dashboards/v3/contexts/extract",
        json={
            "params": {
                "name": "context.txt",
                "size": 12,
                "type": "text/plain",
                "text": "Revenue",
            }
        },
    )


@pytest.mark.parametrize("size", [True, 1.5])
def test_context_extract_rejects_non_integer_size(size: object) -> None:
    with pytest.raises(ValidationError):
        ContextExtractSpec.model_validate({"params": {"name": "x", "size": size}})
