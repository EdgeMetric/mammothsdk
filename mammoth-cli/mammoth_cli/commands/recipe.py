"""``mammoth recipe``: run a goal recipe as one command (#309).

A recipe in ``discovery/recipes.json`` that declares ``inputs`` and ``run`` is executable.
Its ``run`` lines are ``mammoth run`` lines: they read the caller's values as
``{{inputs.NAME}}`` and earlier results as ``{{steps.NAME.data...}}``, and run through the
same path as ``mammoth run`` (validation, dry run, handler, verify, journal). The recipe's
prose steps (what ``mammoth how`` prints) and its run lines live in the same record, and a
test checks that each line runs a command the steps name, so the two cannot drift.

``recipe run`` asks once (prompt or ``--yes``) before a recipe that writes, then confirms
each line that needs it. ``--dry-run`` previews every line. It stops at the first failed
line, but not at a partial one (exit 3: the step made its object, with a warning); the run
then exits 3 and lists it in ``partial_lines``. Output is the ``mammoth run`` stream: one
envelope per line, then a summary naming the recipe.
"""

from __future__ import annotations

import json
from typing import Any

from mammoth_cli.commands import run as run_cmd
from mammoth_cli.discovery import load_recipes
from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.output.emit import run_id
from mammoth_cli.output.envelope import Meta, Result
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.dispatch import EXIT_STATUS_META, STREAMED_META
from mammoth_cli.runtime.invocation import Invocation

HandlerResult = tuple[Any, dict[str, Any]]

CODE_RECIPE_NOT_FOUND = "recipe_not_found"
CODE_RECIPE_INPUT_INVALID = "recipe_input_invalid"

#: The JSON types a recipe input may declare, and the Python types that satisfy each.
_INPUT_TYPES: dict[str, tuple[type, ...]] = {"string": (str,), "integer": (int,)}


def runnable_recipes() -> tuple[dict[str, Any], ...]:
    """The recipes ``recipe run`` can run: those with ``inputs`` and ``run`` lines.

    Returns:
        The executable recipes, in file order.
    """
    return tuple(recipe for recipe in load_recipes() if recipe.get("run"))


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
    return any(_record(line).get("mutation_class", "read") != "read" for line in recipe["run"])


def recipe_list(invocation: Invocation) -> HandlerResult:
    """List the recipes 'recipe run' can run, with their inputs and a ready command."""
    del invocation
    recipes = [
        {
            "id": recipe["id"],
            "title": recipe["title"],
            "inputs": recipe.get("inputs", {}),
            "writes": writes(recipe),
            "steps": [line["cmd"] for line in recipe["run"]],
            "run_command": run_command(recipe),
        }
        for recipe in runnable_recipes()
    ]
    return {"recipes": recipes, "count": len(recipes)}, {}


def recipe_run(invocation: Invocation) -> HandlerResult:
    """Run a recipe's steps in one process; 'inputs' fills them. Prompt or '--yes'."""
    recipe = _recipe(invocation.positionals.get("id"))
    inputs = _inputs(recipe, invocation.bound_input().get("inputs"))
    if writes(recipe) and not invocation.dry_run:
        enforce_confirmation(
            invocation,
            policy=POLICY_PROMPT_OR_YES,
            action=f"run the {recipe['id']} recipe ({len(recipe['run'])} steps)",
        )
    numbered = [
        (number, json.dumps(_confirmed(line), ensure_ascii=False))
        for number, line in enumerate(recipe["run"], start=1)
    ]
    summary = run_cmd.run_lines(
        numbered,
        run_cmd.global_defaults(invocation),
        keep_going=False,
        dry_run=invocation.dry_run,
        scope={"inputs": inputs},
        # A partial step made what it reports (a dashboard with a warning): the read-back
        # after it still shows the caller the result.
        past_partial=True,
    )
    run_exit = summary["exit"]
    data = {"recipe": recipe["id"], "inputs": inputs, **summary}
    meta = Meta(command="recipe run", profile=invocation.profile, exit=run_exit, run_id=run_id())
    run_cmd.write_envelope(Result(data=data, meta=meta).to_envelope())
    return None, {STREAMED_META: True, EXIT_STATUS_META: run_exit}


def _record(line: dict[str, Any]) -> dict[str, Any]:
    return command_by_id(run_cmd.resolve_command_id(line["cmd"].split())) or {}


def _confirmed(line: dict[str, Any]) -> dict[str, Any]:
    """The line with ``yes`` set when its command asks for confirmation.

    ``recipe run`` has already asked once for the whole recipe.
    """
    if _record(line).get("confirmation", "none") == "none":
        return line
    return {**line, "flags": {**line.get("flags", {}), "yes": True}}


def _recipe(recipe_id: Any) -> dict[str, Any]:
    known = runnable_recipes()
    for recipe in known:
        if recipe["id"] == recipe_id:
            return recipe
    raise CliError(
        code=CODE_RECIPE_NOT_FOUND,
        message=f"No runnable recipe is called '{recipe_id}'.",
        exit_status=EXIT_USAGE,
        hint="Run 'mammoth recipe list' for the recipes and their inputs.",
        details={"id": recipe_id, "known": [recipe["id"] for recipe in known]},
    )


def _inputs(recipe: dict[str, Any], given: Any) -> dict[str, Any]:
    """The caller's ``inputs``, checked against what the recipe declares."""
    declared: dict[str, dict[str, Any]] = recipe.get("inputs", {})
    usage = run_command(recipe)
    if given is None:
        given = {}
    if not isinstance(given, dict):
        raise _input_error("'inputs' must be an object.", usage)
    unknown = sorted(set(given) - set(declared))
    if unknown:
        raise _input_error(
            f"The {recipe['id']} recipe takes no input called {', '.join(unknown)}.",
            usage,
            unknown=unknown,
        )
    values: dict[str, Any] = {}
    for name, spec in declared.items():
        if name not in given:
            if spec.get("required"):
                raise _input_error(
                    f"The {recipe['id']} recipe needs '{name}': {spec.get('help', '')}".strip(),
                    usage,
                    missing=name,
                )
            values[name] = spec.get("default")
            continue
        value = given[name]
        allowed = _INPUT_TYPES[spec["type"]]
        if isinstance(value, bool) or not isinstance(value, allowed):
            raise _input_error(f"'{name}' must be {spec['type']}.", usage, field=name)
        values[name] = value
    return values


def _input_error(message: str, usage: str, **details: Any) -> CliError:
    return CliError(
        code=CODE_RECIPE_INPUT_INVALID,
        message=message,
        exit_status=EXIT_USAGE,
        hint=f"For example: {usage}",
        details=details,
    )
