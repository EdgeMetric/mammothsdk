"""Once-a-day update check, and the opt-in automatic upgrade.

The CLI never blocks a command on the network for this. A command reads the
cached answer (``update-check.json`` in the platform state directory, next to
the run log's ``logs/``) and, when that answer is older than a day, refreshes
it *after* its own output has been written, with a short timeout and every
failure swallowed. The hint therefore appears from the next command on.

What a caller sees:

* ``meta.update_available`` in every success envelope: ``null``, or
  ``{"current", "latest", "command"}`` when a newer release is on PyPI.
* one line on stderr in human output modes (never in ``json``/``ndjson``).
* ``MAMMOTH_NO_UPDATE_CHECK=1`` disables the check and the hint entirely.
* ``MAMMOTH_AUTO_UPGRADE=1`` performs the upgrade before the command runs,
  once per detected release, through the same manager detection as
  ``mammoth upgrade``; the running command still completes on the version
  that started it. It is opt-in because pinned environments (locks, CI,
  shared venvs) must never change underneath a task.

``MAMMOTH_UPDATE_CACHE`` overrides the cache file path (tests and sandboxes).
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import sys
from pathlib import Path
from typing import Any

import platformdirs

from mammoth_cli import __version__

DISABLE_ENV = "MAMMOTH_NO_UPDATE_CHECK"
AUTO_UPGRADE_ENV = "MAMMOTH_AUTO_UPGRADE"
CACHE_ENV = "MAMMOTH_UPDATE_CACHE"

#: How long a cached PyPI answer is trusted.
CACHE_TTL = _dt.timedelta(hours=24)
#: The background refresh must not hold a finished command hostage.
REFRESH_TIMEOUT_SECONDS = 3.0
#: Commands that manage the install themselves; no hint, no auto-upgrade.
_SELF_MANAGING = frozenset({"upgrade", "doctor"})

UPGRADE_COMMAND = "mammoth upgrade --yes --output json --no-input"

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _flag(name: str) -> bool:
    return (os.environ.get(name) or "").strip().lower() in _TRUTHY


def enabled() -> bool:
    """Whether the check runs at all (``MAMMOTH_NO_UPDATE_CHECK`` unset)."""
    return not _flag(DISABLE_ENV)


def auto_upgrade_enabled() -> bool:
    return enabled() and _flag(AUTO_UPGRADE_ENV)


def cache_path() -> Path:
    override = os.environ.get(CACHE_ENV)
    if override:
        return Path(override).expanduser()
    return Path(platformdirs.user_state_dir("mammoth-cli", "Mammoth")) / "update-check.json"


def _version_key(version: str) -> tuple[int, ...]:
    """Order release versions numerically; a non-numeric tail sorts lowest."""
    parts: list[int] = []
    for piece in version.strip().split("."):
        digits = ""
        for ch in piece:
            if not ch.isdigit():
                break
            digits += ch
        parts.append(int(digits) if digits else -1)
        if digits != piece:
            break
    return tuple(parts)


def is_newer(latest: str | None, current: str | None = None) -> bool:
    if not latest:
        return False
    try:
        return _version_key(latest) > _version_key(current or __version__)
    except ValueError:
        return False


def read_cache() -> dict[str, Any] | None:
    try:
        document = json.loads(cache_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return document if isinstance(document, dict) else None


def write_cache(latest: str | None, *, upgraded_to: str | None = None) -> None:
    path = cache_path()
    document = {
        "checked_at": _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds"),
        "latest": latest,
        "checked_from": __version__,
    }
    if upgraded_to:
        # Set by a successful automatic upgrade so the same release is not
        # installed again by every command until the cache turns over.
        document["upgraded_to"] = upgraded_to
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(document) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        return


def cache_is_fresh(document: dict[str, Any] | None) -> bool:
    if not document:
        return False
    try:
        checked = _dt.datetime.fromisoformat(str(document.get("checked_at")))
    except (TypeError, ValueError):
        return False
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=_dt.UTC)
    return _dt.datetime.now(_dt.UTC) - checked < CACHE_TTL


def available_update(command_id: str | None = None) -> dict[str, Any] | None:
    """The cached answer for ``meta.update_available``; never touches the network."""
    if not enabled() or (command_id or "").split(".")[0] in _SELF_MANAGING:
        return None
    document = read_cache()
    latest = document.get("latest") if document else None
    if not isinstance(latest, str) or not is_newer(latest):
        return None
    return {"current": __version__, "latest": latest, "command": UPGRADE_COMMAND}


def hint_line(update: dict[str, Any]) -> str:
    return (
        f"mammoth-cli {update['latest']} is available (you have {update['current']}); "
        f"run: {update['command']}"
    )


def _fetch_latest() -> str | None:
    """Ask PyPI once, quietly; ``None`` on any failure."""
    import urllib.request

    from mammoth_cli.commands.upgrade import PYPI_JSON_URL

    # The URL is a fixed https PyPI constant, never caller-controlled.
    request = urllib.request.Request(  # noqa: S310
        PYPI_JSON_URL, headers={"Accept": "application/json"}
    )
    try:
        opened = urllib.request.urlopen(request, timeout=REFRESH_TIMEOUT_SECONDS)  # noqa: S310
        with opened as response:
            document = json.loads(response.read())
        version = document["info"]["version"]
    except Exception:  # noqa: BLE001 -- a background check must never surface
        return None
    return str(version) if version else None


def latest_from_pypi() -> str | None:
    """Fetch the latest release now (short timeout) and refresh the cache.

    Used by ``doctor``, which is allowed to reach the network. Returns None
    when PyPI cannot be reached or the check is disabled.
    """
    if not enabled():
        return None
    latest = _fetch_latest()
    if latest is not None:
        write_cache(latest)
    return latest


def refresh_if_stale(command_id: str | None = None) -> None:
    """Refresh the cache after a command when it is older than :data:`CACHE_TTL`."""
    if not enabled() or (command_id or "").split(".")[0] in _SELF_MANAGING:
        return
    if cache_is_fresh(read_cache()):
        return
    write_cache(_fetch_latest())


def emit_hint(update: dict[str, Any] | None, *, output: str) -> None:
    """One stderr line in human output modes only."""
    if update is None or output in {"json", "ndjson", "yaml"}:
        return
    try:
        sys.stderr.write(hint_line(update) + "\n")
    except OSError:
        return


def auto_upgrade(command_id: str, run_log: Any = None) -> dict[str, Any] | None:
    """Upgrade in place when ``MAMMOTH_AUTO_UPGRADE`` is set and a release is cached.

    Returns a record of what happened (also written to ``run_log`` when
    given), or ``None`` when nothing was attempted. The current process keeps
    running on the version that started it.
    """
    if not auto_upgrade_enabled():
        return None
    update = available_update(command_id)
    if update is None:
        return None
    cached = read_cache() or {}
    if cached.get("upgraded_to") == update["latest"]:
        return None
    from mammoth_cli.commands import upgrade as upgrade_cmd

    manager = upgrade_cmd.detect_manager()
    argv = upgrade_cmd.build_upgrade_command(manager, None)
    record: dict[str, Any] = {
        "event": "auto_upgrade",
        "manager": manager,
        "argv": argv,
        "from_version": update["current"],
        "to_version": update["latest"],
    }
    try:
        completed = upgrade_cmd.run_upgrade(argv)
        record["returncode"] = completed.returncode
        record["ok"] = completed.returncode == 0
        if completed.returncode != 0:
            record["stderr_tail"] = (completed.stderr or "")[-400:]
    except Exception as exc:  # noqa: BLE001 -- never fail the user's command
        record["ok"] = False
        record["error"] = str(exc)[:200]
    if record.get("ok"):
        # The cached answer is now the installed version; stop re-upgrading.
        write_cache(update["latest"], upgraded_to=update["latest"])
        message = (
            f"mammoth-cli upgraded {update['current']} -> {update['latest']} "
            f"({AUTO_UPGRADE_ENV}); this command still runs on {update['current']}."
        )
    else:
        message = (
            f"mammoth-cli auto-upgrade to {update['latest']} failed ({AUTO_UPGRADE_ENV}); "
            f"run: {update['command']}"
        )
    try:
        sys.stderr.write(message + "\n")
    except OSError:
        pass
    if run_log is not None:
        try:
            run_log.write(record)
        except Exception:  # noqa: BLE001, S110 -- the run log is best effort
            pass
    return record
