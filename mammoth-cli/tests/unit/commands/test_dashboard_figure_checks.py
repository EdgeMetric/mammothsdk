"""Figures the board cannot draw, or that the server swapped, never read as clean."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.verify import with_verify
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_API = "mammoth.api.dashboards.DashboardsAPI."
_CANVAS_GET = _API + "canvas_get"
_CANVAS_SAVE = _API + "canvas_save"
_ADD_PAGES = _API + "add_pages"
_GENERATE = _API + "v3_generate"
_FIGURE_ADD = _API + "append_figure"

_PROFILES = [
    {"name": "Region", "type": "dimension"},
    {"name": "Quantity", "type": "measure"},
    {"name": "Sales", "type": "measure"},
]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _doc(tmp_path: Path, payload: dict[str, Any]) -> str:
    path = tmp_path / "in.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _canvas(pages: list[dict[str, Any]], **meta: Any) -> dict[str, Any]:
    return {
        "canvas": {"dataset": {"dataview_id": 42}, "pages": pages},
        "plan": {"hints": {"_profiles": _PROFILES}},
        "meta": {"sequence": 2, **meta},
    }


def test_canvas_save_with_an_unknown_column_is_not_verified(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    bad = {"kind": "hbar", "measure": "Nope", "dim": "Region", "agg": "sum"}
    fake_service.responses[_CANVAS_SAVE] = {"sequence": 2, "bake_job_id": 9}
    fake_service.responses[_CANVAS_GET] = _canvas([{"id": "p1", "added": [bad]}])
    body = {"body": {"params": {"canvas": {"pages": [{"id": "p1", "added": [bad]}]}}}}
    data, _ = dashboard_cmd.generated_dashboard(
        _inv(
            "dashboard.canvas.save",
            extra_args=["7"],
            input_file=_doc(tmp_path, body),
            yes=True,
            confirm="7",
        )
    )
    problem = data["figure_check"]["problems"][0]
    assert (problem["issue"], problem["column"]) == ("unknown_column", "Nope")
    verify = with_verify(data)["verify"]
    assert verify["verified"] is False
    assert verify["outcome"] == "failed"


def test_canvas_save_with_a_bake_error_is_not_verified(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CANVAS_SAVE] = {"sequence": 2}
    fake_service.responses[_CANVAS_GET] = _canvas(
        [{"id": "p1", "added": []}], bake_error="unknown column 'Nope'"
    )
    body = {"body": {"params": {"canvas": {"pages": []}}}}
    data, _ = dashboard_cmd.generated_dashboard(
        _inv(
            "dashboard.canvas.save",
            extra_args=["7"],
            input_file=_doc(tmp_path, body),
            yes=True,
            confirm="7",
        )
    )
    assert "unknown column 'Nope'" in data["figure_check"]["notes"][0]
    assert with_verify(data)["verify"]["outcome"] == "failed"


def test_canvas_save_of_a_good_figure_stays_verified(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    good = {"kind": "hbar", "measure": "Sales", "dim": "Region", "agg": "sum"}
    fake_service.responses[_CANVAS_SAVE] = {"sequence": 2}
    fake_service.responses[_CANVAS_GET] = _canvas([{"id": "p1", "added": [good]}])
    body = {"body": {"params": {"canvas": {"pages": [{"id": "p1", "added": [good]}]}}}}
    data, _ = dashboard_cmd.generated_dashboard(
        _inv(
            "dashboard.canvas.save",
            extra_args=["7"],
            input_file=_doc(tmp_path, body),
            yes=True,
            confirm="7",
        )
    )
    assert "figure_check" not in data
    assert with_verify(data)["verify"]["verified"] is True


def test_pages_add_with_a_swapped_measure_is_partial(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_ADD_PAGES] = {
        "added_page_ids": ["p2"],
        "message": "Built: Page added",
        "sequence": 2,
    }
    swapped = {"kind": "hbar", "title": "Revenue by region", "measure": "Quantity", "dim": "Region"}
    fake_service.responses[_CANVAS_GET] = _canvas([{"id": "p2", "added": [swapped]}])
    body = {
        "body": {
            "params": {
                "pages": [
                    {
                        "title": "Revenue",
                        "charts": [
                            {
                                "kind": "hbar",
                                "title": "Revenue by region",
                                "measure": "Revenue",
                                "dim": "Region",
                                "agg": "sum",
                            }
                        ],
                    }
                ]
            }
        }
    }
    data, _ = dashboard_cmd.generated_dashboard(
        _inv(
            "dashboard.pages.add",
            extra_args=["7"],
            input_file=_doc(tmp_path, body),
            yes=True,
            confirm="7",
        )
    )
    warning = data["substitution_check"]["problems"][0]
    assert warning["issue"] == "measure_substituted"
    assert warning["requested"]["measure"] == "Revenue"
    assert warning["used"]["measure"] == "Quantity"
    verify = with_verify(data)["verify"]
    assert (verify["verified"], verify["outcome"]) == (False, "partial")


def test_v3_generate_swapping_revenue_for_quantity_is_partial(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_GENERATE] = {"id": 7, "message": "done"}
    profiles = [{"name": "Region", "type": "dimension"}, {"name": "Quantity", "type": "measure"}]
    fake_service.responses[_CANVAS_GET] = {
        "canvas": {
            "dataset": {"dataview_id": 42},
            "pages": [{"id": "p1", "added": [{"kind": "hbar", "measure": "Quantity"}]}],
        },
        "plan": {"hints": {"_profiles": profiles}},
    }
    body = {"body": {"params": {"dataview_id": 42, "intent": "revenue by region"}}}
    data, _ = dashboard_cmd.generated_dashboard(
        _inv("dashboard.v3.generate", input_file=_doc(tmp_path, body), yes=True)
    )
    assert data["substitution_check"]["problems"][0]["used"]["measures"] == ["Quantity"]
    assert with_verify(data)["verify"]["outcome"] == "partial"


def test_a_couldnt_do_message_makes_generate_partial(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_GENERATE] = {"id": 7, "message": "Couldn't do: a pie of Region."}
    fake_service.responses[_CANVAS_GET] = _canvas([{"id": "p1", "added": []}])
    body = {"body": {"params": {"dataview_id": 42, "intent": "region mix"}}}
    data, _ = dashboard_cmd.generated_dashboard(
        _inv("dashboard.v3.generate", input_file=_doc(tmp_path, body), yes=True)
    )
    assert data["partial"] is True
    assert with_verify(data)["verify"]["outcome"] == "partial"


def _figure_doc(tmp_path: Path, figure: dict[str, Any]) -> str:
    return _doc(tmp_path, {"dataview_id": 42, "figure": figure})


def test_figure_add_refuses_sum_over_a_text_column(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CANVAS_GET] = _canvas([])
    figure = {"kind": "hbar", "measure": "Region", "dim": "Region", "agg": "sum"}
    with pytest.raises(CliError) as caught:
        dashboard_cmd.dashboard_figure_add(
            _inv("dashboard.figure.add", extra_args=["7"], input_file=_figure_doc(tmp_path, figure))
        )
    error = caught.value
    problem = error.details["problems"][0]
    assert (problem["issue"], problem["column_type"]) == ("non_numeric_measure", "TEXT")
    assert error.recovery_commands[0].startswith("mammoth view transform convert-type 42")
    assert _FIGURE_ADD not in [symbol for symbol, _ in fake_service.call_log]


def test_figure_add_allows_count_over_a_text_column(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CANVAS_GET] = _canvas([])
    fake_service.responses[_FIGURE_ADD] = {"bake_job_id": 3}
    figure = {"kind": "hbar", "measure": "Region", "dim": "Region", "agg": "count_distinct"}
    data, _ = dashboard_cmd.dashboard_figure_add(
        _inv("dashboard.figure.add", extra_args=["7"], input_file=_figure_doc(tmp_path, figure))
    )
    assert data == {"bake_job_id": 3}


def test_figure_add_refuses_an_unknown_column(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CANVAS_GET] = _canvas([])
    figure = {"kind": "hbar", "measure": "Nope", "dim": "Region", "agg": "sum"}
    with pytest.raises(CliError, match="unknown column 'Nope'"):
        dashboard_cmd.dashboard_figure_add(
            _inv("dashboard.figure.add", extra_args=["7"], input_file=_figure_doc(tmp_path, figure))
        )
