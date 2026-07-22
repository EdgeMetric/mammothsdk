"""Enforce a command's reviewed confirmation policy before a mutation runs.

Every command manifest carries a ``confirmation`` policy. This guard turns that
policy plus the invocation's ``--yes`` / ``--confirm`` flags and the terminal
state into a decision: proceed, prompt, or raise a stable
:class:`~mammoth_cli.errors.envelope.CliError`. An autonomous agent satisfies
every policy noninteractively with reviewed flags; a human at a TTY may confirm
a normal deletion with a prompt. Prompts occur only on a real TTY and never in
``--no-input`` or machine-output (``json``/``ndjson``) mode.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

import typer

from mammoth_cli.errors.envelope import (
    CODE_CONFIRMATION_DECLINED,
    CODE_CONFIRMATION_REQUIRED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.output.policy import MACHINE_OUTPUTS
from mammoth_cli.runtime.invocation import Invocation

POLICY_NONE = "none"
POLICY_PROMPT_OR_YES = "prompt_or_yes"
POLICY_CONFIRM_TARGET = "confirm_target"
POLICY_YES_ALWAYS = "yes_always"

Prompter = Callable[[str], bool]


def _required_error(action: str, *, target: str | None, need_target: bool) -> CliError:
    recovery = "mammoth ... --yes"
    if need_target and target is not None:
        recovery = f"mammoth ... --yes --confirm {target}"
    return CliError(
        code=CODE_CONFIRMATION_REQUIRED,
        message=f"This command needs explicit confirmation to {action}.",
        exit_status=EXIT_USAGE,
        hint=(
            "Pass --yes (and --confirm TARGET for high-impact actions), or run it "
            "interactively at a terminal."
        ),
        recovery_commands=[recovery],
    )


def enforce_confirmation(
    invocation: Invocation,
    *,
    policy: str,
    action: str,
    target: str | None = None,
    is_tty: bool | None = None,
    prompt: Prompter | None = None,
) -> None:
    """Enforce ``policy`` for one mutating command, or raise.

    Args:
        invocation: The current command's resolved global options (``yes``,
            ``confirm``, ``no_input``, ``output``).
        policy: The manifest confirmation policy: ``none``, ``prompt_or_yes``,
            ``yes_always``, or ``confirm_target``.
        action: A short phrase naming the action, used in the prompt and error
            (for example ``"delete project 180"``).
        target: The exact string the user must pass to ``--confirm`` under the
            ``confirm_target`` policy.
        is_tty: Whether standard input is an interactive terminal. Defaults to
            ``sys.stdin.isatty()``; injectable for tests.
        prompt: The yes/no prompt function. Defaults to :func:`typer.confirm`;
            injectable for tests.

    Raises:
        CliError: ``confirmation_required`` when a needed flag is absent and no
            prompt is possible; ``confirmation_declined`` when an interactive
            prompt is answered no; ``confirmation_target_mismatch`` when
            ``--confirm`` does not equal ``target``.
    """
    if policy == POLICY_NONE:
        return

    tty = sys.stdin.isatty() if is_tty is None else is_tty
    machine = invocation.output in MACHINE_OUTPUTS
    can_prompt = tty and not invocation.no_input and not machine
    ask = prompt if prompt is not None else typer.confirm

    if policy == POLICY_CONFIRM_TARGET:
        if not invocation.yes:
            raise _required_error(action, target=target, need_target=True)
        if invocation.confirm != target:
            raise CliError(
                code="confirmation_target_mismatch",
                message=f"--confirm must exactly equal the target to {action}.",
                exit_status=EXIT_USAGE,
                hint=f"Pass --confirm {target}." if target is not None else None,
            )
        return

    if policy == POLICY_YES_ALWAYS:
        if invocation.yes:
            return
        raise _required_error(action, target=target, need_target=False)

    # POLICY_PROMPT_OR_YES
    if invocation.yes:
        return
    if can_prompt:
        if ask(f"Confirm: {action}?"):
            return
        raise CliError(
            code=CODE_CONFIRMATION_DECLINED,
            message=f"Declined to {action}.",
            exit_status=EXIT_USAGE,
        )
    raise _required_error(action, target=target, need_target=False)
