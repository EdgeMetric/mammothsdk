"""Independent five-shape M2 command-contract pilot oracles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.commands import file as file_cmd
from mammoth_cli.commands import view_ops as view_ops_cmd
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.commands.schema import schema_entries
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.strict import validate_input_fields
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.command_contract import (
    PILOT_COMMANDS,
    ContractBindingError,
    ResolvedCommandContract,
    resolve_command_contract,
)
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

from .m2_oracles import (
    ASYNC_DASHBOARD_ORACLE,
    FOREIGN_LOOKUP_ORACLE,
    MATH_CONDITION_ORACLE,
    UPLOAD_INPUT_ORACLE,
    UPLOAD_POSITIONAL_ORACLE,
    ZERO_INPUT_ORACLE,
)


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def isolated_cli_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Keep this contract fixture independent from the unit-test conftest."""
    monkeypatch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir",
        lambda *_args, **_kwargs: str(tmp_path),
    )
    return tmp_path


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> FakeMammothService:
    service = FakeMammothService()

    def _build(auth: Any, **kwargs: Any) -> FakeMammothService:
        return service

    monkeypatch.setattr(service_factory, "build_service", _build)
    return service


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, payload: dict[str, Any]) -> str:
    path = tmp_path / "m2-input.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_zero_input_read_has_no_sdk_keywords(fake_service) -> None:
    dashboard_cmd.dashboard_source_list(_inv("dashboard.source.list"))
    assert fake_service.call_log == [(ZERO_INPUT_ORACLE["sdk_symbol"], ZERO_INPUT_ORACLE["kwargs"])]


@pytest.mark.parametrize(
    ("extra_args", "payload", "oracle"),
    [
        (
            ["./pilot-positional.csv"],
            {
                "folder_resource_id": "folder-sentinel",
                "append_to_ds_id": 731,
                "override_target_schema": True,
                "wait_for_completion": False,
                "timeout": 47,
            },
            UPLOAD_POSITIONAL_ORACLE,
        ),
        (
            [],
            {
                "files": ["./pilot-input.csv"],
                "folder_resource_id": "folder-input-sentinel",
                "append_to_ds_id": 732,
                "override_target_schema": False,
                "wait_for_completion": False,
                "timeout": 48,
            },
            UPLOAD_INPUT_ORACLE,
        ),
    ],
)
def test_upload_preserves_positional_or_input_fallback(
    fake_service,
    tmp_path: Path,
    extra_args: list[str],
    payload: dict[str, Any],
    oracle: dict[str, Any],
) -> None:
    file_cmd.file_upload(
        _inv("file.upload", extra_args=extra_args, input_file=_write(tmp_path, payload))
    )
    assert fake_service.call_log == [(oracle["sdk_symbol"], oracle["kwargs"])]


def test_math_forwards_condition_and_distinct_optional_values(fake_service, tmp_path: Path) -> None:
    oracle = MATH_CONDITION_ORACLE
    document = {**oracle["kwargs"], "dataset_id": 122}
    file = _write(tmp_path, document)
    view_ops_cmd.view_transform_math(
        _inv("view.transform.math", extra_args=["41"], input_file=file)
    )
    assert fake_service.view_call_log == [(oracle["view_id"], oracle["method"], document)]


def test_foreign_lookup_forwards_new_column_type(fake_service, tmp_path: Path) -> None:
    oracle = FOREIGN_LOOKUP_ORACLE
    document = {**oracle["kwargs"], "dataset_id": 122}
    file = _write(tmp_path, document)
    view_ops_cmd.view_transform_lookup(
        _inv("view.transform.lookup", extra_args=["42"], input_file=file)
    )
    assert fake_service.view_call_log == [(oracle["view_id"], oracle["method"], document)]


def test_async_dashboard_generation_preserves_job_response(fake_service, tmp_path: Path) -> None:
    oracle = ASYNC_DASHBOARD_ORACLE
    fake_service.responses[oracle["sdk_symbol"]] = oracle["response"]
    data, _ = dashboard_cmd.dashboard_create(
        _inv(
            "dashboard.create",
            extra_args=[oracle["kwargs"]["intent"]],
            input_file=_write(
                tmp_path,
                {
                    "source": oracle["kwargs"]["source"],
                    "enable_filters": oracle["kwargs"]["enable_filters"],
                    "enable_pages": oracle["kwargs"]["enable_pages"],
                },
            ),
        )
    )
    assert fake_service.call_log == [(oracle["sdk_symbol"], oracle["kwargs"])]
    assert data == oracle["response"]


def test_contract_is_immutable_and_rejects_an_undeclared_binding() -> None:
    contract = resolve_command_contract("view.transform.lookup")
    assert contract is not None
    assert isinstance(contract, ResolvedCommandContract)
    with pytest.raises(TypeError):
        contract.input_bindings["dropped"] = "dropped"  # type: ignore[index]
    with pytest.raises(ContractBindingError):
        contract.bind({"dropped": "sentinel"})


def test_contract_rejects_an_undeclared_context_binding() -> None:
    """A handler typo must not silently discard a context value."""
    contract = resolve_command_contract("dashboard.source.list")
    assert contract is not None
    with pytest.raises(ContractBindingError, match="Context field"):
        contract.bind({}, wrong_context=123)


def test_pilot_adapters_are_explicit_and_bound_to_registered_handlers() -> None:
    """The five-case pilot is explicit; it is not a claim of full migration."""
    assert PILOT_COMMANDS == {
        "file.upload",
        "view.transform.math",
        "view.transform.lookup",
        "dashboard.create",
        "dashboard.source.list",
    }
    for command_id in PILOT_COMMANDS:
        contract = resolve_command_contract(command_id)
        assert contract is not None
        assert command_id in HANDLERS
        assert contract.adapter_inputs <= contract.declared_input_names


def test_admission_and_schema_discovery_share_the_resolved_contract() -> None:
    """Schema fields and runtime admission must have one accepted-field set."""
    by_id = {
        entry["command_id"]: entry
        for entry in schema_entries()
        if entry["command_id"] in PILOT_COMMANDS
    }
    assert set(by_id) == PILOT_COMMANDS
    for command_id, entry in by_id.items():
        contract = resolve_command_contract(command_id)
        assert contract is not None
        expected = contract.accepted_field_names
        assert {field["name"] for field in entry["accepted_fields"]} == expected
        assert set(entry["input_schema"]["properties"]) == expected
        # Independent from the handlers: a field not present in the resolved
        # contract must fail before service dispatch.
        with pytest.raises(CliError) as error:
            validate_input_fields(command_id, {"__dropped_binding__": "sentinel"})
        assert getattr(error.value, "code", None) == "unknown_input_field"
