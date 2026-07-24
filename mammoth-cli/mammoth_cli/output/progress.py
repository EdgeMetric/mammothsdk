"""A single spinner used to signal in-flight network work.

Long commands (a pipeline transform, a data fetch, an export) block while the
SDK polls an async job. Without a signal the terminal looks hung. This module
renders a small spinner on **stderr** — never stdout — so it never contaminates
piped or redirected output. It is shown only when
:attr:`~mammoth_cli.output.policy.OutputPolicy.progress_disabled` is false
(interactive terminal, human output, not ``--no-progress``, not CI), so agents
and pipelines see nothing.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

#: Default spinner caption. Deliberately generic — the service layer that shows
#: it does not know the command name, and "Working" reads fine for every path.
DEFAULT_PROGRESS_MESSAGE = "Working"
_SPINNER_STYLE = "dots"


@contextmanager
def spinner(enabled: bool, message: str = DEFAULT_PROGRESS_MESSAGE) -> Iterator[None]:
    """Show a stderr spinner for the duration of the block when ``enabled``.

    Args:
        enabled: Whether to render the spinner. When false this is a no-op, so
            callers can pass the resolved progress policy unconditionally.
        message: The caption shown next to the spinner.

    Yields:
        None. The spinner starts on enter and is cleared on exit (including on
        exception), leaving no residue on the terminal.
    """
    if not enabled:
        yield
        return
    try:
        from rich.console import Console
    except ImportError:  # rich is a hard dependency, but never fail work over a spinner
        yield
        return
    console = Console(stderr=True)
    with console.status(f"[dim]{message}…[/dim]", spinner=_SPINNER_STYLE):
        yield
