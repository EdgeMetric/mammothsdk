"""Unit tests for the mutation confirmation guard."""

from __future__ import annotations

from dataclasses import replace

import pytest
from typer.testing import CliRunner

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


def _enter_at_real_prompt(**kwargs: object) -> None:
    """Run the guard with the real typer prompt and an empty answer (Enter)."""
    with CliRunner().isolation(input="\n"):
        enforce_confirmation(
            _inv(),
            policy="prompt_or_yes",
            action="delete X",
            is_tty=True,
            **kwargs,  # type: ignore[arg-type]
        )


def test_enter_at_prompt_declines_by_default() -> None:
    with pytest.raises(CliError) as excinfo:
        _enter_at_real_prompt()
    assert excinfo.value.code == "confirmation_declined"


def test_enter_at_prompt_proceeds_when_default_is_yes() -> None:
    _enter_at_real_prompt(default=True)


def _guarded_commands() -> list[tuple[str, str]]:
    from mammoth_cli.manifest.loader import load_commands

    return [
        (record["command_id"], record["confirmation"])
        for record in load_commands()
        if record.get("confirmation") not in (None, "none")
    ]


def test_destructive_commands_exist_to_parametrize_over() -> None:
    assert len(_guarded_commands()) > 150


@pytest.mark.parametrize(
    "command_id",
    [cid for cid, policy in _guarded_commands() if policy != "confirm_target"],
)
def test_a_mismatched_confirm_is_refused_for_every_destructive_command(command_id: str) -> None:
    from mammoth_cli.runtime.confirm import _CONFIRMS_NON_POSITIONAL, refuse_mismatched_confirm

    invocation = Invocation(
        command_id=command_id, yes=True, confirm="999999", extra_args=["313432"]
    )
    if command_id in _CONFIRMS_NON_POSITIONAL:
        refuse_mismatched_confirm(invocation)  # compared by its handler, against the real target
        return
    with pytest.raises(CliError) as excinfo:
        refuse_mismatched_confirm(invocation)
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert excinfo.value.exit_status == EXIT_USAGE
    # A matching (or absent) --confirm is let through.
    refuse_mismatched_confirm(replace(invocation, confirm="313432"))
    refuse_mismatched_confirm(replace(invocation, confirm=None))


def test_confirm_target_commands_are_not_precompared_with_their_positionals() -> None:
    """``import-workbook FILE --confirm PROJECT`` confirms a project, not the file path."""
    from mammoth_cli.runtime.confirm import refuse_mismatched_confirm

    refuse_mismatched_confirm(
        Invocation(
            command_id="dashboard.import-workbook",
            yes=True,
            confirm="456",
            extra_args=["/path/x.twb"],
        )
    )
    # a batch whose source_id (from --input) is the confirmed target
    refuse_mismatched_confirm(
        Invocation(command_id="batch.create-spec", yes=True, confirm="77", extra_args=["12"])
    )


def test_confirm_target_commands_still_refuse_a_wrong_target_before_any_call() -> None:
    """The exact comparison moved to enforce_confirmation, which every handler calls first."""
    from mammoth_cli.runtime.confirm import POLICY_CONFIRM_TARGET, enforce_confirmation

    invocation = Invocation(command_id="dashboard.import-workbook", yes=True, confirm="999")
    with pytest.raises(CliError) as excinfo:
        enforce_confirmation(
            invocation, policy=POLICY_CONFIRM_TARGET, action="import", target="456"
        )
    assert excinfo.value.code == "confirmation_target_mismatch"


def test_dataset_delete_with_wrong_confirm_makes_no_api_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from mammoth_cli import app

    # Import the command module first and patch the name it bound: command modules
    # load lazily, so a patch on ``runtime.session`` made before the first import
    # would be captured by the module for the rest of the session.
    import mammoth_cli.commands.dataset  # noqa: F401

    called: list[str] = []
    monkeypatch.setattr(
        "mammoth_cli.commands.dataset.open_service",
        lambda *a, **k: called.append("open") or (_ for _ in ()).throw(AssertionError("api")),
    )
    result = CliRunner().invoke(
        app.app,
        ["dataset", "delete", "313432", "--project", "1", "--yes", "--confirm", "1", "-o", "json"],
    )
    assert result.exit_code == EXIT_USAGE
    assert "confirmation_target_mismatch" in result.output
    assert called == []
