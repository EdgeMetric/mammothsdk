"""Find datasets by name or columns, search their values, and summarize their columns."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mammoth_cli.commands.dataset._common import (
    _meta,
    _require_string_positional,
)
from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services.listing import (
    ambiguity_note,
    compact_columns,
    fit_budget,
    name_hit,
    source_of,
)


def _visible_projects(service: Any) -> list[dict[str, Any]]:
    """Every project the credential is a member of, across all pages."""
    return list(service.list_all_projects())


def _tokens_in_order(needle: str, name: str) -> bool:
    """Every whitespace-separated token of ``needle`` is in ``name``, in order, any case."""
    position = 0
    lowered = name.lower()
    for token in needle.lower().split():
        found = lowered.find(token, position)
        if found < 0:
            return False
        position = found + len(token)
    return True


def _search_term(needle: str) -> str:
    """The longest word of ``needle``: the server searches a substring, the words are
    matched in order here."""
    return max(needle.split(), key=len, default="")


def _hit_record(hit: dict[str, Any]) -> dict[str, Any]:
    """A resource-search hit in the shape of a dataset record, for ``name_hit``/``source_of``."""
    info = hit.get("additional_info")
    original = info.get("ORIGINAL_FILE_PROPS") if isinstance(info, dict) else None
    file_name = original.get("FILE_NAME") if isinstance(original, dict) else None
    return {
        "id": hit.get("object_id"),
        "name": hit.get("name"),
        "status": hit.get("status"),
        "created_at": hit.get("created_at"),
        "updated_at": hit.get("last_updated_at"),
        "stats": {"row_count": hit.get("row_count"), "column_count": hit.get("column_count")},
        "additional_info": info,
        "sources": [
            {
                "type": hit.get("source_type"),
                "details": {"file_name": file_name, "connector_key": hit.get("integration_key")},
            }
        ],
    }


def _find_by_name(
    service: Any, needle: str, projects: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Datasets in ``projects`` whose name has every token of ``needle`` in order, and whether cut.

    One workspace search returns each hit with its size, times and source, so no
    project's dataset list is read: that route costs the server a few queries per
    dataset, and a project of a few hundred datasets took 20+ s to list.
    """
    names = {p.get("id"): p.get("name") for p in projects}
    hits, cut = search_hits(service, "datasource", _search_term(needle), fields="standard")
    matches = []
    for hit in hits:
        name = hit.get("name")
        if hit.get("project_id") not in names or not isinstance(name, str):
            continue
        if not _tokens_in_order(needle, name):
            continue
        record = _hit_record(hit)
        matches.append(
            {
                "project_id": hit["project_id"],
                "project_name": names[hit["project_id"]],
                **name_hit(record),
                "source": source_of(record),
            }
        )
    return matches, cut


#: Pages of resource search read for one name (100 hits each); past it the result says so.
_SEARCH_PAGES = 5


_SEARCH_PAGE_SIZE = 100


def search_hits(
    service: Any,
    resource_type: str,
    needle: str,
    project_id: int | None = None,
    fields: str = "minimal",
) -> tuple[list[dict[str, Any]], bool]:
    """Resources of ``resource_type`` whose name contains ``needle``, from the search route.

    One request (one more per 100 hits) replaces a listing per project: the
    workspace search, or the project's own resource list when ``project_id`` is
    given. Returns the minimal rows and whether the read stopped at
    ``_SEARCH_PAGES`` pages with more hits unread.
    """
    symbol = (
        "mammoth.api.browse.BrowseAPI.resources_search"
        if project_id is None
        else "mammoth.api.browse.BrowseAPI.resources_list"
    )
    scope: dict[str, Any] = {} if project_id is None else {"project_id": project_id}
    rows: list[dict[str, Any]] = []
    cursor: str | None = None
    for _ in range(_SEARCH_PAGES):
        page = service.call(
            symbol,
            search=needle or None,
            resource_type=resource_type,
            limit=_SEARCH_PAGE_SIZE,
            cursor=cursor,
            fields=fields,
            **scope,
        )
        rows += [r for r in page.get("resources", []) if isinstance(r, dict)]
        cursor = page.get("next_cursor")
        if not (page.get("has_more") and cursor):
            return rows, False
    return rows, True


def search_cut_note(kind: str) -> str:
    """Said when a name search stopped early, with how to narrow it."""
    return (
        f"The name matched more than {_SEARCH_PAGES * _SEARCH_PAGE_SIZE} {kind}, so only the "
        "first of them were read. Use a longer name, or --project, to narrow it."
    )


def _other_projects(visible: list[dict[str, Any]], project_id: int) -> list[dict[str, Any]]:
    """Every visible project except ``project_id``."""
    return [p for p in visible if p.get("id") != project_id]


def named_project(service: Any, project_id: int, visible: list[dict[str, Any]]) -> dict[str, Any]:
    """``{"id", "name"}`` of ``project_id``, so a match can say where it was found.

    A search scoped by ``--project`` knew only the id, and its matches came back
    with ``project_name: None``: the agent could not tell the user which project
    held the dataset.
    """
    for project in visible:
        if project.get("id") == project_id:
            return project
    record = service.call("mammoth.api.projects.ProjectsAPI.get", project_id=project_id)
    record = record.model_dump(mode="json") if hasattr(record, "model_dump") else record
    record = record.get("project", record) if isinstance(record, dict) else {}
    return {"id": project_id, "name": record.get("name")}


def _requested_columns(document: dict[str, Any]) -> list[str]:
    """The ``columns`` input as a list of names (a comma-separated string is split)."""
    raw = document.get("columns")
    if raw is None:
        return []
    names = raw.split(",") if isinstance(raw, str) else raw
    if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="'columns' must be a list of column names (or one comma-separated string).",
            exit_status=EXIT_USAGE,
        )
    return [n.strip() for n in names if n.strip()]


def _column_names(hit: dict[str, Any]) -> list[str]:
    """Display names of the columns a full-field search hit carries."""
    properties = hit.get("object_properties")
    metadata = properties.get("metadata") if isinstance(properties, dict) else None
    return [
        str(c["display_name"])
        for c in metadata or []
        if isinstance(c, dict) and c.get("display_name")
    ]


def _find_by_columns(
    service: Any,
    needle: str,
    columns: list[str],
    visible: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    """Datasets (named like ``needle``, when given) that have every one of ``columns``."""
    hits, cut = search_hits(service, "datasource", needle, fields="full")
    names = {p.get("id"): p.get("name") for p in visible}
    wanted = [c.lower() for c in columns]
    matches: list[dict[str, Any]] = []
    for hit in hits:
        have = _column_names(hit)
        if not set(wanted) <= {c.lower() for c in have}:
            continue
        matches.append(
            {
                "project_id": hit.get("project_id"),
                "project_name": names.get(hit.get("project_id")),
                "id": hit.get("object_id"),
                "name": hit.get("name"),
                "rows": hit.get("row_count"),
                "cols": len(have),
                "columns": compact_columns([(c, None) for c in have], limit=None),
            }
        )
    return matches, cut


def _tag_scope(matches: list[dict[str, Any]], project_id: int) -> list[dict[str, Any]]:
    """Mark each match ``in_project``: whether it sits in the project the call runs under."""
    return [{**m, "in_project": m.get("project_id") == project_id} for m in matches]


def all_projects_requested(invocation: Invocation) -> bool:
    """Whether ``--input '{"all_projects": true}'`` asks for matches outside the project."""
    value = (invocation.load_input() or {}).get("all_projects", False)
    if not isinstance(value, bool):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="all_projects must be true or false.",
            exit_status=EXIT_USAGE,
        )
    return value


def narrow_to_project(
    rows: list[dict[str, Any]], is_exact: Callable[[dict[str, Any]], bool]
) -> tuple[list[dict[str, Any]], int]:
    """``(rows, dropped)``: only the project's own rows when one of them is an exact match.

    The name already is in the project the call runs under, so the same name in
    every other project is noise that reads as an ambiguity to ask the user about.
    Rows must carry ``in_project``. With no exact match in the project, all rows
    stay: the name may live elsewhere. ``dropped`` counts the rows left out.
    """
    own = [r for r in rows if r.get("in_project")]
    if not any(is_exact(r) for r in own):
        return rows, 0
    return own, len(rows) - len(own)


def elsewhere_note(dropped: int) -> str:
    """Says how many matches in other projects were left out, and how to list them."""
    if not dropped:
        return ""
    return (
        f"{dropped} more match(es) in other projects are not listed; the match in the "
        "current project is the answer. They matter only when the user names another "
        """project: then --input '{"all_projects": true}' lists them."""
    )


def _find_note(
    matches: list[dict[str, Any]], is_exact: Callable[[dict[str, Any]], bool], needle: str
) -> str | None:
    """The ambiguity note, unless exactly one match in the project is the exact name."""
    own = [m for m in matches if m.get("in_project") and is_exact(m)]
    if len(own) != 1 or len(matches) < 2:
        return ambiguity_note(len(matches), needle)
    return (
        f"'{own[0]['name']}' is dataset {own[0]['id']} in the current project; the other "
        f"{len(matches) - 1} match(es) are other datasets or sit in other projects: use this id."
    )


def _find_scoped(
    service: Any,
    needle: str,
    visible: list[dict[str, Any]],
    project_id: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    """``(matches, projects searched, cut)``: the project's own matches, then every other one's."""
    searched = [named_project(service, project_id, visible), *_other_projects(visible, project_id)]
    found, cut = _find_by_name(service, needle, searched)
    matches = sorted(_tag_scope(found, project_id), key=lambda m: not m["in_project"])
    return matches, searched, cut


#: Trashed datasets read for one name when nothing live matched it.
_TRASH_LOOKUP_LIMIT = 5


def _trashed_matches(service: Any, needle: str, project_id: int) -> list[dict[str, Any]]:
    """Datasets in the project's trash whose name has every token of ``needle`` in order.

    A name that matches nothing live is most often a dataset someone deleted: the
    in-product agent then told the user it did not exist and offered unrelated datasets
    (gap eval 10-10, "Late delivery log").
    """
    data = service.call(
        "mammoth.api.trash.TrashAPI.list",
        project_id=project_id,
        type="dataset",
        q=needle,
        limit=_TRASH_LOOKUP_LIMIT,
    )
    items = data.get("items", []) if isinstance(data, dict) else []
    return [
        {
            "id": item.get("id"),
            "name": item.get("name"),
            "trashed_at": item.get("trashed_at"),
            "trashed_by": (item.get("trashed_by") or {}).get("name"),
            "days_until_purge": item.get("days_until_purge"),
        }
        for item in items
        if isinstance(item, dict)
        and item.get("type") == "dataset"
        and item.get("trashed_at")
        and isinstance(item.get("name"), str)
        and _tokens_in_order(needle, item["name"])
    ]


def _trashed_note(trashed: list[dict[str, Any]], needle: str) -> str:
    """Says the name is in the trash and how to bring it back."""
    first = trashed[0]
    who = f" by {first['trashed_by']}" if first.get("trashed_by") else ""
    return (
        f"No live dataset matches '{needle}', but '{first['name']}' (dataset "
        f"{first['id']}) is in this project's trash, deleted {first['trashed_at']}{who}. "
        "Tell the user it is in the trash and offer to restore it: "
        f"mammoth dataset restore {first['id']}. Do not offer other datasets in its place."
    )


def dataset_find(invocation: Invocation) -> HandlerResult:
    """Search dataset names for a substring across every visible project.

    Read-only local composite: lists the projects the credential can see, then
    reads one workspace search for the name and keeps the datasets whose name has
    every word of the substring, in order, ignoring case. With
    ``--project`` the project's own matches come first and the matches in every
    other visible project are returned too, each row marked ``in_project`` and
    carrying its ``project_id`` and ``project_name``: the in-product agent runs
    every call under the project the user last opened, which is often not the one
    the named dataset is in, so it states where the name is instead of asking the
    user to switch. When the project holds an exact match, only the project's own
    matches are returned and ``elsewhere`` counts the rest; ``--input
    '{"all_projects": true}'`` returns them all. When nothing live matches and a
    project is set, the project's trash is read for the name too: a hit comes back as
    ``trashed_matches`` with a note to offer ``dataset restore``. Does not require an
    active project.
    """
    name_substring = _require_string_positional(invocation, "name substring")
    needle = name_substring.lower()
    dropped = 0

    def is_exact(m: dict[str, Any]) -> bool:
        return str(m.get("name", "")).lower() == needle

    with open_service(invocation) as (service, auth):
        visible = _visible_projects(service)
        cut = False
        if invocation.project is not None:
            matches, projects, cut = _find_scoped(service, needle, visible, invocation.project)
            if not all_projects_requested(invocation):
                matches, dropped = narrow_to_project(matches, is_exact)
        else:
            projects = visible
            matches, cut = _find_by_name(service, needle, visible)
        trashed = (
            _trashed_matches(service, needle, invocation.project)
            if not matches and invocation.project is not None
            else []
        )
        meta = {
            "profile": invocation.profile,
            "workspace_id": auth.workspace_id,
            "project_id": invocation.project,
        }
    result: dict[str, Any] = {
        "matches": matches,
        "projects_searched": len(projects),
    }
    notes = [_find_note(matches, is_exact, name_substring)]
    if trashed:
        result["trashed_matches"] = trashed
        notes = [_trashed_note(trashed, name_substring)]
    if dropped:
        result["elsewhere"] = dropped
        notes.append(elsewhere_note(dropped))
    if cut:
        result["truncated"] = True
        notes.append(search_cut_note("datasets"))
    if note := " ".join(n for n in notes if n):
        result["note"] = note
    return result, meta


#: Matches kept per dataset in a ``dataset search`` row; the rest are counted, not listed.
_SEARCH_MATCHES_PER_DATASET = 5


def _search_row(hit: dict[str, Any]) -> dict[str, Any]:
    """One ``dataset search`` row: the dataset and the first places its content matched."""
    matches = hit.get("matches") or []
    row: dict[str, Any] = {
        "id": hit.get("id"),
        "name": hit.get("name"),
        "matches": matches[:_SEARCH_MATCHES_PER_DATASET],
    }
    if len(matches) > _SEARCH_MATCHES_PER_DATASET:
        row["more_matches"] = len(matches) - _SEARCH_MATCHES_PER_DATASET
    return row


def dataset_search(invocation: Invocation) -> HandlerResult:
    """Find the project's datasets whose name, column names or sampled values hold TERM.

    Read-only: one server call. Each match names where the term was found (``name``,
    ``column`` or ``value``) with the column and the sampled value, so the dataset that
    holds "New Year Sale" in a ``campaign`` column is found without knowing its name.
    Sampled values come from the profile, which keeps up to 30 per text column, so a
    dataset never profiled matches on name and columns only.
    """
    term = _require_string_positional(invocation, "term")
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(
            "mammoth.api.datasets.DatasetsAPI.search", term=term, project_id=project_id
        )
    hits = data.get("datasets", []) if isinstance(data, dict) else []
    kept, omitted = fit_budget([_search_row(h) for h in hits if isinstance(h, dict)])
    result: dict[str, Any] = {"term": term, "datasets": kept, "matched": len(hits)}
    if omitted:
        result["omitted"] = omitted
    if note := ambiguity_note(len(hits), term):
        result["note"] = note
    return result, _meta(invocation, auth.workspace_id, project_id)


#: Columns with blanks kept per dataset in a ``dataset column-stats`` row, worst first.
_COLUMN_STATS_PER_DATASET = 8


_COLUMN_STATS_NOTE = (
    "Blank counts per column for every dataset in the project, read from stats stored at "
    "the last load or pipeline run (not live). Datasets are ordered worst first and each "
    "lists only its columns that have blanks, highest blank_pct (a percentage, 0-100) "
    "first; complete_columns "
    "counts the columns with none. To answer, name the dataset and column with the "
    "highest blank_pct (or blank_count), then the next few, and say the figures are as "
    "of the last load or run. Profile one view only to look closer at a column named here."
)


def _blank_pct(column: dict[str, Any]) -> float:
    value = column.get("blank_pct")
    return float(value) if isinstance(value, (int, float)) else 0.0


def _column_stats_row(dataset: dict[str, Any]) -> dict[str, Any]:
    """One ``dataset column-stats`` row: the dataset and its columns with blanks, worst first."""
    columns = [c for c in dataset.get("columns") or [] if isinstance(c, dict)]
    blank = sorted(
        (c for c in columns if (c.get("blank_count") or 0) > 0),
        key=lambda c: (-_blank_pct(c), -(c.get("blank_count") or 0)),
    )
    row: dict[str, Any] = {
        "id": dataset.get("id"),
        "name": dataset.get("name"),
        "rows": dataset.get("rows"),
        "columns": blank[:_COLUMN_STATS_PER_DATASET],
        "complete_columns": len(columns) - len(blank),
    }
    if len(blank) > _COLUMN_STATS_PER_DATASET:
        row["more_columns_with_blanks"] = len(blank) - _COLUMN_STATS_PER_DATASET
    return row


def _worst_blank_pct(row: dict[str, Any]) -> float:
    return max((_blank_pct(c) for c in row["columns"]), default=0.0)


def dataset_column_stats(invocation: Invocation) -> HandlerResult:
    """Every column's blanks, type and distinct count for each dataset in the project.

    Read-only: one server call over stats the platform already stored, so a question
    about missing values across the project needs no per-view profile. Datasets are
    ordered by their worst column's blank share (newest first among ties), each listing
    its columns with blanks, worst first, and cut to fit the agent tool output cap.
    """
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call("mammoth.api.datasets.DatasetsAPI.column_stats", project_id=project_id)
    datasets = data.get("datasets", []) if isinstance(data, dict) else []
    rows = [_column_stats_row(d) for d in datasets if isinstance(d, dict)]
    rows.sort(key=_worst_blank_pct, reverse=True)
    kept, omitted = fit_budget(rows, overhead=200 + len(_COLUMN_STATS_NOTE))
    result: dict[str, Any] = {"datasets": kept, "dataset_count": len(rows)}
    if omitted:
        result["omitted"] = omitted
    result["note"] = _COLUMN_STATS_NOTE
    return result, _meta(invocation, auth.workspace_id, project_id)
