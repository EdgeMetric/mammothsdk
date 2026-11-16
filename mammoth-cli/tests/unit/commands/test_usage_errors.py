"""Usage errors whose raw Click message is empty or misleading.

Two Click messages cannot be shown to a caller as-is:

* a group invoked with no subcommand raises ``NoArgsIsHelpError`` with a
  deliberately *empty* message (Click has already printed the help text), which
  reached an agent as a ``usage_error`` envelope saying nothing at all;
* a global option with no command after it is resolved as a command name, so
  Click reports ``No such command '--profile'`` — misleading for an option. (One written
  before a command is hoisted behind it; see :func:`hoist_global_options`.)

These pin the replacement messages, and pin that ordinary usage errors (the
did-you-mean suggestions in particular) still pass through untouched.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from typer._click import exceptions as click_exceptions

from mammoth_cli.app.usage import hoist_global_options
from mammoth_cli.testing import make_runner


def _error(args: list[str]) -> dict[str, Any]:
    """Invoke the CLI and return the error object from its machine envelope."""
    result = make_runner().invoke(args)
    assert result.exit_code == 2, result.output
    start = result.output.find("{")
    assert start != -1, f"no envelope in output: {result.output!r}"
    payload = json.loads(result.output[start:])
    return dict(payload["error"])


# --- a group invoked with no subcommand -----------------------------------


def test_bare_invocation_reports_a_real_message_not_an_empty_one() -> None:
    error = _error([])

    assert error["code"] == "usage_error"
    assert error["message"] == "No command given for 'mammoth'."
    assert error["hint"] == "Run 'mammoth --help' to list the available commands."


def test_bare_invocation_suggests_no_command_to_replay() -> None:
    # The caller has to pick a command; inventing a placeholder recovery
    # command (``mammoth schema find QUERY``) would not be runnable.
    assert _error([])["recovery_commands"] == []


@pytest.mark.parametrize("group", ["file", "view", "dataset", "schema"])
def test_group_without_a_subcommand_names_that_group(group: str) -> None:
    error = _error([group])

    assert error["message"] == f"No subcommand given for 'mammoth {group}'."
    assert error["details"]["command_path"] == f"mammoth {group}"


# --- a global option written before the command ---------------------------


def test_global_option_before_the_command_is_hoisted_behind_it() -> None:
    assert hoist_global_options(["--profile", "prod", "doctor"]) == [
        "doctor",
        "--profile",
        "prod",
    ]


def test_equals_and_short_forms_are_hoisted_whole() -> None:
    assert hoist_global_options(["--profile=prod", "-ojson", "-y", "view", "list"]) == [
        "view",
        "list",
        "--profile=prod",
        "-ojson",
        "-y",
    ]


def test_a_boolean_global_flag_does_not_swallow_the_command_name() -> None:
    assert hoist_global_options(["--no-input", "doctor"]) == ["doctor", "--no-input"]


def test_hoisted_options_land_before_a_double_dash_terminator() -> None:
    assert hoist_global_options(["--yes", "run", "--", "-x"]) == ["run", "--yes", "--", "-x"]


def test_a_command_line_without_leading_options_is_unchanged() -> None:
    assert hoist_global_options(["view", "list", "--output", "json"]) == [
        "view",
        "list",
        "--output",
        "json",
    ]


def test_the_same_value_on_both_sides_is_accepted() -> None:
    assert hoist_global_options(["--output", "json", "doctor", "-o", "json"]) == [
        "doctor",
        "-o",
        "json",
        "--output",
        "json",
    ]


def test_different_values_on_both_sides_are_a_usage_error() -> None:
    with pytest.raises(click_exceptions.UsageError, match="given before and after the command"):
        hoist_global_options(["--profile", "a", "doctor", "--profile", "b"])
    with pytest.raises(click_exceptions.UsageError, match="--output"):
        hoist_global_options(["-o", "json", "doctor", "--output", "table"])


def test_a_command_option_value_that_looks_like_a_global_one_is_not_read_as_one() -> None:
    # `-pending` starts with the short form of --profile; it is the value of --filter.
    tokens = ["--profile", "a", "view", "list", "--filter", "-pending", "--profile", "a"]
    assert hoist_global_options(tokens)[:5] == ["view", "list", "--filter", "-pending", "--profile"]
    assert hoist_global_options(["-p", "a", "view", "list", "--filter", "-pb"])


def test_different_values_on_both_sides_fail_through_the_cli() -> None:
    error = _error(["--profile", "a", "doctor", "--profile", "b", "--output", "json"])

    assert error["code"] == "usage_error"
    assert "'--profile' is given before and after the command" in error["message"]


def test_a_leading_global_option_runs_the_command_as_if_it_followed() -> None:
    before = make_runner().invoke(["--output", "json", "schema", "get", "project.list"])
    after = make_runner().invoke(["schema", "get", "project.list", "--output", "json"])

    assert before.exit_code == after.exit_code == 0, before.output
    assert json.loads(before.output)["data"] == json.loads(after.output)["data"]


def test_a_leading_global_option_with_no_command_has_nothing_to_run() -> None:
    error = _error(["--output", "json"])

    assert error["message"] == "Global option '--output' needs a command after it."
    assert error["recovery_commands"] == []


def test_a_global_option_after_a_group_reports_the_missing_subcommand() -> None:
    # ``mammoth file --output json`` has the option in the right place already;
    # what is actually missing is the subcommand, so say that instead.
    error = _error(["file", "--output", "json"])

    assert error["message"] == (
        "'mammoth file' is a command group; it needs a subcommand before '--output'."
    )


# --- ordinary usage errors are unchanged ----------------------------------


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["uplaod"], "mammoth file upload"),
        (["file", "uplod"], "mammoth file upload"),
    ],
)
def test_did_you_mean_suggestions_still_pass_through(args: list[str], expected: str) -> None:
    error = _error(args)

    assert error["message"].startswith(f"No such command '{args[-1]}'")
    assert expected in error["message"]
    assert "mammoth schema find" in error["hint"]


def test_an_unknown_option_on_a_leaf_command_is_untouched() -> None:
    # ``--nope`` is not a global option, so the strict checker still owns it.
    error = _error(["project", "list", "--nope", "--output", "json"])

    assert error["code"] == "unknown_option"


@pytest.mark.parametrize(
    "args", [[], ["file"], ["--profile", "prod", "doctr"], ["file", "--output", "json"]]
)
def test_no_usage_error_ever_renders_an_empty_message(args: list[str]) -> None:
    """The regression guard: an agent must never get a blank explanation."""
    assert _error(args)["message"].strip()


def test_the_only_suggested_command_is_one_the_caller_can_run_verbatim() -> None:
    """A corrected command is echoed back as-is, with no flags bolted on.

    ``--output`` already resolves itself (table on a terminal, JSON when
    piped) and prompts are already off without a terminal, so appending
    ``--output json --no-input`` to the caller's own command would only
    distort what they asked for.
    """
    commands = _error(["--profile", "prod", "doctr"])["recovery_commands"]

    assert commands[0] == "mammoth doctor --help"
    assert not any("--no-input" in command or "--output" in command for command in commands)
