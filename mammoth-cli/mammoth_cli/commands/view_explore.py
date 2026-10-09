"""``view explore-panel edit`` and ``add-to-dashboard``: the Explore controls of the web app.

``edit`` changes cards the way the card menus do (metric, sort, view, level, filter, exclude,
clear, remove, and the search, scatter and ask cards) and writes the panel once, in the card
config the web app reads. ``add-to-dashboard`` is the card menu's "Add to dashboard": the card
becomes a figure on a board (:mod:`mammoth_cli.services.explore_to_figure`). The card logic is
in :mod:`mammoth_cli.services.explore_card_edit`; this module reads the view for it.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.view import (
    _DATAVIEW_GET_SYMBOL,
    _EXPLORE_PANEL_GET_SYMBOL,
    _METADATA_KEY,
    _meta,
    _read_explore_panel,
    _require_field,
    _require_int_positional_at,
    _symbol,
    _verified_dataset_id,
    apply_column_renames,
)
from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services.explore_card_edit import (
    DATE,
    NUMERIC,
    TEXT,
    Lookups,
    apply_edits,
    date_text,
    guess_number_level,
    normalize_ask_condition,
    open_card,
)
from mammoth_cli.services.explore_to_figure import card_level, card_to_figure, count_filters

HandlerResult = tuple[Any, dict[str, Any]]

_EXPLORE_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.explore"
_SEQUENCE_SYMBOL = "mammoth.api.pipeline.PipelineAPI.latest_task_sequence"
_SUGGESTIONS_SYMBOL = "mammoth.api.ai.AIAPI.get_suggestions"
_DASHBOARDS_LIST_SYMBOL = "mammoth.api.dashboards.DashboardsAPI.list"
_CREATE_BLANK_SYMBOL = "mammoth.api.dashboards.DashboardsAPI.create_blank"
_APPEND_FIGURE_SYMBOL = "mammoth.api.dashboards.DashboardsAPI.append_figure"
#: The suggestions call answers this status when it read a condition out of the question.
_ASK_UNDERSTOOD = "AC01"


class _View:
    """One view's ids and a service, so the lookups below need not repeat them."""

    def __init__(self, service: Any, dataset_id: int, dataview_id: int, project_id: int) -> None:
        self.service = service
        self.dataset_id = dataset_id
        self.dataview_id = dataview_id
        self.project_id = project_id

    def columns(self) -> list[dict[str, Any]]:
        """The view's columns under their display names, with the name the pipeline gave each."""
        info = self.service.call(
            _DATAVIEW_GET_SYMBOL,
            dataset_id=self.dataset_id,
            dataview_id=self.dataview_id,
            project_id=self.project_id,
        )
        original = info.get(_METADATA_KEY) or []
        renamed = apply_column_renames(info).get(_METADATA_KEY) or []
        return [
            {**column, "original_name": before.get("display_name")}
            for column, before in zip(renamed, original, strict=True)
        ]

    def explore(
        self,
        column: dict[str, Any],
        level: Any,
        only: list[Any] | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """The buckets the card lists for a column (a read-only grouped count)."""
        kwargs: dict[str, Any] = {
            "dataset_id": self.dataset_id,
            "dataview_id": self.dataview_id,
            "project_id": self.project_id,
            "column": column["internal_name"],
            "column_type": str(column.get("type") or "").upper(),
        }
        if level is not None:
            kwargs["level"] = level
        if only:
            kwargs["condition"] = {column["internal_name"]: {"IN_LIST": {"VALUE": only}}}
            limit = len(only)
        if limit is not None:
            kwargs["limit"] = limit
        data: dict[str, Any] = self.service.call(_EXPLORE_SYMBOL, **kwargs)
        return data

    def buckets(self, column: dict[str, Any], level: Any, only: list[Any] | None) -> list[Any]:
        """Bucket values as the cards store them: text, numbers, or ``YYYY-MM-DD HH:MM:SS``."""
        kind = str(column.get("type") or "").upper()
        values = [row["group_0"] for row in self.explore(column, level, only)["data"]]
        if kind == DATE:
            return [date_text(v) for v in values if v is not None]
        if kind == NUMERIC:
            return [float(v) for v in values if v is not None]
        return values

    def ask(self, question: str) -> dict[str, Any] | None:
        """The condition the web app's ask card reads out of a question, or ``None``."""
        # The step a new task would take, as the web app asks (its task count plus one).
        sequence = 1 + self.service.call(
            _SEQUENCE_SYMBOL, dataview_id=self.dataview_id, dataset_id=self.dataset_id
        )
        reply = self.service.call(
            _SUGGESTIONS_SYMBOL,
            suggestion_type="add_condition",
            params={"sequence_number": sequence, "prompt": question, "origin": "functions_panel"},
            dataset_id=self.dataset_id,
            dataview_id=self.dataview_id,
        )
        response = reply.get("response", reply) if isinstance(reply, dict) else None
        if not isinstance(response, dict) or response.get("status_code") != _ASK_UNDERSTOOD:
            return None
        return normalize_ask_condition(response.get("result"))

    def lookups(self) -> Lookups:
        return Lookups(buckets=self.buckets, ask=self.ask)


def _saved_cards(panel: Any) -> list[dict[str, Any]]:
    """The cards a saved panel holds; the older ``items`` spelling is read as the web app does."""
    if not isinstance(panel, dict):
        return []
    cards = panel.get("cards") if isinstance(panel.get("cards"), list) else panel.get("items")
    return [card for card in cards or [] if isinstance(card, dict)]


def view_explore_panel_edit(invocation: Invocation) -> HandlerResult:
    """Change Explore cards as the card menus do; the result carries the panel read back."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    edits = _require_field(document, "edits")
    with open_service(invocation) as (service, auth):
        dataset_id = _verified_dataset_id(service, invocation, dataview_id, document)
        view = _View(service, dataset_id, dataview_id, project_id)
        saved = _read_explore_panel(
            service, _EXPLORE_PANEL_GET_SYMBOL, dataset_id, dataview_id, project_id
        )
        cards = apply_edits(_saved_cards(saved), edits, view.columns(), view.lookups())
        kept = {key: value for key, value in saved.items() if key not in ("cards", "items")}
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            panel={**kept, "cards": cards},
            project_id=project_id,
        )
        after = _read_explore_panel(
            service, _EXPLORE_PANEL_GET_SYMBOL, dataset_id, dataview_id, project_id
        )
    return {**data, "panel": after}, _meta(invocation, auth.workspace_id, project_id)


def _refuse(message: str, hint: str | None = None) -> CliError:
    return CliError(code=CODE_INVALID_ARGUMENT, message=message, exit_status=EXIT_USAGE, hint=hint)


def _destination(document: dict[str, Any]) -> tuple[int | None, str | None, dict[str, Any]]:
    """The board the card goes to: an existing ``dashboard_id`` or a ``new_dashboard_title``."""
    board, title = document.get("dashboard_id"), document.get("new_dashboard_title")
    if (board is None) == (title is None):
        raise _refuse(
            'Give "dashboard_id" (an existing board) or "new_dashboard_title" (a new one).'
        )
    page = document.get("page") or {}
    if page and (title is not None or set(page) not in ({"id"}, {"new_title"})):
        raise _refuse(
            'A "page" ({"id": ...} or {"new_title": ...}) goes with "dashboard_id"; a new board '
            "puts the tile on its first page."
        )
    if board is not None and (isinstance(board, bool) or not isinstance(board, int)):
        raise _refuse('"dashboard_id" must be a dashboard id.')
    if title is not None and (not isinstance(title, str) or not title.strip()):
        raise _refuse('"new_dashboard_title" must be a non-empty string.')
    return board, title.strip() if title else None, page


def _figure_for(
    view: _View, cards: list[dict[str, Any]], columns: list[dict[str, Any]], name: Any
) -> dict[str, Any]:
    """The tile a column card becomes, with the buckets or value count read from the view."""
    card, column = open_card(cards, columns, name)
    kind = str(column.get("type") or "").upper()
    buckets: list[Any] | None = None
    value_count: int | None = None
    if kind == NUMERIC:
        card, buckets = _number_card(view, card, column)
    elif kind == TEXT:
        value_count = view.explore(column, None, limit=1).get("row_count")
    return card_to_figure(card, column, columns, buckets, value_count, count_filters(cards))


def _number_card(
    view: _View, card: dict[str, Any], column: dict[str, Any]
) -> tuple[dict[str, Any], list[Any]]:
    """A number card with a fixed level, and the buckets it lists at that level."""
    level = card_level(card)
    if not isinstance(level, int):
        level = guess_number_level(view.buckets(column, "AUTO", None))
        if level is None:
            raise _refuse(
                "The card's level is AUTO and its values do not show one. Set it first: "
                'view explore-panel edit VIEW_ID --input \'{"edits": [{"op": "level", '
                '"card": "NAME", "level": 1}]}\'.'
            )
    return {**card, "granularity": {"id": level}}, view.buckets(column, level, None)


def _check_title_free(service: Any, title: str, project_id: int) -> None:
    """The web app does not create a second board with a title the project already has."""
    boards = service.call(_DASHBOARDS_LIST_SYMBOL, project_id=project_id)
    taken = {str(board.get("title") or "").strip().casefold() for board in boards}
    if title.casefold() in taken:
        raise _refuse(
            f"A dashboard titled {title!r} already exists in this project. Pick another title."
        )


def view_explore_panel_add_to_dashboard(invocation: Invocation) -> HandlerResult:
    """Put an Explore card on a dashboard as a figure, like the card menu's Add to dashboard."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    name = _require_field(document, "card")
    board, title, page = _destination(document)
    with open_service(invocation) as (service, auth):
        dataset_id = _verified_dataset_id(service, invocation, dataview_id, document)
        view = _View(service, dataset_id, dataview_id, project_id)
        saved = _read_explore_panel(
            service, _EXPLORE_PANEL_GET_SYMBOL, dataset_id, dataview_id, project_id
        )
        tile = _figure_for(view, _saved_cards(saved), view.columns(), name)
        created = board is None
        if title is not None:
            _check_title_free(service, title, project_id)
            board = service.call(
                _CREATE_BLANK_SYMBOL, params={"dataview_id": dataview_id, "title": title}
            )["id"]
        kwargs: dict[str, Any] = {
            "dashboard_id": board,
            "dataview_id": dataview_id,
            "figure": tile["figure"],
        }
        if tile["banded"]:
            kwargs["banded"] = tile["banded"]
        if page:
            kwargs.update(
                {"page_id": page["id"]} if "id" in page else {"page_new_title": page["new_title"]}
            )
        added = service.call(_APPEND_FIGURE_SYMBOL, **kwargs)
    result = {**tile, "dashboard_id": board, "created_dashboard": created, "added": added}
    return result, _meta(invocation, auth.workspace_id, project_id)
