"""Ownership and atomic replacement checks for the bundled skill installer."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.skills import installer


def test_install_records_hashes_and_preserves_modified_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state.json"
    monkeypatch.setattr(installer, "_state_path", lambda: state)
    home = tmp_path / "home"

    first = installer.install(agents=["codex"], home=home, cwd=tmp_path)
    target = home / ".agents" / "skills" / "mammoth-cli"
    assert first["results"][0]["status"] == "installed"
    assert (target / "references" / "handoff.md").is_file()
    assert installer.list_()["installs"][0]["intact"] is True

    skill = target / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8") + "\nlocal customization\n", encoding="utf-8"
    )
    assert installer.list_()["installs"][0]["intact"] is False
    with pytest.raises(CliError, match="not owned") as conflict:
        installer.update(agents=["codex"], home=home, cwd=tmp_path)
    assert conflict.value.code == "skill_conflict"
    assert "local customization" in skill.read_text(encoding="utf-8")

    forced = installer.update(
        agents=["codex"], home=home, cwd=tmp_path, force=True, timestamp="test"
    )
    assert forced["results"][0]["backup"].endswith("mammoth-cli.backup-test")
    assert installer.list_()["installs"][0]["intact"] is True


def test_uninstall_leaves_modified_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "state.json"
    monkeypatch.setattr(installer, "_state_path", lambda: state)
    home = tmp_path / "home"
    installer.install(agents=["codex"], home=home, cwd=tmp_path)
    target = home / ".agents" / "skills" / "mammoth-cli"
    (target / "README.local").write_text("owned? no\n", encoding="utf-8")

    result = installer.uninstall(agents=["codex"], home=home, cwd=tmp_path)
    assert result["results"][0]["status"] == "modified"
    assert target.exists()
