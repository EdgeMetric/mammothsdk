"""Focused coverage for help navigation and compact schema discovery."""

from __future__ import annotations

import pytest

from mammoth_cli.commands.registry import _schema_find
from mammoth_cli.commands.schema import _COMMAND_DISCOVERY_PURPOSES, find_schemas
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.testing import make_runner


def test_schema_find_returns_compact_matches_with_a_full_schema_route() -> None:
    result = find_schemas("view transform")
    matches = result["matches"]

    assert matches
    sample = next(
        match for match in matches if match["command_id"] == "view.transform.bulk-replace"
    )
    assert set(sample) == {
        "command_id",
        "command_path",
        "mutation_class",
        "confirmation",
        "full_schema_command",
    }
    assert sample["full_schema_command"].startswith(
        "mammoth schema get view.transform.bulk-replace"
    )
    assert "input_schema" not in sample
    assert result["total_matches"] >= len(matches)


def test_schema_find_cli_accepts_a_multiword_query() -> None:
    result = make_runner().invoke(
        ["schema", "find", "view transform", "--output", "json", "--no-input"]
    )

    assert result.exit_code == 0, result.output
    assert "view.transform.bulk-replace" in result.output


def test_schema_find_matches_resource_purpose_not_just_command_tokens() -> None:
    matches = find_schemas("upload csv")["matches"]

    assert matches[0]["command_id"] == "file.upload"


def test_schema_find_prioritizes_path_matches_and_caps_broad_results() -> None:
    result = find_schemas("view transform")

    assert result["total_matches"] > len(result["matches"])
    assert result["truncated"] is True
    assert all(match["command_id"].startswith("view.transform.") for match in result["matches"])
    assert len(result["matches"]) == 20


@pytest.mark.parametrize(
    ("query", "command_id"),
    [
        # A cold agent states the goal, not Mammoth's task name. Each of these
        # returned nothing (or the wrong command) before 2.0.37.
        ("merge two datasets", "view.transform.join"),
        ("combine datasets", "view.transform.join"),
        ("combine two views", "view.transform.join"),
        ("add columns from another dataset", "view.transform.join"),
        ("vlookup", "view.transform.join"),
        ("reference table", "view.transform.lookup"),
        ("dedupe", "view.transform.discard-duplicates"),
        ("remove duplicates", "view.transform.discard-duplicates"),
        ("keep rows", "view.transform.filter"),
        ("delete rows", "view.transform.filter"),
        ("summarise", "view.transform.ai"),
        ("aggregate", "view.transform.pivot"),
        ("calculate", "view.transform.math"),
        ("running total", "view.transform.window"),
        ("rank", "view.transform.window"),
        ("top n", "view.transform.limit-rows"),
        ("unpivot", "view.transform.unnest"),
        ("concatenate", "view.transform.combine-columns"),
        ("combine columns", "view.transform.combine-columns"),
        ("standardise", "view.transform.bulk-replace"),
        ("uppercase", "view.transform.text"),
        ("fill blanks", "view.transform.fill-missing"),
        ("parse date", "view.transform.convert-type"),
        ("classify", "view.transform.ai"),
        ("rename column", "view.transform.copy-columns"),
        ("append rows", "file.upload"),
    ],
)
def test_schema_find_resolves_goal_phrasing_to_the_transform(query: str, command_id: str) -> None:
    matches = find_schemas(query)["matches"]

    assert matches, query
    assert matches[0]["command_id"] == command_id


def test_every_view_transform_has_a_plain_language_discovery_purpose() -> None:
    transforms = {
        str(record["command_id"])
        for record in load_commands()
        if str(record["command_id"]).startswith("view.transform.")
        and record.get("disposition") != "alias"
    }

    assert transforms
    assert transforms <= set(_COMMAND_DISCOVERY_PURPOSES)


def test_schema_find_without_a_full_match_suggests_near_misses_and_the_menu() -> None:
    result = find_schemas("union two views")

    assert result["matches"] == []
    assert result["total_matches"] == 0
    suggested = [item["command_id"] for item in result["suggestions"]]
    assert "file.upload" in suggested and "view.export.dataset" in suggested
    assert all(item["matched_terms"] for item in result["suggestions"])
    assert all(
        item["full_schema_command"].startswith("mammoth schema get ")
        for item in result["suggestions"]
    )
    assert "mammoth view transform --help" in result["hint"]


def test_schema_find_with_a_match_carries_no_suggestions() -> None:
    result = find_schemas("join")

    assert "suggestions" not in result
    assert "hint" not in result


def test_schema_find_rejects_an_empty_query() -> None:
    with pytest.raises(CliError, match="must contain") as error:
        _schema_find(Invocation(command_id="schema.find", extra_args=["   "]))

    assert error.value.code == "empty_search_query"


def test_root_help_groups_commands_by_task_and_explains_discovery() -> None:
    result = make_runner().invoke(["--help"])

    assert result.exit_code == 0, result.output
    for panel in (
        "Start here",
        "Discover commands",
        "Work with data",
        "Build and share",
        "Automate and integrate",
        "CLI and agent tools",
    ):
        assert panel in result.output
    assert "mammoth schema find QUERY" in result.output


def test_schema_group_help_explains_compact_and_full_discovery() -> None:
    result = make_runner().invoke(["schema", "--help"])

    assert result.exit_code == 0, result.output
    assert "Find concise command input guidance or fetch full schemas." in result.output
    assert "find" in result.output


def test_leaf_help_separates_global_options_by_purpose() -> None:
    result = make_runner().invoke(["schema", "find", "--help"])

    assert result.exit_code == 0, result.output
    for panel in ("Output and automation", "Context and timeouts", "Request input", "Safety"):
        assert panel in result.output
