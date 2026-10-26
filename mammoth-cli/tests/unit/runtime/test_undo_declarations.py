"""Undo declarations that claimed a reversing command did not exist (#311)."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import journal, opens
from mammoth_cli.runtime.dispatch import Outcome, Request
from mammoth_cli.runtime.invocation import Invocation


def _request(command_id: str, **positionals: Any) -> Request:
    invocation = Invocation(command_id=command_id, output="json", project=9)
    invocation.positionals.update(positionals)
    return Request(command_id, "json", lambda: ({}, {}), invocation=invocation, profile="p")


def _undo(command_id: str, made: list[dict[str, Any]], **positionals: Any) -> Any:
    return journal.compensation(
        _request(command_id, **positionals),
        Outcome(data={}, meta={"opens": made}),
        journal._Before(),
    )


@pytest.mark.parametrize("command_id", ["file.upload-folder", "dataset.create-from-pdf"])
def test_a_command_that_makes_datasets_is_undone_by_trashing_them(command_id: str) -> None:
    assert command_by_id(command_id)["undo"] == {"strategy": "trash_created"}
    made = [{"kind": "dataset", "id": n, "created": True} for n in (11, 12)]
    lines, reason = _undo(command_id, made)
    assert reason is None
    assert [(line["cmd"], line["args"]) for line in lines] == [
        ("dataset trash", [12]),
        ("dataset trash", [11]),
    ]


def test_an_upload_folder_result_that_is_a_bare_list_of_ids_opens_each_dataset() -> None:
    invocation = Invocation(command_id="file.upload-folder", output="json", project=9)
    result = opens._as_result(invocation, [11, 12])
    assert result == {"dataset_ids": [11, 12]}
    assert opens._as_result(invocation, 11) == {"dataset_ids": [11]}
    assert opens._as_result(invocation, None) == {"dataset_ids": []}
    found = opens._targets(invocation, command_by_id("file.upload-folder") or {}, result)
    assert found == [("dataset", 11, True), ("dataset", 12, True)]


def test_another_command_with_a_bare_result_opens_nothing() -> None:
    invocation = Invocation(command_id="dataset.trash", output="json", project=9)
    assert opens._as_result(invocation, [1, 2]) == {}


def test_a_batch_spec_is_removed_by_batch_delete() -> None:
    undo = command_by_id("batch.create-spec")["undo"]
    assert undo == {"strategy": "manual", "command": "batch.delete"}
    lines, reason = _undo("batch.create-spec", [], dataset_id=3)
    assert lines == [] and reason is not None and "batch delete" in reason


@pytest.mark.parametrize(
    "command_id", ["support.workspace.user.add", "support.workspace.user.remove"]
)
def test_the_workspace_user_pair_names_what_the_other_needs(command_id: str) -> None:
    undo = command_by_id(command_id)["undo"]
    assert undo["strategy"] == "manual" and undo["note"]
    lines, reason = _undo(command_id, [], workspace_id=8)
    assert lines == [] and reason is not None and "not run for you" in reason
    assert "needs the id this write made" not in reason


def test_a_same_argument_pair_says_why_it_is_not_run() -> None:
    lines, reason = _undo("dashboard.filter.add", [], dashboard_id=5)
    assert lines == []
    assert reason is not None
    assert "dashboard filter remove" in reason and "needs the id this write made" not in reason
