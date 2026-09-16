"""Offline release-shape wire controls for additive ``batch.create-spec``."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from mammoth.api.batches import BatchesAPI
from mammoth.exceptions import MammothValidationError

from mammoth_cli.commands import batch as batch_cmd
from mammoth_cli.commands.schema import get_schema
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation

PROJECT = 3
DATASET = 731


def _inv(input_file: str, **kwargs: Any) -> Invocation:
    return Invocation(
        "batch.create-spec",
        output="json",
        project=PROJECT,
        no_input=True,
        extra_args=[str(DATASET)],
        input_file=input_file,
        **kwargs,
    )


def _invocation_for_dataset(input_file: str, dataset_id: str, **kwargs: Any) -> Invocation:
    return Invocation(
        "batch.create-spec",
        output="json",
        project=PROJECT,
        no_input=True,
        extra_args=[dataset_id],
        input_file=input_file,
        **kwargs,
    )


@contextmanager
def _bind(monkeypatch: pytest.MonkeyPatch, service: Any):
    @contextmanager
    def open_service(_invocation: Invocation):
        yield service, type("Auth", (), {"workspace_id": 4})()

    monkeypatch.setattr(batch_cmd, "open_service", open_service)
    yield


def _input(tmp_path: Path, name: str, payload: dict[str, Any]) -> str:
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_file_id_only_and_release_mapping_array_emit_exact_wire(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    api.default(200, {"batch_id": 42, "status": "created"})
    file_input = _input(tmp_path, "file-spec.json", {"file_id": 94})
    with _bind(monkeypatch, service):
        result, _ = batch_cmd.batch_create_spec(_inv(file_input))
    assert result == {"batch_id": 42, "status": "created"}
    assert (api.last().method, api.last().path.removeprefix("/api/v2"), api.last().json_body) == (
        "POST",
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/batches",
        {"file_id": 94},
    )

    mapping = {
        "source_id": 91,
        "mapping": [
            {
                "source_c_name": "amount",
                "destination_c_name": "amount",
                "expected_destination_c_type": "NUMERIC",
            }
        ],
        "validate_only": True,
    }
    mapping_input = _input(tmp_path, "mapping-spec.json", mapping)
    with _bind(monkeypatch, service):
        batch_cmd.batch_create_spec(_inv(mapping_input))
    assert api.last().json_body == mapping


def test_invalid_or_mixed_release_specs_and_destructive_confirmation_are_local(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    for payload in (
        {"source_id": 91, "file_id": 94},
        {"file_id": 0},
        {"source_id": 91, "mapping": []},
        {
            "source_id": 91,
            "mapping": [
                {
                    "source_c_name": "amount",
                    "destination_c_name": "amount",
                    "expected_destination_c_type": "NUMBER",
                }
            ],
        },
        {"file_id": 94, "new_ds_details": {"name": "x", "unexpected": True}},
    ):
        source = _input(tmp_path, "invalid.json", payload)
        with _bind(monkeypatch, service), pytest.raises(CliError):
            batch_cmd.batch_create_spec(_inv(source))
    destructive = _input(
        tmp_path,
        "destructive.json",
        {"source_id": 91, "mapping": [], "delete_source_ds": True},
    )
    with _bind(monkeypatch, service), pytest.raises(CliError) as error:
        batch_cmd.batch_create_spec(_inv(destructive))
    assert error.value.code == "confirmation_required"
    assert api.requests == []


def test_batch_create_spec_rejects_nonpositive_dataset_without_request(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    source = _input(tmp_path, "valid-file.json", {"file_id": 94})
    invocation = _invocation_for_dataset(source, "0")
    with _bind(monkeypatch, service), pytest.raises(CliError):
        batch_cmd.batch_create_spec(invocation)
    assert api.requests == []


def test_batch_create_spec_schema_discloses_release_alternatives() -> None:
    schema = get_schema("batch.create-spec")
    assert schema is not None
    names = {field["name"] for field in schema["accepted_fields"]}
    assert {"source_id", "mapping", "file_id"}.issubset(names)
    alternatives = schema["input_schema"]["oneOf"]
    assert {"source_id", "mapping"}.issubset(alternatives[0]["required"])
    assert alternatives[1]["required"] == ["file_id"]


def test_destructive_release_spec_requires_matching_source_confirmation(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    source = _input(
        tmp_path,
        "destructive-valid.json",
        {
            "source_id": 91,
            "mapping": [
                {
                    "source_c_name": "a",
                    "destination_c_name": "a",
                    "expected_destination_c_type": "TEXT",
                }
            ],
            "delete_source_ds": True,
        },
    )
    with _bind(monkeypatch, service), pytest.raises(CliError) as error:
        batch_cmd.batch_create_spec(_inv(source, yes=True, confirm="92"))
    assert error.value.code == "confirmation_target_mismatch"
    assert api.requests == []


def test_destructive_release_spec_matching_confirmation_emits_exact_wire(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    api.default(200, {"batch_id": 42, "status": "created"})
    source = _input(
        tmp_path,
        "destructive-valid.json",
        {
            "source_id": 91,
            "mapping": [
                {
                    "source_c_name": "a",
                    "destination_c_name": "a",
                    "expected_destination_c_type": "TEXT",
                }
            ],
            "delete_source_ds": True,
        },
    )
    with _bind(monkeypatch, service):
        batch_cmd.batch_create_spec(_inv(source, yes=True, confirm="91"))
    assert api.last().json_body["delete_source_ds"] is True
    assert api.last().json_body["source_id"] == 91


def test_sdk_rejects_bool_ids_and_mixed_mapping_variants_without_request() -> None:
    class FakeClient:
        workspace_id = 4
        project_id = 3

        def __init__(self) -> None:
            self.calls: list[tuple[Any, Any]] = []

        def _request_json(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((args, kwargs))
            return {}

    client = FakeClient()
    api = BatchesAPI(client)
    for dataset_id, spec in (
        (True, {"file_id": 94}),
        (731, {"source_id": True, "mapping": []}),
        (
            731,
            {
                "source_id": 91,
                "mapping": [
                    {
                        "source_c_name": "a",
                        "destination_c_name": "a",
                        "expected_destination_c_type": "TEXT",
                    },
                    {"source_c_id": "b", "expected_destination_c_type": "TEXT"},
                ],
            },
        ),
    ):
        with pytest.raises(MammothValidationError):
            api.create_spec(dataset_id, spec)
    assert client.calls == []
