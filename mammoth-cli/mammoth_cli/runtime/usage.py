"""Which commands ran, kept on disk until a detached sender stores them in Mammoth.

A finished command appends one line to a local spool and, when no sender is running, starts
one (:mod:`mammoth_cli.runtime.usage_sender`). Nothing here touches the network, so a command
never waits on its own measurement.

A spool line holds only the fields :func:`record` names: identifiers, an outcome and a
duration. Never an argument value, a path or any data. The local run log holds the argv, which
is why the sender reads this spool and not that log.

An embedded call records nothing: the host serves every user from one process, and it stores
its own events (see ``agent_command_run`` in mvc-service).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mammoth_cli import __version__
from mammoth_cli.context.resolver import env_token_in_use, env_token_key
from mammoth_cli.runtime import embedded, runlog, trace
from mammoth_cli.runtime.invocation import Invocation

#: Set by the test suite, as ``MAMMOTH_NO_UPDATE_CHECK`` is, so a test never starts a sender.
DISABLE_ENV = "MAMMOTH_NO_USAGE_EVENTS"
#: A sender that left its lock this long ago crashed.
LOCK_TTL_SECONDS = 300
#: Past this a machine that cannot send stops adding lines. About 3,000 commands.
MAX_SPOOL_BYTES = 1024 * 1024

_SPOOL_NAME = "pending.jsonl"
_LOCK_NAME = "sender.lock"
_CLAIMED_GLOB = "sending-*.jsonl"


@dataclass(frozen=True)
class Claim:
    """The lines one sender holds, and the files that keep them until :func:`settle`.

    Attributes:
        lines: The lines, oldest first.
        paths: The claim files. A sender killed mid-send leaves them behind.
    """

    lines: list[dict[str, Any]]
    paths: list[Path]


def enabled() -> bool:
    """Whether this process records usage.

    Returns:
        False inside an embedded call, or when :data:`DISABLE_ENV` is set.
    """
    return not embedded.active() and not os.environ.get(DISABLE_ENV)


def _directory() -> Path:
    """The spool's directory, beside the run logs so it shares their permissions."""
    return runlog.log_dir() / "usage"


def record(
    invocation: Invocation | None,
    *,
    exit_status: int,
    error_code: str | None,
    duration_ms: int,
) -> None:
    """Append one finished command to the spool. A failure is dropped, never raised.

    Args:
        invocation: The command's resolved global options, or None when it has none.
        exit_status: The exit status the command ends with.
        error_code: The CLI error code of a failed command, or None.
        duration_ms: How long the command ran.
    """
    traced = trace.current()
    if invocation is None or traced is None or not enabled():
        return
    line = {
        "ts": time.time(),
        "cmd": traced.command_id,
        "inv": traced.invocation_id,
        "group": traced.group,
        "surface": traced.surface,
        "agent": traced.agent,
        "exit_status": exit_status,
        "error_code": error_code,
        "duration_ms": duration_ms,
        "cli_version": __version__,
        # Local only, so the sender signs in as the user who ran the command.
        "profile": invocation.profile,
        "profile_is_default": invocation.profile_is_default,
        "env_key": env_token_key() if env_token_in_use(invocation) else None,
    }
    try:
        directory = _directory()
        directory.mkdir(parents=True, exist_ok=True)
        spool = directory / _SPOOL_NAME
        if spool.exists() and spool.stat().st_size >= MAX_SPOOL_BYTES:
            return
        with open(spool, "a", encoding="utf-8") as file:
            file.write(json.dumps(line, separators=(",", ":")) + "\n")
    except OSError:
        return


def send_in_background() -> None:
    """Start a detached sender when lines are waiting and none is running."""
    if not enabled():
        return
    try:
        if not (_directory() / _SPOOL_NAME).exists() or not _claim_lock():
            return
    except OSError:
        return
    try:
        subprocess.Popen(  # noqa: S603 -- fixed argv, our own module
            [sys.executable, "-m", "mammoth_cli.runtime.usage_sender"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
    except OSError:
        release_lock()


def _claim_lock() -> bool:
    """Take the sender lock.

    Returns:
        True when this process took it; False while a live sender holds it.
    """
    lock = _directory() / _LOCK_NAME
    try:
        if time.time() - lock.stat().st_mtime < LOCK_TTL_SECONDS:
            return False
        lock.unlink(missing_ok=True)
    except FileNotFoundError:
        pass
    try:
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
    except FileExistsError:
        return False
    return True


def release_lock() -> None:
    """Let the next command start a sender."""
    try:
        (_directory() / _LOCK_NAME).unlink(missing_ok=True)
    except OSError:
        return


def take() -> Claim:
    """Claim every waiting line, for this process alone.

    The rename is the claim, so two senders can never hold the same line. The claim stays on
    disk until :func:`settle`, and one left by a killed sender is taken over once the lock it
    held would have expired. A taken-over claim holds what was already delivered too, so a
    killed sender's lines can go out twice, and ``inv`` tells the copies apart.

    Returns:
        The claim. Unreadable lines are left out.
    """
    directory = _directory()
    own = directory / f"sending-{os.getpid()}-{time.time_ns()}.jsonl"
    try:
        os.replace(directory / _SPOOL_NAME, own)
    except OSError:
        pass
    now = time.time()
    lines: list[dict[str, Any]] = []
    paths: list[Path] = []
    for path in sorted(directory.glob(_CLAIMED_GLOB)):
        try:
            if path != own and now - path.stat().st_mtime < LOCK_TTL_SECONDS:
                continue
            # From here its age is this sender's, not the last command's.
            os.utime(path)
            lines.extend(_read(path))
        except OSError:
            continue
        paths.append(path)
    return Claim(lines, paths)


def _read(path: Path) -> list[dict[str, Any]]:
    """The lines of a claimed file that still parse."""
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        try:
            line = json.loads(raw)
        except ValueError:
            continue
        # A kept claim must never hold a line the sender would raise on.
        if isinstance(line, dict) and isinstance(line.get("ts"), int | float):
            lines.append(line)
    return lines


def settle(claim: Claim, undelivered: list[dict[str, Any]]) -> None:
    """Return the undelivered lines for a later sender, then drop the claim.

    Args:
        claim: What this sender held.
        undelivered: The lines it did not deliver. While they cannot be written back the
            claim stays, so they go out again rather than being lost.
    """
    if not _give_back(undelivered):
        return
    for path in claim.paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            continue


def _give_back(lines: list[dict[str, Any]]) -> bool:
    """Append *lines* to the spool.

    Args:
        lines: The lines to return.

    Returns:
        True when they are safe in the spool.
    """
    if not lines:
        return True
    text = "".join(json.dumps(line, separators=(",", ":")) + "\n" for line in lines)
    try:
        with open(_directory() / _SPOOL_NAME, "a", encoding="utf-8") as file:
            file.write(text)
    except OSError:
        return False
    return True
