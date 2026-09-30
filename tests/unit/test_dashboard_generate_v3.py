"""What the generate route accepts, held to the route's own contract.

The generated wrapper `DashboardsAPI.v3_generate` is pinned to an OpenAPI
snapshot older than the route: it demands an intent, knows no "qa" format and
forbids a title outright. `generate_v3` is the hand-written method that matches
the route as it stands, so these tests are the record of what that is.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.dashboards import DashboardsAPI
from mammoth.exceptions import MammothValidationError
from mammoth.models.dashboards import GenerateV3Params


def _api() -> tuple[DashboardsAPI, MagicMock]:
    client = MagicMock()
    client._request_json = AsyncMock(return_value={"job_id": 5})
    return DashboardsAPI(client), client


async def _refused(params: dict[str, Any]) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError):
        await api.generate_v3(params)
    client._request_json.assert_not_called()


async def test_generate_v3_sends_the_whole_brief_including_the_title() -> None:
    # The title is the field the generated wrapper cannot carry at all.
    api, client = _api()

    await api.generate_v3(
        GenerateV3Params(dataview_id=11, intent="revenue by region", title="Revenue")
    )

    client._request_json.assert_called_once_with(
        "POST",
        "/dashboards/v3/generate",
        json={
            "params": {
                "dataview_id": 11,
                "intent": "revenue by region",
                "title": "Revenue",
            }
        },
    )


async def test_a_question_and_answer_notebook_needs_no_intent() -> None:
    # The reader asks the questions, so the author never writes a brief.
    api, client = _api()

    await api.generate_v3({"dataview_id": 11, "format": "qa"})

    assert client._request_json.call_args.kwargs["json"] == {
        "params": {"dataview_id": 11, "format": "qa"}
    }


async def test_every_other_format_needs_a_brief() -> None:
    await _refused({"dataview_id": 11, "intent": "   "})


async def test_a_format_the_route_does_not_build_is_refused() -> None:
    await _refused({"dataview_id": 11, "intent": "sales", "format": "poster"})


async def test_a_title_longer_than_the_route_takes_is_refused() -> None:
    await _refused({"dataview_id": 11, "intent": "sales", "title": "x" * 201})


async def test_a_dataview_id_below_one_is_refused() -> None:
    await _refused({"dataview_id": 0, "intent": "sales"})
