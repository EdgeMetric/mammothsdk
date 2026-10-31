"""Which command, invocation and caller an API request belongs to, told to the server.

The server already logs every request it serves, with its path, status, latency, user and
``User-Agent`` (``measures.request_log``). The CLI names itself there as
``mammoth-cli/<version>``; this module adds a comment naming the command, so the log can
answer which commands run, from which surface, by which agent, and how they end:

    mammoth-cli/2.4.1 (cmd=view.data.get; inv=3f9c2a1b7d4e; surface=run; agent=claude-code)

``inv`` is the invocation id: every request one command makes carries the same one, and the
local run log (:mod:`mammoth_cli.runtime.runlog`) records it as its ``run_id``, so a local
log and the server's rows join on it. Only identifiers go out: never an argument value,
a path or any data.

The trace lives in a :class:`~contextvars.ContextVar`: a ``mammoth run`` line and an
embedded call each see their own.
"""

from __future__ import annotations

import os
import re
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from mammoth_cli import __version__
from mammoth_cli.runtime import embedded, linecapture

#: Environment variables a coding agent sets in the shells it runs, and the name each maps to.
#: ``MAMMOTH_AGENT`` names the caller outright and wins over the others.
AGENT_ENV: tuple[tuple[str, str | None], ...] = (
    ("MAMMOTH_AGENT", None),
    ("CLAUDECODE", "claude-code"),
    ("CURSOR_AGENT", "cursor"),
    ("GEMINI_CLI", "gemini-cli"),
    ("CODEX_SANDBOX", "codex"),
)

#: A token safe in a ``User-Agent`` comment: no spaces, parentheses or separators.
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")


@dataclass(frozen=True)
class Trace:
    """One command invocation, as the server sees it."""

    command_id: str
    invocation_id: str
    #: ``terminal`` (a typed command), ``run`` (a ``mammoth run`` line) or ``embed``.
    surface: str
    #: The coding agent driving the CLI, when one says so in the environment.
    agent: str | None = None
    #: The outermost invocation in this process: a ``mammoth run`` line's group is the
    #: run's own id, so the journal can undo a whole run. Not sent to the server.
    group: str = ""

    def comment(self) -> str:
        """Format this invocation as a ``User-Agent`` comment.

        Returns:
            ``(cmd=...; inv=...; surface=...)``, with ``; agent=...`` when an agent is known.
        """
        parts = [
            f"cmd={_token(self.command_id)}",
            f"inv={self.invocation_id}",
            f"surface={self.surface}",
        ]
        if self.agent:
            parts.append(f"agent={self.agent}")
        return "(" + "; ".join(parts) + ")"


_CURRENT: ContextVar[Trace | None] = ContextVar("mammoth_cli_trace", default=None)


def current() -> Trace | None:
    """Return the invocation this context runs.

    Returns:
        The current trace, or None outside :func:`begin`.
    """
    return _CURRENT.get()


@contextmanager
def begin(command_id: str) -> Iterator[Trace]:
    """Name a new invocation for the requests made inside this block.

    Args:
        command_id: The manifest command id being run, such as ``view.data.get``.

    Yields:
        The new trace, current until the block ends.
    """
    invocation_id = uuid.uuid4().hex[:12]
    parent = _CURRENT.get()
    trace = Trace(
        command_id=command_id,
        invocation_id=invocation_id,
        surface=_surface(),
        agent=None if embedded.active() else detect_agent(os.environ),
        group=parent.group if parent is not None else invocation_id,
    )
    token = _CURRENT.set(trace)
    try:
        yield trace
    finally:
        _CURRENT.reset(token)


def user_agent() -> str:
    """Build the CLI's part of the ``User-Agent`` header.

    Returns:
        ``mammoth-cli/<version>``, followed by the current invocation's comment
        when there is one.
    """
    trace = _CURRENT.get()
    product = f"mammoth-cli/{__version__}"
    return product if trace is None else f"{product} {trace.comment()}"


def detect_agent(environ: Mapping[str, str]) -> str | None:
    """Name the coding agent that runs the CLI, from the variables it sets.

    An embedded call never asks: the host's environment is shared by every user it serves.

    Args:
        environ: The process environment, or a mapping standing in for it.

    Returns:
        The agent's name (``MAMMOTH_AGENT`` verbatim, made header-safe), or None.
    """
    for name, agent in AGENT_ENV:
        value = environ.get(name, "").strip()
        if value and value != "0":
            return _token(agent or value)[:40] or None
    return None


def _surface() -> str:
    if embedded.active():
        return "embed"
    if linecapture.active():
        return "run"
    return "terminal"


def _token(value: str) -> str:
    return _UNSAFE.sub("-", value)
