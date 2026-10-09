"""What a tool hands a model, cut from what the API answers.

The API's answers are written for the web app. A model reads every word of one,
so each tool gives it only what it can act on: the rows under the names the
user sees, a view without the web app's display settings, a next page only when
there is one, and a missing id with the tool that lists the right ones.
"""

import math

from .consts import ColumnFields, PageFields, ViewShape
from .sdk import JsonValue, api_url

HTTPS = "https://"
HTTP = "http://"


def not_found_message(
    workspace_id: int,
    project_id: int | None = None,
    dataset_id: int | None = None,
    view_id: int | None = None,
) -> str:
    """Say which ids a 404 could be about, and which tool lists the right ones.

    The API answers every missing id alike, so the message names each id the
    call used and the `list_*` tools that show the right ones.
    """
    ids = {"view": view_id, "dataset": dataset_id, "project": project_id}
    named = ", ".join(f"{kind} {one}" for kind, one in ids.items() if one is not None)
    lists = [f"`list_projects` (workspace_id={workspace_id})"]
    if project_id is not None and dataset_id is not None:
        lists.insert(0, f"`list_datasets` (project_id={project_id})")
    if dataset_id is not None and view_id is not None:
        lists.insert(0, f"`list_views` (dataset_id={dataset_id})")
    return (
        f"Not found: one of {named} in workspace {workspace_id} does not exist, or is not"
        f" yours. Check them with {', '.join(lists)}."
    )


def tidy_page(page: dict[str, JsonValue], items_key: str, limit: int) -> dict[str, JsonValue]:
    """Keep `next` only when another page may exist, and as a secure link.

    The API sends a `next` link after every page, empty or not. A page shorter
    than the limit is the last one.
    """
    items = page.get(items_key)
    link = page.get(PageFields.NEXT)
    if not (isinstance(link, str) and link and isinstance(items, list) and len(items) >= limit):
        return {key: value for key, value in page.items() if key != PageFields.NEXT}
    if api_url().startswith(HTTPS) and link.startswith(HTTP):
        link = HTTPS + link[len(HTTP) :]
    return {**page, PageFields.NEXT: link}


def slim_view(view: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """A view as a model needs it: identity, size and the columns with their types."""
    slim = {key: view[key] for key in ViewShape.KEPT if key in view}
    columns = view.get(ViewShape.METADATA)
    if isinstance(columns, list):
        slim[ViewShape.METADATA] = [
            {key: column[key] for key in ViewShape.COLUMN_KEPT if column.get(key) is not None}
            for column in columns
            if isinstance(column, dict)
        ]
    return slim


def _typed(value: JsonValue, column_type: str | None) -> JsonValue:
    """A numeric column's text as the number it is; anything else as it came."""
    if column_type != ViewShape.NUMERIC or not isinstance(value, str):
        return value
    if not value.strip():
        return None
    for parse in (int, float):
        try:
            number = parse(value)
        except ValueError:
            continue
        return number if math.isfinite(number) else value
    return value


def _display_names(columns: list[JsonValue]) -> dict[str, tuple[str, str | None]]:
    """Each internal name's display name and type; a repeated display name keeps its internal one."""
    named = [c for c in columns if isinstance(c, dict)]
    shown = [str(c.get(ColumnFields.DISPLAY_NAME)) for c in named]
    return {
        str(c[ColumnFields.INTERNAL_NAME]): (
            label if shown.count(label) == 1 else str(c[ColumnFields.INTERNAL_NAME]),
            str(c.get(ColumnFields.TYPE)),
        )
        for c, label in zip(named, shown, strict=True)
        if ColumnFields.INTERNAL_NAME in c
    }


def _shaped_rows(rows: JsonValue, view: dict[str, JsonValue]) -> list[JsonValue]:
    """Each row keyed by display name, its values typed by the column's type."""
    columns = view.get(ViewShape.METADATA)
    names = _display_names(columns if isinstance(columns, list) else [])
    return [
        {
            names.get(key, (key, None))[0]: _typed(value, names.get(key, (key, None))[1])
            for key, value in row.items()
        }
        for row in (rows if isinstance(rows, list) else [])
        if isinstance(row, dict)
    ]


def read_rows(
    answer: dict[str, JsonValue],
    view: dict[str, JsonValue],
    offset: int,
    limit: int,
    filtered: bool,
) -> dict[str, JsonValue]:
    """Rows under display names with typed values, and paging that tells the truth.

    The API reports `total: 0` and no next page. The total is known exactly
    when a short page ends the data, and is the view's row count when no filter
    narrows it. A filtered full page may have more behind it: `next_offset` says so.
    """
    rows = _shaped_rows(answer.get(PageFields.DATA), view)
    seen = offset - 1 + len(rows)
    full = len(rows) >= limit
    known = view.get("row_count")
    total = None if (full and filtered) else (known if full else seen)
    paging: dict[str, JsonValue] = {
        PageFields.OFFSET: offset,
        PageFields.COUNT: len(rows),
        PageFields.LIMIT: limit,
    }
    if isinstance(total, int):
        paging[PageFields.TOTAL] = total
    if full and (not isinstance(total, int) or seen < total):
        paging[PageFields.NEXT_OFFSET] = seen + 1
    return {PageFields.DATA: rows, PageFields.PAGING: paging}
