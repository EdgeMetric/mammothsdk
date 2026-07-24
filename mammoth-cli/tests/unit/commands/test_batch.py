"""Unit tests for the ``batch`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import batch as batch_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_LIST = "mammoth.api.batches.BatchesAPI.list"
_GET = "mammoth.api.batches.BatchesAPI.get"
_CREATE = "mammoth.api.batches.BatchesAPI.create"
_UPDATE = "mammoth.api.batches.BatchesAPI.update"
_DELETE = "mammoth.api.batches.BatchesAPI.delete"
_BULK_DELETE = "mammoth.api.batches.BatchesAPI.bulk_delete"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


# ── list ──────────────────────────────────────────────────────────────────


def test_list_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_list(_inv("batch.list", extra_args=["9"]))
    assert excinfo.value.code == "project_required"


def test_list_requires_dataset_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_list(_inv("batch.list", project=180))
    assert excinfo.value.code == "missing_argument"


def test_list_passes_dataset_and_project(fake_service: FakeMammothService) -> None:
    batch_cmd.batch_list(_inv("batch.list", project=180, extra_args=["9"]))
    assert fake_service.call_log == [(_LIST, {"dataset_id": 9, "project_id": 180})]


def test_list_forwards_limit_offset(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"limit": 10, "offset": 5}), encoding="utf-8")
    batch_cmd.batch_list(_inv("batch.list", project=180, extra_args=["9"], input_file=str(doc)))
    assert fake_service.call_log == [
        (_LIST, {"dataset_id": 9, "project_id": 180, "limit": 10, "offset": 5})
    ]


# ── get ───────────────────────────────────────────────────────────────────


def test_get_uses_positional_dataset_and_batch_id(fake_service: FakeMammothService) -> None:
    batch_cmd.batch_get(_inv("batch.get", project=180, extra_args=["9", "3"]))
    assert fake_service.call_log == [(_GET, {"dataset_id": 9, "batch_id": 3, "project_id": 180})]


def test_get_without_dataset_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_get(_inv("batch.get", project=180))
    assert excinfo.value.code == "missing_argument"


def test_get_without_batch_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_get(_inv("batch.get", project=180, extra_args=["9"]))
    assert excinfo.value.code == "missing_argument"


def test_get_invalid_dataset_id_is_invalid_argument(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_get(_inv("batch.get", project=180, extra_args=["abc", "3"]))
    assert excinfo.value.code == "invalid_argument"


# ── create ────────────────────────────────────────────────────────────────


def test_create_requires_source_id(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"mapping": {"a": "b"}}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_create(
            _inv("batch.create", project=180, extra_args=["9"], input_file=str(doc))
        )
    assert excinfo.value.code == "missing_argument"


def test_create_requires_mapping(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_create(
            _inv("batch.create", project=180, extra_args=["9", "5"], input_file=str(doc))
        )
    assert excinfo.value.code == "missing_field"


def test_create_passes_required_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"mapping": {"a": "b"}}), encoding="utf-8")
    batch_cmd.batch_create(
        _inv("batch.create", project=180, extra_args=["9", "5"], input_file=str(doc))
    )
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "dataset_id": 9,
                "source_id": 5,
                "mapping": {"a": "b"},
                "project_id": 180,
            },
        )
    ]


def test_create_forwards_optional_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps(
            {
                "mapping": {"a": "b"},
                "new_ds_params": {"name": "n"},
                "is_validation_required": True,
                "change_map": {"x": "y"},
                "delete_source_ds": True,
            }
        ),
        encoding="utf-8",
    )
    # delete_source_ds is destructive, so the command now needs --yes.
    batch_cmd.batch_create(
        _inv("batch.create", project=180, extra_args=["9", "5"], input_file=str(doc), yes=True)
    )
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "dataset_id": 9,
                "source_id": 5,
                "mapping": {"a": "b"},
                "project_id": 180,
                "new_ds_params": {"name": "n"},
                "is_validation_required": True,
                "change_map": {"x": "y"},
                "delete_source_ds": True,
            },
        )
    ]


# ── update ────────────────────────────────────────────────────────────────


def test_update_requires_patch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_update(_inv("batch.update", project=180, extra_args=["9"]))
    assert excinfo.value.code == "missing_field"


def test_update_forwards_patch(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"patch": [{"op": "remove", "value": [1, 2]}]}), encoding="utf-8")
    # A ``remove`` op is destructive, so the command now needs --yes.
    batch_cmd.batch_update(
        _inv("batch.update", project=180, extra_args=["9"], input_file=str(doc), yes=True)
    )
    assert fake_service.call_log == [
        (
            _UPDATE,
            {
                "dataset_id": 9,
                "patch": [{"op": "remove", "value": [1, 2]}],
                "project_id": 180,
            },
        )
    ]


def test_create_delete_source_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"mapping": {"a": "b"}, "delete_source_ds": True}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_create(
            _inv("batch.create", project=180, extra_args=["9", "5"], input_file=str(doc))
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_create_without_delete_source_needs_no_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"mapping": {"a": "b"}}), encoding="utf-8")
    batch_cmd.batch_create(
        _inv("batch.create", project=180, extra_args=["9", "5"], input_file=str(doc))
    )
    assert fake_service.call_log[0][1]["dataset_id"] == 9


def test_update_remove_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"patch": [{"op": "remove", "value": [1]}]}), encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_update(
            _inv("batch.update", project=180, extra_args=["9"], input_file=str(doc))
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_update_replace_only_needs_no_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"patch": [{"op": "replace", "value": [1]}]}), encoding="utf-8")
    batch_cmd.batch_update(_inv("batch.update", project=180, extra_args=["9"], input_file=str(doc)))
    assert fake_service.call_log[0][1]["dataset_id"] == 9


# ── delete ────────────────────────────────────────────────────────────────


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_delete(
            _inv("batch.delete", project=180, extra_args=["9", "3"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    batch_cmd.batch_delete(_inv("batch.delete", project=180, extra_args=["9", "3"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"dataset_id": 9, "batch_id": 3, "project_id": 180})]


def test_delete_without_batch_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_delete(_inv("batch.delete", project=180, extra_args=["9"], yes=True))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


# ── bulk-delete ───────────────────────────────────────────────────────────


def test_bulk_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_bulk_delete(
            _inv("batch.bulk-delete", project=180, extra_args=["9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_bulk_delete_proceeds_with_yes_and_no_ids(fake_service: FakeMammothService) -> None:
    batch_cmd.batch_bulk_delete(_inv("batch.bulk-delete", project=180, extra_args=["9"], yes=True))
    assert fake_service.call_log == [(_BULK_DELETE, {"dataset_id": 9, "project_id": 180})]


def test_bulk_delete_forwards_ids(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"ids": [1, 2, 3]}), encoding="utf-8")
    batch_cmd.batch_bulk_delete(
        _inv(
            "batch.bulk-delete",
            project=180,
            extra_args=["9"],
            input_file=str(doc),
            yes=True,
        )
    )
    assert fake_service.call_log == [
        (_BULK_DELETE, {"dataset_id": 9, "project_id": 180, "ids": [1, 2, 3]})
    ]


def test_bulk_delete_requires_dataset_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        batch_cmd.batch_bulk_delete(_inv("batch.bulk-delete", project=180, yes=True))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []
