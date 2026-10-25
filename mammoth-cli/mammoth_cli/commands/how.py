"""The ``how`` command: a plain-language goal becomes an ordered command recipe.

``schema find`` names single commands; most goals ("refresh daily", "blend two
files by day") take several, in an order, with ids carried from one step to the
next. ``how`` matches the goal against the recipes in
``mammoth_cli/discovery/recipes.json`` with the same tokens and synonyms
``schema find`` uses, and returns the best recipe's steps, each with the
command, why it is needed, a runnable example and the key flags. Examples are
filled in for the active project and an explicit ``--profile``. A goal no
recipe covers falls back to the ``schema find`` matches and says so.
"""

from __future__ import annotations

import re
from functools import cache
from typing import Any

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.discovery import load_recipes, run_command
from mammoth_cli.errors.envelope import CODE_MISSING_ARGUMENT, EXIT_USAGE, CliError
from mammoth_cli.runtime.invocation import Invocation

#: Goal words that mean the same as words the recipes use. Added to the
#: ``schema find`` synonyms, which also apply.
_HOW_SYNONYMS: dict[str, tuple[str, ...]] = {
    "daily": ("schedule", "refresh", "recurring"),
    "weekly": ("schedule", "refresh", "recurring"),
    "hourly": ("schedule", "refresh", "recurring"),
    "monthly": ("schedule", "refresh", "recurring"),
    "nightly": ("schedule", "refresh", "recurring"),
    "automatically": ("automate", "recurring"),
    "blend": ("join", "merge"),
    "merge": ("join", "blend"),
    "vlookup": ("join", "lookup"),
    "stuck": ("need_action", "pending", "waiting"),
    "hung": ("stuck",),
    "chart": ("dashboard", "figure"),
    "graph": ("chart", "dashboard"),
    "plot": ("chart", "dashboard"),
    "dedupe": ("duplicates", "duplicate"),
    "deduplicate": ("duplicates", "duplicate"),
    "everything": ("cleanup", "all"),
    "erase": ("delete", "remove"),
    "wipe": ("delete", "cleanup"),
    "made": ("created",),
    "created": ("made",),
    "date": ("day",),
    "day": ("date",),
}
_MAX_ALTERNATIVES = 3
_MAX_FALLBACK_STEPS = 5
_NO_RECIPE_HINT = (
    "No recipe matched this goal, so these steps are the closest single commands from "
    "'mammoth schema find'. Run 'mammoth schema get COMMAND_ID' for a command's inputs, "
    "or describe the goal in other words."
)
_NOTHING_HINT = (
    "No recipe and no command matched this goal. Try other words, or run "
    "'mammoth schema list' for every command."
)


@cache
def _recipe_vocabulary(recipe_id: str) -> frozenset[str]:
    from mammoth_cli.commands.schema.find import _tokens

    recipe = next(r for r in load_recipes() if r["id"] == recipe_id)
    words = " ".join([recipe["id"], recipe["title"], *recipe["goals"], *recipe.get("keywords", [])])
    return _tokens(words)


def _term_forms(term: str, compounds: frozenset[str]) -> frozenset[str]:
    from mammoth_cli.commands.schema.find import _token_aliases

    # "refreshes", "joined", "building": the recipe words are the plain forms.
    stems = {term[: -len(end)] for end in ("es", "s", "ed", "ing") if term.endswith(end)}
    stems = {stem for stem in stems if len(stem) >= 3}
    return (
        _token_aliases(term) | frozenset(_HOW_SYNONYMS.get(term, ())) | frozenset(stems) | compounds
    )


#: Where a goal with several parts splits: "join X and Y, then build a dashboard".
_CLAUSE_SPLIT = re.compile(r"\s*(?:;|,|\band then\b|\bthen\b|\band\b|\bthat\b|\bwhich\b)\s*")


def _clause_recipe(clause: str, prefer: str | None = None) -> dict[str, Any] | None:
    """The one recipe a clause of a longer goal clearly asks for, or None.

    Two or more of its words match the recipe, or, in a clause of one or two
    words, one word the recipe itself uses ("join orders", "refresh daily").
    """
    from mammoth_cli.commands.schema.find import _adjacent_compound_forms, _query_tokens, _tokens

    terms = _query_tokens(clause) or tuple(_tokens(clause))
    if not terms:
        return None
    compounds = _adjacent_compound_forms(terms)
    best: tuple[int, int, int, int, dict[str, Any]] | None = None
    for order, recipe in enumerate(load_recipes()):
        vocabulary = _recipe_vocabulary(recipe["id"])
        hits = [t for t in terms if _term_forms(t, compounds.get(t, frozenset())) & vocabulary]
        literal = sum(1 for term in hits if term in vocabulary)
        if not (len(hits) >= 2 or (len(terms) <= 2 and literal >= 1)):
            continue
        # The recipe that fits the whole goal wins any clause it also fits.
        candidate = (int(recipe["id"] == prefer), len(hits), literal, -order, recipe)
        if best is None or candidate[:4] > best[:4]:
            best = candidate
    return best[4] if best else None


#: Where each recipe sits in a pipeline; a composed goal runs them in this order.
_STAGE = {
    "append-rows": 0,
    "stuck-upload": 0,
    "blend-by-key": 1,
    "clean-data": 2,
    "upload-dashboard": 3,
    "share-dashboard": 4,
    "export-csv": 4,
    "export-powerbi": 4,
    "refresh-daily": 5,
    "cleanup-mine": 6,
}


def _compose(goal: str, prefer: str | None = None) -> list[tuple[str, dict[str, Any]]]:
    """Each clause of a several-part goal with its recipe, in pipeline order, no repeats."""
    clauses = [part.strip() for part in _CLAUSE_SPLIT.split(goal) if part.strip()]
    if len(clauses) < 2:
        return []  # one part: the whole-goal match decides
    found: list[tuple[str, dict[str, Any]]] = []
    for clause in clauses:
        recipe = _clause_recipe(clause, prefer)
        if recipe is not None and all(recipe["id"] != seen["id"] for _, seen in found):
            found.append((clause, recipe))
    return sorted(found, key=lambda item: _STAGE.get(item[1]["id"], 3))


def _rank(goal: str) -> list[tuple[int, dict[str, Any]]]:
    """Recipes that fit ``goal``, best first, each with how many goal words it matched."""
    from mammoth_cli.commands.schema.find import _adjacent_compound_forms, _query_tokens, _tokens

    terms = _query_tokens(goal) or tuple(_tokens(goal))
    if not terms:
        return []
    compounds = _adjacent_compound_forms(terms)
    folded = " ".join(goal.casefold().split())
    ranked: list[tuple[float, int, int, int, dict[str, Any]]] = []
    for order, recipe in enumerate(load_recipes()):
        vocabulary = _recipe_vocabulary(recipe["id"])
        matched = sum(
            1 for term in terms if _term_forms(term, compounds.get(term, frozenset())) & vocabulary
        )
        # More than half the words, or half of them when that is at least two
        # (the rest are usually the caller's own data words: "customer id").
        if not (matched * 2 > len(terms) or (matched * 2 == len(terms) and matched >= 2)):
            continue
        # A word the recipe itself uses outranks one reached only through a synonym.
        literal = sum(1 for term in terms if term in vocabulary)
        phrase = int(any(folded == goal_text.casefold() for goal_text in recipe["goals"]))
        ranked.append((matched / len(terms), phrase, literal, -order, recipe))
    ranked.sort(key=lambda item: (item[0], item[1], item[2], item[3]), reverse=True)
    return [(literal, recipe) for _, _, literal, _, recipe in ranked]


def runnable_for(goal: str, limit: int = 2) -> list[dict[str, Any]]:
    """The executable recipes that fit ``goal``, best first, each with its run command.

    Args:
        goal: The caller's goal, in their words.
        limit: The most recipes to return.

    Returns:
        Each recipe's id, title and ``run_command``.
    """
    return [
        {
            "id": recipe["id"],
            "title": recipe["title"],
            "run_command": run_command(recipe),
            "full_detail_command": f"mammoth how \"{recipe['goals'][0]}\"",
        }
        for _, recipe in _rank(goal)
        if recipe.get("run")
    ][:limit]


def _context(invocation: Invocation) -> dict[str, Any]:
    from mammoth_cli.runtime.session import resolved_project

    try:
        project_id = resolved_project(invocation)
    except CliError:
        project_id = invocation.project
    explicit_profile = None if invocation.profile_is_default else invocation.profile
    return {"project_id": project_id, "profile": explicit_profile}


def _scope(command_id: str) -> str:
    from mammoth_cli.commands.schema import command_scope
    from mammoth_cli.manifest.loader import command_by_id

    record = command_by_id(command_id)
    return command_scope(record) if record else "local"


def _fill(example: str, command_id: str, context: dict[str, Any]) -> str:
    """``example`` with the project id and an explicit profile written in."""
    project_id = context["project_id"]
    scope = _scope(command_id)
    filled = example
    if "{project_id}" in filled:
        filled = filled.replace("{project_id}", str(project_id or "PROJECT_ID"))
    elif scope == "project" and project_id is not None:
        filled += f" --project {project_id}"
    if context["profile"] and scope != "local":
        filled += f" --profile {context['profile']}"
    return filled


def _command_path(command_id: str) -> str:
    from mammoth_cli.manifest.loader import command_by_id

    record = command_by_id(command_id)
    path = str(record["command_path"]) if record else command_id.replace(".", " ")
    return f"mammoth {path}"


def _recipe_steps(recipe: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "step": index,
            "command": _command_path(step["command_id"]),
            "command_id": step["command_id"],
            "purpose": step["purpose"],
            "example": _fill(step["example"], step["command_id"], context),
            "key_flags": list(step.get("key_flags", [])),
        }
        for index, step in enumerate(recipe["steps"], start=1)
    ]


def _fallback_steps(goal: str, context: dict[str, Any]) -> list[dict[str, Any]]:
    from mammoth_cli.commands.schema.find import find_schemas
    from mammoth_cli.manifest.loader import command_by_id

    found = find_schemas(goal)
    entries = (found.get("matches") or found.get("suggestions") or [])[:_MAX_FALLBACK_STEPS]
    steps: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        command_id = str(entry["command_id"])
        record = command_by_id(command_id) or {}
        example = entry.get("agent_example") or record.get("agent_example") or ""
        steps.append(
            {
                "step": index,
                "command": _command_path(command_id),
                "command_id": command_id,
                "purpose": entry.get("matched_on") or entry.get("summary") or "",
                "example": _fill(str(example), command_id, context) if example else "",
                "key_flags": [],
            }
        )
    return steps


def how(invocation: Invocation) -> HandlerResult:
    """Turn a plain-language goal into an ordered recipe of commands."""
    goal = invocation.positionals.get("goal")
    if goal is None and invocation.extra_args:
        goal = " ".join(invocation.extra_args)
    if not isinstance(goal, str) or not goal.strip():
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="This command requires a GOAL argument.",
            exit_status=EXIT_USAGE,
            hint='Describe the goal in plain words: mammoth how "refresh a dataset daily".',
        )
    context = _context(invocation)
    ranked = _rank(goal)
    composed = _compose(goal, ranked[0][1]["id"] if ranked else None)
    if len(composed) >= 2 or (composed and not ranked):
        # A goal with several parts gets every part's steps, not only the best one's.
        return _composed_result(goal, composed, context), {}
    if not ranked:
        steps = _fallback_steps(goal, context)
        return {
            "goal": goal,
            "matched": False,
            "context": context,
            "steps": steps,
            "notes": [],
            "alternatives": [],
            "hint": _NO_RECIPE_HINT if steps else _NOTHING_HINT,
        }, {}
    _, best = ranked[0]
    result = {
        "goal": goal,
        "matched": True,
        "recipe": {"id": best["id"], "title": best["title"], "doc": best["doc"]},
        "context": context,
        "steps": _recipe_steps(best, context),
        "notes": list(best.get("notes", [])),
        "alternatives": [
            {
                "id": recipe["id"],
                "title": recipe["title"],
                "command": f'mammoth how "{recipe["goals"][0]}"',
            }
            for _, recipe in ranked[1 : 1 + _MAX_ALTERNATIVES]
        ],
    }
    if best.get("run"):
        # The steps as one command: an agent runs it instead of chaining them by hand.
        result["run_command"] = run_command(best)
        result["inputs"] = best.get("inputs", {})
    return result, {}


#: Steps that set up the data a recipe works on; a composed recipe keeps the first of each.
_SETUP_COMMANDS = frozenset(
    {"file.upload", "view.list", "view.get", "view.data.get", "dataset.get", "dataset.list"}
)


def _composed_result(
    goal: str, composed: list[tuple[str, dict[str, Any]]], context: dict[str, Any]
) -> dict[str, Any]:
    """One ordered recipe from the recipes of a several-part goal's clauses.

    A later recipe works on what the earlier ones made, so its own setup (an upload, a
    read of the view) is left out once an earlier recipe has that step.
    """
    steps: list[dict[str, Any]] = []
    seen: set[str] = set()
    notes: list[str] = []
    uploads = 0
    for _clause, recipe in composed:
        for step in _recipe_steps(recipe, context):
            if step["command_id"] in _SETUP_COMMANDS and step["command_id"] in seen:
                continue
            seen.add(step["command_id"])
            entry = {**step, "recipe": recipe["id"]}
            if step["command_id"] == "file.upload":
                # The data comes first, whichever part of the goal brought the upload.
                steps.insert(uploads, entry)
                uploads += 1
            else:
                steps.append(entry)
        notes.extend(note for note in recipe.get("notes", []) if note not in notes)
    steps = [{**step, "step": index} for index, step in enumerate(steps, start=1)]
    first = composed[0][1]
    return {
        "goal": goal,
        "matched": True,
        "recipe": {"id": first["id"], "title": first["title"], "doc": first["doc"]},
        "recipes": [
            {"id": recipe["id"], "title": recipe["title"], "doc": recipe["doc"], "for": clause}
            for clause, recipe in composed
        ],
        "context": context,
        "steps": steps,
        "notes": notes,
        "alternatives": [],
    }
