"""Check what ``dashboard pages add`` actually built.

The add-pages route keeps every requested page even when it refuses the
page's charts (for example a ``pie`` the data does not support); the refusal
is only prose in ``message`` ("Couldn't do: ..."). An agent that reads
``added_page_ids`` sees success and leaves empty pages on the dashboard. This
module names the refusals, finds the new pages that asked for charts and got
none, and removes those pages with one canvas save.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

CANVAS_GET = "mammoth.api.dashboards.DashboardsAPI.canvas_get"
CANVAS_SAVE = "mammoth.api.dashboards.DashboardsAPI.canvas_save"

#: The notes run to the end of their paragraph; a blank line starts the builder's own
#: "On the board: ..." summary, which is not a refusal.
_REFUSED = re.compile(r"Couldn[’']t do:\s*(?P<notes>.+?)[._\s]*(?:\n\s*\n|$)", re.DOTALL)
_NOT_A_MEASURE = re.compile(r"(?P<col>[\w.-]+) (?:isn[’']t|is not) a measure", re.IGNORECASE)


def refused_notes(message: Any) -> list[str]:
    """Return the server's "Couldn't do" notes from an add-pages ``message``."""
    if not isinstance(message, str):
        return []
    match = _REFUSED.search(message)
    if match is None:
        return []
    return [note.strip() for note in match.group("notes").split(";") if note.strip()]


def refused_warning(note: str) -> dict[str, Any]:
    """One warning for one refused card, with the fallback when a column was refused."""
    detail = f"the server could not do: {note}"
    found = _NOT_A_MEASURE.search(note)
    if found:
        column = found.group("col")
        detail += (
            f". Add it yourself: dashboard figure add DASHBOARD_ID --input "
            f'\'{{"dataview_id": VIEW_ID, "figure": {{"kind": "kpi", "measure": "{column}", '
            f'"agg": "sum", "title": "Total {column}"}}}}\''
        )
    return {"issue": "refused", "detail": detail}


def _as_list(added_ids: Any) -> list[Any]:
    """Return ``added_page_ids`` as a list (empty when the server sent none)."""
    return list(added_ids) if isinstance(added_ids, list) else []


def _dump(value: Any) -> Any:
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def _requested_charts(page: Mapping[str, Any]) -> bool:
    charts = page.get("charts")
    return isinstance(charts, list) and bool(charts) and not page.get("focus")


def _empty(page: Mapping[str, Any]) -> bool:
    return not page.get("added") and not page.get("focus")


def check_added_pages(
    service: Any,
    dashboard_id: int,
    requested: Sequence[Mapping[str, Any]],
    data: Any,
) -> Any:
    """Add ``chart_check`` to an add-pages result and drop pages left empty.

    Args:
        service: The session service.
        dashboard_id: The dashboard the pages were added to.
        requested: ``body.params.pages`` as sent, in order.
        data: The add-pages response (``added_page_ids``, ``message``, ...).

    Returns:
        ``data`` unchanged when no new page asked for charts; otherwise with
        ``chart_check``: ``refused`` (the server's notes),
        ``removed_pages`` (new pages that asked for charts and got none, now
        removed) and, when a removal was needed but failed, ``fix``. After a
        removal, ``sequence`` and ``bake_job_id`` are those of the save.
    """
    data = _dump(data)
    if not isinstance(data, dict):
        return data
    refused = refused_notes(data.get("message"))
    added_ids = data.get("added_page_ids")
    # Pages come back in request order; only a page that asked for charts
    # (and has no focus, whose built-in charts always render) can be empty.
    candidates = {
        page_id: page
        for page_id, page in zip(_as_list(added_ids), requested, strict=False)
        if isinstance(page, Mapping) and _requested_charts(page)
    }
    if not candidates:
        return data
    check: dict[str, Any] = {"refused": refused, "removed_pages": []}
    if not refused:
        data["chart_check"] = check
        return data
    canvas_doc = _dump(service.call(CANVAS_GET, dashboard_id=dashboard_id))
    canvas = canvas_doc.get("canvas") if isinstance(canvas_doc, dict) else None
    pages = canvas.get("pages") if isinstance(canvas, dict) else None
    if not isinstance(canvas, dict) or not isinstance(pages, list):
        data["chart_check"] = check
        return data
    empty = [
        page
        for page in pages
        if isinstance(page, dict) and page.get("id") in candidates and _empty(page)
    ]
    if not empty:
        data["chart_check"] = check
        return data
    removed = [{"id": page.get("id"), "title": page.get("title")} for page in empty]
    empty_ids = {page.get("id") for page in empty}
    kept = [page for page in pages if not (isinstance(page, dict) and page.get("id") in empty_ids)]
    canvas = {**canvas, "pages": kept}
    if canvas.get("active_page_id") in empty_ids:
        canvas["active_page_id"] = next(
            (page.get("id") for page in kept if isinstance(page, dict)), None
        )
    meta = canvas_doc.get("meta") if isinstance(canvas_doc, dict) else None
    params: dict[str, Any] = {"canvas": canvas}
    if isinstance(meta, dict) and isinstance(meta.get("sequence"), int):
        params["base_sequence"] = meta["sequence"]
    try:
        saved = _dump(service.call(CANVAS_SAVE, dashboard_id=dashboard_id, body={"params": params}))
    except Exception as exc:  # noqa: BLE001 - the pages were added; report, do not fail
        check["empty_pages"] = removed
        check["fix"] = (
            f"The pages {', '.join(str(p['id']) for p in removed)} have no charts and could "
            f"not be removed ({exc}). Remove them: mammoth dashboard canvas get {dashboard_id}, "
            "delete them from canvas.pages, then dashboard canvas save."
        )
        data["chart_check"] = check
        return data
    check["removed_pages"] = removed
    if isinstance(saved, dict):
        for key in ("sequence", "bake_job_id"):
            if key in saved:
                data[key] = saved[key]
    data["added_page_ids"] = [
        page_id for page_id in _as_list(added_ids) if page_id not in empty_ids
    ]
    data["chart_check"] = check
    return data


_MONEY_INTENT = re.compile(r"revenue|sales|income|\bgmv\b|\bmrr\b|\barr\b|turnover", re.IGNORECASE)
_MONEY_COLUMN = re.compile(r"revenue|sales|amount|income|total|gmv|mrr|arr", re.IGNORECASE)


def _figures(page: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [f for f in page.get("added") or [] if isinstance(f, Mapping)]


def _used_measure(figure: Mapping[str, Any]) -> Any:
    return figure.get("measure") if figure.get("measure") is not None else figure.get("agg")


def page_substitutions(
    requested: Sequence[Mapping[str, Any]],
    added_ids: Any,
    canvas_doc: Any,
    refused: Sequence[str] = (),
    profile_names: Sequence[str] = (),
) -> list[dict[str, Any]]:
    """Name each requested chart that was swapped, dropped or refused by ``pages add``.

    The route builds what it can and swaps in another column for a measure
    that is not on the board (a "Revenue by region" chart on Quantity), saying so
    only in prose. Each record names what was requested and what was built.
    """
    canvas = canvas_doc.get("canvas") if isinstance(canvas_doc, Mapping) else None
    pages = canvas.get("pages") if isinstance(canvas, Mapping) else None
    built_by_id = {page.get("id"): page for page in pages or [] if isinstance(page, Mapping)}
    known = set(profile_names)
    warnings: list[dict[str, Any]] = []
    for page_id, page in zip(_as_list(added_ids), requested, strict=False):
        if not isinstance(page, Mapping):
            continue
        built = built_by_id.get(page_id)
        if built is None:
            continue
        figures = _figures(built)
        for index, chart in enumerate(
            c for c in page.get("charts") or [] if isinstance(c, Mapping)
        ):
            title = chart.get("title")
            match = next(
                (
                    f
                    for f in figures
                    if isinstance(title, str)
                    and str(f.get("title", "")).casefold() == title.casefold()
                ),
                figures[index] if index < len(figures) else None,
            )
            wanted = {k: chart.get(k) for k in ("kind", "measure", "dim", "agg") if chart.get(k)}
            if match is None:
                warnings.append(
                    {
                        "issue": "chart_dropped",
                        "page": page.get("title") or page_id,
                        "requested": wanted | ({"title": title} if title else {}),
                        "used": None,
                        "detail": (
                            f"the requested chart '{title or wanted.get('kind')}' was not built."
                        ),
                    }
                )
                continue
            measure = chart.get("measure")
            off_board = isinstance(measure, str) and bool(known) and measure not in known
            swapped = isinstance(measure, str) and _used_measure(match) not in (None, measure)
            if off_board or swapped:
                used = {k: match.get(k) for k in ("kind", "measure", "dim", "agg") if match.get(k)}
                warnings.append(
                    {
                        "issue": "measure_substituted",
                        "page": page.get("title") or page_id,
                        "requested": wanted | ({"title": title} if title else {}),
                        "used": (
                            used | ({"title": match.get("title")} if match.get("title") else {})
                        ),
                        "detail": (
                            f"measure '{measure}' was requested"
                            + (" but is not on the board" if off_board else "")
                            + f"; the chart uses '{used.get('measure')}' instead."
                        ),
                    }
                )
    for note in dict.fromkeys(refused):
        warnings.append(refused_warning(note))
    return warnings


def generate_substitutions(
    intent: Any, canvas_doc: Any, message: Any = None
) -> list[dict[str, Any]]:
    """A revenue-style intent whose board shows no money column, or a "Couldn't do" message."""
    warnings: list[dict[str, Any]] = [
        refused_warning(note) for note in dict.fromkeys(refused_notes(message))
    ]
    profiles = (
        (canvas_doc.get("plan") or {}).get("hints", {}).get("_profiles")
        if isinstance(canvas_doc, Mapping) and isinstance(canvas_doc.get("plan"), Mapping)
        else None
    )
    names = [
        p["name"] for p in profiles or [] if isinstance(p, dict) and isinstance(p.get("name"), str)
    ]
    canvas = canvas_doc.get("canvas") if isinstance(canvas_doc, Mapping) else None
    if not isinstance(intent, str) or not isinstance(canvas, Mapping):
        return warnings
    asked = sorted({m.group(0).lower() for m in _MONEY_INTENT.finditer(intent)})
    if not asked:
        return warnings
    measures: list[str] = []
    containers = [canvas, *[p for p in canvas.get("pages") or [] if isinstance(p, Mapping)]]
    for container in containers:
        for figure in _figures(container):
            for key in ("measure", "measure2"):
                if isinstance(figure.get(key), str):
                    measures.append(figure[key])
            for kpi in figure.get("kpis") or []:
                if isinstance(kpi, Mapping) and isinstance(kpi.get("field"), str):
                    measures.append(kpi["field"])
    if not measures or any(_MONEY_COLUMN.search(m) for m in measures):
        return warnings
    if any(_MONEY_COLUMN.search(n) for n in names) or not names:
        reason = "the board has a money column but the charts do not use it"
    else:
        reason = "the board has no revenue-like column"
    warnings.append(
        {
            "issue": "measure_substituted",
            "requested": {"intent_mentions": asked},
            "used": {"measures": sorted(set(measures))},
            "detail": (
                f"the intent asks for {', '.join(asked)} but the charts use "
                f"{', '.join(sorted(set(measures)))} ({reason})."
            ),
        }
    )
    return warnings
