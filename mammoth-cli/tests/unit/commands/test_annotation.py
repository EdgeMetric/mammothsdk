"""Unit tests for the ``annotation`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import annotation as annotation_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_COMMENT_ADD = "mammoth.api.annotations.AnnotationsAPI.comment_add"
_CREATE = "mammoth.api.annotations.AnnotationsAPI.create"
_COMMENT_EDIT = "mammoth.api.annotations.AnnotationsAPI.comment_edit"
_COMMENT_DELETE = "mammoth.api.annotations.AnnotationsAPI.comment_delete"
_ACCESS = "mammoth.api.annotations.AnnotationsAPI.access"
_DELETE = "mammoth.api.annotations.AnnotationsAPI.delete"
_LIST = "mammoth.api.annotations.AnnotationsAPI.list"
_UPDATE = "mammoth.api.annotations.AnnotationsAPI.update"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


# -- comment.add -------------------------------------------------------------


def test_comment_add_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_comment_add(_inv("annotation.comment.add", extra_args=["7"]))
    assert excinfo.value.code == "project_required"


def test_comment_add_requires_annotation_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_comment_add(_inv("annotation.comment.add", project=180))
    assert excinfo.value.code == "missing_argument"


def test_comment_add_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_comment_add(
            _inv("annotation.comment.add", project=180, extra_args=["7"])
        )
    assert excinfo.value.code == "missing_field"


def test_comment_add_dispatches(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"body": "Looks good"}), encoding="utf-8")
    annotation_cmd.annotation_comment_add(
        _inv("annotation.comment.add", project=180, extra_args=["7"], input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_COMMENT_ADD, {"annotation_id": 7, "body": "Looks good", "project_id": 180})
    ]


# -- comment.edit / comment.delete / access (PRD-3685) -------------------------------


def test_comment_edit_needs_both_ids_and_a_body(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as no_comment:
        annotation_cmd.annotation_comment_edit(
            _inv("annotation.comment.edit", project=180, extra_args=["7"])
        )
    assert no_comment.value.code == "missing_argument"
    with pytest.raises(CliError) as not_int:
        annotation_cmd.annotation_comment_edit(
            _inv("annotation.comment.edit", project=180, extra_args=["7", "x"])
        )
    assert not_int.value.code == "invalid_argument"
    with pytest.raises(CliError) as no_body:
        annotation_cmd.annotation_comment_edit(
            _inv("annotation.comment.edit", project=180, extra_args=["7", "9"])
        )
    assert no_body.value.code == "missing_field"
    assert fake_service.call_log == []


def test_comment_edit_dispatches_both_ids_and_the_body(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"body": "Fixed"}), encoding="utf-8")
    annotation_cmd.annotation_comment_edit(
        _inv("annotation.comment.edit", project=180, extra_args=["7", "9"], input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_COMMENT_EDIT, {"annotation_id": 7, "comment_id": 9, "body": "Fixed", "project_id": 180})
    ]


def test_comment_delete_asks_first_then_deletes_the_comment(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_comment_delete(
            _inv("annotation.comment.delete", project=180, extra_args=["7", "9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []
    annotation_cmd.annotation_comment_delete(
        _inv("annotation.comment.delete", project=180, extra_args=["7", "9"], yes=True)
    )
    assert fake_service.call_log == [
        (_COMMENT_DELETE, {"annotation_id": 7, "comment_id": 9, "project_id": 180})
    ]


def test_comment_delete_needs_the_comment_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_comment_delete(
            _inv("annotation.comment.delete", project=180, extra_args=["7"], yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_access_reads_the_project_access(fake_service: FakeMammothService) -> None:
    annotation_cmd.annotation_access(_inv("annotation.access", project=180))
    assert fake_service.call_log == [(_ACCESS, {"project_id": 180})]


def test_access_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_access(_inv("annotation.access"))
    assert excinfo.value.code == "project_required"


# -- create -------------------------------------------------------------------


def test_create_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_create(_inv("annotation.create"))
    assert excinfo.value.code == "project_required"


def test_create_requires_target_type(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_create(_inv("annotation.create", project=180))
    assert excinfo.value.code == "missing_field"


def test_create_requires_target_id(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"target_type": "dataset"}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_create(
            _inv("annotation.create", project=180, input_file=str(doc))
        )
    assert excinfo.value.code == "missing_field"


def test_create_requires_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"target_type": "dataset", "target_id": 9}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_create(
            _inv("annotation.create", project=180, input_file=str(doc))
        )
    assert excinfo.value.code == "missing_field"


def test_create_dispatches(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"target_type": "dataset", "target_id": 9, "body": "Note"}),
        encoding="utf-8",
    )
    annotation_cmd.annotation_create(_inv("annotation.create", project=180, input_file=str(doc)))
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "target_type": "dataset",
                "target_id": 9,
                "body": "Note",
                "project_id": 180,
            },
        )
    ]


# -- delete ---------------------------------------------------------------------


def test_delete_requires_annotation_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_delete(_inv("annotation.delete", project=180))
    assert excinfo.value.code == "missing_argument"


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_delete(
            _inv("annotation.delete", project=180, extra_args=["7"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    annotation_cmd.annotation_delete(
        _inv("annotation.delete", project=180, extra_args=["7"], yes=True)
    )
    assert fake_service.call_log == [(_DELETE, {"annotation_id": 7, "project_id": 180})]


# -- list -------------------------------------------------------------------------


def test_list_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_list(_inv("annotation.list"))
    assert excinfo.value.code == "project_required"


def test_list_passes_project_only(fake_service: FakeMammothService) -> None:
    annotation_cmd.annotation_list(_inv("annotation.list", project=180))
    assert fake_service.call_log == [(_LIST, {"project_id": 180})]


def test_list_forwards_target_filters(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"target_type": "dataset", "target_id": 9}), encoding="utf-8")
    annotation_cmd.annotation_list(_inv("annotation.list", project=180, input_file=str(doc)))
    assert fake_service.call_log == [
        (_LIST, {"project_id": 180, "target_type": "dataset", "target_id": 9})
    ]


# -- update -----------------------------------------------------------------------


def test_update_requires_annotation_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_update(_inv("annotation.update", project=180))
    assert excinfo.value.code == "missing_argument"


def test_update_requires_status(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        annotation_cmd.annotation_update(_inv("annotation.update", project=180, extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_update_dispatches(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"status": "resolved"}), encoding="utf-8")
    annotation_cmd.annotation_update(
        _inv("annotation.update", project=180, extra_args=["7"], input_file=str(doc))
    )
    assert fake_service.call_log == [
        (_UPDATE, {"annotation_id": 7, "status": "resolved", "project_id": 180})
    ]
