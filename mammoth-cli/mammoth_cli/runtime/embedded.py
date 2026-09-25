"""Per-call state for an in-process (embedded) invocation.

:func:`mammoth_cli.embed.invoke` runs a command inside a host process that may
run several commands at once, each for a different user. The login and the
captured envelope therefore live in a :class:`contextvars.ContextVar`, never in
``os.environ`` or a profile file: each thread (or task) sees only its own.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mammoth_cli.context.resolver import ExplicitLogin


@dataclass
class EmbeddedCall:
    """The login for one embedded call and the envelope it produced."""

    login: ExplicitLogin
    envelopes: list[dict[str, Any]] = field(default_factory=list)


_CURRENT: ContextVar[EmbeddedCall | None] = ContextVar("mammoth_cli_embedded", default=None)


def current() -> EmbeddedCall | None:
    """The embedded call running in this context, or None for a normal CLI run."""
    return _CURRENT.get()


def active() -> bool:
    """Whether this context runs an embedded call."""
    return _CURRENT.get() is not None


def capture(envelope: dict[str, Any]) -> bool:
    """Keep ``envelope`` for the embedded caller; False when not embedded."""
    call = _CURRENT.get()
    if call is None:
        return False
    call.envelopes.append(envelope)
    return True


def enter(call: EmbeddedCall) -> Any:
    """Make ``call`` current; returns the token for :func:`leave`."""
    return _CURRENT.set(call)


def leave(token: Any) -> None:
    """Restore the context that was current before :func:`enter`."""
    _CURRENT.reset(token)
