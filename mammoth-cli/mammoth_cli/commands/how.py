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
from mammoth_cli.runtime.embed_scope import recipe_hidden_embedded
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
_NOT_HERE_HINT = (
    "The recipe for this goal needs the user's machine (a local file or the run history), "
    "which the app does not have. Use the app's own tools for that part."
)
_TIED_HINT = (
    "More than one recipe fits this goal equally well, and running the wrong one changes "
    "data. Pick one from 'alternatives' (mammoth how \"...\" shows its steps), or say more "
    "about what the goal changes."
)
_UNRESOLVED_HINT = (
    "Part of this goal fits more than one recipe equally well, and running the wrong one "
    "changes data, so nothing is matched. 'unresolved' names each such part with its "
    "recipes; 'recipes' are the parts that are clear. Say which recipe the unclear part "
    "means, or run the parts one by one with mammoth how."
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

    return _token_aliases(term) | frozenset(_HOW_SYNONYMS.get(term, ())) | _stems(term) | compounds


def _stems(term: str) -> frozenset[str]:
    # "refreshes", "joined", "building": the recipe words are the plain forms.
    stems = {term[: -len(end)] for end in ("es", "s", "ed", "ing") if term.endswith(end)}
    return frozenset(stem for stem in stems if len(stem) >= 3)


def _intent_met(recipe: dict[str, Any], action: list[_Form], rest: list[_Form]) -> bool:
    """Whether the goal says what the recipe does, not only words it shares with it.

    A recipe declares ``intent``: groups of words, the action first and then its object.
    Each group needs one goal word (or a stem or synonym of one). Generic words
    ("column", "view", "convert") sit in the vocabulary of many recipes, so overlap on
    them proves nothing. A recipe marked ``bare_ok`` is also met by its action word alone
    ("undo", "pivot this"): a goal with no other word names no other object. ``action``
    is checked against the first group and ``rest`` against the others; they differ for
    one clause of a longer goal, which may name its object elsewhere ("upload sales.csv,
    then make a dashboard").
    """
    first, *others = recipe["intent"]
    if recipe.get("bare_ok") and not _names_object(first, action):
        return any(form & frozenset(first) for _, form in action)
    return any(form & frozenset(first) and _distinct(others, rest, {word}) for word, form in action)


def _names_object(first: list[str], forms: list[_Form]) -> bool:
    """Whether the goal has a content word besides the recipe's action words."""
    from mammoth_cli.commands.schema.find import _DISCOVERY_STOPWORDS

    return any(not form & (frozenset(first) | _DISCOVERY_STOPWORDS) for _, form in forms)


def _distinct(groups: list[list[str]], forms: list[_Form], used: set[str]) -> bool:
    """Whether each group can be met by a different goal word.

    Words are told apart by the word itself: the same word read in a clause and in the whole
    goal has different compounds, so its form sets differ, but it is still one word.

    One word that a synonym turns into two ("weekly" is also "refresh") must not meet the
    action and the object of a recipe by itself.
    """
    if not groups:
        return True
    head, *tail = groups
    return any(
        word not in used and form & frozenset(head) and _distinct(tail, forms, used | {word})
        for word, form in forms
    )


def _rejected(
    recipe: dict[str, Any], terms: tuple[str, ...], compounds: dict[str, frozenset[str]]
) -> bool:
    """Whether the goal has a word for the opposite job ("merge" for a split)."""
    reject = frozenset(recipe.get("reject", ()))
    return any(form & reject for _, form in _forms(terms, compounds))


#: A goal word and its forms.
_Form = tuple[str, frozenset[str]]


def _forms(terms: tuple[str, ...], compounds: dict[str, frozenset[str]]) -> list[_Form]:
    """Each word with its stems and compounds, but not the ``how`` synonyms or the
    ``schema find`` aliases: those widen a word ("download" also means "csv", "weekly" also
    means "refresh"), which is right for finding a recipe and wrong for deciding what the
    user asked to have done to their data. Intent groups list the words they accept."""
    return [(term, frozenset({term, *compounds.get(term, ())}) | _stems(term)) for term in terms]


#: Where a goal with several parts splits: "join X and Y, then build a dashboard".
_CLAUSE_SPLIT = re.compile(r"\s*(?:;|,|\band then\b|\bthen\b|\band\b|\bthat\b|\bwhich\b)\s*")


def _clause_fits(clause: str, prefer: str | None = None, goal: str = "") -> list[dict[str, Any]]:
    """The recipe a clause of a longer goal clearly asks for, or the recipes tied for it.

    One recipe is a clear ask; two or more fit the clause equally; none is an empty list.

    Two or more of its words match the recipe, or, in a clause of one or two
    words, one word the recipe itself uses ("join orders", "refresh daily").
    """
    from mammoth_cli.commands.schema.find import (
        _adjacent_compound_forms,
        _ordered_tokens,
        _query_tokens,
    )

    terms = _query_tokens(clause) or _ordered_tokens(clause)
    if not terms:
        return []
    compounds = _adjacent_compound_forms(terms)
    whole = _query_tokens(goal) or _ordered_tokens(goal)
    whole_compounds = _adjacent_compound_forms(whole)
    # Intent reads every word, the small ones too ("by", "per"), as in _rank.
    clause_words, whole_words = _ordered_tokens(clause), _ordered_tokens(goal)
    clause_forms = _forms(clause_words, _adjacent_compound_forms(clause_words))
    whole_forms = _forms(whole_words, _adjacent_compound_forms(whole_words))
    fits: list[tuple[tuple[int, int, int, int], dict[str, Any]]] = []
    for order, recipe in enumerate(load_recipes()):
        # The recipe that fits the whole goal is judged on all of it: "upload a csv" alone
        # does not say "clean", and a "merge" anywhere in the goal rules out a split.
        if _rejected(recipe, whole, whole_compounds) or not _intent_met(
            recipe, clause_forms if recipe["id"] != prefer else whole_forms, whole_forms
        ):
            continue
        vocabulary = _recipe_vocabulary(recipe["id"])
        hits = [t for t in terms if _term_forms(t, compounds.get(t, frozenset())) & vocabulary]
        literal = sum(1 for term in hits if term in vocabulary)
        if not (len(hits) >= 2 or (len(terms) <= 2 and literal >= 1)):
            continue
        # The recipe that fits the whole goal wins any clause it also fits.
        fits.append(((int(recipe["id"] == prefer), len(hits), literal, -order), recipe))
    fits.sort(key=lambda fit: fit[0], reverse=True)
    # Recipes that fit equally well: file order must not pick one.
    return [recipe for key, recipe in fits if key[:3] == fits[0][0][:3]]


#: How well a recipe fits a goal: share of words matched, whole-phrase match, literal words.
_Key = tuple[float, int, int]

#: Where each recipe sits in a pipeline; a composed goal runs them in this order.
_STAGE = {
    "append-rows": 0,
    "stuck-upload": 0,
    "upload-clean": 0,
    "blend-by-key": 1,
    "join-files": 1,
    "lookup-column": 1,
    "clean-data": 2,
    "remove-duplicates": 2,
    "fill-blanks-with-value": 2,
    "rename-columns": 2,
    "find-replace": 2,
    "split-column": 2,
    "extract-date-part": 2,
    "add-calculated-column": 2,
    "pivot-summary": 2,
    "top-n": 2,
    "summarize-by": 2,
    "compare-views": 2,
    "upload-dashboard": 3,
    "dashboard-from-view": 3,
    "share-dashboard": 4,
    "export-csv": 4,
    "filter-export-csv": 4,
    "export-xlsx": 4,
    "export-to-s3": 4,
    "email-view": 4,
    "export-powerbi": 4,
    "refresh-daily": 5,
    "refresh-now": 5,
    "undo-last-change": 6,
    "revert-view-version": 6,
    "cleanup-mine": 6,
}


def _compose(
    goal: str, prefer: str | None = None
) -> tuple[list[tuple[str, dict[str, Any]]], list[tuple[str, list[dict[str, Any]]]]]:
    """Each clause of a several-part goal with its recipe, in pipeline order, no repeats.

    Also the clauses that fit two or more recipes equally, each with those recipes: a
    clause the goal does not settle is reported, not dropped.
    """
    clauses = [part.strip() for part in _CLAUSE_SPLIT.split(goal) if part.strip()]
    if len(clauses) < 2:
        return [], []  # one part: the whole-goal match decides
    found: list[tuple[str, dict[str, Any]]] = []
    unresolved: list[tuple[str, list[dict[str, Any]]]] = []
    for clause in clauses:
        fits = [r for r in _clause_fits(clause, prefer, goal) if not recipe_hidden_embedded(r)]
        if len(fits) > 1:
            unresolved.append((clause, fits))
        elif fits and all(fits[0]["id"] != seen["id"] for _, seen in found):
            found.append((clause, fits[0]))
    return sorted(found, key=lambda item: _STAGE.get(item[1]["id"], 3)), unresolved


def _rank(goal: str) -> list[tuple[_Key, dict[str, Any]]]:
    """Recipes that fit ``goal``, best first, each with the key it was ranked by."""
    from mammoth_cli.commands.schema.find import (
        _adjacent_compound_forms,
        _ordered_tokens,
        _query_tokens,
    )

    terms = _query_tokens(goal) or _ordered_tokens(goal)
    if not terms:
        return []
    compounds = _adjacent_compound_forms(terms)
    folded = " ".join(goal.casefold().split())
    # Intent also reads the small words the search drops ("by", "per"): they say what is grouped.
    every_word = _ordered_tokens(goal)
    forms = _forms(every_word, _adjacent_compound_forms(every_word))
    ranked: list[tuple[float, int, int, int, dict[str, Any]]] = []
    for order, recipe in enumerate(load_recipes()):
        if _rejected(recipe, every_word, {}) or not _intent_met(recipe, forms, forms):
            continue
        vocabulary = _recipe_vocabulary(recipe["id"])
        matched = sum(
            1 for term in terms if _term_forms(term, compounds.get(term, frozenset())) & vocabulary
        )
        # The goal states the recipe's intent (above); two of its words in the recipe's
        # vocabulary then suffice (one, for a one-word goal), since the rest are the
        # caller's own data words ("Salesforce", "customer id").
        if matched < min(2, len(terms)):
            continue
        # A word the recipe itself uses outranks one reached only through a synonym.
        literal = sum(1 for term in terms if term in vocabulary)
        phrase = int(any(folded == goal_text.casefold() for goal_text in recipe["goals"]))
        ranked.append((matched / len(terms), phrase, literal, -order, recipe))
    ranked.sort(key=lambda item: (item[0], item[1], item[2], item[3]), reverse=True)
    return [((fit, phrase, literal), recipe) for fit, phrase, literal, _, recipe in ranked]


def _tied(ranked: list[tuple[_Key, dict[str, Any]]]) -> list[tuple[_Key, dict[str, Any]]]:
    """The leading recipes that fit exactly as well as the best one; only file order separates them.

    Two or more of them means the goal does not say which recipe is meant. A recipe run
    changes data, so the caller must choose rather than take the first.
    """
    tied = [item for item in ranked if item[0] == ranked[0][0]]
    return tied if len(tied) > 1 else []


def runnable_for(goal: str, limit: int = 2) -> list[dict[str, Any]]:
    """The executable recipes that fit ``goal``, best first, each with its run command.

    Args:
        goal: The caller's goal, in their words.
        limit: The most recipes to return.

    Returns:
        Each recipe's id, title and ``run_command``.
    """
    # Recipes that fit equally well are all returned: the caller chooses between them, so
    # the limit never cuts inside a tie group.
    fits = [
        (key, recipe)
        for key, recipe in _rank(goal)
        if recipe.get("run") and not recipe_hidden_embedded(recipe)
    ]
    keys = [key for key, _ in fits]
    cut = limit
    while cut < len(fits) and keys[cut] == keys[cut - 1]:
        cut += 1
    return [
        {
            "id": recipe["id"],
            "title": recipe["title"],
            "run_command": run_command(recipe),
            "full_detail_command": f"mammoth how \"{recipe['goals'][0]}\"",
        }
        for _, recipe in fits[:cut]
    ]


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
    # Ranked over every recipe, so a goal this call cannot do is not answered with a
    # weaker recipe that only shares a word with it; the parts it can do still are.
    best_unavailable = bool(ranked) and recipe_hidden_embedded(ranked[0][1])
    ranked = [item for item in ranked if not recipe_hidden_embedded(item[1])]
    tied = _tied(ranked)
    composed, unresolved = _compose(goal, ranked[0][1]["id"] if ranked and not tied else None)
    if unresolved:
        # A part of the goal fits several recipes equally: the whole goal is not run on a guess.
        return _unresolved_result(goal, composed, unresolved, context), {}
    if len(composed) >= 2 or (composed and not ranked):
        # A goal with several parts gets every part's steps, not only the best one's.
        return _composed_result(goal, composed, context), {}
    if best_unavailable:
        return {
            "goal": goal,
            "matched": False,
            "context": context,
            "steps": [],
            "notes": [],
            "alternatives": _alternatives([r for _, r in ranked]),
            "hint": _NOT_HERE_HINT,
        }, {}
    if tied:
        return {
            "goal": goal,
            "matched": False,
            "context": context,
            "steps": [],
            "notes": [],
            "alternatives": _alternatives([r for _, r in tied]),
            "hint": _TIED_HINT,
        }, {}
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
        "alternatives": _alternatives([r for _, r in ranked[1:]]),
    }
    if best.get("run"):
        # The steps as one command: an agent runs it instead of chaining them by hand.
        result["run_command"] = run_command(best)
        result["inputs"] = best.get("inputs", {})
    return result, {}


def _alternatives(recipes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The first few ``recipes``, each with the ``how`` command that shows it.

    Args:
        recipes: Recipes, best first.

    Returns:
        At most ``_MAX_ALTERNATIVES`` records of id, title and command.
    """
    return [
        {
            "id": recipe["id"],
            "title": recipe["title"],
            "command": f'mammoth how "{recipe["goals"][0]}"',
        }
        for recipe in recipes[:_MAX_ALTERNATIVES]
    ]


#: Steps that set up the data a recipe works on; a composed recipe keeps the first of each.
_SETUP_COMMANDS = frozenset(
    {"file.upload", "view.list", "view.get", "view.data.get", "dataset.get", "dataset.list"}
)


def _unresolved_result(
    goal: str,
    composed: list[tuple[str, dict[str, Any]]],
    unresolved: list[tuple[str, list[dict[str, Any]]]],
    context: dict[str, Any],
) -> dict[str, Any]:
    """No match, with the clear parts of a several-part goal and the parts that are tied."""
    return {
        "goal": goal,
        "matched": False,
        "recipes": [
            {"id": recipe["id"], "title": recipe["title"], "doc": recipe["doc"], "for": clause}
            for clause, recipe in composed
        ],
        "unresolved": [
            {"for": clause, "alternatives": _alternatives(fits)} for clause, fits in unresolved
        ],
        "context": context,
        "steps": [],
        "notes": [],
        "alternatives": _alternatives([r for _, fits in unresolved for r in fits]),
        "hint": _UNRESOLVED_HINT,
    }


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
