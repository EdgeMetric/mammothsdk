"""Did you mean: an unknown command, option or column names the nearest real one.

Agents (and people) mistype a command, glue an option to its value or get a
column's case wrong. Each error must name the closest valid choice so the next
call is right, and an unknown command must point at the discovery commands
(``how`` and ``schema find``), not at ``schema get``, which needs an id the
caller does not have yet.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from mammoth_cli.services.sdk_service import SdkMammothService
from mammoth_cli.services.suggest import nearest, option_suggestion
from mammoth_cli.testing import make_runner


def _error(args: list[str]) -> dict[str, Any]:
    result = make_runner().invoke([*args, "--output", "json"])
    assert result.exit_code == 2, result.output
    start = result.output.find("{")
    return dict(json.loads(result.output[start:])["error"])


# --- unknown command --------------------------------------------------------


def test_an_unknown_top_level_command_names_the_command_it_most_likely_meant() -> None:
    error = _error(["uplaod"])
    assert "mammoth file upload" in error["details"]["did_you_mean"]


def test_an_unknown_command_that_is_a_nested_group_word_finds_that_group() -> None:
    """``mammoth pipeline`` is not a top-level command; ``view pipeline`` is."""
    error = _error(["pipeline"])
    assert error["details"]["did_you_mean"][0] == "mammoth view pipeline"


def test_an_unknown_command_points_to_how_and_schema_find_not_schema_get() -> None:
    error = _error(["pipeline"])
    assert "mammoth how" in error["hint"]
    assert "mammoth schema find" in error["hint"]
    assert "schema get" not in error["hint"]


def test_an_unknown_subcommand_suggests_its_sibling() -> None:
    error = _error(["file", "uplod"])
    assert error["details"]["did_you_mean"][0] == "mammoth file upload"


def test_unknown_command_recovery_commands_run_verbatim() -> None:
    """Each recovery command is complete: a --help or a discovery search."""
    error = _error(["pipeline"])
    assert error["recovery_commands"]
    for command in error["recovery_commands"]:
        assert command.startswith("mammoth ")
        assert command.endswith("--help") or command.startswith(
            ("mammoth how ", "mammoth schema find ")
        )


def test_an_unknown_command_in_human_output_prints_the_suggestion() -> None:
    result = make_runner().invoke(["pipeline", "--output", "table"])
    assert result.exit_code == 2
    assert "mammoth view pipeline" in result.output


# --- unknown option ---------------------------------------------------------


def test_an_option_glued_to_its_value_says_to_pass_the_value_separately() -> None:
    """``"--project 3633"`` as one argv token (a quoted shell word)."""
    error = _error(["project", "list", "--project 3633"])
    assert error["code"] == "unknown_option"
    assert "separately" in error["hint"]
    assert "--project 3633" in error["hint"]
    assert error["details"]["did_you_mean"] == "--project"


def test_an_option_run_into_its_value_is_split_back_out() -> None:
    error = _error(["project", "list", "--project3633"])
    assert error["details"]["did_you_mean"] == "--project"
    assert "--project 3633" in error["hint"]


def test_a_misspelt_option_names_the_nearest_valid_option() -> None:
    error = _error(["project", "list", "--profle", "x"])
    assert error["details"]["did_you_mean"] == "--profile"
    assert "--profile" in error["hint"]


def test_a_command_specific_flag_is_a_candidate_too() -> None:
    error = _error(["schema", "get", "view.list", "--ful"])
    assert error["details"]["did_you_mean"] == "--full"


def test_an_option_that_is_a_positional_keeps_the_positional_advice() -> None:
    error = _error(["project", "create", "--name", "x"])
    assert "positional" in error["hint"]


def test_option_suggestion_with_nothing_close_returns_none() -> None:
    assert option_suggestion("--zzzzzzzz", ["--profile", "--project"]) is None


# --- unknown column ---------------------------------------------------------


def test_a_wrong_case_column_suggests_the_real_column() -> None:
    error = SdkMammothService.column_input_error("Day", ["day", "events", "users"])
    assert error.code == "unknown_column"
    assert error.details["did_you_mean"] == "day"
    assert "'day'" in (error.hint or "")


def test_a_misspelt_column_suggests_the_closest_column() -> None:
    error = SdkMammothService.column_input_error("evnts", ["day", "events", "users"])
    assert error.details["did_you_mean"] == "events"


def test_a_column_with_no_close_match_keeps_the_available_list() -> None:
    error = SdkMammothService.column_input_error("zzz", ["day", "events"])
    assert error.details["did_you_mean"] is None
    assert error.details["available"] == ["day", "events"]


@pytest.mark.parametrize(
    ("value", "choices", "expected"),
    [
        ("Day", ["day", "Days"], ["day", "Days"]),
        ("REGION", ["Region"], ["Region"]),
        ("revenu", ["Revenue", "Region"], ["Revenue"]),
        ("x", ["Revenue"], []),
    ],
)
def test_nearest_ranks_a_case_only_difference_first(
    value: str, choices: list[str], expected: list[str]
) -> None:
    assert nearest(value, choices) == expected
