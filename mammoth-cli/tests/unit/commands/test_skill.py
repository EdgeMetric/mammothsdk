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


def test_later_target_conflict_is_preflighted_before_any_install(tmp_path: Path) -> None:
    home = tmp_path / "home"
    conflict = home / ".claude/skills/mammoth-cli"
    conflict.mkdir(parents=True)
    (conflict / "SKILL.md").write_text("user-owned", encoding="utf-8")

    with pytest.raises(CliError) as excinfo:
        installer.install(["all"], "user", home=home)

    assert excinfo.value.code == "skill_conflict"
    assert not (home / ".agents/skills/mammoth-cli").exists()
    assert installer.list_()["installs"] == []

    (conflict / "SKILL.md").unlink()
    conflict.rmdir()
    retried = installer.install(["all"], "user", home=home)
    assert [result["status"] for result in retried["results"]] == [
        "installed",
        "installed",
        "installed",
    ]
    assert len(installer.list_()["installs"]) == 3
    assert all(
        result["status"] == "identical"
        for result in installer.update(["all"], "user", home=home)["results"]
    )
    assert all(
        result["status"] == "removed"
        for result in installer.uninstall(["all"], "user", home=home)["results"]
    )


def test_later_filesystem_failure_preserves_completed_target_ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    real_copy_tree = installer._copy_tree

    def fail_claude_copy(source: Path, destination: Path) -> None:
        if destination == home / ".claude/skills/mammoth-cli":
            raise OSError("simulated later-target failure")
        real_copy_tree(source, destination)

    monkeypatch.setattr(installer, "_copy_tree", fail_claude_copy)
    with pytest.raises(OSError, match="simulated later-target failure"):
        installer.install(["all"], "user", home=home)

    codex = home / ".agents/skills/mammoth-cli"
    assert codex.exists()
    assert not (home / ".claude/skills/mammoth-cli").exists()
    assert not (home / ".cursor/skills/mammoth-cli").exists()
    listed = installer.list_()["installs"]
    assert len(listed) == 1
    assert listed[0]["agent"] == "codex"
    assert listed[0]["intact"] is True
    assert installer.update(["codex"], "user", home=home)["results"][0]["status"] == "identical"
    assert installer.uninstall(["codex"], "user", home=home)["results"][0]["status"] == "removed"
    assert not codex.exists()

    monkeypatch.setattr(installer, "_copy_tree", real_copy_tree)
    retried = installer.install(["all"], "user", home=home)
    assert len(retried["results"]) == 3
    assert len(installer.list_()["installs"]) == 3


def test_force_backs_up_and_replaces(tmp_path: Path) -> None:
    home = tmp_path / "home"
    installer.install(["claude"], "user", home=home)
    skill_md = home / ".claude/skills/mammoth-cli/SKILL.md"
    skill_md.write_text("locally edited", encoding="utf-8")
    result = installer.install(["claude"], "user", home=home, force=True, timestamp="T")
    assert result["results"][0]["backup"] is not None
    assert (home / ".claude/skills/mammoth-cli.backup-T").exists()
    assert skill_md.read_text(encoding="utf-8").startswith("---")


def test_replacement_does_not_delete_unowned_previous_sibling(tmp_path: Path) -> None:
    parent = tmp_path / "skills"
    parent.mkdir()
    sibling = parent / ".mammoth-cli.previous"
    sibling.write_text("user backup", encoding="utf-8")
    destination = parent / "mammoth-cli"

    installer._copy_tree(installer.canonical_skill_dir(), destination)

    assert sibling.read_text(encoding="utf-8") == "user backup"
    assert (destination / "SKILL.md").is_file()


def test_failed_replacement_restores_original_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = tmp_path / "skills"
    destination = parent / "mammoth-cli"
    destination.mkdir(parents=True)
    original = destination / "original.txt"
    original.write_text("keep me", encoding="utf-8")

    real_replace = installer.os.replace

    def fail_destination_replace(source: object, target: object) -> None:
        if Path(target) == destination:
            raise OSError("simulated replacement failure")
        real_replace(source, target)

    monkeypatch.setattr(installer.os, "replace", fail_destination_replace)
    with pytest.raises(OSError, match="simulated replacement failure"):
        installer._copy_tree(installer.canonical_skill_dir(), destination)

    assert original.read_text(encoding="utf-8") == "keep me"
    assert not list(parent.glob("*.displaced-*"))


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
