"""The numbers a dashboard shows, as Mammoth worked them out.

A dashboard read returns what each card and chart is, not what it shows. A
model asked "what is the total?" then adds up the view's rows itself, and gets
it wrong. The numbers come from the board's own baked descriptors, evaluated in
one descriptor-data call, the same way the CLI's `dashboard get` reads them.
"""

from mammoth.api import dashboard_generated
from mammoth.api.dashboards import DashboardsAPI
from mammoth.models.dashboard_generated import DescriptorDataParams, DescriptorDataSpec
from mcp.server.mcpserver.exceptions import ToolError

from .consts import CHART_ROWS_SHOWN, DESCRIPTORS_PER_READ, BoardFields, DashboardFields
from .jobs import wait_for_job
from .sdk import JsonValue, read_sdk_errors

NO_FIGURES = "The dashboard has no cards or charts yet."
OLDER_ENGINE = (
    "This dashboard is on the older engine, which reports no numbers here."
    " Open it in Mammoth to read them."
)

type Json = dict[str, JsonValue]


async def board_values(dashboards: DashboardsAPI, workspace_id: int, dashboard_id: int) -> Json:
    """Each card's and chart's numbers under `values`, or why under `values_unavailable`.

    Never raises: the dashboard itself is still worth reading without them.
    """
    # The SDK attaches its generated routes to DashboardsAPI when it loads, so
    # they are called as the typed functions they are.
    try:
        canvas_read = dashboard_generated.canvas_get(dashboards, dashboard_id)
        canvas = (await read_sdk_errors(canvas_read)).model_dump()
        figures = figure_bindings(canvas)
        if not figures:
            return {DashboardFields.VALUES_UNAVAILABLE: NO_FIGURES}
        ids = sorted({did for figure in figures for did in _descriptors(figure).values()})
        ids = ids[:DESCRIPTORS_PER_READ]
        spec = DescriptorDataSpec(params=DescriptorDataParams(descriptor_ids=ids))
        started = await read_sdk_errors(
            dashboard_generated.descriptor_data(dashboards, dashboard_id, spec)
        )
        evaluated = await wait_for_job(workspace_id, started.model_dump(mode="json"))
    except ToolError as unread:
        return {DashboardFields.VALUES_UNAVAILABLE: str(unread)}
    results = evaluated.get(BoardFields.RESULTS)
    return {DashboardFields.VALUES: attach_values(figures, _object(results))}


def figure_bindings(canvas: Json) -> list[Json]:
    """Every KPI card and chart, in board order, with the descriptors behind its number.

    Filter controls and detail tables carry no number, so they are left out.
    """
    meta = _object(canvas.get(BoardFields.META))
    labels = _labels(_object(canvas.get(BoardFields.CANVAS)))
    receipts = _object(meta.get(BoardFields.RECEIPTS))
    figures: list[Json] = []
    for figure, entry in _object(meta.get(BoardFields.FIGURES)).items():
        parts = figure.split(":")
        kind = BoardFields.KINDS.get(parts[1]) if len(parts) == 3 else None
        descriptors = _object(_object(entry).get(BoardFields.DESCRIPTORS))
        if kind is None or not descriptors:
            continue
        receipt = _object(receipts.get(figure))
        bound: Json = {BoardFields.FIGURE: figure, BoardFields.KIND: kind}
        bound[BoardFields.LABEL] = labels.get(figure)
        bound[BoardFields.PERIOD] = _period_of(receipt)
        bound[BoardFields.FILTERS] = list[JsonValue](_filters_of(receipt))
        bound[BoardFields.DESCRIPTORS] = {name: str(did) for name, did in descriptors.items()}
        figures.append(bound)
    return figures


def attach_values(figures: list[Json], results: Json) -> list[JsonValue]:
    """Each figure with what its descriptors evaluated to, and nothing left empty."""
    values: list[JsonValue] = []
    for figure in figures:
        series = {name: _evaluated(results.get(did)) for name, did in _descriptors(figure).items()}
        shown: Json = {
            key: value
            for key, value in figure.items()
            if key != BoardFields.DESCRIPTORS and value not in (None, [])
        }
        if figure[BoardFields.KIND] == BoardFields.KPI and set(series) == {BoardFields.VALUE}:
            shown.update(_object(series[BoardFields.VALUE]))
        else:
            shown[BoardFields.SERIES] = dict[str, JsonValue](series)
        values.append(shown)
    return values


def _evaluated(entry: JsonValue) -> Json:
    """One descriptor's number, or its first rows and how many there are, or its error."""
    result = _object(entry)
    if result.get(BoardFields.STATUS) not in (None, BoardFields.SUCCESS):
        return {BoardFields.ERROR: result.get(BoardFields.ERROR) or result[BoardFields.STATUS]}
    if BoardFields.VALUE in result:
        return {BoardFields.VALUE: result[BoardFields.VALUE]}
    rows = result.get(BoardFields.DATA)
    if isinstance(rows, list):
        return {BoardFields.ROWS: rows[:CHART_ROWS_SHOWN], BoardFields.ROW_COUNT: len(rows)}
    return {BoardFields.ERROR: "Mammoth returned no number for this."}


def _labels(canvas: Json) -> dict[str, str]:
    """Each figure's title, from the cards and charts of every page."""
    labels: dict[str, str] = {}
    for page_id, page in _pages(canvas):
        kpis = _object(page.get(BoardFields.FOCUS)).get(BoardFields.KPIS)
        for index, card in enumerate(kpis if isinstance(kpis, list) else []):
            _put_label(labels, f"{page_id}:kpi:{index}", _object(card))
        added = page.get(BoardFields.ADDED)
        for index, chart in enumerate(added if isinstance(added, list) else []):
            key = _object(chart).get(BoardFields.ID) or index
            _put_label(labels, f"{page_id}:add:{key}", _object(chart))
    return labels


def _put_label(labels: dict[str, str], figure: str, item: Json) -> None:
    for field in (BoardFields.LABEL, BoardFields.TITLE):
        if isinstance(item.get(field), str) and item[field]:
            labels[figure] = str(item[field])
            return


def _pages(canvas: Json) -> list[tuple[str, Json]]:
    """The canvas's first page and each page after it, by id."""
    if not canvas:
        return []
    pages = [(BoardFields.FIRST_PAGE, canvas)]
    more = canvas.get(BoardFields.PAGES)
    for page in more if isinstance(more, list) else []:
        page_id = _object(page).get(BoardFields.ID)
        if isinstance(page_id, str):
            pages.append((page_id, _object(page)))
    return pages


def _receipt_filters(receipt: Json) -> list[Json]:
    """Every filter a figure's series count under, as its bake recorded them."""
    filters: list[Json] = []
    for series in _object(receipt.get(BoardFields.SERIES)).values():
        listed = _object(series).get(BoardFields.FILTERS)
        filters.extend(_object(one) for one in (listed if isinstance(listed, list) else []))
    return filters


def _period_of(receipt: Json) -> str | None:
    """The board period a figure counts, such as "Q1 2026"."""
    for one in _receipt_filters(receipt):
        period = one.get(BoardFields.LABEL) or one.get(BoardFields.MONTH)
        if one.get(BoardFields.ORIGIN) == BoardFields.PERIOD and period:
            return str(period)
    return None


def _filters_of(receipt: Json) -> list[str]:
    """The filters the figure's author set, such as "Channel = Online"."""
    texts: list[str] = []
    for one in _receipt_filters(receipt):
        term = _object(one.get(BoardFields.TERM))
        if one.get(BoardFields.ORIGIN) == BoardFields.PERIOD or not term:
            continue
        op = str(term.get(BoardFields.OP))
        text = f"{term.get(BoardFields.FIELD)} {BoardFields.OPERATORS.get(op, op)} {term.get(BoardFields.VALUE)}"
        if text not in texts:
            texts.append(text)
    return texts


def _descriptors(figure: Json) -> dict[str, str]:
    return {name: str(did) for name, did in _object(figure[BoardFields.DESCRIPTORS]).items()}


def _object(value: JsonValue) -> Json:
    """`value` when it is an object; an empty one when the API sent something else."""
    return value if isinstance(value, dict) else {}
