"""Prompt, color, progress, and pager policy resolution.

The resolved policy is deterministic for a given set of inputs. Machine output
modes and ``--no-input`` disable every interactive affordance so an agent or CI
job never blocks on a prompt, pager, or progress animation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

MACHINE_OUTPUTS = {"json", "ndjson"}

#: Every output mode the renderer supports. The tuple order is the order shown
#: in ``--output`` help and error hints.
VALID_OUTPUTS = ("table", "json", "yaml", "ndjson", "plain")

#: Every ``--color`` policy value. The tuple order is the order shown in help.
COLOR_MODES = ("auto", "always", "never")


@dataclass(frozen=True)
class OutputPolicy:
    output: str
    prompts_disabled: bool
    progress_disabled: bool
    pager_disabled: bool
    color_enabled: bool

    @property
    def is_machine(self) -> bool:
        return self.output in MACHINE_OUTPUTS


def _ci_like(env: dict[str, str]) -> bool:
    return bool(env.get("CI")) or env.get("TERM") == "dumb"


def resolve_policy(
    *,
    output: str = "table",
    no_input: bool = False,
    no_progress: bool = False,
    is_tty: bool = True,
    color: str = "auto",
    env: dict[str, str] | None = None,
) -> OutputPolicy:
    """Resolve the interaction policy for one command invocation."""
    env = env if env is not None else dict(os.environ)
    machine = output in MACHINE_OUTPUTS
    ci = _ci_like(env)

    prompts_disabled = machine or no_input or not is_tty or ci
    progress_disabled = machine or no_progress or not is_tty or ci
    pager_disabled = machine or no_input or not is_tty or ci

    if color == "always":
        color_enabled = True
    elif color == "never" or machine:
        color_enabled = False
    else:  # auto
        color_enabled = is_tty and not ci and "NO_COLOR" not in env

    return OutputPolicy(
        output=output,
        prompts_disabled=prompts_disabled,
        progress_disabled=progress_disabled,
        pager_disabled=pager_disabled,
        color_enabled=color_enabled,
    )
