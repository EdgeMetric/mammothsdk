"""``history resume``: results the journal could not keep, and secrets in unfinished items."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.app import app
from mammoth_cli.commands import run as run_cmd
from mammoth_cli.runtime import journal
from mammoth_cli.testing import login_default_profile, make_runner


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def ran(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Every line's argv; each succeeds."""
    calls: list[list[str]] = []

    def execute(argv: list[str], command: str = "") -> tuple[int, dict[str, Any]]:
        calls.append(list(argv))
        return 0, {"data": {"id": 5}}

    monkeypatch.setattr(run_cmd, "execute_line", execute)
    return calls


def _cli(*argv: str) -> tuple[int, dict[str, Any]]:
    result = make_runner()._runner.invoke(app, [*argv, "-o", "json"])
    text = result.stdout.strip() or result.stderr.strip()
    return result.exit_code, json.loads(text.splitlines()[-1])


def _plan(group: str, *lines: dict[str, Any]) -> journal.FileJournal:
    store = journal.FileJournal(journal.journal_dir())
    store.append(
        {
            "event": "plan",
            "group": group,
            "command": "run",
            "lines": [[number, json.dumps(line)] for number, line in enumerate(lines, start=1)],
            "defaults": {"--project": "--project=9"},
            "scope": {},
        }
    )
    return store


def _item(
    store: journal.FileJournal, line: int, index: int, exit_status: int, **extra: Any
) -> None:
    store.append(
        {"event": "item", "group": "g9", "line": line, "index": index, "exit": exit_status, **extra}
    )


def _step(store: journal.FileJournal, line: int, exit_status: int, **fields: Any) -> None:
    store.append({"event": "step", "group": "g9", "line": line, "exit": exit_status, **fields})


def _ids(calls: list[list[str]]) -> list[str]:
    return [argv[2] for argv in calls]


def test_an_item_result_over_the_limit_is_journaled_as_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = journal.FileJournal(journal.journal_dir())
    monkeypatch.setattr(journal, "_run_store", lambda: (store, "g9"))
    journal.record_item(1, 0, 0, {"rows": "x" * (journal.MAX_STEP_BYTES + 1)})
    journal.record_item(1, 1, 0, {"rows": "small"})
    items = [r for r in store.records() if r["event"] == "item"]
    assert items[0]["omitted"] is True and items[0]["data"] is None
    assert "omitted" not in items[1] and items[1]["data"] == {"rows": "small"}


def test_a_resume_runs_a_read_item_again_whose_result_was_not_kept(ran: list[list[str]]) -> None:
    line = {"cmd": "dataset get", "args": ["{{item}}"], "for_each": [1, 2, 3], "name": "each"}
    store = _plan("g9", line)
    _item(store, 1, 0, 0, data=None, omitted=True)
    _item(store, 1, 1, 0, data={"id": 2})
    _item(store, 1, 2, 1)
    _step(store, 1, 1)
    code, summary = _cli("history", "resume", "g9", "--yes")
    assert code == 0, summary
    assert _ids(ran) == ["1", "3"], "item 0 lost its result, so it runs again; item 1 is done"


def test_a_resume_refuses_to_repeat_a_write_item_whose_result_was_not_kept(
    ran: list[list[str]],
) -> None:
    line = {"cmd": "dataset trash", "args": ["{{item}}"], "for_each": [1, 2], "name": "each"}
    store = _plan("g9", line)
    _item(store, 1, 0, 0, data=None, omitted=True)
    _step(store, 1, 1)
    code, envelope = _cli("history", "resume", "g9", "--yes")
    assert code == 2 and envelope["error"]["code"] == "resume_result_too_large"
    assert "from_line" in envelope["error"]["hint"]
    assert ran == []


def test_a_resume_names_the_line_that_reads_a_result_too_large_to_keep(
    ran: list[list[str]],
) -> None:
    first = {"name": "big", "cmd": "dataset get", "args": [7]}
    second = {"cmd": "dataset get", "args": ["{{steps.big.data.id}}"]}
    store = _plan("g9", first, second)
    _step(store, 1, 0, steps={}, omitted=["big"])
    code, envelope = _cli("history", "resume", "g9", "--yes")
    assert code == 2 and envelope["error"]["code"] == "resume_result_too_large"
    assert envelope["error"]["details"] == {"line": 2, "step": "big", "made_by": 1}
    assert '"from_line": 1' in envelope["error"]["hint"]
    assert ran == []
    code, _ = _cli("history", "resume", "g9", "--input", '{"from_line": 1}', "--yes")
    assert code == 0, "running the line again makes the result the next line reads"


def test_a_resume_refuses_a_line_that_reads_a_secret_inside_an_unfinished_for_each(
    ran: list[list[str]],
) -> None:
    each = {"cmd": "dataset get", "args": ["{{item}}"], "for_each": [1, 2], "name": "each"}
    reads = {"cmd": "dataset get", "args": ["{{steps.each.data[0].id}}"]}
    store = _plan("g9", each, reads)
    _item(store, 1, 0, 0, data={"id": 1, "api_key": journal.REDACTED})
    _step(store, 1, 1)
    code, envelope = _cli("history", "resume", "g9", "--yes")
    assert code == 2 and envelope["error"]["code"] == "resume_secret_needed"
    assert envelope["error"]["details"]["references"] == ["steps.each"]
    assert ran == []
