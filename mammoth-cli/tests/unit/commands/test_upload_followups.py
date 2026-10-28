"""``file upload`` follow-ups: waiting workbooks, update method, batch ids, undo, needs_user."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import batch as batch_cmd
from mammoth_cli.commands import file as file_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime import journal
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.verify import with_verify
from mammoth_cli.services import update_method
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_UPLOAD_RESULT = "mammoth.api.files.FilesAPI.upload_result"
_EXTRACT_SHEETS = "mammoth.api.files.FilesAPI.extract_sheets"
_DATASET_GET = "mammoth.api.datasets.DatasetsAPI.get"
_BATCH_LIST = "mammoth.api.batches.BatchesAPI.list"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    login_default_profile()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.csv").write_text("h\n1\n", encoding="utf-8")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _doc(tmp_path: Path, document: dict[str, Any]) -> str:
    path = tmp_path / "in.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return str(path)


_WORKBOOK = {
    "file_id": 77,
    "name": "book.xlsx",
    "status": "action_needed",
    "action_needed": "sheet_selection_required",
    "sheets_info": [{"sheet_name": "Q1"}, {"sheet_name": "Q2"}],
}


def test_a_workbook_waiting_for_sheets_names_the_extract_command(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_UPLOAD_RESULT] = {"dataset_ids": [], "errors": {}, "files": [_WORKBOOK]}
    data, _ = file_cmd.file_upload(_inv("file.upload", extra_args=["a.csv"]))
    assert data["status"] == "needs_sheet_choice"
    assert data["files"][0]["sheets_info"] == ["Q1", "Q2"]
    assert data["files"][0]["next_command"] == (
        'mammoth file extract-sheets 77 --input \'{"sheets": ["Q1"]}\''
    )
    assert "choose" in data["message"]
    assert "cannot do yet" not in data["message"]


def test_a_password_protected_file_names_set_password(fake_service: FakeMammothService) -> None:
    locked = {"file_id": 5, "name": "x.xlsx", "action_needed": "password_required"}
    fake_service.responses[_UPLOAD_RESULT] = {"dataset_ids": [], "errors": {}, "files": [locked]}
    data, _ = file_cmd.file_upload(_inv("file.upload", extra_args=["a.csv"]))
    assert data["status"] == "needs_password"
    assert data["next_command"].startswith("mammoth file set-password 5 --input ./password.json")
    assert "PASSWORD" not in data["next_command"]


def test_a_pdf_with_no_explaining_file_keeps_the_pdf_message(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_UPLOAD_RESULT] = {"dataset_ids": [], "errors": {}, "files": []}
    data, _ = file_cmd.file_upload(_inv("file.upload", extra_args=["a.csv"]))
    assert data["status"] == "no_dataset"
    assert "cannot do yet" not in data["message"]


def test_sheets_input_extracts_the_chosen_sheets(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_UPLOAD_RESULT] = {"dataset_ids": [], "errors": {}, "files": [_WORKBOOK]}
    fake_service.responses[_EXTRACT_SHEETS] = {"job_id": 3}
    data, _ = file_cmd.file_upload(
        _inv("file.upload", extra_args=["a.csv"], input_file=_doc(tmp_path, {"sheets": ["Q2"]}))
    )
    assert (_EXTRACT_SHEETS, {"file_id": 77, "sheets": ["Q2"]}) in fake_service.call_log
    assert data["extract_sheets"] == {"job_id": 3}


def test_need_action_by_header_cause_points_at_interpretation(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_UPLOAD_RESULT] = {"dataset_ids": [58], "errors": {}}
    fake_service.responses[_DATASET_GET] = {
        "dataset": {"id": 58, "status": "need_action", "status_info": {"need_action": "Header row"}}
    }
    data, _ = file_cmd.file_upload(_inv("file.upload", extra_args=["a.csv"]))
    assert data["datasets"][0]["next_command"] == "mammoth dataset interpretation preview 58"


def test_mode_without_append_target_is_invalid(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as excinfo:
        file_cmd.file_upload(
            _inv("file.upload", extra_args=["a.csv"], input_file=_doc(tmp_path, {"mode": "add"}))
        )
    assert excinfo.value.code == "invalid_argument"


def test_append_sets_the_mode_first_and_reports_new_batch_ids(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_UPLOAD_RESULT] = {"dataset_ids": [900], "errors": {}}
    fake_service.responses[update_method.SET_SYMBOL] = {
        "data_addition_mode": "replace",
        "previous_data_addition_mode": "combine",
    }
    fake_service.responses[_DATASET_GET] = {
        "dataset": {"id": 9, "status": "ready", "stats": {"row_count": 4}}
    }

    def _batches(log: list[Any]) -> dict[str, Any]:
        listed = [s for s, _ in log if s == _BATCH_LIST]
        return {"batches": [{"id": 1}] if len(listed) == 1 else [{"id": 1}, {"id": 2}, {"id": 3}]}

    fake_service.responses[_BATCH_LIST] = _batches
    data, _ = file_cmd.file_upload(
        _inv(
            "file.upload",
            extra_args=["a.csv"],
            input_file=_doc(tmp_path, {"append_to_ds_id": 9, "mode": "replace"}),
        )
    )
    assert fake_service.call_log[0][0] == update_method.SET_SYMBOL
    assert fake_service.call_log[0][1]["mode"] == "replace"
    assert data["update_method"]["mode"] == "replace"
    assert data["update_method"]["previous_mode"] == "add"
    assert data["batch_ids"] == [2, 3]
    assert "staging_dataset_ids" not in data
    assert any("keeps it" in w for w in data["warnings"])


def test_append_undo_deletes_each_batch_newest_first() -> None:
    data = {"appended_to": 9, "batch_ids": [2, 3]}
    lines, reason = journal._append_undo(data, {"project": 9}) or ([], None)
    assert [line["args"] for line in lines] == [[9, 3], [9, 2]]
    assert all(line["cmd"] == "batch delete" and line["flags"]["yes"] for line in lines)
    assert reason is None


def test_a_replace_upload_has_no_undo_and_says_why() -> None:
    data = {"appended_to": 9, "batch_ids": [2], "update_method": {"mode": "replace"}}
    lines, reason = journal._append_undo(data, {}) or ([], None)
    assert lines == []
    assert reason == "It replaced the dataset's rows; the rows it replaced are not kept."


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


def test_batch_list_marks_deleted_sources(fake_service: FakeMammothService) -> None:
    fake_service.responses[_BATCH_LIST] = {
        "batches": [
            {"id": 1, "source_props": {"ds_name": "stage (Deleted)"}},
            {"id": 2, "source_props": {"ds_name": "kept"}},
        ]
    }
    data, _ = batch_cmd.batch_list(_inv("batch.list", project=180, extra_args=["9"]))
    first, second = data["batches"]
    assert first["source_deleted"] is True and first["display_name"] == "stage"
    assert first["source_props"] == {"ds_name": "stage (Deleted)"}
    assert "source_deleted" not in second


def test_a_dataset_list_with_need_action_entries_does_not_set_needs_user() -> None:
    data = {"datasets": [{"id": 5, "status": "need_action"}]}
    assert with_verify(data, _inv("dataset.list"))["verify"]["needs_user"] is None
    assert with_verify(data)["verify"]["needs_user"] is None


def test_batch_list_marks_a_deleted_view_source(fake_service: FakeMammothService) -> None:
    fake_service.responses[_BATCH_LIST] = {
        "batches": [{"id": 1, "source_props": {"source_props": {"view_name": "v (Deleted)"}}}]
    }
    data, _ = batch_cmd.batch_list(_inv("batch.list", project=180, extra_args=["9"]))
    assert data["batches"][0]["display_name"] == "v"
