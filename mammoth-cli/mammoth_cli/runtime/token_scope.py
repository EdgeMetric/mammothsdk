"""The projects, if any, a credential is pinned to.

A token created for one project, or a sign-in limited to a few, is refused (HTTP 403
``authorization_required``) in every other project. The server says which projects
in ``GET /workspaces/current``: ``projects`` (every one, sorted) and ``project`` (the
lowest; the only field a server older than multi-project sign-in sends). This module
reads them so a command can refuse before it creates something the token cannot open.

A pin is a non-empty sorted tuple of project ids; None means not limited.

The answer is fixed for the life of a credential, so it is cached on disk for an hour,
keyed by a fingerprint of the long-lived credential. The cache only decides which refusal
or hint the CLI shows; the server enforces the pin on every request, so a stale answer can
never grant access. Diagnostics (``doctor``, ``auth status``) and the 403 hint read it live.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from mammoth_cli.context import credentials, profiles
from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.errors.envelope import CODE_AUTHORIZATION_REQUIRED, EXIT_AUTH, CliError
from mammoth_cli.manifest.loader import _cache_enabled, cache_dir
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.labels import label, project_name
from mammoth_cli.services.mapping import PINNED_PROJECT_HINT
from mammoth_cli.services.protocol import MammothService

Pins = tuple[int, ...]

_CURRENT_SYMBOL = "mammoth.api.workspace.WorkspaceAPI.current"

#: How long a cached pin answer is trusted.
PIN_CACHE_TTL_SECONDS = 3600
_PIN_CACHE_PREFIX = "pins-"

#: Above this many pinned projects, messages give ids only: one name read per project.
MAX_NAMED_PINS = 5


def _is_id(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def as_pins(pin: int | Pins | None) -> Pins | None:
    """One project id, or a set of them, as a pin; None (or nothing) is not limited."""
    if pin is None:
        return None
    ids = sorted({pin} if isinstance(pin, int) else set(pin))
    return tuple(ids) or None


def _fingerprint(auth: ResolvedAuth, profile: str | None) -> str | None:
    """A digest naming this credential, workspace and endpoint; None when it has no stable one.

    An OAuth login is named by its client and connection (``grant_id``, else the refresh
    token's family id), never by the hourly access token or the rotating refresh token.
    """
    if auth.headers:
        return None
    if auth.api_token is not None:
        identity = f"token:{auth.api_token}"
    elif auth.api_key is not None:
        identity = f"key:{auth.api_key}:{auth.api_secret}"
    elif auth.token_provider is not None:
        name = profile or profiles.get_selected()
        credential = credentials.load_credential(name)
        session = credential.oauth if credential is not None else None
        if session is None:
            return None
        connection = session.grant_id
        if connection is None:
            family = session.refresh.partition(".")[0]
            if not family.isdecimal():
                return None
            connection = int(family)
        identity = f"oauth:{session.client_id}:{connection}"
    else:
        return None
    parts = (identity, profile or "", auth.base_url, str(auth.workspace_id))
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()[:32]


def _pin_cache_path(fingerprint: str) -> Path:
    return cache_dir() / f"{_PIN_CACHE_PREFIX}{fingerprint}.json"


def _read_pin_cache(path: Path) -> tuple[bool, Pins | None]:
    """``(True, pins)`` for a fresh cached answer; ``(False, None)`` on a miss or any error."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        at, pins = data["at"], data["pins"]
        if not isinstance(at, int | float) or not 0 <= time.time() - at < PIN_CACHE_TTL_SECONDS:
            return False, None
        if pins is None:
            return True, None
        if not isinstance(pins, list) or not all(_is_id(pin) for pin in pins) or not pins:
            return False, None
        return True, tuple(sorted(set(pins)))
    except (OSError, ValueError, KeyError, TypeError):
        return False, None


def _write_pin_cache(path: Path, pins: Pins | None) -> None:
    """Write the answer atomically, owner-only; a cache that cannot be written is skipped."""
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump({"at": time.time(), "pins": list(pins) if pins else None}, handle)
            os.chmod(tmp, 0o600)
            os.replace(tmp, path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        for old in path.parent.glob(f"{_PIN_CACHE_PREFIX}*.json"):
            if old != path and time.time() - old.stat().st_mtime > PIN_CACHE_TTL_SECONDS:
                old.unlink(missing_ok=True)
    except OSError:
        return


def pinned_projects(
    service: MammothService,
    auth: ResolvedAuth | None = None,
    *,
    profile: str | None = None,
    refresh: bool = False,
) -> Pins | None:
    """The projects this credential is limited to, sorted; None when it is not limited.

    With ``auth`` the answer comes from the on-disk cache when it is fresh, and a live
    read refreshes the cache. ``refresh`` skips the cached answer (diagnostics, a 403).
    Without ``auth`` the server is always asked.
    """
    path: Path | None = None
    if auth is not None and not embedded.active() and _cache_enabled():
        try:
            fingerprint = _fingerprint(auth, profile)
        except CliError:
            fingerprint = None
        if fingerprint is not None:
            path = _pin_cache_path(fingerprint)
            if not refresh:
                hit, cached = _read_pin_cache(path)
                if hit:
                    return cached
    pins = _live_pins(service)
    if path is not None:
        _write_pin_cache(path, pins)
    return pins


def _live_pins(service: MammothService) -> Pins | None:
    current = service.call(_CURRENT_SYMBOL)

    def read(key: str) -> Any:
        return current.get(key) if isinstance(current, dict) else getattr(current, key, None)

    projects = read("projects")
    if isinstance(projects, list):
        ids = sorted({project for project in projects if _is_id(project)})
        if ids:
            return tuple(ids)
    project = read("project")
    return (project,) if _is_id(project) else None


def pin_names(service: MammothService, pins: Pins | None) -> dict[int, str | None]:
    """Each pinned project's name (None when unreadable); empty past MAX_NAMED_PINS."""
    if pins is None or len(pins) > MAX_NAMED_PINS:
        return {}
    return {pin: project_name(service, pin) for pin in pins}


def pins_label(pins: Pins, names: Mapping[int, str | None] | None = None) -> str:
    """``project Sales (3)``, or ``projects Sales (3), 7`` for a token limited to several."""
    names = names or {}
    if len(pins) == 1:
        return label("project", pins[0], names.get(pins[0]))
    named = (f"{names[pin]} ({pin})" if names.get(pin) else str(pin) for pin in pins)
    return "projects " + ", ".join(named)


def pin_details(pins: Pins) -> dict[str, Any]:
    """Error details naming the pin: the lowest project, and every one when several."""
    details: dict[str, Any] = {"pinned_project_id": pins[0]}
    if len(pins) > 1:
        details["pinned_project_ids"] = list(pins)
    return details


def require_unpinned_token(service: MammothService, action: str) -> None:
    """Refuse ``action`` when the server says the token is limited to some projects."""
    pins = pinned_projects(service)
    refuse_pinned_project(pins, action, project_names=pin_names(service, pins))


def refuse_pinned_project(
    project_ids: int | Pins | None,
    action: str,
    *,
    project_name: str | None = None,
    project_names: Mapping[int, str | None] | None = None,
) -> None:
    """Refuse ``action`` for a token limited to ``project_ids``; None means not limited.

    Raises:
        CliError: ``authorization_required`` naming the projects the token is
            limited to, before anything is created.
    """
    pins = as_pins(project_ids)
    if pins is None:
        return
    names = dict(project_names or {})
    if project_name is not None:
        names.setdefault(pins[0], project_name)
    where = f"project {pins[0]}" if len(pins) == 1 else "one of those projects"
    raise CliError(
        code=CODE_AUTHORIZATION_REQUIRED,
        message=(
            f"This token is limited to {pins_label(pins, names)}, "
            f"so it cannot {action}: "
            "a project it creates would be closed to it."
        ),
        exit_status=EXIT_AUTH,
        hint=(
            f"Work in {where} (pass --project {pins[0]}), or ask the operator "
            "for a token created without a project."
        ),
        details=pin_details(pins),
        authorization_required=True,
        recovery_commands=[f"mammoth project get {pins[0]}"],
    )


_NOT_A_MEMBER = re.compile(r"You are not a member of project (\d+)\.?$")


def _looked_up_names(
    pins: Pins, name_lookup: Callable[[int], str | None] | None
) -> dict[int, str | None]:
    if name_lookup is None or len(pins) > MAX_NAMED_PINS:
        return {}
    names: dict[int, str | None] = {}
    for pin in pins:
        try:
            names[pin] = name_lookup(pin)
        except Exception:  # noqa: BLE001 -- a name is a courtesy; keep the id
            names[pin] = None
    return names


def qualify_pin_hint(
    error: CliError,
    pin_lookup: Callable[[], int | Pins | None],
    name_lookup: Callable[[int], str | None] | None = None,
) -> CliError:
    """Say whether a 403's "project-limited token" hint applies to this token.

    The generic 403 hint blames a token limited to one project. ``pin_lookup`` reads the
    real pin (``None`` when the token is not limited, or the read fails). When the token
    is not limited the sentence is dropped; when it is, it names the projects, with their
    names when ``name_lookup`` finds them (a failed lookup leaves the bare id).
    """
    if error.code != CODE_AUTHORIZATION_REQUIRED:
        return error
    membership = _NOT_A_MEMBER.match(error.message or "")
    if membership is None and PINNED_PROJECT_HINT not in (error.hint or ""):
        return error
    try:
        pins = as_pins(pin_lookup())
    except Exception:  # noqa: BLE001 -- keep the original error when the lookup fails
        return error
    if membership is not None:
        # A token limited to some projects is refused elsewhere; "ask an admin to add
        # you" is the wrong fix for that. Inside the pin it is the right one.
        if pins is None or int(membership.group(1)) in pins:
            return error
        error.message = (
            f"This token is limited to {pins_label(pins, _looked_up_names(pins, name_lookup))}"
            f", so it cannot open project {membership.group(1)}."
        )
        error.hint = f"Pass --project {pins[0]}, or log in with a token created without a project."
        error.details = {**(error.details or {}), **pin_details(pins)}
        return error
    assert error.hint is not None
    if pins is None:
        error.hint = error.hint.replace(PINNED_PROJECT_HINT, "").strip()
        return error
    specific = (
        f"This token is limited to {pins_label(pins, _looked_up_names(pins, name_lookup))}: "
        f"pass --project {pins[0]}, or log in with a token created without a project."
    )
    error.hint = error.hint.replace(PINNED_PROJECT_HINT, specific)
    error.details = {**(error.details or {}), **pin_details(pins)}
    return error
