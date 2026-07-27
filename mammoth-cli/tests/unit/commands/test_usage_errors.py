"""Usage errors whose raw Click message is empty or misleading.

Two Click messages cannot be shown to a caller as-is:

* a group invoked with no subcommand raises ``NoArgsIsHelpError`` with a
  deliberately *empty* message (Click has already printed the help text), which
  reached an agent as a ``usage_error`` envelope saying nothing at all;
* a global option written before the command is resolved as a command name, so
  Click reports ``No such command '--profile'`` — misleading for an option.

These pin the replacement messages, and pin that ordinary usage errors (the
did-you-mean suggestions in particular) still pass through untouched.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

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


def test_global_option_before_the_command_is_named_as_an_option() -> None:
    error = _error(["--profile", "prod", "doctor"])

    assert error["message"] == (
        "Global option '--profile' must come after the command, not before it."
    )
    assert error["details"]["option"] == "--profile"


def test_global_option_before_the_command_suggests_the_corrected_order() -> None:
    error = _error(["--profile", "prod", "doctor"])

    assert error["hint"] == "Try: mammoth doctor --profile prod"
    assert error["recovery_commands"] == ["mammoth doctor --profile prod"]


def test_equals_form_reports_the_option_not_the_whole_token() -> None:
    error = _error(["--profile=prod", "doctor"])

    assert error["message"].startswith("Global option '--profile' must come after")
    assert error["recovery_commands"] == ["mammoth doctor --profile=prod"]


def test_a_boolean_global_flag_does_not_swallow_the_command_name() -> None:
    # ``--no-input`` takes no value, so the command must not be consumed as one.
    error = _error(["--no-input", "doctor"])

    assert error["recovery_commands"] == ["mammoth doctor --no-input"]


def test_several_leading_global_options_all_move_after_the_command() -> None:
    error = _error(["--output", "json", "--profile", "prod", "view", "list"])

    assert error["recovery_commands"] == ["mammoth view list --output json --profile prod"]


def test_a_leading_global_option_with_no_command_has_nothing_to_suggest() -> None:
    error = _error(["--output", "json"])

    assert error["message"].startswith("Global option '--output' must come after")
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
        (["uplaod"], "No such command 'uplaod'. Did you mean 'upgrade'?"),
        (["file", "uplod"], "No such command 'uplod'. Did you mean 'upload'?"),
    ],
)
def test_did_you_mean_suggestions_still_pass_through(args: list[str], expected: str) -> None:
    error = _error(args)

    assert error["message"] == expected
    assert error["hint"] == "Check the command schema with 'mammoth schema get'."


def test_an_unknown_option_on_a_leaf_command_is_untouched() -> None:
    # ``--nope`` is not a global option, so the strict checker still owns it.
    error = _error(["project", "list", "--nope", "--output", "json"])

    assert error["code"] == "unknown_option"


@pytest.mark.parametrize(
    "args", [[], ["file"], ["--profile", "prod", "doctor"], ["file", "--output", "json"]]
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
    assert _error(["--profile", "prod", "doctor"])["recovery_commands"] == [
        "mammoth doctor --profile prod"
    ]
