"""The task layer (#309): every recipe is executable, plans under ``--dry-run`` and ranks first."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.app import app
from mammoth_cli.commands import how as how_cmd
from mammoth_cli.commands.capability import find_capabilities
from mammoth_cli.commands.schema import schema_index
from mammoth_cli.commands.schema.find import find_schemas
from mammoth_cli.context import resolver
from mammoth_cli.discovery import load_recipes, runnable_recipes
from mammoth_cli.runtime import journal, leaf
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_FIND_DATASET = "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview"
_HISTORY_ID = "97b9ee41d15d"
_BASE = ["--output", "json", "--project", "9"]
_RUNNABLE = runnable_recipes()


_STOPS_ON_NO_DUPLICATES = {"remove-duplicates"}


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> FakeMammothService:
    fake = FakeMammothService()
    fake.responses[_FIND_DATASET] = 5
    # remove-duplicates reads the view's columns to turn key_columns into ignore_columns.
    fake.responses["mammoth.api.dataviews.DataviewsAPI.get"] = {
        "metadata": (
            [{"display_name": "Order ID", "internal_name": "c1"}]
            + [{"display_name": "Other", "internal_name": "c2"}]
        )
    }
    store = journal.FileJournal(journal.journal_dir())
    store.append(
        {"event": "begin", "inv": _HISTORY_ID, "group": "g1", "command": "dataset.trash", "ts": "t"}
    )
    store.append({"event": "end", "inv": _HISTORY_ID, "exit": 0, "undo": [], "irreversible": None})
    monkeypatch.setattr(service_factory, "build_service", lambda *_a, **_k: fake)
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_a, **_k: 4)
    # The fake keeps its dry-run gate on while a preview names its targets; no target read here.
    monkeypatch.setattr(leaf, "resolve_targets", lambda *_a, **_k: [])
    monkeypatch.setattr(leaf, "resolve_dependents", lambda *_a, **_k: None)
    return fake


def _example(spec: dict[str, Any], tmp_path: Path) -> Any:
    """The input's example, with a file path swapped for a real file under ``tmp_path``."""
    value = spec["example"]
    if isinstance(value, str) and value.startswith("./"):
        path = tmp_path / Path(value).name
        path.write_text("a,b\n1,2\n", encoding="utf-8")
        return str(path)
    return value


def _dry_run(recipe: dict[str, Any], tmp_path: Path) -> tuple[int, list[dict[str, Any]]]:
    example = {name: _example(spec, tmp_path) for name, spec in recipe["inputs"].items()}
    args = ["recipe", "run", recipe["id"], "--dry-run", "--input", json.dumps({"inputs": example})]
    result = make_runner()._runner.invoke(app, [*args, *_BASE])
    text = result.stdout + result.stderr
    return result.exit_code, [json.loads(line) for line in text.splitlines() if line]


@pytest.mark.parametrize("recipe", _RUNNABLE, ids=lambda recipe: recipe["id"])
def test_a_dry_run_plans_every_line(
    service: FakeMammothService, recipe: dict[str, Any], tmp_path: Path
) -> None:
    code, lines = _dry_run(recipe, tmp_path)
    if recipe["id"] in _STOPS_ON_NO_DUPLICATES:
        # The fake view holds no rows: the preview counts zero duplicates and stops the recipe
        # before any copy is made (the live test covers the run with duplicates).
        assert lines[-1]["data"]["failed_lines"] == [1], lines
        assert lines[0]["error"]["code"] == "no_op", lines
        return
    assert code == 0, lines
    summary = lines[-1]["data"]
    assert summary["recipe"] == recipe["id"]
    assert summary["dry_run"] is True
    assert summary["failed"] == 0 and summary["lines"] == len(recipe["run"])
    # Every line answers: planned, skipped by its 'when', or previewed with the call it makes.
    assert len(lines) - 1 >= len(recipe["run"])


def test_every_recipe_is_an_executable_task() -> None:
    assert len(runnable_recipes()) == len(load_recipes()) >= 20


def test_every_task_has_a_stage_for_composed_goals() -> None:
    assert {recipe["id"] for recipe in load_recipes()} <= set(how_cmd._STAGE)


@pytest.mark.parametrize("recipe", load_recipes(), ids=lambda recipe: recipe["id"])
def test_a_tasks_first_goal_finds_that_task(recipe: dict[str, Any]) -> None:
    ranked = how_cmd._rank(recipe["goals"][0])
    assert ranked and ranked[0][1]["id"] == recipe["id"]
    found = find_schemas(recipe["goals"][0])
    assert recipe["id"] in [task["id"] for task in found["recipes"]]


def test_an_optional_line_is_skipped_when_its_input_is_empty(
    service: FakeMammothService,
) -> None:
    inputs = {"view_id": 1, "dataset_id": 2, "fill_column": "region"}
    args = ["recipe", "run", "clean-data", "--dry-run", "--input", json.dumps({"inputs": inputs})]
    result = make_runner()._runner.invoke(app, [*args, *_BASE])
    lines = [json.loads(line) for line in (result.stdout + result.stderr).splitlines() if line]
    assert result.exit_code == 0, lines
    assert lines[0]["cmd"] == "view transform convert-type" and lines[0]["skipped"] is True
    assert lines[1]["data"]["would_call"]["sdk_symbol"] == "View.discard_duplicates"


def test_schema_list_puts_tasks_before_the_families() -> None:
    index = schema_index()
    assert next(iter(index)) == "tasks"
    assert {task["id"] for task in index["tasks"]} == {r["id"] for r in runnable_recipes()}
    assert all(task["run_command"].startswith("mammoth recipe run ") for task in index["tasks"])
    # The long tail is still there: every family, and each family's own listing.
    assert any(family["family"] == "view" for family in index["families"])
    assert schema_index("view")["total"] > 100
    assert "tasks" not in schema_index("view")


def test_capability_find_offers_the_task_before_the_operations() -> None:
    found = find_capabilities("export a view to csv")
    assert next(iter(found)) == "query" and list(found)[1] == "tasks"
    assert found["tasks"][0]["id"] == "export-csv"
    assert found["matches"], "the matching operations are still listed"
    assert "tasks" not in find_capabilities("export a view to csv", cursor=1)


def test_schema_find_lists_tasks_before_matches() -> None:
    found = find_schemas("deduplicate a dataset")
    keys = list(found)
    assert keys.index("recipes") < keys.index("matches")
    assert found["recipes"][0]["id"] == "remove-duplicates"
    assert found["matches"], "single commands stay reachable after the task"
