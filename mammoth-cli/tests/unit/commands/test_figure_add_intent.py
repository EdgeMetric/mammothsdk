"""``dashboard figure add`` accepts ``{"intent": "..."}``, as the bundled skill says.

An intent goes through the figure-intent route (the server picks the chart);
an exact ``figure`` spec still goes through the append route. Both at once, or
neither, is a usage error that names both shapes and ``figure-intent``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.strict import validate_input_fields
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_API = "mammoth.api.dashboards.DashboardsAPI."
_FIGURE_INTENT = _API + "figure_intent"
_FIGURE_ADD = _API + "append_figure"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _add(tmp_path: Path, payload: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    path = tmp_path / "in.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return dashboard_cmd.dashboard_figure_add(
        Invocation(command_id="dashboard.figure.add", extra_args=["7"], input_file=str(path))
    )


def test_the_contract_admits_intent_and_kind() -> None:
    validate_input_fields("dashboard.figure.add", {"intent": "Revenue by region"})
    validate_input_fields("dashboard.figure.add", {"intent": "Revenue by region", "kind": "hbar"})


def test_an_intent_goes_through_the_figure_intent_route(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_FIGURE_INTENT] = {
        "kind": "hbar",
        "added": {"id": "f1"},
        "intent_applied": True,
    }
    data, _ = _add(tmp_path, {"intent": "Revenue by region", "kind": "hbar"})
    symbols = [symbol for symbol, _ in fake_service.call_log]
    assert _FIGURE_INTENT in symbols and _FIGURE_ADD not in symbols
    kwargs = dict(fake_service.call_log)[_FIGURE_INTENT]
    assert kwargs == {
        "dashboard_id": 7,
        "body": {"params": {"intent": "Revenue by region", "kind": "hbar"}},
    }
    assert data["intent_applied"] is True
    assert data["route"] == "figure-intent"


def test_an_exact_figure_still_goes_through_the_append_route(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_API + "canvas_get"] = {"canvas": {"pages": []}, "meta": {}}
    fake_service.responses[_FIGURE_ADD] = {"bake_job_id": 3}
    figure = {"kind": "hbar", "measure": "Sales", "dim": "Region", "agg": "sum"}
    _add(tmp_path, {"dataview_id": 42, "figure": figure})
    symbols = [symbol for symbol, _ in fake_service.call_log]
    assert _FIGURE_ADD in symbols and _FIGURE_INTENT not in symbols


@pytest.mark.parametrize(
    "payload",
    [
        {"intent": "Revenue by region", "figure": {"kind": "hbar"}, "dataview_id": 1},
        {"dataview_id": 1},
        {},
    ],
)
def test_both_or_neither_is_a_usage_error_naming_both_shapes(
    fake_service: FakeMammothService, tmp_path: Path, payload: dict[str, Any]
) -> None:
    with pytest.raises(CliError) as caught:
        _add(tmp_path, payload)
    error = caught.value
    assert error.exit_status == 2
    assert "intent" in (error.hint or "") and "figure" in (error.hint or "")
    assert "figure-intent" in (error.hint or "")
    assert fake_service.call_log == []


def test_a_figure_without_a_view_still_needs_dataview_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError, match="dataview_id"):
        _add(tmp_path, {"figure": {"kind": "hbar"}})
