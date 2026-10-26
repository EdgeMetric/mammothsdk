"""``mammoth how "GOAL"``: a plain-language goal becomes an ordered command recipe.

The recipes live in a data file shipped in the package. Every step names a real
command, every example parses, and a goal no recipe covers falls back to the
``schema find`` matches and says so.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from mammoth_cli.commands import how as how_cmd
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.testing import make_runner

_COMMANDS = {
    str(record["command_id"]): str(record["command_path"])
    for record in load_commands()
    if record.get("disposition") != "alias"
}
_SKILL = Path(how_cmd.__file__).parents[1] / "bundled_skill" / "mammoth-cli"


def _how(goal: str, **invocation: object) -> dict[str, object]:
    data, _ = how_cmd.how(
        Invocation(command_id="how", positionals={"goal": goal}, **invocation)  # type: ignore[arg-type]
    )
    return dict(data)


@pytest.mark.parametrize(
    ("goal", "recipe"),
    [
        ("refresh daily", "refresh-daily"),
        ("blend two files by day", "blend-by-key"),
        ("upload and build a dashboard", "upload-dashboard"),
        ("fix a stuck upload", "stuck-upload"),
        ("export to power bi", "export-powerbi"),
        ("delete everything I made", "cleanup-mine"),
        ("schedule a weekly refresh of my dataset", "refresh-daily"),
        ("join two datasets on customer id", "blend-by-key"),
        ("download my view as csv", "export-csv"),
        ("remove duplicate rows", "clean-data"),
    ],
)
def test_a_goal_finds_its_recipe(goal: str, recipe: str) -> None:
    result = _how(goal)
    assert result["matched"] is True
    assert result["recipe"]["id"] == recipe  # type: ignore[index]


def test_every_recipe_step_names_a_real_command_and_an_example_of_it() -> None:
    for recipe in how_cmd.load_recipes():
        assert recipe["doc"] and (_SKILL / recipe["doc"]).is_file(), recipe["id"]
        for step in recipe["steps"]:
            command_id = step["command_id"]
            assert command_id in _COMMANDS, (recipe["id"], command_id)
            assert step["example"].startswith(f"mammoth {_COMMANDS[command_id]}"), step
            assert step["purpose"].strip()


def test_every_example_input_is_valid_json_once_ids_are_filled() -> None:
    for recipe in how_cmd.load_recipes():
        for step in recipe["steps"]:
            found = re.search(r"--input '(.*)'", step["example"])
            if not found:
                continue
            document = re.sub(r"\b[A-Z][A-Z_]*_ID\b", "1", found.group(1))
            json.loads(document)


def test_steps_are_a_stable_ordered_list_of_command_purpose_example() -> None:
    steps = _how("fix a stuck upload")["steps"]
    assert isinstance(steps, list) and steps
    for index, step in enumerate(steps, start=1):
        assert step["step"] == index
        assert {"command", "command_id", "purpose", "example", "key_flags"} <= set(step)
        assert step["command"] == f"mammoth {_COMMANDS[step['command_id']]}"


def test_examples_are_filled_in_for_the_given_project_and_profile() -> None:
    result = _how("fix a stuck upload", project=3633, profile="release")
    steps = result["steps"]
    assert steps[0]["example"] == "mammoth project needs-attention 3633 --profile release"  # type: ignore[index]
    dataset_get = next(s for s in steps if s["command_id"] == "dataset.get")  # type: ignore[union-attr]
    assert dataset_get["example"].endswith("--project 3633 --profile release")
    assert result["context"] == {"project_id": 3633, "profile": "release"}


def test_a_profile_chosen_by_default_is_not_written_into_examples() -> None:
    result = _how("download my view as csv", project=7, profile="x", profile_is_default=True)
    for step in result["steps"]:  # type: ignore[attr-defined]
        assert "--profile" not in step["example"]
        assert step["example"].endswith("--project 7"), step


def test_a_goal_no_recipe_covers_falls_back_to_schema_find_and_says_so() -> None:
    result = _how("rename a dataset")
    assert result["matched"] is False
    assert "recipe" not in result
    assert "schema find" in str(result["hint"])
    steps = result["steps"]
    assert steps, "the schema find matches become the steps"
    assert all(str(step["command"]).startswith("mammoth ") for step in steps)  # type: ignore[index]
    assert any("rename" in str(step["command"]) for step in steps)  # type: ignore[index]


def test_alternatives_name_other_recipes_that_also_fit() -> None:
    result = _how("upload a file and export to csv")
    assert result["matched"] is True
    ids = {result["recipe"]["id"], *(alt["id"] for alt in result["alternatives"])}  # type: ignore[index,attr-defined]
    assert "export-csv" in ids


def test_how_runs_from_the_command_line_as_json() -> None:
    result = make_runner().invoke(["how", "refresh daily", "-o", "json"])
    assert result.exit_code == 0, result.output
    envelope = json.loads(result.stdout)
    assert envelope["data"]["recipe"]["id"] == "refresh-daily"
    assert [step["command_id"] for step in envelope["data"]["steps"]][-2:] == [
        "automation.create",
        "automation.get",
    ]


def test_the_skill_tells_agents_to_try_how_first() -> None:
    text = (_SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert 'mammoth how "' in text


def test_a_goal_with_several_parts_gets_each_parts_steps_in_pipeline_order() -> None:
    # The bug bash's own sample goal: blend two sources by day, chart it, refresh daily.
    result = _how("blend user events with docs by day and build a dashboard that refreshes daily")
    assert result["matched"] is True
    assert [r["id"] for r in result["recipes"]] == [
        "blend-by-key",
        "upload-dashboard",
        "refresh-daily",
    ]
    commands = [step["command_id"] for step in result["steps"]]
    assert commands.index("view.transform.join") < commands.index("dashboard.v3.generate")
    assert commands.index("dashboard.v3.generate") < commands.index("automation.create")
    # One upload, first: the dashboard is built on the joined view, not a new file.
    assert commands.count("file.upload") == 1 and commands[0] == "file.upload"
    assert [step["step"] for step in result["steps"]] == list(range(1, len(commands) + 1))


def test_cleaning_named_in_a_goal_runs_before_its_dashboard() -> None:
    result = _how("upload sales.csv, remove duplicates, then make a dashboard")
    commands = [step["command_id"] for step in result["steps"]]
    assert commands[0] == "file.upload"
    assert commands.index("view.transform.batch") < commands.index("dashboard.v3.generate")


def test_a_goal_one_recipe_covers_is_not_split() -> None:
    result = _how("upload a file and build a dashboard")
    assert result["recipe"]["id"] == "upload-dashboard"
    assert "recipes" not in result


def test_a_verb_form_reaches_its_recipe_word() -> None:
    result = _how("join orders and customers on customer id")
    assert result["matched"] is True
    assert result["recipe"]["id"] == "blend-by-key"
