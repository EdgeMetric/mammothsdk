"""Bespoke `context project status|use|clear` command tests. All local."""

from __future__ import annotations

import json
from pathlib import Path

from mammoth_cli.context import profiles
from mammoth_cli.testing import make_runner


def test_status_reports_no_project_when_nothing_set(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(["context", "project", "status", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["project_id"] is None
    assert envelope["data"]["source"] == "none"


def test_use_requires_an_existing_profile(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(["context", "project", "use", "42", "--output", "json", "--no-input"])
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "profile_not_found"


def test_use_rejects_nonpositive_project_id(isolated_cli_config: Path) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=4))
    runner = make_runner()
    result = runner.invoke(["context", "project", "use", "0", "--output", "json", "--no-input"])
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "invalid_project_id"


def test_use_then_status_reports_saved_project(isolated_cli_config: Path) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=4))
    runner = make_runner()
    result = runner.invoke(["context", "project", "use", "42", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    result = runner.invoke(["context", "project", "status", "--output", "json", "--no-input"])
    envelope = json.loads(result.stdout)
    assert envelope["data"]["project_id"] == 42
    assert envelope["data"]["source"] == "profile"


def test_global_project_flag_overrides_saved_project(isolated_cli_config: Path) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=4, project_id=42))
    runner = make_runner()
    result = runner.invoke(
        ["context", "project", "status", "--project", "7", "--output", "json", "--no-input"]
    )
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["project_id"] == 7
    assert envelope["data"]["source"] == "flag"


def test_clear_is_idempotent(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(["context", "project", "clear", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["project_id"] is None


def test_clear_removes_saved_project(isolated_cli_config: Path) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=4, project_id=42))
    runner = make_runner()
    result = runner.invoke(["context", "project", "clear", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    assert profiles.get_profile("default").project_id is None  # type: ignore[union-attr]
