"""Board values name the pages they could not evaluate (mammothsdk#442)."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.board_values import board_style, board_values, pages_without_values
from mammoth_cli.services.dashboard_pages import check_page_specs, own_table
from mammoth_cli.services.testing import FakeMammothService

_CANVAS_GET = "mammoth.api.dashboards.DashboardsAPI.canvas_get"
_DESCRIPTOR_DATA = "mammoth.api.dashboards.DashboardsAPI.descriptor_data"


def _two_page_canvas() -> dict[str, Any]:
    return {
        "canvas": {
            "focus": {"kpis": [{"field": "Sales", "label": "Sales"}]},
            "pages": [
                {"id": "p2", "title": "Payroll", "added": [{"id": "a1", "kind": "line"}]},
                {"id": "p3", "title": "Notes"},
            ],
        },
        "meta": {"figures": {"p1:kpi:0": {"descriptors": {"value": "d1"}}}},
    }


def test_a_page_with_tiles_but_no_bound_figure_is_named() -> None:
    canvas = _two_page_canvas()
    bindings = [{"figure": "p1:kpi:0"}]
    assert pages_without_values(canvas, bindings) == [{"page": "p2", "title": "Payroll"}]


def test_board_values_reports_the_pages_it_left_out() -> None:
    service = FakeMammothService()
    service.responses[_CANVAS_GET] = _two_page_canvas()
    service.responses[_DESCRIPTOR_DATA] = {"results": {"d1": {"status": "success", "value": 5}}}
    out = board_values(service, 7)
    assert out["values"][0]["value"] == 5
    assert out["pages_not_evaluated"] == [{"page": "p2", "title": "Payroll"}]
    assert "mammoth dashboard get 7" in out["note"]


def test_every_page_bound_adds_no_note() -> None:
    canvas = _two_page_canvas()
    canvas["meta"]["figures"]["p2:add:a1"] = {"descriptors": {"Sales": "d2"}}
    bindings = [{"figure": "p1:kpi:0"}, {"figure": "p2:add:a1"}]
    assert pages_without_values(canvas, bindings) == []


def test_board_style_reads_theme_and_mode_from_the_canvas() -> None:
    # mammothsdk#419: the theme was readable only from a screenshot.
    doc = {"canvas": {"style_id": "stone", "mode": "dark", "objects": []}}
    assert board_style(doc) == {"style_id": "stone", "mode": "dark"}
    assert board_style({"canvas": {}}) is None


def test_a_non_mapping_page_dataset_is_refused() -> None:
    with pytest.raises(CliError) as excinfo:
        check_page_specs([{"title": "P", "dataset": 99}])
    assert excinfo.value.code == "invalid_argument"


def test_two_table_keys_give_one_hint() -> None:
    with pytest.raises(CliError) as excinfo:
        check_page_specs([{"title": "P", "dataview_id": 1, "dataset_id": 2}])
    assert (excinfo.value.hint or "").count("name a page's own table") == 1


def test_a_page_on_the_boards_own_table_is_not_a_different_table() -> None:
    root = {"dataview_id": 7}
    assert own_table({"dataset": {"dataview_id": 7}}, root) is False
    assert own_table({"dataset": {"dataview_id": 8}}, root) is True
