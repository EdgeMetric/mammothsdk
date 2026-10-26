"""``mammoth history``: list the journaled writes, show one, undo one or a whole run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.app import app
from mammoth_cli.commands import history
from mammoth_cli.commands import run as run_cmd
from mammoth_cli.runtime import journal
from mammoth_cli.testing import login_default_profile, make_runner


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _journal(*entries: dict[str, Any]) -> journal.FileJournal:
    store = journal.FileJournal(journal.journal_dir())
    for entry in entries:
        store.append(
            {
                "event": "begin",
                "inv": entry["inv"],
                "group": entry.get("group", "g1"),
                "command": entry.get("command", "dataset.trash"),
                "ts": "t",
            }
        )
        if "undo" in entry or "exit" in entry:
            store.append(
                {
                    "event": "end",
                    "inv": entry["inv"],
                    "exit": entry.get("exit", 0),
                    "undo": entry.get("undo", []),
                    "irreversible": entry.get("why"),
                }
            )
    return store


def _cli(*argv: str) -> tuple[int, dict[str, Any]]:
    result = make_runner()._runner.invoke(app, [*argv, "-o", "json"])
    text = result.stdout.strip() or result.stderr.strip()
    return result.exit_code, json.loads(text.splitlines()[-1])


@pytest.fixture
def ran(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Every undo line's argv; each succeeds unless its argv names 'fail'."""
    calls: list[list[str]] = []

    def execute(argv: list[str], command: str = "") -> tuple[int, dict[str, Any]]:
        calls.append(list(argv))
        if "fail" in argv:
            return 1, {"error": {"code": "not_found", "message": "Gone."}}
        if argv[:3] == ["view", "task", "list"]:
            tasks = [{"id": 1, "sequence": 1}, {"id": 2, "sequence": 2}, {"id": 3, "sequence": 3}]
            return 0, {"data": {"tasks": tasks}}
        return 0, {"data": {}}

    monkeypatch.setattr(run_cmd, "execute_line", execute)
    return calls


def test_list_shows_newest_first() -> None:
    _journal(
        {"inv": "a", "undo": [{"cmd": "dataset restore", "args": [5]}]}, {"inv": "b", "exit": 1}
    )
    code, envelope = _cli("history", "list")
    assert code == 0
    entries = envelope["data"]["entries"]
    assert [entry["inv"] for entry in entries] == ["b", "a"]
    assert [entry["status"] for entry in entries] == ["failed", "done"]
    assert entries[1]["undoable"] is True


def test_show_finds_a_whole_run_by_group() -> None:
    _journal({"inv": "a", "exit": 0}, {"inv": "b", "exit": 0}, {"inv": "c", "group": "g2"})
    code, envelope = _cli("history", "show", "g1")
    assert code == 0
    assert [entry["inv"] for entry in envelope["data"]["entries"]] == ["a", "b"]


def test_an_unknown_id_is_a_usage_error() -> None:
    _journal({"inv": "a", "exit": 0})
    code, envelope = _cli("history", "show", "nope")
    assert code == 2
    assert envelope["error"]["code"] == "history_not_found"


def test_undo_runs_the_lines_newest_first_and_marks_them(ran: list[list[str]]) -> None:
    _journal(
        {"inv": "a", "undo": [{"cmd": "dataset restore", "args": [5], "flags": {"project": 9}}]},
        {"inv": "b", "undo": [{"cmd": "view trash", "args": [8], "flags": {"project": 9}}]},
        {"inv": "c", "exit": 0, "why": "It deleted something permanently."},
    )
    code, envelope = _cli("history", "undo", "g1", "--yes")
    assert code == 0, envelope
    assert [argv[:3] for argv in ran] == [["view", "trash", "8"], ["dataset", "restore", "5"]]
    assert "--project=9" in ran[0]
    assert envelope["data"]["not_undoable"][0]["inv"] == "c"
    statuses = {e.inv: e.view()["status"] for e in journal.entries(_journal())}
    assert statuses == {"a": "undone", "b": "undone", "c": "done"}


def test_undo_needs_confirmation(ran: list[list[str]]) -> None:
    _journal({"inv": "a", "undo": [{"cmd": "dataset restore", "args": [5]}]})
    code, envelope = _cli("history", "undo", "a", "--no-input")
    assert code == 2
    assert envelope["error"]["code"] == "confirmation_required"
    assert ran == []


def test_dry_run_previews_every_line_and_marks_nothing(ran: list[list[str]]) -> None:
    _journal({"inv": "a", "undo": [{"cmd": "dataset restore", "args": [5]}]})
    code, envelope = _cli("history", "undo", "a", "--dry-run")
    assert code == 0, envelope
    assert "--dry-run" in ran[0]
    assert envelope["data"]["dry_run"] is True
    (entry,) = journal.entries(_journal())
    assert entry.view()["status"] == "done"


def test_a_failed_line_stops_the_undo_and_reports_partial(ran: list[list[str]]) -> None:
    _journal(
        {"inv": "a", "undo": [{"cmd": "dataset restore", "args": [5]}]},
        {"inv": "b", "undo": [{"cmd": "dataset restore", "args": ["fail"]}]},
        {"inv": "c", "undo": [{"cmd": "dataset restore", "args": [6]}]},
    )
    code, envelope = _cli("history", "undo", "g1", "--yes")
    data = envelope["data"]
    assert code == 3, envelope
    assert data["outcome"] == "partial"
    assert data["failed"]["inv"] == "b"
    assert data["not_undone"] == ["b", "a"]
    statuses = {e.inv: e.view()["status"] for e in journal.entries(_journal())}
    assert statuses == {"a": "done", "b": "done", "c": "undone"}


def test_a_first_pipeline_edit_deletes_the_added_steps_newest_first(
    ran: list[list[str]],
) -> None:
    undo = [{"cmd": "view task delete", "args": [7], "flags": {"yes": True}, "keep_tasks": [1]}]
    _journal({"inv": "a", "undo": undo})
    code, envelope = _cli("history", "undo", "a", "--yes")
    assert code == 0, envelope
    deletes = [argv[:5] for argv in ran if argv[:3] == ["view", "task", "delete"]]
    assert deletes == [["view", "task", "delete", "7", "3"], ["view", "task", "delete", "7", "2"]]
    assert all("--yes" in argv for argv in ran if argv[:3] == ["view", "task", "delete"])


def test_history_is_refused_when_the_journal_is_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(journal.JOURNAL_ENV, "off")
    code, envelope = _cli("history", "list")
    assert code == 2
    assert envelope["error"]["code"] == history.CODE_JOURNAL_OFF


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


def _step(
    store: journal.FileJournal, group: str, line: int, exit_status: int, **steps: Any
) -> None:
    store.append(
        {"event": "step", "group": group, "line": line, "exit": exit_status, "steps": steps}
    )


_LINES = (
    {"name": "up", "cmd": "dataset get", "args": [7]},
    {"cmd": "dataset get", "args": ["fail"]},
    {"cmd": "dataset get", "args": ["{{steps.up.data.id}}"]},
)


def test_resume_goes_on_from_the_first_unfinished_line(ran: list[list[str]]) -> None:
    store = _plan("g9", *_LINES)
    _step(store, "g9", 1, 0, up={"data": {"id": 41}, "exit": 0})
    _step(store, "g9", 2, 5)
    code, summary = _cli("history", "resume", "g9", "--yes")
    assert code == 1
    assert [argv[:3] for argv in ran] == [["dataset", "get", "fail"]]
    assert summary["data"]["resumed"] == "g9" and summary["data"]["from_line"] == 2
    assert "--project=9" in ran[0]


def test_resume_from_a_line_reads_the_journaled_results(ran: list[list[str]]) -> None:
    store = _plan("g9", *_LINES)
    _step(store, "g9", 1, 0, up={"data": {"id": 41}, "exit": 0})
    code, summary = _cli("history", "resume", "g9", "--input", '{"from_line": 3}', "--yes")
    assert code == 0, summary
    assert [argv[:3] for argv in ran] == [["dataset", "get", "41"]]


def test_resume_refuses_a_write_whose_outcome_is_unknown(ran: list[list[str]]) -> None:
    store = _plan("g9", *_LINES)
    _step(store, "g9", 1, 0, up={"data": {"id": 41}, "exit": 0})
    store.append({"event": "begin", "inv": "w2", "group": "g9", "command": "dataset.trash"})
    code, envelope = _cli("history", "resume", "g9", "--yes")
    assert code == 2
    assert envelope["error"]["code"] == "resume_outcome_unknown"
    assert envelope["error"]["details"] == {"unknown": ["w2"], "line": 2}
    assert ran == []


def test_resume_of_a_finished_run_says_so(ran: list[list[str]]) -> None:
    store = _plan("g9", _LINES[0])
    _step(store, "g9", 1, 0)
    code, envelope = _cli("history", "resume", "g9", "--yes")
    assert code == 2
    assert envelope["error"]["code"] == "nothing_to_resume"


def test_resume_of_an_unknown_group_is_not_found(ran: list[list[str]]) -> None:
    code, envelope = _cli("history", "resume", "nope", "--yes")
    assert code == 2
    assert envelope["error"]["code"] == "history_not_found"


def test_a_run_journals_its_plan_and_steps(ran: list[list[str]], tmp_path: Path) -> None:
    path = tmp_path / "lines.jsonl"
    path.write_text("\n".join(json.dumps(line) for line in _LINES) + "\n", encoding="utf-8")
    code, summary = _cli("run", str(path), "--project", "9")
    assert code == 1
    plan = journal.plan_for(journal.FileJournal(journal.journal_dir()), summary["meta"]["run_id"])
    assert plan is not None
    assert [number for number, _ in plan.lines] == [1, 2, 3]
    assert plan.finished == {1}
    assert plan.steps == {"up": {"data": {}, "exit": 0}}
    assert plan.defaults["--project"] == "--project=9"


def test_a_step_result_too_large_to_keep_is_named(monkeypatch: pytest.MonkeyPatch) -> None:
    store = journal.FileJournal(journal.journal_dir())
    monkeypatch.setattr(journal, "_run_store", lambda: (store, "g7"))
    monkeypatch.setattr(journal, "MAX_STEP_BYTES", 10)
    journal.record_plan([(1, "{}")], {}, scope=None, keep_going=False, past_partial=False)
    journal.record_step(1, 0, {"big": {"data": "x" * 20}, "small": 1})
    plan = journal.plan_for(store, "g7")
    assert plan is not None
    assert plan.steps == {"small": 1} and plan.omitted == ["big"]


def _ids(calls: list[list[str]]) -> list[str]:
    return [argv[2] for argv in calls]


def test_resume_reruns_a_failed_named_line(ran: list[list[str]]) -> None:
    store = _plan("g9", {"name": "p", "cmd": "dataset get", "args": ["fail"]}, _LINES[0])
    _step(store, "g9", 1, 5, p={"data": None, "exit": 5})
    code, summary = _cli("history", "resume", "g9", "--yes")
    assert summary["data"]["from_line"] == 1
    assert _ids(ran) == ["fail"], summary
    assert code == 1


def test_resume_from_a_line_reruns_a_finished_named_line(ran: list[list[str]]) -> None:
    store = _plan("g9", _LINES[0], {"cmd": "dataset get", "args": [8]})
    _step(store, "g9", 1, 0, up={"data": {"id": 41}, "exit": 0})
    code, summary = _cli("history", "resume", "g9", "--input", '{"from_line": 1}', "--yes")
    assert code == 0, summary
    assert _ids(ran) == ["7", "8"]


def test_resume_refuses_a_write_that_timed_out(ran: list[list[str]]) -> None:
    store = _plan("g9", *_LINES)
    _step(store, "g9", 1, 0, up={"data": {"id": 41}, "exit": 0})
    store.append({"event": "begin", "inv": "w2", "group": "g9", "command": "file.upload"})
    store.append({"event": "end", "inv": "w2", "exit": 75, "outcome_unknown": True})
    code, envelope = _cli("history", "resume", "g9", "--yes")
    assert code == 2 and envelope["error"]["code"] == "resume_outcome_unknown"
    assert ran == []


def test_resume_does_not_rerun_a_partial_line_of_a_run_past_partial(ran: list[list[str]]) -> None:
    store = journal.FileJournal(journal.journal_dir())
    lines = [[1, json.dumps(_LINES[0])], [2, json.dumps({"cmd": "dataset get", "args": [8]})]]
    store.append(
        {
            "event": "plan",
            "group": "g9",
            "command": "recipe.run",
            "lines": lines,
            "past_partial": True,
        }
    )
    _step(store, "g9", 1, 3)
    code, summary = _cli("history", "resume", "g9", "--yes")
    assert code == 0, summary
    assert _ids(ran) == ["8"]


def test_a_second_resume_skips_what_the_first_did(ran: list[list[str]], tmp_path: Path) -> None:
    path = tmp_path / "lines.jsonl"
    lines = [_LINES[0], {"cmd": "dataset get", "args": [8]}, _LINES[1]]
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")
    code, first = _cli("run", str(path), "--project", "9")
    group = first["meta"]["run_id"]
    assert code == 1 and _ids(ran) == ["7", "8", "fail"]
    ran.clear()
    store = journal.FileJournal(journal.journal_dir())
    # The third line failed. Pretend the second never finished, so the first resume runs it.
    store.append({"event": "step", "group": group, "line": 2, "exit": 1, "ts": journal._now()})
    code, _ = _cli("history", "resume", group, "--yes")
    assert _ids(ran) == ["8", "fail"]
    ran.clear()
    code, summary = _cli("history", "resume", group, "--yes")
    assert summary["data"]["from_line"] == 3
    assert _ids(ran) == ["fail"]


def test_the_writes_of_a_resume_belong_to_the_original_run() -> None:
    store = _journal({"inv": "w1", "group": "g9", "exit": 0, "undo": []})
    store.append({"event": "resume", "group": "r2", "of": "g9"})
    store.append({"event": "begin", "inv": "w3", "group": "r2", "command": "dataset.trash"})
    code, shown = _cli("history", "show", "g9")
    assert code == 0
    assert [entry["inv"] for entry in shown["data"]["entries"]] == ["w1", "w3"]
    assert {entry["group"] for entry in shown["data"]["entries"]} == {"g9"}


def test_a_for_each_resume_goes_on_from_the_first_unfinished_item(ran: list[list[str]]) -> None:
    line = {"cmd": "dataset get", "args": ["{{item}}"], "for_each": [1, "fail", 3], "name": "each"}
    store = _plan("g9", line)
    for index, exit_status in enumerate((0, 1, 0)):
        store.append(
            {"event": "item", "group": "g9", "line": 1, "index": index, "exit": exit_status}
        )
    _step(store, "g9", 1, 1)
    code, summary = _cli("history", "resume", "g9", "--yes")
    assert _ids(ran) == ["fail"], summary
    assert code == 1


def test_a_resume_refuses_a_line_that_needs_a_secret(ran: list[list[str]]) -> None:
    store = journal.FileJournal(journal.journal_dir())
    secret = {"cmd": "dataset get", "args": [7], "input": {"password": journal.REDACTED}}
    lines = [[1, json.dumps(secret)]]
    store.append({"event": "plan", "group": "g9", "command": "run", "lines": lines})
    code, envelope = _cli("history", "resume", "g9", "--yes")
    assert code == 2 and envelope["error"]["code"] == "resume_secret_needed"
    assert ran == []


def _edit(*, expect: str | None) -> None:
    undo: dict[str, Any] = {"cmd": "view version apply", "args": [7, 40, 6], "flags": {}}
    if expect is not None:
        undo["expect"] = expect
    _journal({"inv": "e1", "group": "e1", "command": "view.transform.filter", "undo": [undo]})


def test_an_undo_of_an_edit_refuses_when_the_view_changed_since(ran: list[list[str]]) -> None:
    _edit(expect="not-the-fingerprint")
    code, envelope = _cli("history", "undo", "e1", "--yes")
    assert code == 1
    assert envelope["data"]["failed"]["code"] == "view_changed_since_edit"
    assert ["view", "version", "apply"] not in [argv[:3] for argv in ran]


def test_an_undo_of_an_edit_runs_when_the_view_is_as_the_edit_left_it(
    ran: list[list[str]],
) -> None:
    _edit(expect=journal.fingerprint([{}, {}, {}]))
    code, _ = _cli("history", "undo", "e1", "--yes")
    assert code == 0
    assert ["view", "version", "apply"] in [argv[:3] for argv in ran]


def test_force_undoes_an_edit_whatever_changed_since(ran: list[list[str]]) -> None:
    _edit(expect="not-the-fingerprint")
    code, _ = _cli("history", "undo", "e1", "--input", '{"force": true}', "--yes")
    assert code == 0
    assert ["view", "version", "apply"] in [argv[:3] for argv in ran]


def test_a_retried_undo_skips_the_lines_that_ran(ran: list[list[str]]) -> None:
    store = _journal(
        {
            "inv": "w1",
            "undo": [
                {"cmd": "dataset restore", "args": [1]},
                {"cmd": "dataset restore", "args": [2]},
            ],
        }
    )
    store.append({"event": "undo_step", "inv": "w1", "lines": 1})
    code, _ = _cli("history", "undo", "w1", "--yes")
    assert code == 0
    assert _ids(ran) == ["2"]


def test_two_undos_of_one_write_do_not_run_together(ran: list[list[str]]) -> None:
    store = _journal({"inv": "w1", "undo": [{"cmd": "dataset restore", "args": [1]}]})
    with store.claim("undo-w1"):
        code, envelope = _cli("history", "undo", "w1", "--yes")
    assert code == 2 and envelope["error"]["code"] == "undo_in_progress"
    assert ran == []


@pytest.mark.parametrize("limit", [0, -3])
def test_list_refuses_a_limit_below_one(limit: int) -> None:
    code, envelope = _cli("history", "list", "--input", json.dumps({"limit": limit}))
    assert code == 2 and envelope["error"]["code"] == "invalid_argument"
