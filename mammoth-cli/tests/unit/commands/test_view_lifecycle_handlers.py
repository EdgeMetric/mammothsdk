"""Restore, trash, impact, analyze, optimize, compare, rename and the Explore panel of a view.

Expected values are the SDK calls each command must make (argument names are the SDK's own,
``mammoth/api/dataviews.py``), the rules in each handler's docstring (an unconstrained patch is
refused, ``analyze`` takes several ids and keeps one id's failure as an entry), and the manifest
(``optimize`` needs a yes).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_API = "mammoth.api.dataviews.DataviewsAPI."
_GET = _API + "get"
_RESTORE = _API + "restore"
_TRASH = _API + "trash"
_UPDATE = _API + "update"
_IMPACT = _API + "delete_impact"
_ANALYSIS = _API + "analysis"
_OPTIMIZE = _API + "optimize"
_COMPARE = _API + "compare"
_PANEL_GET = _API + "explore_panel"
_PANEL_SET = _API + "set_explore_panel"
_FIND = "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview"
_ITEMS = "mammoth.api.pipeline.PipelineAPI.items_all"
_DATASET = "mammoth.api.datasets.DatasetsAPI.get"
_ARGS = ["--project", "180", "--output", "json", "--no-input"]

_VIEW = {
    "id": 7,
    "name": "Sales",
    "metadata": [
        {"display_name": "Channel", "internal_name": "column_ch", "type": "TEXT"},
        {"display_name": "Quantity", "internal_name": "column_qt", "type": "NUMERIC"},
    ],
}


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def service(fake_service: FakeMammothService) -> FakeMammothService:
    fake_service.responses[_FIND] = 9
    fake_service.responses[_GET] = _VIEW
    return fake_service


def _run(
    args: list[str], payload: dict[str, Any] | None = None, *extra: str
) -> tuple[int, dict[str, Any]]:
    argv = [*args, *_ARGS, *extra]
    if payload is not None:
        argv += ["--input", json.dumps(payload)]
    result = make_runner().invoke(argv)
    start = result.output.find("{")
    assert start != -1, result.output
    return result.exit_code, json.loads(result.output[start:])


def _calls(service: FakeMammothService, symbol: str) -> list[dict[str, Any]]:
    return [kwargs for name, kwargs in service.call_log if name == symbol]


# ── restore / trash ──


@pytest.mark.parametrize(("verb", "symbol"), [("restore", _RESTORE), ("trash", _TRASH)])
def test_restore_and_trash_find_the_parent_dataset_and_pass_the_view(
    service: FakeMammothService, verb: str, symbol: str
) -> None:
    service.responses[symbol] = {"status": "ok"}
    code, out = _run(["view", verb, "7", "9"])
    assert code == 0, out
    assert _calls(service, symbol) == [{"dataset_id": 9, "dataview_id": 7, "project_id": 180}]
    assert out["data"]["status"] == "ok"


def test_a_given_dataset_id_is_used_without_a_lookup(service: FakeMammothService) -> None:
    service.responses[_TRASH] = {}
    code, _ = _run(["view", "trash", "7", "33"])
    assert code == 0
    assert _calls(service, _FIND) == []
    assert _calls(service, _TRASH)[0]["dataset_id"] == 33


@pytest.mark.parametrize(("verb", "symbol"), [("restore", _RESTORE), ("trash", _TRASH)])
def test_a_write_with_no_known_parent_dataset_does_not_guess_one(
    service: FakeMammothService, verb: str, symbol: str
) -> None:
    code, out = _run(["view", verb, "7"])
    assert code == 2
    assert out["error"]["code"] == "missing_argument"
    assert _calls(service, symbol) == []


# ── impact ──


def test_impact_of_a_whole_view_needs_only_the_scope(service: FakeMammothService) -> None:
    service.responses[_IMPACT] = {"affected": []}
    code, out = _run(["view", "impact", "7"], {"scope": "view"})
    assert code == 0, out
    assert _calls(service, _IMPACT) == [
        {"dataview_id": 7, "project_id": 180, "scope": "view", "dataset_id": 9}
    ]


def test_impact_of_a_task_forwards_the_task_id(service: FakeMammothService) -> None:
    service.responses[_IMPACT] = {}
    _run(["view", "impact", "7"], {"scope": "task", "task_id": 12})
    assert _calls(service, _IMPACT)[0]["task_id"] == 12


def test_impact_needs_a_scope(service: FakeMammothService) -> None:
    code, out = _run(["view", "impact", "7"], {})
    assert code == 2
    assert "scope" in out["error"]["message"]
    assert _calls(service, _IMPACT) == []


# ── analyze ──

_STEPS = {
    "items": [
        {"item_type": "task"},
        {"item_type": "task"},
        {"item_type": "export"},
    ]
}


def _analysis_world(service: FakeMammothService, *, missing: tuple[int, ...] = ()) -> None:
    """Views 7 and 8 live in datasets 9 and 10; ``missing`` views are unknown to the project."""
    parents = {7: 9, 8: 10}

    def find(log: list[tuple[str, dict[str, Any]]]) -> int:
        view_id = log[-1][1]["dataview_id"]
        if view_id in missing:
            raise CliError(code="resource_not_found", message=f"no view {view_id}", exit_status=5)
        return parents[view_id]

    service.responses[_FIND] = find
    service.responses[_ANALYSIS] = {"findings": [{"rule": "drop_unused"}]}
    service.responses[_ITEMS] = _STEPS
    service.responses[_DATASET] = lambda log: {"id": log[-1][1]["dataset_id"], "name": "Orders"}


def test_analyze_of_one_view_carries_its_findings_and_step_count(
    service: FakeMammothService,
) -> None:
    _analysis_world(service)
    code, out = _run(["view", "analyze", "7"])
    assert code == 0, out
    data = out["data"]
    assert data["findings"] == [{"rule": "drop_unused"}]
    assert data["steps"] == 2  # an export is not a pipeline step
    assert data["view"]["dataset_id"] == 9 or data["view"]["dataset"]["id"] == 9


def test_analyze_of_several_views_reads_each_dataset_once_and_lists_both(
    service: FakeMammothService,
) -> None:
    _analysis_world(service)
    service.responses[_FIND] = lambda log: {7: 9, 8: 9}[log[-1][1]["dataview_id"]]
    code, out = _run(["view", "analyze", "7,8"])
    assert code == 0, out
    data = out["data"]
    assert data["requested"] == 2
    assert [a["view_id"] for a in data["analyses"]] == [7, 8]
    assert data["errors"] == []
    assert len(_calls(service, _DATASET)) == 1  # both views are in dataset 9


def test_one_view_failing_among_several_is_an_error_entry_not_a_failed_call(
    service: FakeMammothService,
) -> None:
    _analysis_world(service, missing=(8,))
    code, out = _run(["view", "analyze", "7,8"])
    assert code == 0, out
    data = out["data"]
    assert [a["view_id"] for a in data["analyses"]] == [7]
    assert data["errors"] == [{"view_id": 8, "code": "resource_not_found", "message": "no view 8"}]


def test_a_single_view_failing_fails_the_command(service: FakeMammothService) -> None:
    _analysis_world(service, missing=(7,))
    code, out = _run(["view", "analyze", "7"])
    assert code == 5
    assert out["error"]["code"] == "resource_not_found"


def test_a_failed_read_of_a_found_view_is_that_ids_error(service: FakeMammothService) -> None:
    _analysis_world(service)
    service.responses[_ANALYSIS] = CliError(code="api_error", message="boom", exit_status=1)
    code, out = _run(["view", "analyze", "7"])
    assert code == 1
    assert out["error"]["message"] == "boom"


def test_analyze_needs_a_view_id() -> None:
    code, out = _run(["view", "analyze"])
    assert code == 2


def test_analyze_refuses_an_id_that_is_not_an_integer(service: FakeMammothService) -> None:
    code, out = _run(["view", "analyze", "7,x"])
    assert code == 2
    assert out["error"]["message"] == (
        "The view id argument '7,x' is not an integer or a comma-separated list."
    )


# ── optimize ──


def test_optimize_without_a_yes_changes_nothing(service: FakeMammothService) -> None:
    code, out = _run(["view", "optimize", "7"])
    assert code != 0
    assert _calls(service, _OPTIMIZE) == []


def test_optimize_applies_the_named_rules_and_waits_for_the_rerun_it_queued(
    service: FakeMammothService,
) -> None:
    service.responses[_OPTIMIZE] = {"applied": ["drop_unused"], "job_id": 55}
    service.job_result = {"state": "done"}
    code, out = _run(["view", "optimize", "7"], {"apply_rules": ["drop_unused"]}, "--yes")
    assert code == 0, out
    assert _calls(service, _OPTIMIZE) == [
        {"dataview_id": 7, "project_id": 180, "apply_rules": ["drop_unused"], "dataset_id": 9}
    ]
    assert service.wait_log[0] == {"job_id": 55}  # the rerun the server queued


@pytest.mark.xfail(
    strict=True,
    raises=KeyError,
    reason=(
        "BUG (suspected): the handler's result keeps job_id after its own wait, so the verify "
        "step polls it again and replaces the whole result with the job's payload; the "
        "documented applied/skipped counts and job_state are lost"
    ),
)
def test_optimize_result_keeps_what_the_server_applied_and_the_job_state(
    service: FakeMammothService,
) -> None:
    service.responses[_OPTIMIZE] = {"applied": ["drop_unused"], "job_id": 55}
    service.job_result = {"state": "done"}
    _, out = _run(["view", "optimize", "7"], None, "--yes")
    assert out["data"]["applied"] == ["drop_unused"]
    assert out["data"]["job_state"] == "success"


def test_optimize_that_queued_no_job_reports_no_job_state(service: FakeMammothService) -> None:
    service.responses[_OPTIMIZE] = {"applied": [], "job_id": None}
    code, out = _run(["view", "optimize", "7"], None, "--yes")
    assert code == 0
    assert "job_state" not in out["data"]
    assert "apply_rules" not in _calls(service, _OPTIMIZE)[0]


# ── compare ──


def test_compare_sends_the_pairs_and_needs_no_project(service: FakeMammothService) -> None:
    service.responses[_COMPARE] = {"results": []}
    pairs = [[7, 8]]
    code, out = _run(["view", "compare"], {"pairs": pairs})
    assert code == 0, out
    assert _calls(service, _COMPARE) == [{"pairs": pairs}]


def test_compare_needs_pairs(service: FakeMammothService) -> None:
    code, out = _run(["view", "compare"], {})
    assert code == 2
    assert "pairs" in out["error"]["message"]


# ── update (rename) ──


def test_update_renames_the_view_with_one_replace_on_name(service: FakeMammothService) -> None:
    service.responses[_UPDATE] = {"id": 7}
    code, out = _run(["view", "update", "7", "9"], {"name": "  Revenue "})
    assert code == 0, out
    assert _calls(service, _UPDATE) == [
        {
            "dataset_id": 9,
            "dataview_id": 7,
            "patch_data": [{"op": "replace", "path": "name", "value": "Revenue"}],
            "project_id": 180,
        }
    ]


@pytest.mark.parametrize(
    "payload", [{"name": "  "}, {"name": "X", "color": "red"}, {"color": "red"}]
)
def test_any_other_patch_is_refused_and_nothing_is_sent(
    service: FakeMammothService, payload: dict[str, Any]
) -> None:
    code, out = _run(["view", "update", "7", "9"], payload)
    assert code == 2
    assert _calls(service, _UPDATE) == []


def test_a_blank_name_is_named_as_an_untyped_patch(service: FakeMammothService) -> None:
    code, out = _run(["view", "update", "7", "9"], {"name": " "})
    assert out["error"]["message"] == (
        "Raw dataview patch operations are not available through the CLI."
    )
    assert out["error"]["code"] == "unsupported_contract"


def test_a_field_the_command_does_not_take_is_refused_by_name(
    service: FakeMammothService,
) -> None:
    code, out = _run(["view", "update", "7", "9"], {"name": "X", "extra": 1})
    assert out["error"]["message"] == (
        "Unknown input field(s) for 'view update': extra. Accepted fields: dataset_id, name."
    )


# ── explore panel get / set ──


def test_panel_get_returns_what_the_view_saved(service: FakeMammothService) -> None:
    service.responses[_PANEL_GET] = {"cards": [{"colId": "column_ch"}]}
    code, out = _run(["view", "explore-panel", "get", "7"])
    assert code == 0
    assert out["data"] == {"cards": [{"colId": "column_ch"}]}
    assert _calls(service, _PANEL_GET) == [{"dataset_id": 9, "dataview_id": 7, "project_id": 180}]


def test_panel_set_with_cards_writes_them_as_given_and_returns_the_panel_read_back(
    service: FakeMammothService,
) -> None:
    panel = {"cards": [{"colId": "column_ch"}], "height": 300}
    service.responses[_PANEL_GET] = panel
    service.responses[_PANEL_SET] = {"saved": True}
    code, out = _run(["view", "explore-panel", "set", "7"], {"panel": panel})
    assert code == 0, out
    (written,) = _calls(service, _PANEL_SET)
    assert written["panel"] == panel
    assert (written["dataset_id"], written["dataview_id"], written["project_id"]) == (9, 7, 180)
    assert out["data"]["saved"] is True
    assert out["data"]["panel"] == panel


def test_panel_set_with_columns_adds_a_default_card_for_each_column_after_the_saved_ones(
    service: FakeMammothService,
) -> None:
    saved: dict[str, Any] = {"cards": [{"colId": "column_ch", "renderType": "list"}], "height": 300}
    service.responses[_PANEL_GET] = saved
    service.responses[_PANEL_SET] = {}
    code, out = _run(
        ["view", "explore-panel", "set", "7"], {"panel": {"columns": ["Channel", "Quantity"]}}
    )
    assert code == 0, out
    (written,) = _calls(service, _PANEL_SET)
    cards = written["panel"]["cards"]
    assert [c["colId"] for c in cards] == ["column_ch", "column_qt"]
    assert cards[0] == saved["cards"][0]  # a column that has a card keeps it
    assert cards[1]["renderType"] == "chart"  # a NUMERIC column opens as a chart
    assert written["panel"]["height"] == 300


def test_panel_set_refuses_a_panel_the_web_app_would_show_empty(
    service: FakeMammothService,
) -> None:
    service.responses[_PANEL_GET] = {}
    code, out = _run(["view", "explore-panel", "set", "7"], {"panel": {"height": 1}})
    assert code == 2
    assert out["error"]["message"] == (
        'The panel has no "cards" list, so the web app would show "No cards yet" '
        "(keys given: height)."
    )
    assert _calls(service, _PANEL_SET) == []
