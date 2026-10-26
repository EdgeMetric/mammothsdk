"""``recipe run``: defects a second independent review found (#318)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli import discovery
from mammoth_cli.app import app
from mammoth_cli.commands import file as file_cmd
from mammoth_cli.commands import recipe as recipe_cmd
from mammoth_cli.commands import run as run_cmd
from mammoth_cli.context import resolver
from mammoth_cli.discovery import runnable_recipes
from mammoth_cli.runtime import dryrun_targets, leaf
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_DATASET_GET = "mammoth.api.datasets.DatasetsAPI.get"
_DATASET_TRASH = "mammoth.api.datasets.DatasetsAPI.trash"
_DELETE = "mammoth.api.datasets.DatasetsAPI.delete"
_BASE = ["--output", "json", "--project", "9"]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> FakeMammothService:
    fake = FakeMammothService()
    fake.responses[_DATASET_GET] = {"dataset": {"id": 7, "name": "Test upload"}}
    fake.responses["mammoth.api.dataviews.DataviewsAPI.list"] = {"dataviews": [{"id": 1}]}

    def build(*_a: Any, **_k: Any) -> FakeMammothService:
        # One service per line, as the real ones are: a dry-run line's gate stays with it.
        return FakeMammothService(responses=fake.responses, call_log=fake.call_log)

    monkeypatch.setattr(service_factory, "build_service", build)
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_a, **_k: 4)
    # The fake keeps its dry-run gate on while a preview names its targets; no target read here.
    monkeypatch.setattr(leaf, "resolve_targets", lambda *_a, **_k: [])
    monkeypatch.setattr(leaf, "resolve_dependents", lambda *_a, **_k: None)
    return fake


def _recipe(*args: str) -> tuple[int, list[dict[str, Any]]]:
    result = make_runner()._runner.invoke(app, ["recipe", *args, *_BASE])
    text = result.stdout + result.stderr
    return result.exit_code, [json.loads(line) for line in text.splitlines() if line]


def _inputs(document: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps({"inputs": document})]


def test_no_shipped_recipe_runs_a_permanent_delete_line() -> None:
    bad = [
        (recipe["id"], line["cmd"])
        for recipe in runnable_recipes()
        for line in recipe["run"]
        if discovery.line_record(line).get("mutation_class") == "destructive"
    ]
    assert bad == []


def test_cleanup_trashes_the_dataset_when_the_name_matches(service: FakeMammothService) -> None:
    code, lines = _recipe(
        "run", "cleanup-mine", *_inputs({"dataset_id": 7, "name": "Test upload"}), "--yes"
    )
    assert code == 0, lines
    symbols = [symbol for symbol, _ in service.call_log]
    assert _DELETE not in symbols
    assert symbols.count(_DATASET_TRASH) == 1, "the dry run sends nothing, the trash sends once"
    assert (_DATASET_TRASH, {"dataset_id": 7, "project_id": 9}) in service.call_log
    assert lines[-1]["data"]["recipe"] == "cleanup-mine"


def test_cleanup_trashes_nothing_when_the_name_differs(service: FakeMammothService) -> None:
    code, lines = _recipe(
        "run", "cleanup-mine", *_inputs({"dataset_id": 7, "name": "Quarterly sales"}), "--yes"
    )
    assert code == 0, lines
    assert _DATASET_TRASH not in [symbol for symbol, _ in service.call_log]
    skipped = [line["cmd"] for line in lines[:-1] if line.get("skipped")]
    assert skipped == ["dataset trash", "dataset trash"]


def test_cleanup_dry_run_previews_the_dependents(service: FakeMammothService) -> None:
    code, lines = _recipe(
        "run", "cleanup-mine", *_inputs({"dataset_id": 7, "name": "Test upload"}), "--dry-run"
    )
    assert code == 0, lines
    assert _DATASET_TRASH not in [symbol for symbol, _ in service.call_log]


def test_a_dataset_trash_dry_run_lists_what_depends_on_the_dataset() -> None:
    fake = FakeMammothService()
    fake.responses["mammoth.api.projects.ProjectsAPI.resource_dependencies"] = {"7": ["view 3"]}
    found = dryrun_targets.resolve_dependents(fake, "dataset.trash", {"dataset_id": 7}, 9)
    assert found is not None and found["checked"] is True and found["resource_ids"] == ["7"]


_DELETE_LINE = {"cmd": "dataset delete", "args": ["{{inputs.dataset_id}}"]}


def test_a_destructive_line_is_confirmed_only_by_the_callers_yes() -> None:
    assert "flags" not in recipe_cmd._confirmed(_DELETE_LINE, False)
    assert recipe_cmd._confirmed(_DELETE_LINE, True)["flags"] == {"yes": True}
    benign = {"cmd": "dataset refresh", "args": [1]}
    assert recipe_cmd._confirmed(benign, False)["flags"] == {"yes": True}


@pytest.mark.parametrize("name", ["dry-run", "dry_run", "--dry-run"])
def test_a_destructive_line_under_dry_run_is_not_a_real_delete(name: str) -> None:
    recipe = {"run": [{**_DELETE_LINE, "flags": {name: True}}]}
    assert recipe_cmd._destructive_lines(recipe) == []


def test_a_recipe_with_a_destructive_line_needs_yes_and_names_the_line(
    service: FakeMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    recipe = {
        "id": "one-delete",
        "title": "Delete one dataset",
        "goals": [],
        "keywords": [],
        "doc": "x.md",
        "steps": [],
        "inputs": {
            "dataset_id": {"type": "integer", "required": True, "example": 1, "help": "A dataset."}
        },
        "run": [_DELETE_LINE],
    }
    monkeypatch.setattr(discovery, "load_recipes", lambda: (recipe,))
    code, lines = _recipe("run", "one-delete", *_inputs({"dataset_id": 7}), "--no-input")
    assert code == 2
    assert lines[-1]["error"]["code"] == "confirmation_required"
    assert "destructive steps: dataset delete" in lines[-1]["error"]["message"]
    assert service.call_log == []
    code, _ = _recipe("run", "one-delete", *_inputs({"dataset_id": 7}), "--yes")
    assert code == 0
    assert (_DELETE, {"dataset_id": 7, "project_id": 9}) in service.call_log


@pytest.mark.parametrize("value", ["Active", 3, 2.5, ["a", "b"], {"from": 1, "to": 2}, True])
def test_an_any_input_takes_any_json_value(value: Any) -> None:
    recipe = {
        "id": "x",
        "inputs": {"value": {"type": "any", "required": True, "help": "A value."}},
        "run": [],
    }
    assert recipe_cmd._inputs(recipe, {"value": value}) == {"value": value}


_VIEWLESS = "This file has more than one plausible way to be read."


def _needs_view_upload(dataset_ids: list[int]) -> dict[str, Any]:
    """What the real ``file upload`` returns for datasets that came up ready with no view."""
    return file_cmd._upload_result(
        dataset_ids, lambda dataset_id: ("ready", {"ready": _VIEWLESS}, f"d{dataset_id}.csv")
    )


@pytest.fixture
def uploads_without_a_view(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """``file upload`` answers with the real needs_view shape; every other line is recorded."""
    calls: list[list[str]] = []
    next_ids = iter([[7], [8]])

    def execute(argv: list[str], command: str = "") -> tuple[int, dict[str, Any]]:
        calls.append(list(argv))
        if argv[:2] == ["file", "upload"]:
            return 0, {"data": _needs_view_upload(next(next_ids))}
        return 0, {"data": {"dataset": {"id": 7}}}

    monkeypatch.setattr(run_cmd, "execute_line", execute)
    return calls


def _example_inputs(recipe_id: str, tmp_path: Path) -> dict[str, Any]:
    recipe = next(r for r in runnable_recipes() if r["id"] == recipe_id)
    inputs: dict[str, Any] = {}
    for name, spec in recipe["inputs"].items():
        value = spec["example"]
        if isinstance(value, str) and value.startswith("./"):
            path = tmp_path / Path(value).name
            path.write_text("a,b\n1,2\n", encoding="utf-8")
            value = str(path)
        inputs[name] = value
    return inputs


@pytest.mark.parametrize("recipe_id", ["upload-clean", "upload-dashboard", "join-files"])
def test_an_upload_with_no_view_ends_the_recipe_with_the_dataset_not_a_crash(
    service: FakeMammothService,
    uploads_without_a_view: list[list[str]],
    recipe_id: str,
    tmp_path: Path,
) -> None:
    inputs = _example_inputs(recipe_id, tmp_path)
    code, lines = _recipe("run", recipe_id, *_inputs(inputs), "--yes")
    assert code == 0, lines
    ran = [argv[:2] for argv in uploads_without_a_view]
    assert ran[-1] == ["dataset", "get"], "the dataset is shown, with its status"
    assert all(argv[0] in ("file", "dataset") for argv in uploads_without_a_view), ran
    assert lines[-1]["data"]["failed"] == 0
    skipped = [line["cmd"] for line in lines[:-1] if line.get("skipped")]
    assert skipped and "dataset get" not in skipped


@pytest.mark.parametrize("recipe_id", ["upload-clean", "upload-dashboard", "join-files"])
def test_a_dry_run_still_plans_the_lines_that_wait_on_the_upload(
    service: FakeMammothService, recipe_id: str, tmp_path: Path
) -> None:
    inputs = _example_inputs(recipe_id, tmp_path)
    code, lines = _recipe("run", recipe_id, *_inputs(inputs), "--dry-run")
    assert code == 0, lines
    waiting = [
        line
        for line in lines[:-1]
        if line["cmd"] in ("view data get", "dashboard v3 generate", "view transform join")
    ]
    assert waiting and not any(line.get("skipped") for line in waiting)
