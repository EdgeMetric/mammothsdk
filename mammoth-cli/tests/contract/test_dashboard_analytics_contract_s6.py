"""Independent C2/S6 controls for dashboard and analytics route families.

The route ledger lives in the readiness workbook rather than in the product
resolver.  These controls keep its expected SDK destinations and wire shapes
separate from the shared contract implementation, while exercising the owned
family adapters with a network-free service fake.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.commands import data_app as data_app_cmd
from mammoth_cli.commands import report as report_cmd
from mammoth_cli.commands import template as template_cmd
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

# Keep the executable oracle beside this test so the suite works from a wheel
# checkout or another workspace. The readiness workbook retains the canonical
# handover copy; this fixture is the shipped, reviewable test resource.
LEDGER = Path(__file__).with_name("fixtures") / "C2-S6-ROUTES.json"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def isolated_cli_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Keep profile writes in the test's temporary directory."""
    monkeypatch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir",
        lambda *_args, **_kwargs: str(tmp_path),
    )
    return tmp_path


@pytest.fixture
def fake_family_service(
    monkeypatch: pytest.MonkeyPatch,
) -> FakeMammothService:
    service = FakeMammothService()

    class _ServiceContext:
        def __enter__(self) -> tuple[FakeMammothService, SimpleNamespace]:
            return service, SimpleNamespace(workspace_id=4)

        def __exit__(self, *_args: object) -> None:
            return None

    def context(_invocation: Invocation) -> _ServiceContext:
        return _ServiceContext()

    for module in (dashboard_cmd, data_app_cmd, report_cmd, template_cmd):
        monkeypatch.setattr(module, "open_service", context)
    return service


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, payload: dict[str, Any]) -> str:
    path = tmp_path / "s6-input.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _ledger() -> dict[str, Any]:
    assert LEDGER.exists(), f"missing independent S6 ledger: {LEDGER}"
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_s6_ledger_closes_exact_106_route_surface() -> None:
    ledger = _ledger()
    routes = ledger["routes"]
    assert ledger["route_count"] == 105
    assert ledger["families"] == {"dashboard": 87, "data-app": 12, "report": 1, "template": 5}
    assert len(routes) == 105
    ids = {route["command_id"] for route in routes}
    assert len(ids) == 105
    for route in routes:
        command_id = route["command_id"]
        record = command_by_id(command_id)
        assert record is not None, command_id
        assert command_id in HANDLERS, command_id
        assert route["sdk_symbol"] == record["sdk_symbol"]
        assert route["wire"]["method"] in {"GET", "POST", "PUT", "PATCH", "DELETE"}
        assert route["wire"]["path"].startswith("/")
        assert route["dropped_field_sentinel"] == "__s6_dropped_field__"
        assert route["wire_verification"]["status"] == "unverified"
        assert route["wire_verification"]["executed_controls"] == []
        assert set(route["wire_verification"]["planned_controls"]) == {
            "exact_sdk_symbol",
            "field_consumption",
            "wire_method_path_body",
            "reject_dropped_field",
        }
        for name, destination in route["field_destinations"].items():
            assert destination["destination"], f"missing destination for {command_id}.{name}"


@pytest.mark.parametrize(
    ("module", "handler", "command_id", "args", "payload"),
    [
        (
            dashboard_cmd,
            dashboard_cmd.dashboard_action,
            "dashboard.action",
            ["17"],
            {"action": "sync"},
        ),
        (
            dashboard_cmd,
            dashboard_cmd.dashboard_update,
            "dashboard.update",
            ["17"],
            {"patch": []},
        ),
        (
            data_app_cmd,
            data_app_cmd.data_app_create,
            "data-app.create",
            [],
            {"body": {"name": "S6"}},
        ),
        (report_cmd, report_cmd.report_list, "report.list", [], {"limit": 913, "offset": 17}),
        (
            template_cmd,
            template_cmd.template_update,
            "template.update",
            ["17"],
            {"body": {"name": "S6"}},
        ),
    ],
)
def test_dropped_field_rejected_before_owned_adapter_dispatch(
    module: object,
    handler: object,
    command_id: str,
    args: list[str],
    payload: dict[str, Any],
    fake_family_service: FakeMammothService,
    tmp_path: Path,
) -> None:
    del module
    payload["__s6_dropped_field__"] = "must-not-reach-sdk"
    with pytest.raises(CliError) as error:
        handler(  # type: ignore[operator]
            _inv(
                command_id,
                extra_args=args,
                input_file=_write(tmp_path, payload),
                yes=True,
            )
        )
    assert error.value.code == "unknown_input_field"
    assert fake_family_service.call_log == []


def test_distinctive_fields_reach_owned_family_destinations(
    fake_family_service: FakeMammothService, tmp_path: Path
) -> None:
    dashboard_cmd.dashboard_action(
        _inv(
            "dashboard.action",
            extra_args=["17"],
            input_file=_write(
                tmp_path,
                {
                    "action": "auto-sync",
                    "params_enabled": False,
                    "params_view_id": 913,
                },
            ),
            yes=True,
        )
    )
    data_app_cmd.data_app_upload(
        _inv(
            "data-app.upload",
            extra_args=["23", "/tmp/s6-upload.csv"],
            input_file=_write(tmp_path, {"append_to_ds_id": 917}),
        )
    )
    report_cmd.report_list(
        _inv("report.list", input_file=_write(tmp_path, {"limit": 919, "offset": 923}))
    )
    template_cmd.template_update(
        _inv(
            "template.update",
            extra_args=["29"],
            input_file=_write(tmp_path, {"body": {"name": "S6-template"}}),
        )
    )
    assert fake_family_service.call_log == [
        (
            "mammoth.api.dashboards.DashboardsAPI.action",
            {
                "dashboard_id": 17,
                "action": "auto-sync",
                "params_enabled": False,
                "params_view_id": 913,
            },
        ),
        (
            "mammoth.api.data_apps.DataAppsAPI.upload",
            {"data_app_id": 23, "file": "/tmp/s6-upload.csv", "append_to_ds_id": 917},
        ),
        (
            "mammoth.api.reports.ReportsAPI.list",
            {"limit": 919, "offset": 923},
        ),
        (
            "mammoth.api.templates.TemplatesAPI.update",
            {"template_id": 29, "body": {"name": "S6-template"}},
        ),
    ]


def test_generated_dashboard_route_binds_positional_and_input_values(
    fake_family_service: FakeMammothService, tmp_path: Path
) -> None:
    dashboard_cmd.generated_dashboard(
        _inv(
            "dashboard.canvas.get",
            extra_args=["31"],
            input_file=_write(tmp_path, {"sequence": 937}),
        )
    )
    assert fake_family_service.call_log == [
        (
            "mammoth.api.dashboards.DashboardsAPI.canvas_get",
            {"sequence": 937, "dashboard_id": 31},
        )
    ]


def test_s6_positional_identity_cannot_be_overridden_by_input(
    fake_family_service: FakeMammothService, tmp_path: Path
) -> None:
    """A resource positional is context, never an input-field fallback."""
    with pytest.raises(CliError) as error:
        dashboard_cmd.generated_dashboard(
            _inv(
                "dashboard.canvas.get",
                extra_args=["31"],
                input_file=_write(tmp_path, {"dashboard_id": 999, "sequence": 937}),
            )
        )
    assert error.value.code == "unknown_input_field"
    assert fake_family_service.call_log == []
