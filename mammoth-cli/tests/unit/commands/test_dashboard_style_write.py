"""``dashboard create-blank`` and ``dashboard update`` set the board's theme and mode (#419)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.commands.dashboard import generated as dashboard_generated
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_API = "mammoth.api.dashboards.DashboardsAPI."
_CREATE_BLANK = _API + "create_blank"
_CANVAS_GET = _API + "canvas_get"
_CANVAS_SAVE = _API + "canvas_save"
_UPDATE = _API + "update"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, tmp_path: Path, payload: dict[str, object], **kw: object) -> Invocation:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return Invocation(command_id=command_id, input_file=str(doc), **kw)  # type: ignore[arg-type]


def _canvas(**extra: object) -> dict[str, object]:
    return {"canvas": {"title": "T", "pages": [], **extra}, "meta": {"sequence": 4}}


def _saves(fake: FakeMammothService) -> list[dict[str, object]]:
    return [kwargs for symbol, kwargs in fake.call_log if symbol == _CANVAS_SAVE]


def test_create_blank_sets_style_and_mode_on_the_new_canvas(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CREATE_BLANK] = {"id": 9, "sequence": 1}
    fake_service.responses[_CANVAS_GET] = _canvas(style_tokens={"id": "old"}, style_id="stone")
    fake_service.responses[_CANVAS_SAVE] = {"sequence": 5, "bake_job_id": 31}
    payload = {"params": {"dataview_id": 42}, "style_id": "midnight", "mode": "dark"}
    data, _ = dashboard_generated.generated_dashboard(
        _inv("dashboard.create-blank", tmp_path, payload)
    )
    # The style fields never reach the SDK create call.
    assert fake_service.call_log[0] == (_CREATE_BLANK, {"params": {"dataview_id": 42}})
    (saved,) = _saves(fake_service)
    assert saved["dashboard_id"] == 9
    params = saved["body"]["params"]  # type: ignore[index]
    assert params["base_sequence"] == 4
    assert params["canvas"]["style_id"] == "midnight"
    assert params["canvas"]["mode"] == "dark"
    # Inlined tokens would shadow the new style id on the renderer.
    assert "style_tokens" not in params["canvas"]
    assert data["style"] == {"style_id": "midnight", "mode": "dark"}
    assert data["bake"] == "done"
    assert fake_service.wait_log == [{"job_id": 31}]


def test_create_blank_without_style_saves_nothing(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CREATE_BLANK] = {"id": 9}
    dashboard_generated.generated_dashboard(
        _inv("dashboard.create-blank", tmp_path, {"params": {"dataview_id": 42}})
    )
    assert _saves(fake_service) == []


def test_create_blank_refuses_a_bad_mode_before_any_request(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    payload = {"params": {"dataview_id": 42}, "mode": "sepia"}
    with pytest.raises(CliError) as excinfo:
        dashboard_generated.generated_dashboard(_inv("dashboard.create-blank", tmp_path, payload))
    # the manifest's mode enum refuses it before the command runs
    assert excinfo.value.code == "invalid_input_field_type"
    assert "dark" in excinfo.value.message
    assert fake_service.call_log == []


def test_create_blank_reports_a_style_that_could_not_be_saved(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CREATE_BLANK] = {"id": 9}
    fake_service.responses[_CANVAS_GET] = {}
    payload = {"params": {"dataview_id": 42}, "style_id": "stone"}
    data, _ = dashboard_generated.generated_dashboard(
        _inv("dashboard.create-blank", tmp_path, payload)
    )
    assert data["id"] == 9
    assert "no canvas" in data["style_error"]
    assert data["style_fix"].startswith("mammoth dashboard update 9 --input")


def test_update_style_only_needs_no_patch_and_saves_the_canvas(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CANVAS_GET] = _canvas(style_id="stone", mode="light")
    fake_service.responses[_CANVAS_SAVE] = {"sequence": 5}
    data, _ = dashboard_cmd.dashboard_update(
        _inv("dashboard.update", tmp_path, {"mode": "dark"}, extra_args=["7"])
    )
    assert [symbol for symbol, _ in fake_service.call_log] == [_CANVAS_GET, _CANVAS_SAVE]
    canvas = _saves(fake_service)[0]["body"]["params"]["canvas"]  # type: ignore[index]
    assert (canvas["style_id"], canvas["mode"]) == ("stone", "dark")
    assert data["style"] == {"style_id": "stone", "mode": "dark"}
    assert data["sequence"] == 5


def test_update_patch_and_style_patches_first(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    patch = [{"op": "replace", "path": "title", "value": "X"}]
    fake_service.responses[_CANVAS_GET] = _canvas()
    dashboard_cmd.dashboard_update(
        _inv("dashboard.update", tmp_path, {"patch": patch, "style_id": "sand"}, extra_args=["7"])
    )
    assert [symbol for symbol, _ in fake_service.call_log] == [_UPDATE, _CANVAS_GET, _CANVAS_SAVE]
    assert fake_service.call_log[0][1] == {"dashboard_id": 7, "patch": patch}


def test_update_style_only_failure_is_an_error(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CANVAS_GET] = {}
    with pytest.raises(CliError):
        dashboard_cmd.dashboard_update(
            _inv("dashboard.update", tmp_path, {"style_id": "sand"}, extra_args=["7"])
        )


@pytest.mark.parametrize(
    ("payload", "code"),
    [({"mode": "blue"}, "invalid_input_field_type"), ({"style_id": "  "}, "invalid_argument")],
)
def test_update_refuses_bad_style_input_before_any_request(
    fake_service: FakeMammothService, tmp_path: Path, payload: dict[str, object], code: str
) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_update(
            _inv("dashboard.update", tmp_path, payload, extra_args=["7"])
        )
    assert excinfo.value.code == code
    assert fake_service.call_log == []
