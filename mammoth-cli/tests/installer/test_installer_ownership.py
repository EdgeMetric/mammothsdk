"""Ownership and atomic replacement checks for the bundled skill installer."""

from __future__ import annotations

import json
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


def test_sync_refreshes_owned_stale_install_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state" / "install-state-v1.json"
    monkeypatch.setattr(installer, "_state_path", lambda: state)
    home = tmp_path / "home"
    installer.install(["claude"], home=home, cwd=tmp_path)
    destination = home / ".claude/skills/mammoth-cli"
    # Simulate an install made by an older CLI: the files and the ownership
    # record both describe an older bundled skill.
    (destination / "SKILL.md").write_text("old guidance\n", encoding="utf-8")
    key = next(iter(json.loads(state.read_text())["installs"]))
    document = json.loads(state.read_text())
    document["installs"][key]["SKILL.md"] = installer._sha256(destination / "SKILL.md")
    state.write_text(json.dumps(document))

    assert installer.list_()["installs"][0]["current"] is False  # type: ignore[index]
    assert installer.sync_owned_installs("9.9.9") == [str(destination)]
    assert (destination / "SKILL.md").read_text(encoding="utf-8") != "old guidance\n"
    assert installer.list_()["installs"][0]["current"] is True  # type: ignore[index]
    # The marker makes the next run a no-op.
    assert installer.sync_owned_installs("9.9.9") == []


def test_sync_leaves_locally_modified_install_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state" / "install-state-v1.json"
    monkeypatch.setattr(installer, "_state_path", lambda: state)
    home = tmp_path / "home"
    installer.install(["claude"], home=home, cwd=tmp_path)
    destination = home / ".claude/skills/mammoth-cli"
    (destination / "SKILL.md").write_text("my own edits\n", encoding="utf-8")

    assert installer.sync_owned_installs("9.9.9") == []
    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "my own edits\n"


def test_update_without_agents_only_touches_recorded_installs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(installer, "_state_path", lambda: tmp_path / "state.json")
    home = tmp_path / "home"
    installer.install(["claude"], home=home, cwd=tmp_path)

    result = installer.update(home=home, cwd=tmp_path)

    assert [r["target"] for r in result["results"]] == [  # type: ignore[attr-defined]
        str(home / ".claude/skills/mammoth-cli")
    ]
    assert not (home / ".agents").exists()
    assert not (home / ".cursor").exists()


def test_update_without_any_install_is_a_no_op(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(installer, "_state_path", lambda: tmp_path / "state.json")
    home = tmp_path / "home"
    assert installer.update(home=home, cwd=tmp_path) == {"skill": "mammoth-cli", "results": []}
    assert not home.exists()
