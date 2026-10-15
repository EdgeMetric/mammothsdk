"""The projects, if any, a credential is pinned to.

A token created for one project, or a sign-in limited to a few, is refused (HTTP 403
``authorization_required``) in every other project. The server says which projects
in ``GET /workspaces/current``: ``projects`` (every one, sorted) and ``project`` (the
lowest; the only field a server older than multi-project sign-in sends). This module
reads them so a command can refuse before it creates something the token cannot open.

A pin is a non-empty sorted tuple of project ids; None means not limited.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

from mammoth_cli.errors.envelope import CODE_AUTHORIZATION_REQUIRED, EXIT_AUTH, CliError
from mammoth_cli.runtime.labels import label, project_name
from mammoth_cli.services.mapping import PINNED_PROJECT_HINT
from mammoth_cli.services.protocol import MammothService

Pins = tuple[int, ...]

_CURRENT_SYMBOL = "mammoth.api.workspace.WorkspaceAPI.current"

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


def pinned_projects(service: MammothService) -> Pins | None:
    """The projects this credential is limited to, sorted; None when it is not limited."""
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
