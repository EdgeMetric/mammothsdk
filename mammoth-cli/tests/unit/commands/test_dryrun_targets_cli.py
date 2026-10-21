"""``--dry-run`` of destructive commands through the real CLI: targets named, nothing deleted."""

from __future__ import annotations

import json
from pathlib import Path

from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import dryrun_targets as dt
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner


def sym(command_id: str) -> str:
    record = command_by_id(command_id)
    assert record is not None
    return str(record["sdk_symbol"])


def test_dry_run_of_a_dataset_delete_reports_the_named_target_and_changes_nothing(
    fake_service: FakeMammothService, isolated_cli_config: Path
) -> None:
    login_default_profile()
    fake_service.responses[sym("dataset.get")] = {"dataset": {"id": 7, "name": "Sales 2026"}}
    fake_service.responses[dt._DEPENDENCIES_SYMBOL] = {"7": []}

    result = make_runner().invoke(
        [
            "dataset",
            "delete",
            "7",
            "--project",
            "180",
            "--dry-run",
            "--output",
            "json",
            "--no-input",
        ]
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output[result.output.find("{") :])["data"]
    assert data["dry_run"] is True
    assert data["targets"] == [{"type": "dataset", "id": 7, "name": "Sales 2026"}]
    assert data["dependents"]["checked"] is True
    assert sym("dataset.delete") not in [name for name, _ in fake_service.call_log]


def test_dry_run_of_an_unreadable_destructive_command_fails_with_the_unresolvable_error(
    fake_service: FakeMammothService, isolated_cli_config: Path
) -> None:
    login_default_profile()
    result = make_runner().invoke(
        [
            "collection",
            "delete",
            "5",
            "--project",
            "180",
            "--dry-run",
            "--output",
            "json",
            "--no-input",
        ]
    )
    envelope = json.loads(result.output[result.output.find("{") :])
    assert result.exit_code == 2, result.output
    assert envelope["error"]["code"] == "dry_run_targets_unresolvable"
