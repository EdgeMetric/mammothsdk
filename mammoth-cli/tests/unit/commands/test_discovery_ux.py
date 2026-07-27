"""Focused coverage for help navigation and compact schema discovery."""

from __future__ import annotations

import pytest

from mammoth_cli.commands.registry import _schema_find
from mammoth_cli.commands.schema import find_schemas
from mammoth_cli.errors.envelope import CliError
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
