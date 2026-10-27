"""Recipe versions, the per-step impact markers of a dry run, and the recipes added with them."""

from __future__ import annotations

import pytest

from mammoth_cli.commands import recipe as recipe_cmd
from mammoth_cli.commands import run as run_cmd
from mammoth_cli.discovery import load_recipes, runnable_recipes
from mammoth_cli.runtime.strict import validate_input_fields


def test_every_recipe_has_an_integer_version() -> None:
    for recipe in load_recipes():
        assert isinstance(recipe["version"], int) and recipe["version"] >= 1, recipe["id"]


def test_a_repaired_recipe_has_a_higher_version() -> None:
    versions = {recipe["id"]: recipe["version"] for recipe in load_recipes()}
    assert versions["remove-duplicates"] >= 2
    assert versions["summarize-by"] >= 2


def test_recipe_list_carries_the_version() -> None:
    listed = recipe_cmd.recipe_list(None)[0]["recipes"]  # type: ignore[arg-type]
    assert {r["id"]: r["version"] for r in listed}["remove-duplicates"] >= 2


@pytest.mark.parametrize(
    ("impact", "marker"),
    [
        ({"rows_removed": 3, "row_count": 10, "rows_after": 7, "exact": True}, "counted"),
        ({"rows_removed": 3, "row_count": 10, "rows_after": 7, "exact": False}, "upper_bound"),
        ({"rows_matching": 4}, "upper_bound"),
        ({"blank_cells": 9}, "upper_bound"),
        ({"checked": False, "reason": "no columns"}, "not_measured"),
        (None, "not_measured"),
    ],
)
def test_an_impact_is_counted_an_upper_bound_or_not_measured(
    impact: dict | None, marker: str
) -> None:
    assert recipe_cmd._impact_marker(impact) == marker


def test_only_previewed_writes_get_a_marker() -> None:
    envelopes = [
        {"line": 1, "cmd": "view get", "exit": 0, "data": {"id": 1}},
        {
            "line": 2,
            "cmd": "view transform filter",
            "exit": 0,
            "data": {"would_call": "x", "predicted_impact": {"exact": True, "rows_removed": 2}},
        },
        {"line": 3, "cmd": "view transform math", "exit": 0, "data": {"would_call": "y"}},
        {"line": 4, "cmd": "view create", "exit": 2, "error": {}},
    ]
    assert recipe_cmd._impact_markers(envelopes) == [
        {"line": 2, "cmd": "view transform filter", "impact": "counted"},
        {"line": 3, "cmd": "view transform math", "impact": "not_measured"},
    ]


def test_observing_notes_each_envelope_and_still_writes_it(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with run_cmd.observing() as seen:
        run_cmd.write_envelope({"line": 1})
    assert seen == [{"line": 1}]
    assert capsys.readouterr().out.strip() == '{"line":1}'


def test_discard_duplicates_takes_key_columns() -> None:
    validate_input_fields("view.transform.discard-duplicates", {"key_columns": ["Order ID"]})


def test_remove_duplicates_runs_on_a_copy_unless_in_place() -> None:
    recipe = next(r for r in runnable_recipes() if r["id"] == "remove-duplicates")
    assert recipe["inputs"]["in_place"]["default"] is False
    previews = [line for line in recipe["run"] if line["name"] == "preview"]
    assert previews and previews[0]["flags"] == {"dry-run": True}
    assert all("when" in line for line in recipe["run"] if line["name"] != "preview")


def test_create_projects_makes_each_name_once() -> None:
    recipe = next(r for r in runnable_recipes() if r["id"] == "create-projects")
    (line,) = recipe["run"]
    assert line["cmd"] == "project ensure" and line["for_each"] == "{{inputs.names}}"
