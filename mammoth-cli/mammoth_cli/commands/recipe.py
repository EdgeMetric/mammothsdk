"""``mammoth recipe``: run a goal recipe as one command (#309).

A recipe in ``discovery/recipes.json`` that declares ``inputs`` and ``run`` is executable.
Its ``run`` lines are ``mammoth run`` lines: they read the caller's values as
``{{inputs.NAME}}`` and earlier results as ``{{steps.NAME.data...}}``, and run through the
same path as ``mammoth run`` (validation, dry run, handler, verify, journal). The recipe's
prose steps (what ``mammoth how`` prints) and its run lines live in the same record, and a
test checks that each line runs a command the steps name, so the two cannot drift.

``recipe run`` asks once (prompt or ``--yes``) before a recipe that writes, then confirms
each line that needs it. A recipe with a destructive line needs ``--yes`` (no prompt), and
only that ``--yes`` confirms the destructive line. ``--dry-run`` previews every line. It stops
at the first failed line, but not at a partial one (exit 3: the step made its object, with a
warning); the run then exits 3 and lists it in ``partial_lines``. Output is the ``mammoth run``
stream: one envelope per line, then a summary naming the recipe.
"""

from __future__ import annotations

import json
from typing import Any

from mammoth_cli.commands import run as run_cmd
from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.discovery import line_record, run_command, runnable_recipes, writes
from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.output.emit import run_id
from mammoth_cli.output.envelope import Meta, Result
from mammoth_cli.runtime.confirm import (
    POLICY_PROMPT_OR_YES,
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.dispatch import Outcome
from mammoth_cli.runtime.invocation import Invocation

CODE_RECIPE_NOT_FOUND = "recipe_not_found"
CODE_RECIPE_INPUT_INVALID = "recipe_input_invalid"

#: The JSON types a recipe input may declare, and the Python types that satisfy each.
_INPUT_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "integer": (int,),
    "array": (list,),
    "object": (dict,),
    # Any JSON value but null: text, a number, a boolean, a list (IN_LIST) or an object.
    "any": (str, int, float, bool, list, dict),
}


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


def recipe_run(invocation: Invocation) -> HandlerResult | Outcome:
    """Run a recipe's steps in one process; 'inputs' fills them. Prompt or '--yes'."""
    recipe = _recipe(invocation.positionals.get("id"))
    inputs = _inputs(recipe, invocation.bound_input().get("inputs"))
    if writes(recipe) and not invocation.dry_run:
        destructive = _destructive_lines(recipe)
        action = f"run the {recipe['id']} recipe ({len(recipe['run'])} steps)"
        if destructive:
            action += f", including destructive steps: {', '.join(destructive)}"
        enforce_confirmation(
            invocation,
            # A destructive step is never confirmed by a prompt the caller may click through:
            # the caller names it by passing --yes.
            policy=POLICY_YES_ALWAYS if destructive else POLICY_PROMPT_OR_YES,
            action=action,
        )
    numbered = [
        (number, json.dumps(_confirmed(line, invocation.yes), ensure_ascii=False))
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
    return Outcome(streamed=True, exit_status=run_exit)


def _destructive_lines(recipe: dict[str, Any]) -> list[str]:
    """The commands of the recipe's destructive lines that really run (not a ``--dry-run``)."""
    return [
        line["cmd"]
        for line in recipe["run"]
        if line_record(line).get("mutation_class") == "destructive" and not _dry_run(line)
    ]


def _dry_run(line: dict[str, Any]) -> bool:
    """Whether the line sets ``--dry-run``, under any spelling ``mammoth run`` accepts."""
    flags = line.get("flags", {})
    return any(
        value is True
        for name, value in flags.items()
        if str(name).lstrip("-").replace("_", "-") == "dry-run"
    )


def _confirmed(line: dict[str, Any], explicit_yes: bool) -> dict[str, Any]:
    """The line with ``yes`` set when its command asks for confirmation.

    ``recipe run`` has already asked once for the whole recipe. A destructive line gets
    ``yes`` only from a caller who passed ``--yes`` themselves, never from the prompt.

    Args:
        line: One of the recipe's ``run`` lines.
        explicit_yes: Whether the caller passed ``--yes`` to ``recipe run``.

    Returns:
        The line, with ``flags.yes`` set where it applies.
    """
    record = line_record(line)
    if record.get("confirmation", "none") == "none":
        return line
    if record.get("mutation_class") == "destructive" and not explicit_yes:
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
        # A boolean is an int in Python, but only an 'any' input means it as a value.
        if not isinstance(value, allowed) or (isinstance(value, bool) and spec["type"] != "any"):
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
