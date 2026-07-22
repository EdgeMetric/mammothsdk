"""Unit tests for the mutation confirmation guard."""

from __future__ import annotations

import pytest

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.runtime.confirm import enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation


def _inv(**overrides: object) -> Invocation:
    return Invocation(command_id="x", **overrides)  # type: ignore[arg-type]


def test_none_policy_never_blocks() -> None:
    enforce_confirmation(_inv(), policy="none", action="do it")


def test_prompt_or_yes_passes_with_yes_flag() -> None:
    enforce_confirmation(_inv(yes=True), policy="prompt_or_yes", action="delete X")


def test_prompt_or_yes_blocks_without_yes_in_machine_mode() -> None:
    with pytest.raises(CliError) as excinfo:
        enforce_confirmation(
            _inv(output="json"), policy="prompt_or_yes", action="delete X", is_tty=True
        )
    assert excinfo.value.code == "confirmation_required"
    assert excinfo.value.exit_status == EXIT_USAGE


def test_prompt_or_yes_blocks_when_no_input() -> None:
    with pytest.raises(CliError) as excinfo:
        enforce_confirmation(
            _inv(no_input=True), policy="prompt_or_yes", action="delete X", is_tty=True
        )
    assert excinfo.value.code == "confirmation_required"


def test_prompt_or_yes_blocks_without_tty() -> None:
    with pytest.raises(CliError):
        enforce_confirmation(_inv(), policy="prompt_or_yes", action="delete X", is_tty=False)


def test_prompt_or_yes_prompts_when_interactive() -> None:
    calls: list[str] = []

    def prompt(message: str) -> bool:
        calls.append(message)
        return True

    enforce_confirmation(
        _inv(), policy="prompt_or_yes", action="delete X", is_tty=True, prompt=prompt
    )
    assert calls and "delete X" in calls[0]


def test_prompt_declined_raises() -> None:
    with pytest.raises(CliError) as excinfo:
        enforce_confirmation(
            _inv(), policy="prompt_or_yes", action="delete X", is_tty=True, prompt=lambda _: False
        )
    assert excinfo.value.code == "confirmation_declined"


def test_yes_always_requires_yes_even_on_tty() -> None:
    with pytest.raises(CliError) as excinfo:
        enforce_confirmation(
            _inv(), policy="yes_always", action="change billing", is_tty=True, prompt=lambda _: True
        )
    assert excinfo.value.code == "confirmation_required"


def test_yes_always_passes_with_yes() -> None:
    enforce_confirmation(_inv(yes=True), policy="yes_always", action="change billing")


def test_confirm_target_requires_yes() -> None:
    with pytest.raises(CliError) as excinfo:
        enforce_confirmation(
            _inv(confirm="180"), policy="confirm_target", action="delete", target="180"
        )
    assert excinfo.value.code == "confirmation_required"


def test_confirm_target_requires_exact_match() -> None:
    with pytest.raises(CliError) as excinfo:
        enforce_confirmation(
            _inv(yes=True, confirm="179"), policy="confirm_target", action="delete", target="180"
        )
    assert excinfo.value.code == "confirmation_target_mismatch"


def test_confirm_target_passes_on_exact_match() -> None:
    enforce_confirmation(
        _inv(yes=True, confirm="180"), policy="confirm_target", action="delete", target="180"
    )
