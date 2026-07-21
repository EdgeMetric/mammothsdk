"""Unit tests for the skill installer and its commands."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.skills import installer


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect the install-state dir into tmp so tests never touch real data."""
    state_dir = tmp_path / "state"
    monkeypatch.setattr(
        "mammoth_cli.skills.installer.platformdirs.user_data_dir",
        lambda *_a, **_k: str(state_dir),
    )


def test_canonical_skill_has_skill_md() -> None:
    assert (installer.canonical_skill_dir() / "SKILL.md").is_file()


def test_install_all_agents_user_scope(tmp_path: Path) -> None:
    home = tmp_path / "home"
    result = installer.install(["all"], "user", home=home)
    results = result["results"]
    assert isinstance(results, list) and len(results) == 3
    for subdir in (".agents/skills", ".claude/skills", ".cursor/skills"):
        assert (home / subdir / "mammoth-cli/SKILL.md").is_file()


def test_reinstall_is_identical(tmp_path: Path) -> None:
    home = tmp_path / "home"
    installer.install(["claude"], "user", home=home)
    again = installer.install(["claude"], "user", home=home)
    assert again["results"][0]["status"] == "identical"


def test_modified_destination_conflicts_without_force(tmp_path: Path) -> None:
    home = tmp_path / "home"
    installer.install(["claude"], "user", home=home)
    skill_md = home / ".claude/skills/mammoth-cli/SKILL.md"
    skill_md.write_text("locally edited", encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        installer.install(["claude"], "user", home=home)
    assert excinfo.value.code == "skill_conflict"


def test_force_backs_up_and_replaces(tmp_path: Path) -> None:
    home = tmp_path / "home"
    installer.install(["claude"], "user", home=home)
    skill_md = home / ".claude/skills/mammoth-cli/SKILL.md"
    skill_md.write_text("locally edited", encoding="utf-8")
    result = installer.install(["claude"], "user", home=home, force=True, timestamp="T")
    assert result["results"][0]["backup"] is not None
    assert (home / ".claude/skills/mammoth-cli.backup-T").exists()
    assert skill_md.read_text(encoding="utf-8").startswith("---")


def test_uninstall_removes_owned(tmp_path: Path) -> None:
    home = tmp_path / "home"
    installer.install(["cursor"], "user", home=home)
    result = installer.uninstall(["cursor"], "user", home=home)
    assert result["results"][0]["status"] == "removed"
    assert not (home / ".cursor/skills/mammoth-cli").exists()


def test_uninstall_keeps_modified(tmp_path: Path) -> None:
    home = tmp_path / "home"
    installer.install(["cursor"], "user", home=home)
    (home / ".cursor/skills/mammoth-cli/SKILL.md").write_text("edited", encoding="utf-8")
    result = installer.uninstall(["cursor"], "user", home=home)
    assert result["results"][0]["status"] == "modified"
    assert (home / ".cursor/skills/mammoth-cli").exists()


def test_list_reports_installs(tmp_path: Path) -> None:
    home = tmp_path / "home"
    installer.install(["codex"], "user", home=home)
    listed = installer.list_()
    installs = listed["installs"]
    assert isinstance(installs, list) and len(installs) == 1
    assert installs[0]["intact"] is True


def test_path_reports_targets(tmp_path: Path) -> None:
    home = tmp_path / "home"
    info = installer.path(["claude"], "user", home=home)
    assert info["canonical"].endswith("bundled_skill/mammoth-cli")
    assert info["targets"][0]["path"].endswith(".claude/skills/mammoth-cli")


def test_unknown_agent_is_usage_error(tmp_path: Path) -> None:
    with pytest.raises(CliError) as excinfo:
        installer.install(["nope"], "user", home=tmp_path)
    assert excinfo.value.code == "unknown_agent"
