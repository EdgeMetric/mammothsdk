"""The journal: a record before and after every write, with the lines that undo it."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime import embedded, journal, trace
from mammoth_cli.runtime.dispatch import Outcome, Request, dispatch
from mammoth_cli.runtime.invocation import Invocation


class _Memory:
    def __init__(self) -> None:
        self.kept: list[dict[str, Any]] = []

    def append(self, record: Any) -> None:
        self.kept.append(dict(record))

    def records(self) -> list[dict[str, Any]]:
        return list(self.kept)


def _request(command_id: str, **positionals: Any) -> Request:
    invocation = Invocation(command_id=command_id, output="json", project=9)
    invocation.positionals.update(positionals)
    return Request(command_id, "json", lambda: ({}, {}), invocation=invocation, profile="p")


def _success(**meta: Any) -> Outcome:
    return Outcome(data={}, meta=meta)


def test_a_trash_is_undone_by_a_restore() -> None:
    lines, reason = journal.compensation(
        _request("dataset.trash", dataset_id=5), _success(), journal._Before()
    )
    assert reason is None
    assert lines == [
        {"cmd": "dataset restore", "args": [5], "flags": {"profile": "p", "project": 9}}
    ]


def test_created_objects_go_to_the_trash_newest_first() -> None:
    opens = [
        {"kind": "dataset", "id": 1, "created": True},
        {"kind": "view", "id": 2, "created": True},
        {"kind": "view", "id": 3, "created": False},
    ]
    lines, reason = journal.compensation(
        _request("file.upload"), _success(opens=opens, project_id=4), journal._Before()
    )
    assert reason is None
    assert [(line["cmd"], line["args"]) for line in lines] == [
        ("view trash", [2]),
        ("dataset trash", [1]),
    ]
    assert lines[0]["flags"]["project"] == 4


def test_a_pipeline_edit_is_undone_by_its_previous_version() -> None:
    before = journal._Before(view_id=7, dataset_id=6, version_id=40)
    lines, _ = journal.compensation(
        _request("view.transform.filter", view_id=7), _success(), before
    )
    assert lines == [
        {"cmd": "view version apply", "args": [7, 40, 6], "flags": {"profile": "p", "project": 9}}
    ]


def test_a_first_pipeline_edit_deletes_the_steps_it_added() -> None:
    before = journal._Before(view_id=7, dataset_id=6, task_ids=[])
    lines, _ = journal.compensation(
        _request("view.transform.filter", view_id=7), _success(), before
    )
    assert lines[0]["cmd"] == "view task delete"
    assert lines[0]["keep_tasks"] == []


def test_an_unread_pipeline_cannot_be_undone() -> None:
    lines, reason = journal.compensation(
        _request("view.transform.filter", view_id=7), _success(), journal._Before(view_id=7)
    )
    assert lines == [] and reason is not None


def test_a_permanent_delete_says_why_it_cannot_be_undone() -> None:
    lines, reason = journal.compensation(
        _request("dataset.delete", dataset_id=5), _success(), journal._Before()
    )
    assert lines == []
    assert reason is not None and "permanently" in reason


def test_a_declared_inverse_is_run_with_the_arguments_of_the_write() -> None:
    lines, reason = journal.compensation(
        _request("agent.run.pause", run_id=12), _success(), journal._Before()
    )
    assert reason is None
    assert lines == [
        {"cmd": "agent run resume", "args": [12], "flags": {"profile": "p", "project": 9}}
    ]


def test_a_manual_inverse_is_named_but_not_run() -> None:
    lines, reason = journal.compensation(
        _request("webhook.create", name="w"), _success(), journal._Before()
    )
    assert lines == []
    assert reason is not None and "webhook delete" in reason


def test_a_write_that_made_nothing_for_the_trash_says_so() -> None:
    lines, reason = journal.compensation(
        _request("file.upload"), _success(opens=[]), journal._Before()
    )
    assert lines == [] and reason is not None


def test_an_external_effect_gives_its_own_reason() -> None:
    _, reason = journal.compensation(
        _request("view.export.postgres", view_id=3), _success(), journal._Before()
    )
    assert reason is not None and "PostgreSQL" in reason


def _journaled(
    command_id: str, producer: Any, store: _Memory, **positionals: Any
) -> tuple[Outcome, list[dict[str, Any]]]:
    request = _request(command_id, **positionals)
    request = Request(command_id, "json", producer, invocation=request.invocation, profile="p")
    interceptor = journal.journal_writes(lambda: store, lambda _r: journal._Before())
    with trace.begin(command_id):
        outcome = dispatch(request, (interceptor,))
    return outcome, store.kept


def test_a_read_is_not_journaled() -> None:
    _, kept = _journaled("dataset.get", lambda: ({}, {}), _Memory(), dataset_id=5)
    assert kept == []


def test_a_write_is_journaled_before_and_after() -> None:
    _, kept = _journaled("dataset.trash", lambda: ({"ok": 1}, {}), _Memory(), dataset_id=5)
    assert [record["event"] for record in kept] == ["begin", "end"]
    begin, end = kept
    assert begin["command"] == "dataset.trash" and begin["inv"] == begin["group"]
    assert end["exit"] == 0 and end["undo"][0]["cmd"] == "dataset restore"


def test_a_failed_write_is_journaled_without_an_undo() -> None:
    def refused() -> tuple[Any, dict[str, Any]]:
        raise CliError(code="not_found", message="No.", exit_status=1)

    outcome, kept = _journaled("dataset.trash", refused, _Memory(), dataset_id=5)
    assert outcome.error is not None
    assert kept[-1]["exit"] == 1 and kept[-1]["error_code"] == "not_found"
    assert "undo" not in kept[-1]


def test_a_dry_run_is_not_journaled() -> None:
    store = _Memory()
    request = _request("dataset.trash", dataset_id=5)
    assert request.invocation is not None
    object.__setattr__(request.invocation, "dry_run", True)
    dispatch(request, (journal.journal_writes(lambda: store),))
    assert store.kept == []


def test_a_run_line_joins_the_run_group() -> None:
    store = _Memory()
    interceptor = journal.journal_writes(lambda: store, lambda _r: journal._Before())
    with trace.begin("run") as outer, trace.begin("dataset.trash"):
        dispatch(_request("dataset.trash", dataset_id=5), (interceptor,))
    assert store.kept[0]["group"] == outer.invocation_id
    assert store.kept[0]["inv"] != outer.invocation_id


def test_entries_fold_records_and_status() -> None:
    store = _Memory()
    _journaled("dataset.trash", lambda: ({}, {}), store, dataset_id=5)
    (entry,) = journal.entries(store)
    assert entry.view()["status"] == "done" and entry.view()["undoable"]
    journal.mark_undone(store, entry.inv, "abc")
    (entry,) = journal.entries(store)
    assert entry.view()["status"] == "undone" and not entry.view()["undoable"]


def test_a_begin_without_an_end_is_unknown() -> None:
    store = _Memory()
    store.append({"event": "begin", "inv": "a", "group": "a", "command": "dataset.trash"})
    (entry,) = journal.entries(store)
    assert entry.view()["status"] == "unknown"


def test_the_file_journal_is_owner_only_and_rotates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(journal, "MAX_BYTES", 100)
    store = journal.FileJournal(tmp_path / "journal")
    for number in range(5):
        store.append({"event": "begin", "inv": str(number), "pad": "x" * 40})
    path = tmp_path / "journal" / "journal.jsonl"
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert (tmp_path / "journal" / "journal.1.jsonl").exists()
    assert [record["inv"] for record in store.records()] == ["0", "1", "2", "3", "4"][
        -len(list(store.records())) :
    ]


def test_the_journal_is_off_when_switched_off_or_embedded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert journal.default_store() is not None
    monkeypatch.setenv(journal.JOURNAL_ENV, "0")
    assert journal.default_store() is None
    monkeypatch.delenv(journal.JOURNAL_ENV)
    monkeypatch.setattr(embedded, "active", lambda: True)
    assert journal.default_store() is None
