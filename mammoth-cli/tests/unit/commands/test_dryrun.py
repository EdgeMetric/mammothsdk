"""``--dry-run``: the gate stops the command's own request and nothing else."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.confirm import POLICY_YES_ALWAYS, enforce_confirmation
from mammoth_cli.runtime.dryrun import (
    NOTE_OWN,
    NOTE_UNDECLARED,
    DryRunStop,
    jsonable,
    make_gate,
    resolve_targets,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_DELETE = "mammoth.api.datasets.DatasetsAPI.delete"
_DATASET_GET = "mammoth.api.datasets.DatasetsAPI.get"
_DATAVIEW_GET = "mammoth.api.dataviews.DataviewsAPI.get"
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
    assert record["irreversible"] is True
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
    fake_service.responses[_DATASET_GET] = {"id": 7, "name": "sales.csv"}
    result = make_runner().invoke(
        ["dataset", "delete", "7", "--project", "180", "--dry-run", *_JSON_NO_INPUT]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["dry_run"] is True
    assert data["would_call"]["sdk_symbol"] == _DELETE
    assert data["would_call"]["arguments"] == {"dataset_id": 7, "project_id": 180}
    # dataset_delete reads the dataset first to name the export writing into it
    # (T1-O-10) in the confirmation message; that read is a `read` symbol, so
    # the gate lets it through even under --dry-run. Only the delete itself,
    # the command's own symbol, is withheld.
    # The second read is the target-name lookup for the report's ``targets``.
    assert fake_service.call_log == [(_DATASET_GET, {"dataset_id": 7, "project_id": 180})] * 2


def test_local_validation_still_fails_under_dry_run(fake_service: FakeMammothService) -> None:
    result = make_runner().invoke(
        ["dataset", "delete", "abc", "--project", "180", "--dry-run", *_JSON_NO_INPUT]
    )
    assert result.exit_code == 2
    assert fake_service.call_log == []


class _NamedService:
    """Answers each get by id, so a bulk report can be checked target by target."""

    def __init__(self, names: dict[int, object]) -> None:
        self.names = names

    def call(self, sdk_symbol: str, /, **kwargs: int) -> dict[str, object]:
        key = kwargs.get("dataview_id", kwargs.get("dataset_id"))
        assert isinstance(key, int)
        return {"id": key, "name": self.names.get(key)}


def test_dry_run_delete_reports_the_named_target(fake_service: FakeMammothService) -> None:
    fake_service.responses[_DATASET_GET] = {"id": 7, "name": "sales.csv"}
    result = make_runner().invoke(
        ["dataset", "delete", "7", "--project", "180", "--dry-run", *_JSON_NO_INPUT]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["targets"] == [{"type": "dataset", "id": 7, "name": "sales.csv"}]
    assert (data["mutation_class"], data["irreversible"]) == ("destructive", True)


def test_dry_run_non_destructive_mutation_is_reversible_and_named(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_DATASET_GET] = {"id": 7, "name": "sales.csv"}
    result = make_runner().invoke(
        ["dataset", "rename", "7", "--input", '{"name": "x"}', "--project", "180"]
        + ["--dry-run", *_JSON_NO_INPUT]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert (data["mutation_class"], data["irreversible"]) == ("benign_mutation", False)
    assert data["targets"] == [{"type": "dataset", "id": 7, "name": "sales.csv"}]


def test_dry_run_view_delete_names_the_view_not_its_parent(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_DATAVIEW_GET] = {"id": 9, "name": "Q3 view"}
    result = make_runner().invoke(
        ["view", "delete", "9", "5", "--project", "180", "--dry-run", *_JSON_NO_INPUT]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["data"]["targets"] == [
        {"type": "view", "id": 9, "name": "Q3 view"}
    ]
    assert fake_service.call_log[-1] == (
        _DATAVIEW_GET,
        {"dataset_id": 5, "dataview_id": 9},
    )


def test_resolve_targets_bulk_names_every_id() -> None:
    service = _NamedService({7: "a.csv", 8: "b.csv"})
    would = {"arguments": {"dataset_ids": [7, 8], "project_id": 180}}
    assert resolve_targets(service, "dataset.bulk-delete", would) == [  # type: ignore[arg-type]
        {"type": "dataset", "id": 7, "name": "a.csv"},
        {"type": "dataset", "id": 8, "name": "b.csv"},
    ]
    views = {"arguments": {"dataset_id": 5, "dataview_ids": [8, 7]}}
    assert [t["name"] for t in resolve_targets(service, "view.bulk-delete", views)] == [  # type: ignore[arg-type]
        "b.csv",
        "a.csv",
    ]


def test_unresolvable_target_fails_loud_naming_the_id(fake_service: FakeMammothService) -> None:
    fake_service.responses[_DATASET_GET] = {"id": 8}
    result = make_runner().invoke(
        ["dataset", "bulk-delete", "--input", '{"dataset_ids": [8]}', "--project", "180"]
        + ["--dry-run", *_JSON_NO_INPUT]
    )
    assert result.exit_code == 5, result.output
    error = json.loads(result.output)["error"]
    assert error["code"] == "resource_not_found"
    assert "dataset 8" in error["message"]
    assert error["hint"]
    assert "targets" not in result.output
