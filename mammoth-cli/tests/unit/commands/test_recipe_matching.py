"""Recipe matching: ``mammoth how`` and the ``recipes`` that ``schema find`` ranks first.

A recipe run changes user data, so a wrong match is worse than none. The goals are in
``recipe_goals.py``, written from what a person would type; the recipes are the real
ones shipped in the package (no stand-ins).
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from mammoth_cli.commands import how as how_cmd
from mammoth_cli.discovery import load_recipes
from mammoth_cli.runtime.invocation import Invocation
from tests.unit.commands.recipe_goals import (
    BLIND_NEGATIVES,
    BLIND_POSITIVES,
    NEGATIVES,
    POSITIVES,
    SHORT_NEGATIVES,
    SHORT_POSITIVES,
    SHORT_TIED,
)


def _how(goal: str) -> str | None:
    data, _ = how_cmd.how(Invocation(command_id="how", positionals={"goal": goal}))
    return str(data["recipe"]["id"]) if data["matched"] else None  # type: ignore[index]


def _find(goal: str) -> str | None:
    recipes = how_cmd.runnable_for(goal)
    return str(recipes[0]["id"]) if recipes else None


_MATCHERS = pytest.mark.parametrize("match", [_how, _find], ids=["how", "schema-find"])


def test_every_recipe_has_three_phrasings_and_the_set_has_twenty_near_misses() -> None:
    counts = Counter(recipe for _, recipe in POSITIVES)
    assert {r["id"] for r in load_recipes()} == set(counts)
    assert min(counts.values()) >= 3
    assert len(NEGATIVES) >= 20


@_MATCHERS
def test_a_goal_no_recipe_covers_matches_nothing(match) -> None:  # type: ignore[no-untyped-def]
    wrong = {
        goal: match(goal)
        for goal in NEGATIVES + BLIND_NEGATIVES + SHORT_NEGATIVES
        if match(goal) is not None
    }
    assert wrong == {}


@_MATCHERS
def test_a_goal_finds_its_own_recipe_and_never_another(match) -> None:  # type: ignore[no-untyped-def]
    got = {
        goal: (recipe, match(goal))
        for goal, recipe in POSITIVES + BLIND_POSITIVES + SHORT_POSITIVES
    }
    wrong = {goal: pair for goal, pair in got.items() if pair[1] != pair[0]}
    assert wrong == {}


@_MATCHERS
def test_the_goals_in_the_recipe_data_find_their_own_recipe(match) -> None:  # type: ignore[no-untyped-def]
    wrong = {
        goal: (recipe["id"], match(goal))
        for recipe in load_recipes()
        for goal in recipe["goals"]
        if match(goal) != recipe["id"]
    }
    assert wrong == {}


@pytest.mark.parametrize(
    ("goal", "recipe"),
    [
        ("convert Admission_Date column to a date", None),
        ("publish view to a postgres table", None),
        ("top 10 rows by score", "top-n"),
        ("create a dashboard from a view", "dashboard-from-view"),
        ("add a column with the first name from Name", "split-column"),
        ("highlight rows where Admission_Cost is over 5000", None),
        ("add 5 to Cost", None),
    ],
)
def test_the_observed_wrong_and_right_matches(goal: str, recipe: str | None) -> None:
    assert _how(goal) == recipe
    assert _find(goal) == recipe


def test_every_recipe_declares_what_it_does() -> None:
    for recipe in load_recipes():
        groups = recipe["intent"]
        assert groups and all(
            group and all(w == w.lower() for w in group) for group in groups
        ), recipe["id"]


def test_two_recipes_that_fit_equally_well_are_listed_not_picked() -> None:
    # A spreadsheet is a CSV file to export-csv and an Excel file to export-xlsx: the goal
    # fits both equally, and file order must not pick the one that writes the file.
    data, _ = how_cmd.how(
        Invocation(command_id="how", positionals={"goal": "download a spreadsheet"})
    )
    assert data["matched"] is False
    assert {a["id"] for a in data["alternatives"]} == {"export-csv", "export-xlsx"}  # type: ignore[attr-defined]
    assert [r["id"] for r in how_cmd.runnable_for("download a spreadsheet")] == [
        "export-csv",
        "export-xlsx",
    ]


@pytest.mark.parametrize(("goal", "tied"), SHORT_TIED)
def test_a_short_goal_two_recipes_share_lists_both(goal: str, tied: frozenset[str]) -> None:
    data, _ = how_cmd.how(Invocation(command_id="how", positionals={"goal": goal}))
    assert data["matched"] is False
    assert {a["id"] for a in data["alternatives"]} == tied  # type: ignore[attr-defined]
    assert {r["id"] for r in how_cmd.runnable_for(goal)} == tied


@pytest.mark.parametrize(
    ("goal", "recipe"),
    [
        ("combine left.csv and right.csv on a shared key column", "join-files"),
        ("combine two datasets on a shared key", "blend-by-key"),
        ("count the rows in my dataset", None),
        ("remove the duplicate column", None),
        ("send a weekly email report to my team every Monday", None),
        ("email this view to my team", "email-view"),
    ],
)
def test_the_rule_behind_each_blind_miss(goal: str, recipe: str | None) -> None:
    assert _how(goal) == recipe
    assert _find(goal) == recipe


def _result(goal: str) -> dict[str, object]:
    data, _ = how_cmd.how(Invocation(command_id="how", positionals={"goal": goal}))
    return dict(data)


def test_a_tied_part_of_a_several_part_goal_is_reported_not_dropped() -> None:
    result = _result("remove duplicates then rollback")
    assert result["matched"] is False and result["steps"] == []
    assert [r["id"] for r in result["recipes"]] == ["remove-duplicates"]  # type: ignore[attr-defined]
    (part,) = result["unresolved"]  # type: ignore[misc]
    assert part["for"] == "rollback"
    assert {a["id"] for a in part["alternatives"]} == {"undo-last-change", "revert-view-version"}


def test_each_part_of_a_goal_is_resolved_on_its_own() -> None:
    # Not "pick one of three": the first part is clear, only the second is tied.
    result = _result("remove duplicates, then download a spreadsheet")
    assert result["matched"] is False
    assert [r["id"] for r in result["recipes"]] == ["remove-duplicates"]  # type: ignore[attr-defined]
    (part,) = result["unresolved"]  # type: ignore[misc]
    assert part["for"] == "download a spreadsheet"
    assert {a["id"] for a in part["alternatives"]} == {"export-csv", "export-xlsx"}


def test_the_limit_never_cuts_a_tie_group() -> None:
    # Three recipes fit this goal equally well; a limit of two must not hide the third.
    goal = "remove duplicates, then download a spreadsheet"
    ids = [r["id"] for r in how_cmd.runnable_for(goal, limit=2)]
    assert set(ids) == {"export-csv", "remove-duplicates", "export-xlsx"}


_HASH_SEEDS = (0, 5, 12, 19)
_PROBE = (
    "import json, sys\n"
    "from mammoth_cli.commands import how\n"
    "from mammoth_cli.runtime.invocation import Invocation\n"
    "data, _ = how.how(Invocation(command_id='how', positionals={'goal': sys.argv[1]}))\n"
    "print(json.dumps([data['matched'], [r['id'] for r in data.get('recipes', [])]]))\n"
)


def test_a_composed_goal_gives_the_same_answer_under_every_hash_seed() -> None:
    # Words were once paired in set order, so which clause matched depended on the seed
    # (seeds 12 and 19 matched nothing). Real subprocesses: the seed is fixed at start-up.
    root = str(Path(how_cmd.__file__).resolve().parents[2])
    goal = "remove duplicates then pivot by region"
    answers = {
        seed: (
            subprocess.run(
                [sys.executable, "-c", _PROBE, goal],
                env={**os.environ, "PYTHONHASHSEED": str(seed), "PYTHONPATH": root},
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
        for seed in _HASH_SEEDS
    }
    assert set(answers.values()) == {'[true, ["remove-duplicates", "pivot-summary"]]'}, answers
