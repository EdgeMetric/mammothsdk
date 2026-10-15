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


# -- workbook import and assess wait for their job -----------------------------

_IMPORT = _API + "import_workbook"
_ASSESS_TWB = _API + "assess_twb"


def test_import_workbook_waits_and_says_the_rows_are_synthetic(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    book = tmp_path / "book.twbx"
    book.write_bytes(b"x")
    fake_service.responses[_IMPORT] = {"job_id": "j1"}
    fake_service.job_result = {"dataview_id": 5, "data_source": "fitted_sample"}
    data, _ = dashboard_cmd.dashboard_import_workbook(
        _inv(
            "dashboard.import-workbook",
            extra_args=[str(book)],
            project=3,
            yes=True,
            confirm="3",
        )
    )
    assert fake_service.wait_log == [{"job_id": "j1"}]
    assert data["dataview_id"] == 5
    assert data["synthetic_data"] is True
    assert "synthetic" in data["data_note"]


def test_assess_twb_surfaces_not_a_workbook(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    junk = tmp_path / "junk.twb"
    junk.write_bytes(b"not xml")
    fake_service.responses[_ASSESS_TWB] = {"job_id": "j2"}
    fake_service.job_result = {"rejected": {"reason": "not_a_workbook"}, "source": {}}
    with pytest.raises(CliError) as caught:
        dashboard_cmd.dashboard_assess_twb(_inv("dashboard.assess-twb", extra_args=[str(junk)]))
    assert caught.value.code == "not_a_workbook"
    assert fake_service.wait_log == [{"job_id": "j2"}]


def _twbx_with_rows(path: Path, rows: int) -> None:
    import zipfile

    with zipfile.ZipFile(path, "w") as bundle:
        bundle.writestr("a.twb", "<workbook/>")
        csv = "day,events\n" + "".join(f"2026-10-{i + 1:02d},{i}\n" for i in range(rows))
        bundle.writestr("Data/data.csv", csv)


def test_import_workbook_with_synthetic_rows_is_partial_not_settled(
    isolated_cli_config: Path, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """Bug bash 2026-10-15: 8 real rows became 4000 made-up ones and verify said settled."""
    import json

    from mammoth_cli.testing import login_default_profile, make_runner

    login_default_profile()
    book = tmp_path / "b.twbx"
    _twbx_with_rows(book, 8)
    fake_service.responses[_IMPORT] = {"job_id": "j1"}
    fake_service.job_result = {
        "dataview_id": 5,
        "data_source": "fitted_sample",
        "row_count": 4000,
    }
    result = make_runner().invoke(
        [
            "dashboard", "import-workbook", str(book), "--project", "3", "--yes",
            "--confirm", "3", "--output", "json", "--no-input",
        ]
    )  # fmt: skip
    assert result.exit_code == 3, result.output
    data = json.loads(result.output)["data"]
    assert data["verify"]["outcome"] == "partial"
    assert data["verify"]["verified"] is False
    warning = " ".join(data["warnings"])
    assert "synthetic" in warning and "8" in warning and "4000" in warning
    assert any("file upload" in step for step in data["next_steps"])
    assert data["verify"]["warnings"] == data["warnings"]
