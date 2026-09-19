"""Contract tests for typed ``View.export`` destination routes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import view as view_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _doc(tmp_path: Path, payload: dict[str, object]) -> str:
    path = tmp_path / "input.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


@pytest.fixture(autouse=True)
def _auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def test_dataset_route_uses_view_export_and_exact_parent(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=180,
            extra_args=["7", "9"],
            input_file=_doc(tmp_path, {"dataset_name": "snapshot", "timeout": 30}),
            yes=True,
        )
    )
    assert fake_service.view_call_log == [
        (7, "to_dataset", {"dataset_id": 9, "dataset_name": "snapshot", "timeout": 30})
    ]


def test_dataset_route_names_the_written_dataset_and_its_project(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.view_responses[(7, "to_dataset")] = 114
    data, _meta = view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=58,
            extra_args=["7", "9"],
            input_file=_doc(tmp_path, {"dataset_name": "feed", "target_project_id": 57}),
            yes=True,
        )
    )
    assert fake_service.view_call_log == [
        (7, "to_dataset", {"dataset_id": 9, "dataset_name": "feed", "target_project_id": 57})
    ]
    assert data == {
        "dataset_id": 114,
        "project_id": 57,
        "source_view_id": 7,
        "next": "mammoth view list 114 --project 57",
    }


@pytest.mark.parametrize("file_type", ["csv", "json", "parquet"])
def test_managed_s3_omitted_filename_reaches_sdk_default(
    fake_service: FakeMammothService, tmp_path: Path, file_type: str
) -> None:
    view_cmd.view_export_specialized(
        _inv(
            "view.export.managed-s3",
            project=180,
            extra_args=["7", "9"],
            input_file=_doc(tmp_path, {"file_type": file_type}),
            yes=True,
        )
    )
    assert fake_service.view_call_log == [(7, "to_s3", {"dataset_id": 9, "file_type": file_type})]


def test_postgres_route_requires_confirmation_and_forwards_secret(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    payload = {
        "host": "db.example",
        "port": 5432,
        "database": "analytics",
        "table": "sales",
        "username": "agent",
        "password": "secret",
    }
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.postgres",
                project=180,
                extra_args=["7"],
                input_file=_doc(tmp_path, payload),
            )
        )
    assert error.value.code == "confirmation_required"
    assert fake_service.view_call_log == []

    view_cmd.view_export_specialized(
        _inv(
            "view.export.postgres",
            project=180,
            extra_args=["7", "9"],
            input_file=_doc(tmp_path, payload),
            yes=True,
        )
    )
    assert fake_service.view_call_log == [(7, "to_postgres", {"dataset_id": 9, **payload})]


def test_specialized_route_rejects_unknown_fields_before_service(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.email",
                project=180,
                extra_args=["7"],
                input_file=_doc(tmp_path, {"emails": ["a@example.com"], "recipients": []}),
                yes=True,
            )
        )
    assert error.value.code == "unknown_input_field"
    assert fake_service.view_call_log == []


def test_destination_specific_field_cannot_leak_through_kwargs(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    payload = {
        "host": "db.example",
        "port": 5432,
        "database": "analytics",
        "table": "sales",
        "username": "agent",
        "password": "secret",
        "subject": "email-only option",
    }
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.postgres",
                project=180,
                extra_args=["7", "9"],
                input_file=_doc(tmp_path, payload),
                yes=True,
            )
        )
    assert error.value.code == "unknown_input_field"
    assert error.value.details["unknown"] == ["subject"]
    assert fake_service.view_call_log == []


def test_secret_destination_requires_required_secret_field(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.azure-blob",
                project=180,
                extra_args=["7"],
                input_file=_doc(
                    tmp_path,
                    {
                        "storage_account_name": "acct",
                        "tenant_id": "tenant",
                        "client_id": "client",
                        "container_name": "exports",
                    },
                ),
                yes=True,
            )
        )
    assert error.value.code == "missing_field"
    assert fake_service.view_call_log == []
