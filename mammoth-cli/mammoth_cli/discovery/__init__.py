"""Data files for command discovery: goal recipes, known limitations, next commands.

The recipe helpers here only read the recipes and the command manifests, so ``how`` and
``schema find`` can offer a recipe without importing the command runner.
"""

from __future__ import annotations

import json
from functools import cache
from importlib import resources
from typing import Any

from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.embed_scope import recipe_hidden_embedded


@cache
def load_recipes() -> tuple[dict[str, Any], ...]:
    """The goal recipes shipped in the package.

    Returns:
        Every recipe in ``recipes.json``, in file order.
    """
    text = resources.files(__name__).joinpath("recipes.json").read_text("utf-8")
    return tuple(json.loads(text)["recipes"])


def runnable_recipes() -> tuple[dict[str, Any], ...]:
    """The recipes ``recipe run`` can run: those with ``inputs`` and ``run`` lines.

    Returns:
        The executable recipes, in file order.
    """
    return tuple(recipe for recipe in load_recipes() if recipe.get("run"))


def visible_recipes() -> tuple[dict[str, Any], ...]:
    """The recipes this call can follow: an embedded call drops those that need a local file.

    Returns:
        The recipes discovery may offer, in file order.
    """
    return tuple(recipe for recipe in load_recipes() if not recipe_hidden_embedded(recipe))


def offered_recipes() -> tuple[dict[str, Any], ...]:
    """The runnable recipes this call can run.

    Returns:
        The executable recipes among :func:`visible_recipes`, in file order.
    """
    return tuple(recipe for recipe in visible_recipes() if recipe.get("run"))


def task_summaries() -> list[dict[str, Any]]:
    """The executable recipes as one short record each, for the index commands.

    ``schema list`` and ``capability find`` put these ahead of the single commands, so an
    agent picks a whole task before it reads a family of operations.

    Returns:
        Each task's ``id``, ``title``, whether it ``writes`` and its ``run_command``.
    """
    return [
        {
            "id": recipe["id"],
            "title": recipe["title"],
            "writes": writes(recipe),
            "run_command": run_command(recipe),
        }
        for recipe in offered_recipes()
    ]


def run_command(recipe: dict[str, Any]) -> str:
    """The ``recipe run`` command for a recipe, with each input's example value.

    Args:
        recipe: An executable recipe.

    Returns:
        A command line an agent can adapt.
    """
    example = {name: spec.get("example") for name, spec in recipe.get("inputs", {}).items()}
    document = json.dumps({"inputs": example}, separators=(", ", ": "))
    confirm = " --yes" if writes(recipe) else ""
    return f"mammoth recipe run {recipe['id']} --input '{document}'{confirm}"


def writes(recipe: dict[str, Any]) -> bool:
    """Whether any of the recipe's lines runs a command that is not a read.

    Args:
        recipe: An executable recipe.

    Returns:
        True when running the recipe changes something.
    """
    return any(line_record(line).get("mutation_class", "read") != "read" for line in recipe["run"])


def line_record(line: dict[str, Any]) -> dict[str, Any]:
    """The manifest record of the command a recipe line runs.

    A recipe line's ``cmd`` is a full command path (its positionals go in ``args``), so it
    names the command id directly; a contract test checks it against the command tree.

    Args:
        line: One of a recipe's ``run`` lines.

    Returns:
        The command record, or an empty dict for an unknown command.
    """
    return command_by_id(line["cmd"].replace(" ", ".")) or {}
