"""``DataviewsAPI.set_explore_panel`` and ``DashboardsAPI.append_figure`` refuse bad input first.

Every case here fails inside the method before it reads ``self._client``, so the real
sub-client is built over no client at all.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from mammoth.api.dashboards import DashboardsAPI
from mammoth.api.dataviews import DataviewsAPI
from mammoth.exceptions import MammothValidationError

_FIGURE: dict[str, Any] = {"kind": "hbar", "dim": "Region", "measure": "Revenue", "agg": "sum"}


def _dashboards() -> DashboardsAPI:
    return DashboardsAPI(None)  # type: ignore[arg-type]


def _dataviews() -> DataviewsAPI:
    return DataviewsAPI(None)  # type: ignore[arg-type]


@pytest.mark.parametrize("dashboard_id", [0, -1])
async def test_append_figure_needs_a_positive_dashboard_id(dashboard_id: int) -> None:
    with pytest.raises(MammothValidationError):
        await _dashboards().append_figure(dashboard_id, 3, _FIGURE)


@pytest.mark.parametrize("dataview_id", [0, -1, True])
async def test_append_figure_needs_a_positive_dataview_id(dataview_id: int) -> None:
    with pytest.raises(MammothValidationError, match="dataview_id"):
        await _dashboards().append_figure(7, dataview_id, _FIGURE)


async def test_append_figure_needs_a_non_empty_figure() -> None:
    with pytest.raises(MammothValidationError, match="figure"):
        await _dashboards().append_figure(7, 3, {})


async def test_append_figure_takes_one_page_target_not_two() -> None:
    with pytest.raises(MammothValidationError, match="page_id"):
        await _dashboards().append_figure(7, 3, _FIGURE, page_id="p1", page_new_title="New")


@pytest.mark.parametrize(
    ("kwargs", "named"),
    [
        ({"tile": " ", "text": "From Stripe"}, "tile"),
        ({"tile": "t-1", "text": " "}, "text"),
        ({"tile": "t-1", "text": "From Stripe", "kind": "note"}, "kind"),
    ],
)
async def test_add_text_block_refuses_bad_input(kwargs: dict[str, str], named: str) -> None:
    with pytest.raises(MammothValidationError, match=named):
        await _dashboards().add_text_block(7, **kwargs)


async def test_add_text_block_needs_a_positive_dashboard_id() -> None:
    with pytest.raises(MammothValidationError, match="dashboard_id"):
        await _dashboards().add_text_block(0, "t-1", "From Stripe")


async def test_add_text_block_posts_the_block() -> None:
    client = AsyncMock()
    client._request_json.return_value = {"created": True}

    await DashboardsAPI(client).add_text_block(7, "t-1", "From Stripe", title="Source")

    client._request_json.assert_awaited_once_with(
        "POST",
        "/dashboards/7/text-blocks",
        json={
            "params": {"tile": "t-1", "text": "From Stripe", "kind": "source", "title": "Source"}
        },
    )


async def test_set_explore_panel_needs_a_dict() -> None:
    with pytest.raises(ValueError, match="panel"):
        await _dataviews().set_explore_panel(1, 2, [])  # type: ignore[arg-type]
