"""The Explore panel a view's saved ``EXPLORE_PANEL`` holds, in the shape the web app reads.

The web app saves ``{height, cards}`` and reopens a view from ``cards`` only
(``readSavedCards`` in ``explore-panel.utils.js``); a panel with any other key, such as
``{open, items}``, is stored but shows "No cards yet". A card is the web app's own card
config (``newColumnCard`` in ``exploreSection.storePinia.js``): a COUNT card, a list for a
TEXT column and range buckets for a NUMERIC or DATE one.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError

_TEXT = "TEXT"
_COLUMNS_ALL = "all"
_LIST = "list"
_CHART = "chart"


def card_for_column(internal_name: str, column_type: str) -> dict[str, Any]:
    """A new COUNT card for one column, as the web app builds it."""
    card: dict[str, Any] = {
        "colId": internal_name,
        "renderType": _LIST,
        "condition": None,
        "aggregation": {"type": "COUNT", "targetColId": None, "format": {"separator": True}},
        "granularity": None,
        "sortBy": None,
        "view": _LIST if column_type == _TEXT else "columns",
    }
    if column_type == _TEXT:
        card["sortBy"] = [["unformatted", "DESC"]]
        card["activeValues"] = []
    else:
        card["renderType"] = _CHART
        card["charts"] = [{"queryIndex": 0, "activeValues": [], "level": "AUTO"}]
    return card


def _refuse(message: str) -> CliError:
    return CliError(
        code=CODE_INVALID_ARGUMENT,
        message=message,
        exit_status=EXIT_USAGE,
        hint=(
            'Open cards with {"panel": {"columns": "all"}} or {"panel": {"columns": ["Region"]}}; '
            'or write {"panel": {"cards": [...]}} as `view explore-panel get` returns it.'
        ),
    )


def _wanted_columns(columns: Any, metadata: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The view's columns a ``columns`` selector names, in the view's order."""
    if not metadata:
        raise _refuse("The view's columns could not be read, so no card was written.")
    if columns == _COLUMNS_ALL:
        return [column for column in metadata if column.get("internal_name")]
    if not isinstance(columns, list) or not all(isinstance(name, str) for name in columns):
        raise _refuse('"columns" must be "all" or a list of column names.')
    by_name = {column.get("display_name"): column for column in metadata}
    unknown = [name for name in columns if name not in by_name]
    if unknown:
        raise _refuse(f"Not columns of this view: {', '.join(unknown)}.")
    return [by_name[name] for name in dict.fromkeys(columns)]


def resolve_panel(
    panel: dict[str, Any], metadata: list[dict[str, Any]], saved: dict[str, Any]
) -> dict[str, Any]:
    """The panel to write: ``panel`` as given when it holds ``cards``, else cards for ``columns``.

    ``columns`` adds a card for each named column the saved panel has no card for, after the
    saved cards, and keeps the rest of the saved panel (its ``height``). A panel with neither
    ``cards`` nor ``columns`` is refused: the web app would not show it.
    """
    if isinstance(panel.get("cards"), list):
        return panel
    if "columns" not in panel:
        raise _refuse(
            'The panel has no "cards" list, so the web app would show "No cards yet" '
            f"(keys given: {', '.join(sorted(panel)) or 'none'})."
        )
    kept = [card for card in saved.get("cards") or [] if isinstance(card, dict)]
    have = {card.get("colId") for card in kept}
    added = [
        card_for_column(str(column["internal_name"]), str(column.get("type") or "").upper())
        for column in _wanted_columns(panel["columns"], metadata)
        if column["internal_name"] not in have
    ]
    return {**{key: value for key, value in saved.items() if key != "cards"}, "cards": kept + added}
