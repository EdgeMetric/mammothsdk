"""Recipe matching: ``mammoth how`` and the ``recipes`` that ``schema find`` ranks first.

A recipe run changes user data, so a wrong match is worse than none. The goals are in
``recipe_goals.py``, written from what a person would type; the recipes are the real
ones shipped in the package (no stand-ins).
"""

from __future__ import annotations

from collections import Counter

import pytest

from mammoth_cli.commands import how as how_cmd
from mammoth_cli.discovery import load_recipes
from mammoth_cli.runtime.invocation import Invocation
from tests.unit.commands.recipe_goals import (
    BLIND_NEGATIVES,
    BLIND_POSITIVES,
    NEGATIVES,
    POSITIVES,
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
    wrong = {goal: match(goal) for goal in NEGATIVES + BLIND_NEGATIVES if match(goal) is not None}
    assert wrong == {}


@_MATCHERS
def test_a_goal_finds_its_own_recipe_and_never_another(match) -> None:  # type: ignore[no-untyped-def]
    got = {goal: (recipe, match(goal)) for goal, recipe in POSITIVES + BLIND_POSITIVES}
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


def test_two_recipes_that_fit_equally_well_match_neither() -> None:
    # A spreadsheet is a CSV file to export-csv and an Excel file to export-xlsx: the goal
    # fits both equally, and file order must not pick the one that writes the file.
    assert _how("download a spreadsheet") is None
    assert _find("download a spreadsheet") is None


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
