"""``file upload`` follow-ups: waiting workbooks, batch ids, undo, needs_user (pure functions)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import file as file_cmd
from mammoth_cli.runtime import journal
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.verify import with_verify


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _no_status(_dataset_id: int) -> tuple[str, None, None]:
    raise AssertionError("no dataset was made, so no status is read")


_WORKBOOK = {
    "file_id": 77,
    "name": "book.xlsx",
    "status": "action_needed",
    "action_needed": "sheet_selection_required",
    "sheets_info": [{"sheet_name": "Q1"}, {"sheet_name": "Q2"}],
}


def test_a_workbook_waiting_for_sheets_names_the_extract_command() -> None:
    data = file_cmd._upload_result([], _no_status, files=[_WORKBOOK])
    assert data["status"] == "needs_sheet_choice"
    assert data["files"][0]["sheets_info"] == ["Q1", "Q2"]
    assert data["next_command"] == 'mammoth file extract-sheets 77 --input \'{"sheets": ["Q1"]}\''
    assert "choose" in data["message"]


def test_a_password_protected_file_names_set_password() -> None:
    locked = {"file_id": 5, "name": "x.xlsx", "action_needed": "password_required"}
    data = file_cmd._upload_result([], _no_status, files=[locked])
    assert data["status"] == "needs_password"
    assert data["next_command"].startswith("mammoth file set-password 5 --input ./password.json")


def test_a_pdf_with_no_explaining_file_keeps_the_pdf_message() -> None:
    data = file_cmd._upload_result([], _no_status, files=[])
    assert data["status"] == "no_dataset"


def test_need_action_by_header_cause_points_at_interpretation() -> None:
    info = {"need_action": "Header row"}
    data = file_cmd._upload_result([58], lambda _id: ("need_action", info, None))
    assert data["datasets"][0]["next_command"] == "mammoth dataset interpretation preview 58"


def _batch(batch_id: int, file_name: str | None = None, **source: Any) -> dict[str, Any]:
    named = {"file_name": file_name} if file_name else {}
    return {"id": batch_id, "name": "", "row_count": 1, "source": {**named, **source}}


def test_only_the_batch_whose_source_is_the_sent_file_is_this_uploads() -> None:
    before = [_batch(1, "old.csv")]
    after = [_batch(1, "old.csv"), _batch(2, "a.csv"), _batch(3, "other.csv")]
    ours, unmatched = file_cmd._batches_of_upload(before, after, ["a.csv"], [900])
    assert ours == [2]
    assert unmatched == [3]


def test_names_are_compared_by_basename_and_case() -> None:
    after = [_batch(2, "/tmp/x/A.CSV")]
    assert file_cmd._batches_of_upload([], after, ["a.csv"], []) == ([2], [])


def test_a_batch_from_the_staging_dataset_is_this_uploads() -> None:
    after = [_batch(4, datasource_id=900)]
    assert file_cmd._batches_of_upload([], after, ["a.csv"], [900]) == ([4], [])


def test_new_batches_that_match_nothing_are_reported_not_claimed() -> None:
    after = [_batch(5, type="cloud"), _batch(6)]
    assert file_cmd._batches_of_upload([], after, ["a.csv"], [900]) == ([], [5, 6])


def test_sent_names_take_the_basename_of_paths() -> None:
    assert file_cmd._sent_names(["dir/a.csv", Path("b.csv")]) == ["a.csv", "b.csv"]


def test_append_undo_deletes_each_batch_newest_first() -> None:
    data = {"appended_to": 9, "batch_ids": [2, 3], "update_method": {"mode": "add"}}
    lines, reason = journal._append_undo(data, {"project": 9}) or ([], None)
    assert [line["args"] for line in lines] == [[9, 3], [9, 2]]
    assert all(line["cmd"] == "batch delete" and line["flags"]["yes"] for line in lines)
    assert reason is None


def test_a_replace_upload_has_no_undo_and_says_why() -> None:
    data = {"appended_to": 9, "batch_ids": [2], "update_method": {"mode": "replace"}}
    lines, reason = journal._append_undo(data, {}) or ([], None)
    assert lines == []
    assert reason == "It replaced the dataset's rows; the rows it replaced are not kept."


def test_a_replace_mode_read_from_the_stored_settings_refuses_undo() -> None:
    # No ``mode`` was passed: the result carries the mode the dataset already held.
    data = {
        "appended_to": 9,
        "batch_ids": [2],
        "update_method": {"mode": "replace", "effect": "Each new file replaces the rows."},
    }
    lines, reason = journal._append_undo(data, {}) or ([], None)
    assert lines == [] and "replaced" in str(reason)


@pytest.mark.parametrize(
    "method", [None, {"mode": None, "effect": "Unknown."}, {"effect": "no mode"}]
)
def test_an_unknown_mode_refuses_undo_with_a_reason(method: Any) -> None:
    data = {"appended_to": 9, "batch_ids": [2], "update_method": method}
    if method is None:
        del data["update_method"]
    lines, reason = journal._append_undo(data, {}) or ([], None)
    assert lines == []
    assert reason is not None and "not known" in reason


def test_unmatched_batches_alone_give_no_undo_and_say_so() -> None:
    data = {
        "appended_to": 9,
        "batch_ids": [],
        "unmatched_batch_ids": [5],
        "update_method": {"mode": "add"},
    }
    lines, reason = journal._append_undo(data, {}) or ([], None)
    assert lines == [] and reason is not None and "none is deleted" in reason


def test_an_upload_that_is_not_an_append_has_no_batch_undo() -> None:
    assert journal._append_undo({"dataset_ids": [1]}, {}) is None


@pytest.mark.parametrize(
    "data",
    [
        {
            "status": "need_action",
            "datasets": [
                {
                    "id": 5,
                    "status": "need_action",
                    "next_command": "mammoth dataset file-settings get 5",
                }
            ],
        },
        {"status": "unhealthy", "datasets": [{"id": 5, "status": "unhealthy"}]},
        {
            "status": "needs_view",
            "datasets": [
                {"id": 5, "status": "needs_view", "next_command": "mammoth view create 5"}
            ],
        },
        {
            "status": "needs_sheet_choice",
            "message": "Choose sheets.",
            "datasets": [],
            "next_command": "mammoth file extract-sheets 7 --input '{}'",
        },
        {"status": "needs_password", "message": "Locked.", "datasets": []},
    ],
)
def test_upload_outcomes_that_wait_on_a_person_set_needs_user(data: dict[str, Any]) -> None:
    assert with_verify(data, _inv("file.upload"))["verify"]["needs_user"]


def test_needs_user_names_the_dataset_and_next_command() -> None:
    data = {
        "status": "need_action",
        "datasets": [
            {
                "id": 5,
                "name": "a.csv",
                "status": "need_action",
                "next_command": "mammoth dataset file-settings get 5",
            }
        ],
    }
    said = with_verify(data, _inv("file.upload"))["verify"]["needs_user"]
    assert "a.csv" in said and "mammoth dataset file-settings get 5" in said


def test_a_ready_upload_does_not_set_needs_user() -> None:
    data = {"status": "ready", "datasets": [{"id": 5, "status": "ready"}]}
    assert with_verify(data, _inv("file.upload"))["verify"]["needs_user"] is None


def test_a_dataset_list_with_need_action_entries_does_not_set_needs_user() -> None:
    data = {"datasets": [{"id": 5, "status": "need_action"}]}
    assert with_verify(data, _inv("dataset.list"))["verify"]["needs_user"] is None
    assert with_verify(data)["verify"]["needs_user"] is None
