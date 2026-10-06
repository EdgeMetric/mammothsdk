"""The ``resolve`` command: read-only, says what a name refers to.

A user types a name ("uqa-w29-ren") and the agent has to know whether it is a
dataset, a view or a project, and where. Reading it as the wrong kind sent the
agent looking for a project that was a dataset's name, and a name that lives in
another project made it ask the user to switch scope. One call answers both:
every dataset, view and project whose name matches, with ids and projects.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.dataset import (
    _require_string_positional,
    _visible_projects,
    search_cut_note,
    search_hits,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service

HandlerResult = tuple[Any, dict[str, Any]]

#: Resource-search type for each kind of match, in the order the kinds are listed.
_SEARCH_TYPES = (("dataset", "datasource"), ("view", "dataview"))


def _row(
    kind: str, needle: str, entry: dict[str, Any], names: dict[Any, Any], home: int | None
) -> dict[str, Any]:
    """One match: its kind, ids, project, whether the name is exact and where it sits."""
    is_project = kind == "project"
    project_id = entry.get("id") if is_project else entry.get("project_id")
    name = entry.get("name")
    row: dict[str, Any] = {
        "kind": kind,
        "id": entry.get("id") if is_project else entry.get("object_id"),
        "name": name,
        "project_id": project_id,
        "project_name": name if is_project else names.get(project_id),
        "exact": isinstance(name, str) and name.lower() == needle,
    }
    if home is not None:
        row["in_project"] = project_id == home
    return row


def resolve_matches(
    needle: str,
    projects: list[dict[str, Any]],
    hits_by_kind: dict[str, list[dict[str, Any]]],
    home: int | None = None,
) -> list[dict[str, Any]]:
    """Every project, dataset and view whose name contains ``needle`` (any case).

    Exact names come first, then the project the call runs under (``home``), then
    projects, datasets and views in that order. Pure: no network.
    """
    lowered = needle.lower()
    names = {p.get("id"): p.get("name") for p in projects}
    rows = [
        _row("project", lowered, p, names, home)
        for p in projects
        if isinstance(p.get("name"), str) and lowered in p["name"].lower()
    ]
    for kind, _ in _SEARCH_TYPES:
        rows += [_row(kind, lowered, h, names, home) for h in hits_by_kind.get(kind, [])]
    order = {"project": 0, "dataset": 1, "view": 2}
    return sorted(
        rows, key=lambda r: (not r["exact"], not r.get("in_project", False), order[r["kind"]])
    )


def kinds_note(name: str, rows: list[dict[str, Any]]) -> str:
    """Says what the name is: one kind, or several, so it is never read as the wrong one."""
    if not rows:
        return f"Nothing visible to this login is named like '{name}'."
    exact = [r for r in rows if r["exact"]] or rows
    kinds = sorted({r["kind"] for r in exact}, key=("project", "dataset", "view").index)
    if len(exact) == 1:
        only = exact[0]
        return f"'{name}' is a {only['kind']} (id {only['id']}) in project {only['project_name']}."
    if len(kinds) == 1:
        where = sorted({str(r["project_name"]) for r in exact})
        return f"'{name}' is {len(exact)} {kinds[0]}s, in projects {', '.join(where)}: ask which."
    return (
        f"'{name}' names {len(exact)} things ({', '.join(kinds)}): tell them apart by "
        "kind and project before using an id."
    )


def resolve(invocation: Invocation) -> HandlerResult:
    """Say what NAME refers to: a dataset, a view or a project, with ids and projects.

    Read-only. NAME is a case-insensitive substring and the only argument; the
    command has no options besides the global ``--project``, which only marks
    each match ``in_project`` (matches elsewhere are always returned). Searches
    every project the credential can see. Does not require an active project.
    """
    name = _require_string_positional(invocation, "name")
    cut = False
    with open_service(invocation) as (service, auth):
        projects = _visible_projects(service)
        hits: dict[str, list[dict[str, Any]]] = {}
        for kind, resource_type in _SEARCH_TYPES:
            hits[kind], more = search_hits(service, resource_type, name)
            cut = cut or more
        meta = {
            "profile": invocation.profile,
            "workspace_id": auth.workspace_id,
            "project_id": invocation.project,
        }
    rows = resolve_matches(name, projects, hits, invocation.project)
    result: dict[str, Any] = {"name": name, "matches": rows, "note": kinds_note(name, rows)}
    if cut:
        result["truncated"] = True
        result["note"] += " " + search_cut_note("datasets or views")
    return result, meta
