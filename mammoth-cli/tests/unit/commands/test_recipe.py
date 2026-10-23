"""``mammoth recipe list`` and ``mammoth recipe run``: a goal recipe as one command (#309)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.app import app
from mammoth_cli.commands import how as how_cmd
from mammoth_cli.commands import recipe as recipe_cmd
from mammoth_cli.commands import run as run_cmd
from mammoth_cli.commands.schema import find_schemas
from mammoth_cli.context import resolver
from mammoth_cli.errors.envelope import EXIT_PARTIAL
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_DATASET_GET = "mammoth.api.datasets.DatasetsAPI.get"
_BASE = ["--output", "json", "--project", "9"]

#: A recipe of reads only, so a run needs no confirmation.
_READS = {
    "id": "two-reads",
    "title": "Read a dataset twice",
    "goals": ["read twice"],
    "keywords": [],
    "doc": "references/recipes/x.md",
    "steps": [],
    "inputs": {
        "dataset_id": {"type": "integer", "required": True, "example": 1, "help": "A dataset."},
        "note": {"type": "string", "required": False, "default": "none", "help": "A note."},
    },
    "run": [
        {"name": "first", "cmd": "dataset get", "args": ["{{inputs.dataset_id}}"]},
        {"cmd": "dataset get", "args": ["{{steps.first.data.dataset.id}}"]},
    ],
}
#: A recipe that writes: 'recipe run' asks before it.
_WRITES = {
    **_READS,
    "id": "one-delete",
    "run": [{"cmd": "dataset delete", "args": ["{{inputs.dataset_id}}"]}],
}


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> FakeMammothService:
    fake = FakeMammothService()
    fake.responses[_DATASET_GET] = {"dataset": {"id": 7, "name": "sales"}}
    monkeypatch.setattr(service_factory, "build_service", lambda *_a, **_k: fake)
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_a, **_k: 4)
    monkeypatch.setattr(recipe_cmd, "load_recipes", lambda: (_READS, _WRITES))
    return fake


def _recipe(*args: str) -> tuple[int, list[dict[str, Any]]]:
    result = make_runner()._runner.invoke(app, ["recipe", *args, *_BASE])
    text = result.stdout + result.stderr
    return result.exit_code, [json.loads(line) for line in text.splitlines() if line]


def _inputs(document: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps({"inputs": document})]


def test_run_fills_inputs_and_chains_steps(service: FakeMammothService) -> None:
    code, lines = _recipe("run", "two-reads", *_inputs({"dataset_id": 7}))
    assert code == 0, lines
    assert [line["exit"] for line in lines[:2]] == [0, 0]
    reads = [kw["dataset_id"] for sym, kw in service.call_log if sym == _DATASET_GET]
    assert reads == [7, 7]
    summary = lines[-1]
    assert summary["meta"]["command"] == "recipe run"
    assert summary["data"]["recipe"] == "two-reads"
    assert summary["data"]["inputs"] == {"dataset_id": 7, "note": "none"}
    assert summary["data"]["ok"] == 2


@pytest.mark.parametrize(
    ("document", "message"),
    [
        ({}, "needs 'dataset_id'"),
        ({"dataset_id": "7"}, "must be integer"),
        ({"dataset_id": True}, "must be integer"),
        ({"dataset_id": 7, "colour": "red"}, "no input called colour"),
    ],
)
def test_run_refuses_bad_inputs(
    service: FakeMammothService, document: dict[str, Any], message: str
) -> None:
    code, lines = _recipe("run", "two-reads", *_inputs(document))
    assert code == 2
    error = lines[-1]["error"] if lines else {}
    assert error["code"] == "recipe_input_invalid"
    assert message in error["message"]
    assert "mammoth recipe run two-reads" in error["hint"]
    assert service.call_log == []


def test_run_names_the_recipes_it_knows(service: FakeMammothService) -> None:
    code, lines = _recipe("run", "nope")
    assert code == 2
    assert lines[-1]["error"]["code"] == "recipe_not_found"
    assert lines[-1]["error"]["details"]["known"] == ["two-reads", "one-delete"]


def test_a_writing_recipe_asks_first(service: FakeMammothService) -> None:
    code, lines = _recipe("run", "one-delete", *_inputs({"dataset_id": 7}), "--no-input")
    assert code == 2
    assert lines[-1]["error"]["code"] == "confirmation_required"
    assert service.call_log == []


def test_a_dry_run_previews_without_asking(service: FakeMammothService) -> None:
    code, lines = _recipe("run", "one-delete", *_inputs({"dataset_id": 7}), "--dry-run")
    assert code == 0, lines
    assert lines[0]["data"]["dry_run"] is True
    assert lines[-1]["data"]["dry_run"] is True


def test_list_shows_inputs_and_a_ready_command(service: FakeMammothService) -> None:
    code, lines = _recipe("list")
    assert code == 0
    recipes = {entry["id"]: entry for entry in lines[0]["data"]["recipes"]}
    assert recipes["two-reads"]["writes"] is False
    assert recipes["one-delete"]["writes"] is True
    assert recipes["one-delete"]["run_command"] == (
        'mammoth recipe run one-delete --input \'{"inputs": {"dataset_id": 1, "note": null}}\''
        " --yes"
    )


def test_run_lines_goes_past_a_partial_line_when_asked(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    exits = iter([EXIT_PARTIAL, 0])
    monkeypatch.setattr(run_cmd, "execute_line", lambda *_a: (next(exits), {"data": {}}))
    numbered = [(1, '{"cmd": "dataset get", "args": [1]}'), (2, '{"cmd": "dataset get"}')]
    summary = run_cmd.run_lines(numbered, {}, keep_going=False, dry_run=False, past_partial=True)
    assert summary["ok"] == 1 and summary["failed"] == 0
    assert summary["partial_lines"] == [1]
    assert summary["exit"] == EXIT_PARTIAL
    assert len(capsys.readouterr().out.splitlines()) == 2


def test_how_and_schema_find_offer_the_runnable_recipe() -> None:
    data, _ = how_cmd.how(how_cmd.Invocation(command_id="how", extra_args=["export to csv"]))
    assert data["recipe"]["id"] == "export-csv"
    assert data["run_command"].startswith("mammoth recipe run export-csv ")
    found = find_schemas("export a view to csv")
    assert next(iter(found)) == "query"
    assert found["recipes"][0]["id"] == "export-csv"
