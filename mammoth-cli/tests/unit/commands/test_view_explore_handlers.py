"""``view explore-panel edit`` / ``export-image`` / ``add-to-dashboard`` through the real CLI.

The card rules themselves are checked in ``tests/unit/services/test_explore_card_edit_ops.py``.
Here the expected values are the wire calls the handlers must make: the panel written once as
``{**other panel keys, cards}``, the grouped-count read for a card's buckets (``explore`` with
the column's internal name and type), and the dashboard calls of the card menu's "Add to
dashboard" (a new board titled by the caller, or an existing one; a title already taken in the
project is refused as the web app does).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands.view_explore import _destination
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_FIND = "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview"
_PANEL_GET = "mammoth.api.dataviews.DataviewsAPI.explore_panel"
_PANEL_SET = "mammoth.api.dataviews.DataviewsAPI.set_explore_panel"
_EXPLORE = "mammoth.api.dataviews.DataviewsAPI.explore"
_SEQUENCE = "mammoth.api.pipeline.PipelineAPI.latest_task_sequence"
_SUGGEST = "mammoth.api.ai.AIAPI.get_suggestions"
_BOARDS = "mammoth.api.dashboards.DashboardsAPI.list"
_BLANK = "mammoth.api.dashboards.DashboardsAPI.create_blank"
_APPEND = "mammoth.api.dashboards.DashboardsAPI.append_figure"
_SVG = "mammoth.api.dashboards.DashboardsAPI.render_figure_svg"

_VIEW = {
    "id": 7,
    "metadata": [
        {"display_name": "Channel", "internal_name": "column_ch", "type": "TEXT"},
        {"display_name": "Quantity", "internal_name": "column_qt", "type": "NUMERIC"},
    ],
}
_ARGS = ["--project", "180", "--output", "json", "--no-input"]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def service(fake_service: FakeMammothService) -> FakeMammothService:
    fake_service.responses[_GET] = _VIEW
    fake_service.responses[_FIND] = 9
    fake_service.responses[_PANEL_GET] = {"cards": [], "layout": "grid"}
    fake_service.responses[_PANEL_SET] = {"ok": True}
    return fake_service


def _run(args: list[str], payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    argv = [*args, *_ARGS]
    if payload is not None:
        argv += ["--input", json.dumps(payload)]
    result = make_runner().invoke(argv)
    start = result.output.find("{")
    assert start != -1, result.output
    return result.exit_code, json.loads(result.output[start:])


def _calls(service: FakeMammothService, symbol: str) -> list[dict[str, Any]]:
    return [kwargs for name, kwargs in service.call_log if name == symbol]


def _text_card() -> dict[str, Any]:
    return {
        "colId": "column_ch",
        "renderType": "list",
        "view": "list",
        "sortBy": [["unformatted", "DESC"]],
        "activeValues": [],
    }


# ── panel edit ──


def test_edit_writes_the_changed_cards_once_and_keeps_the_panels_other_keys(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = {"cards": [_text_card()], "layout": "grid"}
    code, out = _run(
        ["view", "explore-panel", "edit", "7"],
        {"edits": [{"op": "sort", "card": "Channel", "by": "value", "direction": "asc"}]},
    )
    assert code == 0, out
    (written,) = _calls(service, _PANEL_SET)
    assert written["dataset_id"] == 9
    assert written["dataview_id"] == 7
    assert written["project_id"] == 180
    assert written["panel"]["layout"] == "grid"
    assert [c["sortBy"] for c in written["panel"]["cards"]] == [[["value", "ASC"]]]
    # the result is the write's answer plus the panel read back
    assert out["data"]["ok"] is True
    assert out["data"]["panel"] == {"cards": [_text_card()], "layout": "grid"}


def test_edit_reads_the_older_items_spelling_and_writes_it_back_as_cards(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = {"items": [_text_card()], "layout": "grid"}
    code, _ = _run(
        ["view", "explore-panel", "edit", "7"],
        {"edits": [{"op": "view", "card": "Channel", "view": "donut"}]},
    )
    assert code == 0
    (written,) = _calls(service, _PANEL_SET)
    assert "items" not in written["panel"]
    assert written["panel"]["cards"][0]["view"] == "donut"


def test_edit_of_a_view_with_no_saved_panel_cannot_edit_a_closed_card(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = None
    code, out = _run(
        ["view", "explore-panel", "edit", "7"],
        {"edits": [{"op": "remove", "card": "Channel"}]},
    )
    assert code == 2
    assert out["error"]["message"] == "No card is open for 'Channel'. Open cards: none."
    assert _calls(service, _PANEL_SET) == []


def test_a_filter_reads_the_values_the_card_lists_for_that_column_only(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = {"cards": [_text_card()]}
    service.responses[_EXPLORE] = {"data": [{"group_0": "Amazon"}, {"group_0": "Shop"}]}
    code, _ = _run(
        ["view", "explore-panel", "edit", "7"],
        {"edits": [{"op": "filter", "card": "Channel", "values": ["Amazon"]}]},
    )
    assert code == 0
    (read,) = _calls(service, _EXPLORE)
    assert read == {
        "dataset_id": 9,
        "dataview_id": 7,
        "project_id": 180,
        "column": "column_ch",
        "column_type": "TEXT",
        "condition": {"column_ch": {"IN_LIST": {"VALUE": ["Amazon"]}}},
        "limit": 1,
    }
    (written,) = _calls(service, _PANEL_SET)
    assert written["panel"]["cards"][0]["condition"] == {
        "column_ch": {"IN_LIST": {"VALUE": ["Amazon"]}}
    }


def test_a_value_the_view_does_not_have_is_refused_and_nothing_is_written(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = {"cards": [_text_card()]}
    service.responses[_EXPLORE] = {"data": []}
    code, out = _run(
        ["view", "explore-panel", "edit", "7"],
        {"edits": [{"op": "filter", "card": "Channel", "values": ["Nope"]}]},
    )
    assert code == 2
    assert out["error"]["code"] == "invalid_argument"
    assert _calls(service, _PANEL_SET) == []


def test_ask_sends_the_question_at_the_next_task_step_and_keeps_an_understood_reading(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = {"cards": [_text_card()]}
    service.responses[_SEQUENCE] = 4
    service.responses[_SUGGEST] = {
        "response": {
            "status_code": "AC01",
            "result": {"column_ch": {"IS_EMPTY": True}, "FILTER_TYPE": "CONDITION"},
        }
    }
    code, _ = _run(
        ["view", "explore-panel", "edit", "7"],
        {"edits": [{"op": "ask", "question": "missing channel"}]},
    )
    assert code == 0
    (asked,) = _calls(service, _SUGGEST)
    assert asked == {
        "suggestion_type": "add_condition",
        "params": {
            "sequence_number": 5,
            "prompt": "missing channel",
            "origin": "functions_panel",
        },
        "dataset_id": 9,
        "dataview_id": 7,
    }
    (written,) = _calls(service, _PANEL_SET)
    ask_card = written["panel"]["cards"][0]
    assert ask_card["colId"] == "__ask_1"
    assert ask_card["condition"] == {"column_ch": {"IS_EMPTY": True}}


@pytest.mark.parametrize(
    "reply",
    [
        {"response": {"status_code": "AC09", "result": {"column_ch": {"IS_EMPTY": True}}}},
        {"status_code": "AC09"},
        "nope",
    ],
)
def test_an_ask_the_service_did_not_understand_is_refused(
    service: FakeMammothService, reply: Any
) -> None:
    service.responses[_PANEL_GET] = {"cards": [_text_card()]}
    service.responses[_SEQUENCE] = 0
    service.responses[_SUGGEST] = reply
    code, out = _run(
        ["view", "explore-panel", "edit", "7"],
        {"edits": [{"op": "ask", "question": "gibberish"}]},
    )
    assert code == 2
    assert out["error"]["message"].startswith("The question could not be read as a condition")
    assert _calls(service, _PANEL_SET) == []


def test_edit_needs_the_edits_field(service: FakeMammothService) -> None:
    code, out = _run(["view", "explore-panel", "edit", "7"], {})
    assert code == 2
    assert "edits" in json.dumps(out)


# ── export-image ──


def test_export_image_draws_a_text_card_as_a_table_of_its_grouped_rows(
    service: FakeMammothService, tmp_path: Path
) -> None:
    service.responses[_PANEL_GET] = {"cards": [_text_card()]}
    service.responses[_EXPLORE] = {"data": [{"group_0": "Amazon", "agg_0": 3}]}
    service.responses[_SVG] = "<svg>card</svg>"
    target = tmp_path / "card.svg"
    code, out = _run(
        ["view", "explore-panel", "export-image", "7"],
        {"card": "Channel", "output_path": str(target), "style_id": "s1"},
    )
    assert code == 0, out
    assert target.read_text(encoding="utf-8") == "<svg>card</svg>"
    assert out["data"] == {"output_path": str(target)}
    (spec_call,) = _calls(service, _SVG)
    assert spec_call["style_id"] == "s1"
    assert spec_call["spec"]["chart"] == "table"
    assert spec_call["spec"]["title"] == "Count by Channel"
    assert spec_call["spec"]["rows"] == [{"cells": ["Amazon", 3]}]


def test_export_image_reads_a_measured_card_with_its_metric(
    service: FakeMammothService, tmp_path: Path
) -> None:
    card = {
        "colId": "column_ch",
        "renderType": "list",
        "view": "list",
        "aggregation": {"type": "SUM", "targetColId": "column_qt"},
    }
    service.responses[_PANEL_GET] = {"cards": [card]}
    service.responses[_EXPLORE] = {"data": [{"group_0": "Amazon", "agg_1": 30}]}
    service.responses[_SVG] = "<svg/>"
    code, _ = _run(
        ["view", "explore-panel", "export-image", "7"],
        {"card": "Channel", "output_path": str(tmp_path / "m.svg")},
    )
    assert code == 0
    (read,) = _calls(service, _EXPLORE)
    assert read["metric"] == {"column": "column_qt", "function": "SUM"}
    assert _calls(service, _SVG)[0]["spec"]["title"] == "Sum of Quantity by Channel"


def test_export_image_output_path_must_be_text_before_any_request(
    service: FakeMammothService,
) -> None:
    """The manifest's input contract refuses it first, so the handler's own check never runs."""
    code, out = _run(
        ["view", "explore-panel", "export-image", "7"], {"card": "Channel", "output_path": ["a"]}
    )
    assert code == 2
    assert out["error"]["code"] == "invalid_input_field_type"
    assert "must be a string" in out["error"]["message"]
    assert service.call_log == []


def test_export_image_of_a_card_that_is_not_open_writes_no_file(
    service: FakeMammothService, tmp_path: Path
) -> None:
    target = tmp_path / "x.svg"
    code, out = _run(
        ["view", "explore-panel", "export-image", "7"],
        {"card": "Channel", "output_path": str(target)},
    )
    assert code == 2
    assert out["error"]["message"] == "No card is open for 'Channel'. Open cards: none."
    assert not target.exists()


# ── add-to-dashboard ──

_ONE_OF = 'Give "dashboard_id" (an existing board) or "new_dashboard_title" (a new one).'
_PAGE = (
    'A "page" ({"id": ...} or {"new_title": ...}) goes with "dashboard_id"; a new board puts '
    "the tile on its first page."
)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"card": "Channel"}, _ONE_OF),
        ({"card": "Channel", "dashboard_id": 3, "new_dashboard_title": "T"}, _ONE_OF),
        ({"card": "Channel", "new_dashboard_title": "T", "page": {"id": "p1"}}, _PAGE),
        ({"card": "Channel", "dashboard_id": 3, "page": {"id": "p", "new_title": "q"}}, _PAGE),
        (
            {"card": "Channel", "new_dashboard_title": "  "},
            '"new_dashboard_title" must be a non-empty string.',
        ),
    ],
)
def test_the_destination_must_name_one_board_and_a_fitting_page(
    service: FakeMammothService, payload: dict[str, Any], message: str
) -> None:
    code, out = _run(["view", "explore-panel", "add-to-dashboard", "7"], payload)
    assert code == 2, out
    assert out["error"]["message"] == message
    assert _calls(service, _APPEND) == []
    assert _calls(service, _BLANK) == []


def test_a_text_card_goes_to_an_existing_board_page_as_a_figure(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = {"cards": [_text_card()]}
    service.responses[_EXPLORE] = {"data": [{"group_0": "Amazon"}], "row_count": 4}
    service.responses[_APPEND] = {"figure_id": "f1"}
    code, out = _run(
        ["view", "explore-panel", "add-to-dashboard", "7"],
        {"card": "Channel", "dashboard_id": 3, "page": {"id": "p1"}},
    )
    assert code == 0, out
    (read,) = _calls(service, _EXPLORE)
    assert read["limit"] == 1  # only the number of values is needed
    (appended,) = _calls(service, _APPEND)
    assert appended["dashboard_id"] == 3
    assert appended["dataview_id"] == 7
    assert appended["page_id"] == "p1"
    assert "page_new_title" not in appended
    assert appended["figure"]["title"] == "Count by Channel"
    assert _calls(service, _BLANK) == []
    assert out["data"]["dashboard_id"] == 3
    assert out["data"]["created_dashboard"] is False
    assert out["data"]["added"] == {"figure_id": "f1"}


def test_a_new_page_title_is_sent_as_page_new_title(service: FakeMammothService) -> None:
    service.responses[_PANEL_GET] = {"cards": [_text_card()]}
    service.responses[_EXPLORE] = {"data": [], "row_count": 0}
    service.responses[_APPEND] = {}
    _run(
        ["view", "explore-panel", "add-to-dashboard", "7"],
        {"card": "Channel", "dashboard_id": 3, "page": {"new_title": "Sales"}},
    )
    (appended,) = _calls(service, _APPEND)
    assert appended["page_new_title"] == "Sales"
    assert "page_id" not in appended


def test_a_new_board_is_created_for_the_view_with_the_trimmed_title(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = {"cards": [_text_card()]}
    service.responses[_EXPLORE] = {"data": [], "row_count": 0}
    service.responses[_BOARDS] = [{"title": "Other"}]
    service.responses[_BLANK] = {"id": 41}
    service.responses[_APPEND] = {}
    code, out = _run(
        ["view", "explore-panel", "add-to-dashboard", "7"],
        {"card": "Channel", "new_dashboard_title": "  By channel "},
    )
    assert code == 0, out
    assert _calls(service, _BLANK) == [{"params": {"dataview_id": 7, "title": "By channel"}}]
    assert _calls(service, _APPEND)[0]["dashboard_id"] == 41
    assert out["data"]["created_dashboard"] is True


def test_a_title_the_project_already_has_is_refused_ignoring_case_and_nothing_is_created(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = {"cards": [_text_card()]}
    service.responses[_EXPLORE] = {"data": [], "row_count": 0}
    service.responses[_BOARDS] = [{"title": " BY CHANNEL "}]
    code, out = _run(
        ["view", "explore-panel", "add-to-dashboard", "7"],
        {"card": "Channel", "new_dashboard_title": "by channel"},
    )
    assert code == 2
    assert out["error"]["message"] == (
        "A dashboard titled 'by channel' already exists in this project. Pick another title."
    )
    assert _calls(service, _BLANK) == []
    assert _calls(service, _APPEND) == []


@pytest.mark.parametrize("board", ["3", True, 1.5])
def test_a_dashboard_id_must_be_an_integer(board: Any) -> None:
    with pytest.raises(CliError) as refused:
        _destination({"dashboard_id": board})
    assert refused.value.message == '"dashboard_id" must be a dashboard id.'


def test_a_destination_is_the_board_title_trimmed_or_the_id_and_page() -> None:
    assert _destination({"new_dashboard_title": " T "}) == (None, "T", {})
    assert _destination({"dashboard_id": 3, "page": {"new_title": "P"}}) == (
        3,
        None,
        {"new_title": "P"},
    )


def _number_card(level: Any) -> dict[str, Any]:
    card: dict[str, Any] = {
        "colId": "column_qt",
        "renderType": "chart",
        "view": "columns",
        "charts": [{"queryIndex": 0, "level": level, "activeValues": []}],
    }
    if level != "AUTO":
        card["granularity"] = {"id": level, "name": "10"}
    return card


def test_a_number_card_is_placed_with_the_buckets_read_at_its_fixed_level(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = {"cards": [_number_card(1)]}
    service.responses[_EXPLORE] = {"data": [{"group_0": 0}, {"group_0": 10}, {"group_0": None}]}
    service.responses[_APPEND] = {}
    code, out = _run(
        ["view", "explore-panel", "add-to-dashboard", "7"],
        {"card": "Quantity", "dashboard_id": 3},
    )
    assert code == 0, out
    (read,) = _calls(service, _EXPLORE)
    assert (read["column"], read["column_type"], read["level"]) == ("column_qt", "NUMERIC", 1)
    assert _calls(service, _APPEND)[0]["figure"]["title"] == "Count by Quantity"


def test_a_number_card_at_auto_level_with_no_visible_width_asks_to_set_one(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = {"cards": [_number_card("AUTO")]}
    service.responses[_EXPLORE] = {"data": [{"group_0": 5}]}  # one bucket shows no width
    code, out = _run(
        ["view", "explore-panel", "add-to-dashboard", "7"],
        {"card": "Quantity", "dashboard_id": 3},
    )
    assert code == 2
    assert out["error"]["message"].startswith(
        "The card's level is AUTO and its values do not show one. Set it first:"
    )
    assert _calls(service, _APPEND) == []


def test_a_number_card_at_auto_level_uses_the_width_its_buckets_show(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = {"cards": [_number_card("AUTO")]}
    service.responses[_EXPLORE] = {"data": [{"group_0": 0}, {"group_0": 10}, {"group_0": 20}]}
    service.responses[_APPEND] = {}
    code, _ = _run(
        ["view", "explore-panel", "add-to-dashboard", "7"],
        {"card": "Quantity", "dashboard_id": 3},
    )
    assert code == 0
    levels = [c.get("level") for c in _calls(service, _EXPLORE)]
    assert levels == ["AUTO", 1]  # first to learn the width, then at it
