"""Unit tests for ``dashboard template thumbnail *`` and ``dashboard gallery *``.

All five dispatch through the generic
:func:`mammoth_cli.commands.dashboard.generated_dashboard` handler; these tests
pin the SDK symbol, the kwargs and the confirmation policy of each.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_THUMB_GET = "mammoth.api.dashboards.DashboardsAPI.template_thumbnail_get"
_THUMB_SET = "mammoth.api.dashboards.DashboardsAPI.template_thumbnail_set"
_THUMB_CLEAR = "mammoth.api.dashboards.DashboardsAPI.template_thumbnail_clear"
_GALLERY_LIST = "mammoth.api.dashboards.DashboardsAPI.gallery_list"
_GALLERY_GET = "mammoth.api.dashboards.DashboardsAPI.gallery_get"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_thumbnail_get_uses_positional_template(fake_service: FakeMammothService) -> None:
    dashboard_cmd.generated_dashboard(
        _inv("dashboard.template.thumbnail.get", extra_args=["sales-overview"])
    )
    assert fake_service.call_log == [(_THUMB_GET, {"template_id": "sales-overview"})]


def test_thumbnail_set_passes_template_and_file(fake_service: FakeMammothService) -> None:
    dashboard_cmd.generated_dashboard(
        _inv("dashboard.template.thumbnail.set", extra_args=["sales-overview", "card.png"])
    )
    assert fake_service.call_log == [
        (_THUMB_SET, {"template_id": "sales-overview", "file": "card.png"})
    ]


def test_thumbnail_clear_requires_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.generated_dashboard(
            _inv("dashboard.template.thumbnail.clear", extra_args=["sales-overview"])
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_thumbnail_clear_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    dashboard_cmd.generated_dashboard(
        _inv("dashboard.template.thumbnail.clear", extra_args=["sales-overview"], yes=True)
    )
    assert fake_service.call_log == [(_THUMB_CLEAR, {"template_id": "sales-overview"})]


def test_gallery_list_forwards_facets(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text('{"function": "sales"}', encoding="utf-8")
    dashboard_cmd.generated_dashboard(_inv("dashboard.gallery.list", input_file=str(doc)))
    assert fake_service.call_log == [(_GALLERY_LIST, {"function": "sales"})]


def test_gallery_get_uses_positional_slug(fake_service: FakeMammothService) -> None:
    dashboard_cmd.generated_dashboard(_inv("dashboard.gallery.get", extra_args=["sales-overview"]))
    assert fake_service.call_log == [(_GALLERY_GET, {"slug": "sales-overview"})]
