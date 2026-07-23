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

#: The default ``--output`` value: resolves to a human table on a terminal and
#: machine JSON when stdout is piped or redirected.
OUTPUT_AUTO = "auto"

#: Every value a caller may pass to ``--output``: the renderable modes plus the
#: ``auto`` alias. The tuple order is the order shown in help and error hints.
SELECTABLE_OUTPUTS = (OUTPUT_AUTO, *VALID_OUTPUTS)

#: Every ``--color`` policy value. The tuple order is the order shown in help.
COLOR_MODES = ("auto", "always", "never")


def resolve_output(output: str, *, is_tty: bool) -> str:
    """Resolve the ``auto`` output alias to a concrete renderable mode.

    ``auto`` renders a human table on a terminal and machine JSON when stdout is
    piped or redirected, so an interactive user gets a readable table while an
    agent or pipeline gets parseable JSON without passing any flag. A concrete
    mode is returned unchanged.

    Args:
        output: The requested output value, possibly ``auto``.
        is_tty: Whether the output stream is an interactive terminal.

    Returns:
        A concrete output mode drawn from :data:`VALID_OUTPUTS`.
    """
    if output == OUTPUT_AUTO:
        return "table" if is_tty else "json"
    return output


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
