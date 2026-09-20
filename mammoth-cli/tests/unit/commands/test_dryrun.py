"""``--dry-run``: the gate stops the command's own request and nothing else."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.confirm import POLICY_YES_ALWAYS, enforce_confirmation
from mammoth_cli.runtime.dryrun import NOTE_OWN, NOTE_UNDECLARED, DryRunStop, jsonable, make_gate
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_DELETE = "mammoth.api.datasets.DatasetsAPI.delete"
_DATASET_GET = "mammoth.api.datasets.DatasetsAPI.get"
_JSON_NO_INPUT = ["--output", "json", "--no-input"]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def test_gate_stops_the_commands_own_symbol_and_reports_it() -> None:
    gate = make_gate("dataset.delete")
    with pytest.raises(DryRunStop) as stop:
        gate(_DELETE, {"dataset_id": 7, "project_id": 180})
    record = stop.value.record
    assert record["dry_run"] is True
    assert record["command"] == "dataset delete"
    assert record["mutation_class"] == "destructive"
    assert record["would_call"] == {
        "sdk_symbol": _DELETE,
        "arguments": {"dataset_id": 7, "project_id": 180},
    }
    assert record["note"] == NOTE_OWN


def test_gate_lets_reads_through_and_stops_undeclared_writes() -> None:
    gate = make_gate("dataset.delete")
    gate(_DATASET_GET, {"dataset_id": 7})  # a read command's symbol: allowed
    with pytest.raises(DryRunStop) as stop:
        gate("mammoth.api.projects.ProjectsAPI.delete", {"project_id": 1})
    assert stop.value.record["note"] == NOTE_UNDECLARED


def test_gate_matches_view_methods_by_the_manifest_symbol() -> None:
    gate = make_gate("view.transform.filter")
    with pytest.raises(DryRunStop) as stop:
        gate("filter_rows", {"filter_type": "REMOVE"}, view_id=144, dataset_id=122)
    would = stop.value.record["would_call"]
    assert would["sdk_symbol"].endswith(".filter_rows")
    assert (would["view_id"], would["dataset_id"]) == (144, 122)


def test_composed_command_writes_count_as_its_own() -> None:
    gate = make_gate("project.ensure")
    with pytest.raises(DryRunStop) as stop:
        gate("mammoth.api.projects.ProjectsAPI.create", {"name": "x"})
    assert stop.value.record["note"] == NOTE_OWN


def test_jsonable_renders_sdk_objects_without_leaking_them() -> None:
    class Cond:
        def to_dict(self) -> dict[str, object]:
            return {"column": "a", "op": "EQ"}

    class View:
        id = 5
        dataset_id = 9

    assert jsonable({"c": Cond(), "v": View(), "n": (1, 2)}) == {
        "c": {"column": "a", "op": "EQ"},
        "v": {"view_id": 5, "dataset_id": 9},
        "n": [1, 2],
    }


def test_confirmation_is_not_required_under_dry_run() -> None:
    invocation = Invocation(command_id="dataset.delete", output="json", dry_run=True)
    enforce_confirmation(invocation, policy=POLICY_YES_ALWAYS, action="delete dataset 7")
    with pytest.raises(CliError):
        enforce_confirmation(
            Invocation(command_id="dataset.delete", output="json"),
            policy=POLICY_YES_ALWAYS,
            action="delete dataset 7",
        )


def test_dry_run_delete_reports_and_sends_nothing(fake_service: FakeMammothService) -> None:
    result = make_runner().invoke(
        ["dataset", "delete", "7", "--project", "180", "--dry-run", *_JSON_NO_INPUT]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["dry_run"] is True
    assert data["would_call"]["sdk_symbol"] == _DELETE
    assert data["would_call"]["arguments"] == {"dataset_id": 7, "project_id": 180}
    assert fake_service.call_log == []


def test_local_validation_still_fails_under_dry_run(fake_service: FakeMammothService) -> None:
    result = make_runner().invoke(
        ["dataset", "delete", "abc", "--project", "180", "--dry-run", *_JSON_NO_INPUT]
    )
    assert result.exit_code == 2
    assert fake_service.call_log == []
