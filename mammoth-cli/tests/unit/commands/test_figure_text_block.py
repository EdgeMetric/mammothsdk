"""``dashboard figure text-block`` puts a source or caveat on a tile with no chat turn."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands.dashboard.generated import generated_dashboard
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_ADD = "mammoth.api.dashboards.DashboardsAPI.add_text_block"
_CREATED = {"sequence": 5, "bake_job_id": 9, "page_id": "p1", "block_id": "tb", "created": True}


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _run(tmp_path: Path, payload: dict[str, Any]) -> Any:
    path = tmp_path / "in.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    data, _ = generated_dashboard(
        Invocation(command_id="dashboard.figure.text-block", extra_args=["7"], input_file=str(path))
    )
    return data


def test_it_sends_the_block_and_returns_where_it_landed(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_ADD] = _CREATED

    data = _run(tmp_path, {"tile": "t-1", "text": "From Stripe", "kind": "caveat"})

    assert data["block_id"] == "tb" and data["created"] is True
    sent = dict(fake_service.call_log)[_ADD]
    assert sent["dashboard_id"] == 7
    assert (sent["tile"], sent["text"], sent["kind"]) == ("t-1", "From Stripe", "caveat")


@pytest.mark.parametrize("missing", ["tile", "text"])
def test_it_refuses_a_block_without_its_tile_or_words(
    fake_service: FakeMammothService, tmp_path: Path, missing: str
) -> None:
    payload = {"tile": "t-1", "text": "From Stripe"}
    del payload[missing]

    with pytest.raises(CliError, match=missing):
        _run(tmp_path, payload)
    assert _ADD not in dict(fake_service.call_log)
