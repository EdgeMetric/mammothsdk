"""The detached process that stores spooled commands in Mammoth's user events.

:func:`mammoth_cli.runtime.usage.send_in_background` starts this once the CLI has work for it.
It waits so a burst of commands goes out together, sends what it finds, and exits. It is not a
daemon: nothing runs while the CLI is idle. Lines it cannot deliver stay in the spool until they
age out.
"""

from __future__ import annotations

import platform
import time
from contextlib import closing
from typing import Any
from urllib.parse import urlsplit

from mammoth_cli.context.resolver import ResolvedAuth, env_token_in_use, env_token_key, resolve_auth
from mammoth_cli.runtime import runlog, usage
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.sdk_service import SdkMammothService

#: How long to gather a burst of commands before sending.
WAIT_SECONDS = 60
#: The most events one drain sends; the rest wait for the next sender.
MAX_BATCH = 500
#: Older lines are dropped, as the run log drops its own.
MAX_AGE_SECONDS = runlog.RETENTION_DAYS * 24 * 60 * 60

_SEND_TIMEOUT_SECONDS = 10.0
_DRAINS = 2
_ORIGIN = "cli"
_EVENT_NAME = "cli_command_run"
_PRODUCT = "mammoth-cli"
_OK = "ok"
_FAILED = "failed"


def main() -> None:
    """Wait for the burst to end, drain the spool, and let the next command start a sender."""
    time.sleep(WAIT_SECONDS)
    try:
        for _ in range(_DRAINS):
            if not drain():
                break
    finally:
        usage.release_lock()


def drain() -> bool:
    """Send one batch of waiting lines and return the ones not delivered.

    Returns:
        True when at least one event was delivered.
    """
    oldest = time.time() - MAX_AGE_SECONDS
    lines = [line for line in usage.take() if float(line.get("ts") or 0) > oldest]
    batch, later = lines[:MAX_BATCH], lines[MAX_BATCH:]
    undelivered = _send(batch)
    usage.give_back(undelivered + later)
    return len(undelivered) < len(batch)


def _send(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deliver lines per login.

    Args:
        lines: The lines to deliver.

    Returns:
        The lines that were not delivered.
    """
    logins: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = {}
    for line in lines:
        key = (line.get("profile"), line.get("profile_is_default"), line.get("env_key"))
        logins.setdefault(key, []).append(line)
    undelivered: list[dict[str, Any]] = []
    for login_lines in logins.values():
        undelivered.extend(_send_login(login_lines))
    return undelivered


def _send_login(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deliver the lines of one login, stopping at its first failure.

    Args:
        lines: Lines that share a profile and environment token.

    Returns:
        The lines that were not delivered.
    """
    first = lines[0]
    invocation = Invocation(
        command_id="usage.send",
        profile=first.get("profile"),
        profile_is_default=bool(first.get("profile_is_default")),
    )
    # This process may hold another token than the command did: an event sent with it
    # would be stored as someone else's.
    in_use = env_token_key() if env_token_in_use(invocation) else None
    if in_use != first.get("env_key"):
        return lines
    sent = 0
    try:
        auth = resolve_auth(invocation)
        with closing(SdkMammothService(auth, timeout=_SEND_TIMEOUT_SECONDS)) as service:
            for line in lines:
                service.send_user_event(_user_event(line, auth))
                sent += 1
    except Exception:
        return lines[sent:]
    return []


def _user_event(line: dict[str, Any], auth: ResolvedAuth) -> dict[str, Any]:
    """Build the event Mammoth's user events take. Mammoth adds the user from the token.

    Args:
        line: One spool line.
        auth: The login sending it.

    Returns:
        The event. ``additional_info`` lists every field that describes the command.
    """
    version = str(line.get("cli_version") or "")
    failed = bool(line.get("exit_status")) or line.get("error_code") is not None
    return {
        "event_name": _EVENT_NAME,
        "event_origin": _ORIGIN,
        "event_context": {},
        "additional_info": {
            "cmd": line.get("cmd"),
            "inv": line.get("inv"),
            "surface": line.get("surface"),
            "agent": line.get("agent"),
            "outcome": _FAILED if failed else _OK,
            "exit_status": line.get("exit_status"),
            "error_code": line.get("error_code"),
            "duration_ms": line.get("duration_ms"),
        },
        # The fields a browser fills in. Here the CLI stands in for the browser.
        "browser_name": _PRODUCT,
        "browser_version": version,
        "browser_size": {},
        "device_info": f"{_PRODUCT}/{version}",
        "domain": urlsplit(auth.base_url).netloc,
        "os_name": platform.system(),
        # Empty: Mammoth fills in the caller's own email.
        "email_id": "",
        "user_name": "",
        # When the command finished, not when this process got to it.
        "timestamp": line.get("ts"),
        # One id per command, or one for all the lines of a ``mammoth run``.
        "session_identifier": line.get("group") or line.get("inv"),
    }


if __name__ == "__main__":  # pragma: no cover - the detached sender process
    main()
