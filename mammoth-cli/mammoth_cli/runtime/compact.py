"""Lean success payloads for dashboard writes; ``--full`` returns the whole response.

A dashboard write (``figure add``, ``v3 generate``, ``chat edit``, ...) answered
with the whole canvas, some 15-20 KB that is mostly nulls, when the agent needs
the new ids, the checks and ``verify``. By default this keeps every id and
value, turns each ``canvas`` into a short summary (page count and each
figure's id, kind, title and page), leaves out the planner's ``plan`` and
``specs``, and drops null-only fields. ``verify`` is never trimmed. The result
names what was left out and the read that returns it; ``--full`` on the command
returns the old payload.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mammoth_cli.runtime.invocation import Invocation

FULL_FLAG = "--full"

#: The commands whose success payload is compacted by default.
COMPACT_COMMANDS = frozenset(
    {
        "dashboard.figure.add",
        "dashboard.figure-intent",
        "dashboard.v3.generate",
        "dashboard.chat.edit",
        "dashboard.filter.add",
        "dashboard.canvas.restore",
        "dashboard.canvas.save",
    }
)

#: Keys left out in compact mode: the planner's working state, not a result.
_OMITTED_KEYS = ("plan", "specs")
#: Keys kept exactly as they are, nulls included.
_KEPT_AS_IS = frozenset({"verify"})
_MAX_FIGURES = 50
_DROP = object()


def _canvas_summary(canvas: dict[str, Any]) -> dict[str, Any]:
    pages = [page for page in canvas.get("pages") or [] if isinstance(page, dict)]
    figures: list[dict[str, Any]] = []
    for container in [canvas, *pages]:
        page_id = container.get("id") if container is not canvas else None
        for figure in [container.get("focus"), *(container.get("added") or [])]:
            if not isinstance(figure, dict):
                continue
            entry = {
                "id": figure.get("id"),
                "kind": figure.get("kind"),
                "title": figure.get("title"),
                "page": page_id,
            }
            figures.append({key: value for key, value in entry.items() if value is not None})
    summary: dict[str, Any] = {"pages": len(pages), "figures": figures[:_MAX_FIGURES]}
    if len(figures) > _MAX_FIGURES:
        summary["figures_total"] = len(figures)
    return summary


def _compact(value: Any, path: str, omitted: list[str]) -> Any:
    if isinstance(value, list):
        return [_compact(item, path, omitted) for item in value]
    if not isinstance(value, dict):
        return value
    result: dict[str, Any] = {}
    for key, item in value.items():
        where = f"{path}.{key}" if path else str(key)
        if key in _KEPT_AS_IS:
            result[key] = item
        elif key == "canvas" and isinstance(item, dict):
            result["canvas_summary"] = _canvas_summary(item)
            omitted.append(where)
        elif key in _OMITTED_KEYS and item is not None:
            omitted.append(where)
        elif item is not None:
            compacted = _compact(item, where, omitted)
            if not _null_only(item, compacted):
                result[key] = compacted
    return result


def _null_only(original: Any, compacted: Any) -> bool:
    """A dict that had keys and lost them all to nulls says nothing; drop it."""
    return isinstance(original, dict) and bool(original) and compacted == {}


def _dashboard_id(invocation: Invocation, data: dict[str, Any]) -> Any:
    for value in (invocation.positionals.get("dashboard_id"), data.get("dashboard_id")):
        if isinstance(value, (int, str)) and str(value):
            return value
    return "DASHBOARD_ID"


def with_compact(invocation: Invocation, data: Any) -> Any:
    """``data`` compacted for a command in :data:`COMPACT_COMMANDS`, unless ``--full``."""
    if (
        invocation.command_id not in COMPACT_COMMANDS
        or invocation.full_output
        or invocation.dry_run
        or not isinstance(data, dict)
    ):
        return data
    omitted: list[str] = []
    result = _compact(data, "", omitted)
    if omitted:
        result["compact"] = {
            "omitted": omitted,
            "read_with": f"mammoth dashboard canvas get {_dashboard_id(invocation, data)}",
            "full": (
                f"This write already ran: read the rest with read_with. Pass {FULL_FLAG} "
                "on a later run of the command for the complete response."
            ),
        }
    return result
