"""The project, if any, a credential is pinned to.

A token created for one project is refused (HTTP 403 ``authorization_required``)
in every other project. The server says which project that is in
``GET /workspaces/current`` (field ``project``); this module reads it so a
command can refuse before it creates something the token cannot open.
"""

from __future__ import annotations

from collections.abc import Callable

from mammoth_cli.errors.envelope import CODE_AUTHORIZATION_REQUIRED, EXIT_AUTH, CliError
from mammoth_cli.services.mapping import PINNED_PROJECT_HINT
from mammoth_cli.services.protocol import MammothService

_CURRENT_SYMBOL = "mammoth.api.workspace.WorkspaceAPI.current"


def pinned_project(service: MammothService) -> int | None:
    """The project id this credential is limited to, or None when it is not limited."""
    current = service.call(_CURRENT_SYMBOL)
    project = current.get("project") if isinstance(current, dict) else current.project
    return project if isinstance(project, int) and project > 0 else None


def require_unpinned_token(service: MammothService, action: str) -> None:
    """Refuse ``action`` when the server says the token is limited to one project."""
    refuse_pinned_project(pinned_project(service), action)


def refuse_pinned_project(project_id: int | None, action: str) -> None:
    """Refuse ``action`` for a token limited to ``project_id``; None means not limited.

    Raises:
        CliError: ``authorization_required`` naming the project the token is
            limited to, before anything is created.
    """
    if project_id is None:
        return
    raise CliError(
        code=CODE_AUTHORIZATION_REQUIRED,
        message=(
            f"This token is limited to project {project_id}, so it cannot {action}: "
            "a project it creates would be closed to it."
        ),
        exit_status=EXIT_AUTH,
        hint=(
            f"Work in project {project_id} (pass --project {project_id}), or ask the operator "
            "for a token created without a project."
        ),
        details={"pinned_project_id": project_id},
        authorization_required=True,
        recovery_commands=[f"mammoth project get {project_id}"],
    )


def qualify_pin_hint(error: CliError, pin_lookup: Callable[[], int | None]) -> CliError:
    """Say whether a 403's "project-limited token" hint applies to this token.

    The generic 403 hint blames a token limited to one project. ``pin_lookup`` reads the
    real pin (``None`` when the token is not limited, or the read fails). When the token
    is not limited the sentence is dropped; when it is, it names the project.
    """
    if error.code != CODE_AUTHORIZATION_REQUIRED or PINNED_PROJECT_HINT not in (error.hint or ""):
        return error
    try:
        pin = pin_lookup()
    except Exception:  # noqa: BLE001 -- keep the original error when the lookup fails
        return error
    assert error.hint is not None
    if pin is None:
        error.hint = error.hint.replace(PINNED_PROJECT_HINT, "").strip()
        return error
    specific = (
        f"This token is limited to project {pin}: pass --project {pin}, or log in with a "
        "token created without a project."
    )
    error.hint = error.hint.replace(PINNED_PROJECT_HINT, specific)
    error.details = {**(error.details or {}), "pinned_project_id": pin}
    return error
