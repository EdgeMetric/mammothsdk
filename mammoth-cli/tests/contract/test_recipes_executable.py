"""The executable recipes in ``discovery/recipes.json`` agree with their own prose steps.

A recipe is one record: ``steps`` (what ``mammoth how`` prints) and ``run`` (what
``mammoth recipe run`` runs). These checks keep the two from drifting: every run line
runs a command the steps name, reads only declared inputs and earlier named lines, and
builds into a valid command line.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from mammoth_cli.commands import recipe as recipe_cmd
from mammoth_cli.commands import run as run_cmd
from mammoth_cli.discovery import line_record, load_recipes, runnable_recipes
from mammoth_cli.runtime import bindings

_REFERENCE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
_RUNNABLE = runnable_recipes()


def _references(value: Any) -> list[str]:
    if isinstance(value, str):
        return _REFERENCE.findall(value)
    if isinstance(value, dict):
        return [ref for item in value.values() for ref in _references(item)]
    if isinstance(value, list):
        return [ref for item in value for ref in _references(item)]
    return []


def test_the_top_recipes_are_executable() -> None:
    assert {recipe["id"] for recipe in _RUNNABLE} >= {
        "append-rows",
        "upload-dashboard",
        "export-csv",
        "share-dashboard",
    }


def test_a_recipe_has_both_inputs_and_run_or_neither() -> None:
    for recipe in load_recipes():
        assert ("run" in recipe) == ("inputs" in recipe), recipe["id"]


@pytest.mark.parametrize("recipe", _RUNNABLE, ids=lambda recipe: recipe["id"])
def test_run_lines_follow_the_steps(recipe: dict[str, Any]) -> None:
    named_in_steps = {step["command_id"] for step in recipe["steps"]}
    for line in recipe["run"]:
        command_id = run_cmd.resolve_command_id(line["cmd"].split())
        assert command_id in named_in_steps, (recipe["id"], command_id)
        # 'cmd' is the whole command path: discovery reads its record without the tree.
        assert line_record(line)["command_id"] == command_id, (recipe["id"], line["cmd"])


@pytest.mark.parametrize("recipe", _RUNNABLE, ids=lambda recipe: recipe["id"])
def test_inputs_are_declared_typed_and_used(recipe: dict[str, Any]) -> None:
    declared = recipe["inputs"]
    used: set[str] = set()
    earlier: set[str] = set()
    for line in recipe["run"]:
        assert set(line) <= set(run_cmd.LINE_KEYS), line
        for reference in _references(line):
            root, name = (bindings.split_path(reference) + [""])[:2]
            if root == "inputs":
                assert name in declared, (recipe["id"], reference)
                used.add(str(name))
            else:
                assert root == "steps" and name in earlier, (recipe["id"], reference)
        if "name" in line:
            earlier.add(line["name"])
    assert used == set(declared), recipe["id"]
    for spec in declared.values():
        assert spec["type"] in recipe_cmd._INPUT_TYPES
        assert spec.get("help")
        assert "example" in spec


@pytest.mark.parametrize("recipe", _RUNNABLE, ids=lambda recipe: recipe["id"])
def test_run_lines_build_with_example_inputs(recipe: dict[str, Any]) -> None:
    inputs = {name: spec["example"] for name, spec in recipe["inputs"].items()}
    pending = [line["name"] for line in recipe["run"] if "name" in line]
    scope = {"inputs": inputs, "steps": {}, "pending": pending}
    for number, line in enumerate(recipe["run"], start=1):
        # Earlier lines' results are not known here: plan=True stands a placeholder in.
        bound = {
            key: _as_id(bindings.resolve(line[key], scope, plan=True))
            for key in run_cmd.BOUND_KEYS
            if key in line
        }
        spec = run_cmd.build_spec(number, {**line, **bound}, {}, run_cmd.command_flags)
        assert spec.argv, (recipe["id"], number)


def _as_id(value: Any) -> Any:
    """``value`` with each placeholder for an unrun step's result read as the id 1."""
    if isinstance(value, bindings.Unresolved):
        return 1
    if isinstance(value, dict):
        return {key: _as_id(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_as_id(item) for item in value]
    return value
