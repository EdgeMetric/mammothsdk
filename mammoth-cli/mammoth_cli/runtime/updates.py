"""Daily update check, and the automatic update (on by default).

The CLI never blocks a command on the network for this. A command reads the
cached answer (``update-check.json`` in the platform state directory, next to
the run log's ``logs/``) and, when that answer is older than a day, starts a
detached process *after* its own output has been written. That process asks
PyPI and, when a newer release exists, installs it through the same manager
detection as ``mammoth upgrade``. The install runs after the command and
outside it on purpose: replacing the installed files under a running command
would break its lazy imports, and a failed install must not touch the command
that started it. The attempt, and any failure, is written to the run log
(``auto_upgrade`` records); nothing is printed and the exit status is never
changed.

What a caller sees:

* ``meta.update_available`` in every success envelope: ``null``, or
  ``{"current", "latest", "command"}`` when a newer release is on PyPI and
  will not be installed by itself (auto-update off, or the install failed).
* one line on stderr in human output modes (never in ``json``/``ndjson``) in
  that same case.
* ``MAMMOTH_NO_AUTO_UPDATE=1`` (or ``MAMMOTH_AUTO_UPGRADE=0``) keeps the check
  and the hint but never installs: set it in CI, containers and agent
  sandboxes whose installed version must not change.
* ``MAMMOTH_NO_UPDATE_CHECK=1`` disables the check, the hint and the update.
* ``upgrade`` and ``doctor`` never start an update.
* a pinned install is never updated by itself. ``mammoth upgrade --version X``
  and ``mammoth-install.sh --version X`` record the pin (``pin.json`` next to
  the cache); a plain ``mammoth upgrade`` (the latest) clears it. While it is
  set the daily check still runs and ``meta.update_available`` still shows, so
  the newer release is visible but only an explicit ``mammoth upgrade`` installs it.

``MAMMOTH_UPDATE_CACHE`` overrides the cache file path (tests and sandboxes).
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import platformdirs

from mammoth_cli import __version__
from mammoth_cli.runtime import embedded

DISABLE_ENV = "MAMMOTH_NO_UPDATE_CHECK"
AUTO_UPGRADE_ENV = "MAMMOTH_AUTO_UPGRADE"
NO_AUTO_UPDATE_ENV = "MAMMOTH_NO_AUTO_UPDATE"
CACHE_ENV = "MAMMOTH_UPDATE_CACHE"

#: How long a cached PyPI answer is trusted: PyPI is asked at most once a day.
CACHE_TTL = _dt.timedelta(days=1)
#: The background refresh must not hold a finished command hostage.
REFRESH_TIMEOUT_SECONDS = 3.0
#: Commands that manage the install themselves; no hint, no auto-upgrade.
# Commands that check PyPI themselves, so the background refresh skips them.
_SELF_MANAGING = frozenset({"upgrade", "doctor"})
# Commands whose envelope never carries the notice: only ``upgrade``. doctor
# carries it too, because agents act on ``meta.update_available`` and doctor
# is the first command they run.
_NO_NOTICE = frozenset({"upgrade"})

UPGRADE_COMMAND = "mammoth upgrade --yes"

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_FALSY = frozenset({"0", "false", "no", "off"})


def _flag(name: str) -> bool:
    return (os.environ.get(name) or "").strip().lower() in _TRUTHY


def enabled() -> bool:
    """Whether the check runs at all (``MAMMOTH_NO_UPDATE_CHECK`` unset, not embedded)."""
    return not _flag(DISABLE_ENV) and not embedded.active()


def auto_upgrade_enabled() -> bool:
    """On by default; ``MAMMOTH_NO_AUTO_UPDATE=1`` or ``MAMMOTH_AUTO_UPGRADE=0`` turns it off."""
    if not enabled() or _flag(NO_AUTO_UPDATE_ENV):
        return False
    return (os.environ.get(AUTO_UPGRADE_ENV) or "").strip().lower() not in _FALSY


def cache_path() -> Path:
    override = os.environ.get(CACHE_ENV)
    if override:
        return Path(override).expanduser()
    return Path(platformdirs.user_state_dir("mammoth-cli", "Mammoth")) / "update-check.json"


def pin_path() -> Path:
    return cache_path().with_name("pin.json")


def read_pin() -> str | None:
    """The release this install is pinned to, or None when it follows the latest."""
    try:
        document = json.loads(pin_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    version = document.get("version") if isinstance(document, dict) else None
    return version if isinstance(version, str) and version else None


def write_pin(version: str) -> bool:
    """Record that this install is pinned to ``version``; False when it cannot be written."""
    path = pin_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": version}) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        return False
    return True


def clear_pin() -> None:
    try:
        pin_path().unlink()
    except OSError:
        return


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


def write_cache(
    latest: str | None, *, upgraded_to: str | None = None, upgrade_failed: str | None = None
) -> None:
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
    if upgrade_failed:
        # The release the automatic install could not put in place: the hint
        # comes back so the user can run the upgrade by hand.
        document["upgrade_failed"] = upgrade_failed
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
    if not enabled() or (command_id or "").split(".")[0] in _NO_NOTICE:
        return None
    document = read_cache()
    if not document:
        return None
    latest = document.get("latest")
    if not isinstance(latest, str) or not is_newer(latest):
        return None
    if auto_upgrade_enabled() and read_pin() is None and document.get("upgrade_failed") != latest:
        # The next daily check installs it; a notice would only repeat itself.
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


def refresh_in_background(command_id: str | None = None) -> None:
    """Refresh a stale cache in a detached process, so the command exits at once.

    :func:`refresh_if_stale` asks PyPI with a 3 s timeout; run inline it keeps
    the finished command alive for up to that long once a day. The cache is
    stamped first so concurrent commands do not each spawn a check; the child
    (``python -m mammoth_cli.runtime.updates``) writes the answer and, with
    auto-update on, installs a newer release.
    """
    if not enabled() or (command_id or "").split(".")[0] in _SELF_MANAGING:
        return
    cached = read_cache()
    if cache_is_fresh(cached):
        return
    previous = cached.get("latest") if cached else None
    write_cache(previous if isinstance(previous, str) else None)
    try:
        subprocess.Popen(  # noqa: S603 -- fixed argv, our own module
            [sys.executable, "-m", "mammoth_cli.runtime.updates"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
    except OSError:
        return


def emit_hint(update: dict[str, Any] | None, *, output: str) -> None:
    """One stderr line in human output modes only."""
    if update is None or output in {"json", "ndjson", "yaml"}:
        return
    try:
        sys.stderr.write(hint_line(update) + "\n")
    except OSError:
        return


def auto_upgrade(latest: str, run_log: Any = None) -> dict[str, Any] | None:
    """Install release ``latest`` through the manager that owns this install.

    Returns a record of what happened (also written to ``run_log`` when
    given), or ``None`` when nothing was attempted: auto-update is off,
    ``latest`` is not newer, the install is pinned, or it was already
    installed. Never raises.
    """
    if not auto_upgrade_enabled() or not is_newer(latest):
        return None
    if read_pin() is not None:
        # A pinned install stays on its release; ``available_update`` still shows the hint.
        return None
    if (read_cache() or {}).get("upgraded_to") == latest:
        return None
    record: dict[str, Any] = {
        "event": "auto_upgrade",
        "from_version": __version__,
        "to_version": latest,
    }
    try:
        from mammoth_cli.commands import upgrade as upgrade_cmd

        manager = upgrade_cmd.detect_manager()
        argv = upgrade_cmd.build_upgrade_command(manager, None)
        record.update(manager=manager, argv=argv)
        completed = upgrade_cmd.run_upgrade(argv)
        record["returncode"] = completed.returncode
        record["ok"] = completed.returncode == 0
        if completed.returncode != 0:
            record["stderr_tail"] = (completed.stderr or "")[-400:]
    except Exception as exc:  # noqa: BLE001 -- never fail the user's command
        record["ok"] = False
        record["error"] = str(exc)[:200]
    if record["ok"]:
        # The installed release is the cached one: stop trying it again.
        write_cache(latest, upgraded_to=latest)
    else:
        write_cache(latest, upgrade_failed=latest)
    if run_log is not None:
        try:
            run_log.write(record)
        except Exception:  # noqa: BLE001, S110 -- the run log is best effort
            pass
    return record


def _check_and_upgrade() -> None:  # pragma: no cover - the detached process
    """Ask PyPI, refresh the cache and install a newer release; log, never print."""
    from mammoth_cli.runtime.runlog import RunLog

    latest = _fetch_latest()
    if latest is None:
        # PyPI did not answer: keep the earlier answer for the hint and install nothing.
        previous = (read_cache() or {}).get("latest")
        write_cache(previous if isinstance(previous, str) else None)
        return
    write_cache(latest)
    if not auto_upgrade_enabled() or not is_newer(latest):
        return
    run_log = RunLog.start("auto-update", argv=[])
    try:
        auto_upgrade(latest, run_log)
    finally:
        run_log.finish(0)


if __name__ == "__main__":  # pragma: no cover - the detached refresh process
    _check_and_upgrade()
