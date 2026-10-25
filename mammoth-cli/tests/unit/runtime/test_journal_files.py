"""The journal's files: a write that cannot be journaled says so, and claims clean up."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.app import app
from mammoth_cli.commands import run as run_cmd
from mammoth_cli.runtime import journal
from mammoth_cli.testing import login_default_profile, make_runner


def test_a_journal_that_cannot_be_written_warns_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    blocked = tmp_path / "blocked"
    blocked.write_text("a file where the journal directory should be")
    monkeypatch.setattr(journal, "_unwritable_warned", False)
    store = journal.FileJournal(blocked / "journal")
    store.append({"event": "begin", "inv": "a"})
    store.append({"event": "begin", "inv": "b"})
    warning = capsys.readouterr().err
    assert warning.count("could not be written") == 1
    assert "cannot be undone" in warning


def test_a_finished_claim_leaves_no_lock_file(tmp_path: Path) -> None:
    store = journal.FileJournal(tmp_path)
    with store.claim("undo-a"):
        assert (tmp_path / "undo-a.lock").exists()
        with pytest.raises(journal.JournalBusy), store.claim("undo-a"):
            pass
        assert (tmp_path / "undo-a.lock").exists(), "a refused claim leaves the holder's file"
    assert list(tmp_path.glob("undo-*.lock")) == []
    with store.claim("undo-a"):
        pass


@pytest.fixture
def ran(monkeypatch: pytest.MonkeyPatch, isolated_cli_config: Path) -> list[list[str]]:
    login_default_profile()
    calls: list[list[str]] = []

    def execute(argv: list[str], command: str = "") -> tuple[int, dict[str, Any]]:
        calls.append(list(argv))
        return 0, {"data": {}}

    monkeypatch.setattr(run_cmd, "execute_line", execute)
    return calls


def test_a_busy_write_does_not_hide_the_ones_already_undone(ran: list[list[str]]) -> None:
    store = journal.FileJournal(journal.journal_dir())
    for inv, dataset in (("a", 1), ("b", 2)):
        store.append(
            {"event": "begin", "inv": inv, "group": "g1", "command": "dataset.trash", "ts": "t"}
        )
        undo = [{"cmd": "dataset restore", "args": [dataset]}]
        store.append({"event": "end", "inv": inv, "exit": 0, "undo": undo})
    # The newest write (b) is undone first; the older one (a) is held by another process.
    with store.claim("undo-a"):
        result = make_runner()._runner.invoke(app, ["history", "undo", "g1", "--yes", "-o", "json"])
    envelope = json.loads((result.stdout.strip() or result.stderr.strip()).splitlines()[-1])
    assert result.exit_code == 3, envelope
    data = envelope["data"]
    assert [item["inv"] for item in data["undone"]] == ["b"]
    assert data["failed"]["code"] == "undo_in_progress" and data["failed"]["inv"] == "a"
    assert data["not_undone"] == ["a"] and data["outcome"] == "partial"
    assert [argv[:3] for argv in ran] == [["dataset", "restore", "2"]]
