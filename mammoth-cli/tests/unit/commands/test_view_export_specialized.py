"""Contract tests for typed ``View.export`` destination routes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import view as view_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import POLICY_NONE
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


def test_dataset_route_inlines_the_target_view_instead_of_a_relist_hint(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    # A dataset export (create or append) never changes the target dataset's
    # view id; when it can be resolved here, the response carries it instead
    # of sending the agent back through a separate 'view list' call.
    fake_service.view_responses[(7, "to_dataset")] = 114
    fake_service.responses["mammoth.api.dataviews.DataviewsAPI.list"] = {
        "dataviews": [{"id": 220, "name": "Store sales combined"}]
    }
    data, _meta = view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=58,
            extra_args=["7", "9"],
            input_file=_doc(tmp_path, {"dataset_name": "feed", "target_ds_id": 114}),
            yes=True,
        )
    )
    assert data == {
        "dataset_id": 114,
        "project_id": 58,
        "source_view_id": 7,
        "view_id": 220,
        "view_name": "Store sales combined",
    }
    assert "next" not in data
    assert (
        "mammoth.api.dataviews.DataviewsAPI.list",
        {"dataset_id": 114, "project_id": 58},
    ) in fake_service.call_log


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


# ---------------------------------------------------------------------------
# DEFECT 1 parity: runtime confirmation gate vs. manifest `confirmation`
# ---------------------------------------------------------------------------
#
# The in-app agent product decides whether to show a confirmation card from
# the MANIFEST's `confirmation` field alone -- it never runs the CLI to find
# out. A runtime gate the manifest does not declare (or a manifest promise
# the runtime does not honor) is therefore invisible to that product. This
# sweeps every typed `view.export.*` destination and asserts the two agree,
# so a future destination cannot silently drift the same way
# `view.export.dataset` did (manifest: confirmation=none; runtime: always
# demanded --yes).

# One plausible value per required field name used across `_SPECIAL_EXPORTS`,
# just enough to satisfy `_require_field` and reach the confirmation gate.
_FIELD_FAKES: dict[str, object] = {
    "dataset_name": "snapshot",
    "storage_account_name": "acct",
    "tenant_id": "tenant",
    "client_id": "client",
    "client_secret": "secret",
    "container_name": "exports",
    "selected_profile": {"name": "dataset", "value": [["proj", "dataset"]]},
    "selected_identity": {"identity_config": {}, "host": "sa@example.iam.gserviceaccount.com"},
    "table": "sales",
    "host": "db.example",
    "username": "agent",
    "password": "secret",
    "index": "logs",
    "emails": ["a@example.com"],
    "domain": "example.com",
    "directory": "/exports",
    "file": "out.csv",
    "port": 5432,
    "database": "analytics",
    "user_id": "user-1",
    "dataset": "reports",
    "base_url": "https://api.example.com",
    "endpoint_path": "/ingest",
    "site_url": "https://tenant.sharepoint.com/sites/team",
    "server_url": "https://tableau.example.com",
    "token_name": "token",
    "token_secret": "token-secret",
}


def _payload_for(required: tuple[str, ...]) -> dict[str, object]:
    return {name: _FIELD_FAKES[name] for name in required}


@pytest.mark.parametrize("command_id", sorted(view_cmd._SPECIAL_EXPORTS))
def test_export_route_confirmation_matches_manifest(
    command_id: str, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    record = command_by_id(command_id)
    assert record is not None, command_id
    _method, required, _secrets = view_cmd._SPECIAL_EXPORTS[command_id]
    payload = _payload_for(required)

    try:
        view_cmd.view_export_specialized(
            _inv(
                command_id,
                project=180,
                extra_args=["7", "9"],
                input_file=_doc(tmp_path, payload),
            )
        )
    except CliError as error:
        runtime_requires_confirmation = error.code == "confirmation_required"
    else:
        runtime_requires_confirmation = False

    manifest_requires_confirmation = record["confirmation"] != POLICY_NONE
    assert runtime_requires_confirmation == manifest_requires_confirmation, (
        f"{command_id}: manifest confirmation={record['confirmation']!r} but the runtime "
        f"{'did' if runtime_requires_confirmation else 'did not'} demand --yes without it"
    )


def test_csv_export_route_confirmation_matches_manifest(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """`view.export.csv` never calls `enforce_confirmation`; assert that
    matches its manifest entry (`confirmation: none`) rather than assuming it."""
    record = command_by_id("view.export.csv")
    assert record is not None
    assert record["confirmation"] == POLICY_NONE

    try:
        view_cmd.view_export_csv(
            _inv(
                "view.export.csv",
                extra_args=["7"],
                input_file=_doc(tmp_path, {"output_path": str(tmp_path / "out.csv")}),
            )
        )
    except CliError as error:
        assert error.code != "confirmation_required"
