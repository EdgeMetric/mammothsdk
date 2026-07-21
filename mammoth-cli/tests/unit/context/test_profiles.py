"""Non-secret profile store: name validation, roundtrip, selection, modes."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import CliError


@pytest.mark.parametrize("name", ["default", "a", "A1", "team.prod", "team_prod", "team-prod"])
def test_valid_profile_names_pass(name: str) -> None:
    profiles.validate_profile_name(name)  # does not raise


@pytest.mark.parametrize("name", ["", "-abc", ".abc", "_abc", "has space", "has/slash"])
def test_invalid_profile_names_are_rejected(name: str) -> None:
    with pytest.raises(CliError) as excinfo:
        profiles.validate_profile_name(name)
    assert excinfo.value.code == "invalid_profile_name"


def test_get_selected_defaults_to_default(isolated_cli_config: Path) -> None:
    assert profiles.get_selected() == "default"


def test_save_and_get_profile_roundtrip(isolated_cli_config: Path) -> None:
    record = profiles.ProfileRecord(name="default", workspace_id=4, server_prefix="release")
    profiles.save_profile(record)
    loaded = profiles.get_profile("default")
    assert loaded == record


def test_save_profile_rejects_conflicting_endpoint(isolated_cli_config: Path) -> None:
    record = profiles.ProfileRecord(
        name="default", workspace_id=4, server_prefix="release", base_url="https://x/api/v2"
    )
    with pytest.raises(CliError) as excinfo:
        profiles.save_profile(record)
    assert excinfo.value.code == "conflicting_endpoint"


def test_list_profiles_sorted(isolated_cli_config: Path) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="zeta", workspace_id=1))
    profiles.save_profile(profiles.ProfileRecord(name="alpha", workspace_id=2))
    names = [record.name for record in profiles.list_profiles()]
    assert names == ["alpha", "zeta"]


def test_set_and_get_selected(isolated_cli_config: Path) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="work", workspace_id=1))
    profiles.set_selected("work")
    assert profiles.get_selected() == "work"


def test_delete_profile_is_idempotent(isolated_cli_config: Path) -> None:
    assert profiles.delete_profile("missing") is False


def test_delete_selected_profile_falls_back_to_default(isolated_cli_config: Path) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=1))
    profiles.save_profile(profiles.ProfileRecord(name="work", workspace_id=2))
    profiles.set_selected("work")
    profiles.delete_profile("work")
    assert profiles.get_selected() == "default"
    assert profiles.get_profile("work") is None


def test_delete_selected_profile_clears_selection_when_no_default(
    isolated_cli_config: Path,
) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="work", workspace_id=2))
    profiles.set_selected("work")
    profiles.delete_profile("work")
    assert profiles.get_selected() == "default"
    assert profiles.get_profile("default") is None


def test_clearing_project_id_removes_stale_value(isolated_cli_config: Path) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=1, project_id=42))
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=1, project_id=None))
    assert profiles.get_profile("default").project_id is None  # type: ignore[union-attr]


def test_settings_roundtrip(isolated_cli_config: Path) -> None:
    assert profiles.get_setting("default", "output") is None
    profiles.set_setting("default", "output", "json")
    assert profiles.get_setting("default", "output") == "json"
    assert profiles.list_settings("default") == {"output": "json"}


@pytest.mark.skipif(os.name != "posix", reason="POSIX file mode check")
def test_profiles_file_and_dir_have_restrictive_modes(isolated_cli_config: Path) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=1))
    path = profiles.profiles_path()
    assert stat.S_IMODE(path.stat().st_mode) == stat.S_IRUSR | stat.S_IWUSR
    assert stat.S_IMODE(path.parent.stat().st_mode) == stat.S_IRWXU


def test_save_profile_leaves_no_temp_files(isolated_cli_config: Path) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=1))
    leftovers = [p for p in isolated_cli_config.iterdir() if p.name.startswith(".profiles-")]
    assert leftovers == []
