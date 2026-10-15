"""Workspace and project names for human messages.

A message that says only ``workspace 519`` or ``project 4460`` makes the reader look
the id up. These helpers name them (``workspace Filipe Silva (519)``) with one cheap
read each, and fall back to the bare id when the read fails or finds no name: a name
is a courtesy and must never make a login, a status or an error report fail.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.services.protocol import MammothService

_WORKSPACE_GET = "mammoth.api.workspace.WorkspaceAPI.get"
_PROJECT_GET = "mammoth.api.projects.ProjectsAPI.get"


def _name_of(record: Any) -> str | None:
    if not isinstance(record, dict):
        return None
    inner = record.get("workspace", record.get("project", record))
    name = inner.get("name") if isinstance(inner, dict) else None
    return name.strip() if isinstance(name, str) and name.strip() else None


def workspace_name(service: MammothService, workspace_id: int) -> str | None:
    """The workspace's name, or None when it cannot be read."""
    try:
        return _name_of(service.call(_WORKSPACE_GET, workspace_id=workspace_id))
    except Exception:  # noqa: BLE001 -- a name lookup never fails the command
        return None


def project_name(service: MammothService, project_id: int) -> str | None:
    """The project's name, or None when it cannot be read."""
    try:
        return _name_of(service.call(_PROJECT_GET, project=project_id))
    except Exception:  # noqa: BLE001 -- a name lookup never fails the command
        return None


def label(kind: str, ident: int, name: str | None) -> str:
    """``workspace Filipe Silva (519)``; the bare ``workspace 519`` without a name."""
    return f"{kind} {name} ({ident})" if name else f"{kind} {ident}"
