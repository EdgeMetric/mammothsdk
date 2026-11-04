"""``dashboard duplicate``: the inputs that keep the source's title and tags."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_DUPLICATE = "mammoth.api.dashboards.DashboardsAPI.duplicate"


@pytest.fixture(autouse=True)
def _auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def test_title_and_keep_tags_reach_the_copy(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """mammothsdk#381 item 8: the copy was "Copy of ..." with no tags, fixed by hand per board."""
    fake_service.responses[_DUPLICATE] = {"id": 9, "title": "School P&L", "tags": ["Finance"]}
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"title": "School P&L", "keep_tags": True}), encoding="utf-8")
    data, _meta = dashboard_cmd.dashboard_duplicate(
        Invocation(
            command_id="dashboard.duplicate",
            project=40,
            extra_args=["3"],
            input_file=str(doc),
        )
    )
    (call,) = [kwargs for symbol, kwargs in fake_service.call_log if symbol == _DUPLICATE]
    assert (call["title"], call["keep_tags"]) == ("School P&L", True)
    assert data["title"] == "School P&L"
