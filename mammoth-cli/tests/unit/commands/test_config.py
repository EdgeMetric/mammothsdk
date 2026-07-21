"""Bespoke `config get|set|list|path` command tests. All local, no network."""

from __future__ import annotations

import json
from pathlib import Path

from mammoth_cli.context import profiles
from mammoth_cli.testing import make_runner


def test_config_path_reports_profiles_file(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(["config", "path", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["profiles_path"] == str(profiles.profiles_path())


def test_config_get_unknown_key_fails(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(["config", "get", "nonsense", "--output", "json", "--no-input"])
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "unknown_config_key"


def test_config_set_and_get_output(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(["config", "set", "output", "yaml", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    result = runner.invoke(["config", "get", "output", "--output", "json", "--no-input"])
    envelope = json.loads(result.stdout)
    assert envelope["data"]["value"] == "yaml"


def test_config_set_output_rejects_invalid_mode(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(
        ["config", "set", "output", "not-a-mode", "--output", "json", "--no-input"]
    )
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "invalid_config_value"


def test_config_set_timeout_roundtrip(isolated_cli_config: Path) -> None:
    runner = make_runner()
    runner.invoke(["config", "set", "timeout", "45", "--output", "json", "--no-input"])
    result = runner.invoke(["config", "get", "timeout", "--output", "json", "--no-input"])
    envelope = json.loads(result.stdout)
    assert envelope["data"]["value"] == "45"


def test_config_set_project_requires_existing_profile(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(["config", "set", "project", "42", "--output", "json", "--no-input"])
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "profile_not_found"


def test_config_set_project_after_profile_exists(isolated_cli_config: Path) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=4))
    runner = make_runner()
    result = runner.invoke(["config", "set", "project", "42", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    assert profiles.get_profile("default").project_id == 42  # type: ignore[union-attr]


def test_config_set_server_prefix_validates_format(isolated_cli_config: Path) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=4))
    runner = make_runner()
    result = runner.invoke(
        ["config", "set", "server_prefix", "bad prefix", "--output", "json", "--no-input"]
    )
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "invalid_server_prefix"


def test_config_list_returns_every_key(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(["config", "list", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert set(envelope["data"]["values"]) == {
        "base_url",
        "job_timeout",
        "output",
        "pipeline_timeout",
        "project",
        "server_prefix",
        "timeout",
    }
