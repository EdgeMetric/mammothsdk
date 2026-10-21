"""Dataview metadata, column currencies and display-name relabelling helpers."""

from __future__ import annotations

import re
from typing import Any

from mammoth_cli.commands.view._common import (
    _COLUMNS_KEY,
    _DATAVIEW_GET_SYMBOL,
    _DISPLAY_NAME_KEY,
    _INTERNAL_NAME_KEY,
    _METADATA_KEY,
    _ROWS_KEY,
    _SYSTEM_COLUMNS,
    apply_column_renames,
)
from mammoth_cli.output.normalize import DataRows
from mammoth_cli.services import read_queries
from mammoth_cli.services.conditions import CONDITION_KWARG, compile_condition
from mammoth_cli.services.read_queries import ReadContext


def _dataview_info(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> dict[str, Any]:
    """Return a dataview's info (renames applied), or ``{}`` on any failure."""
    try:
        info = service.call(
            _DATAVIEW_GET_SYMBOL,
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    except Exception:  # noqa: BLE001 -- labels are a presentation nicety, never fatal
        return {}
    info = apply_column_renames(info)
    return info if isinstance(info, dict) else {}


def _metadata_of(info: dict[str, Any]) -> list[dict[str, Any]]:
    """The column metadata records of a dataview's info."""
    metadata = info.get(_METADATA_KEY)
    if not isinstance(metadata, list):
        return []
    return [column for column in metadata if isinstance(column, dict)]


def _dataview_metadata(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> list[dict[str, Any]]:
    """Return a dataview's column metadata records, or ``[]`` on any failure."""
    return _metadata_of(_dataview_info(service, dataset_id, dataview_id, project_id))


def _column_currencies(info: dict[str, Any]) -> dict[str, str]:
    """Display name -> the currency symbol its column's format sets, for each column
    that sets one (``display_properties.FORMAT_INFO[internal].currency_symbol``)."""
    props = info.get("display_properties")
    formats = props.get("FORMAT_INFO") if isinstance(props, dict) else None
    if not isinstance(formats, dict):
        return {}
    currencies: dict[str, str] = {}
    for column in _metadata_of(info):
        fmt = formats.get(column.get(_INTERNAL_NAME_KEY))
        symbol = fmt.get(_CURRENCY_SYMBOL_KEY) if isinstance(fmt, dict) else None
        display = column.get(_DISPLAY_NAME_KEY)
        if isinstance(symbol, str) and symbol and isinstance(display, str):
            currencies[display] = symbol
    return currencies


#: A measure's currency comes only from its column's format; a count has none.
_UNITLESS_FUNCTIONS = frozenset({"COUNT", "DISTINCT_COUNT"})
_CURRENCY_SYMBOL_KEY = "currency_symbol"
_NO_CURRENCY_NOTE = (
    "No currency is set on these columns: give the amounts as plain numbers, without a "
    "currency symbol or code, unless the user named one."
)


#: Measure names that read as money; the note about a missing currency is only for these.
_MONEY_COLUMN = re.compile(
    r"revenue|sales|amount|price|cost|profit|income|spend|margin|fee|salary|payment|"
    r"balance|budget|discount|tax|total|value",
    re.IGNORECASE,
)


def _with_currency(data: Any, measures: list[dict[str, Any]], currencies: dict[str, str]) -> Any:
    """``data`` with ``currency``: each money measure's symbol, from its column's format,
    or null where the column sets none, plus ``currency_note`` when none is set at all and a
    measure reads as money.

    The in-product agent put "$" on rupee store sales whose columns carry no currency
    (gap eval 10-10, S03); a figure's unit has to come from the data, not a guess.
    """
    money = {
        str(item["as_name"]): currencies.get(str(item["column"]))
        for item in measures
        if item.get("column") and str(item.get("function", "")).upper() not in _UNITLESS_FUNCTIONS
    }
    if not money or not isinstance(data, dict):
        return data
    marked = {**data, "currency": money}
    if not any(money.values()) and any(
        _MONEY_COLUMN.search(str(item.get("column"))) for item in measures
    ):
        marked["currency_note"] = _NO_CURRENCY_NOTE
    return marked


def _measures(document: dict[str, Any]) -> list[dict[str, Any]]:
    """The ``{column, function, as_name}`` of each measure a read asks for, by display
    name (``metric`` and ``aggregations``)."""
    items = [document["metric"]] if isinstance(document.get("metric"), dict) else []
    items += [a for a in document.get("aggregations") or [] if isinstance(a, dict)]
    return [{**_resolved_aggregate_item(item, {}), "column": item.get("column")} for item in items]


def _display_name_map(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> dict[str, str]:
    """Return an internal-name -> display-name map for a dataview.

    Data endpoints report internal column ids (``column_1``); the CLI presents
    the display names the user actually works with. Best-effort: any failure
    yields an empty map, so a data command still returns its rows.
    """
    mapping: dict[str, str] = {}
    for column in _dataview_metadata(service, dataset_id, dataview_id, project_id):
        internal = column.get(_INTERNAL_NAME_KEY)
        display = column.get(_DISPLAY_NAME_KEY)
        if isinstance(internal, str) and isinstance(display, str):
            mapping[internal] = display
    return mapping


def _compile_query_filters(
    service: Any,
    dataset_id: int,
    dataview_id: int,
    project_id: int | None,
    document: dict[str, Any],
    kwargs: dict[str, Any],
    reads: ReadContext | None = None,
) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    """Translate a data query's ``condition`` and ``columns`` to the wire format.

    The data route takes the backend condition shape (``{internal: {OP: ...}}``,
    the one every pipeline task uses), not the CLI's ``{column, operator,
    value}`` spec; forwarding the spec verbatim fails the job with "A clause can
    only have one key". The spec is compiled through the shared condition
    service and built against the view's display -> internal name and type
    maps, and ``columns`` given as display names are mapped the same way.
    Returns the internal -> display map and the display -> type map when
    metadata was fetched, so the row relabelling and checks can reuse them.
    """
    if CONDITION_KWARG not in document and "columns" not in document:
        return None, None
    metadata = _dataview_metadata(service, dataset_id, dataview_id, project_id)
    column_map: dict[str, str] = {}
    column_types: dict[str, str] = {}
    for column in metadata:
        internal = column.get(_INTERNAL_NAME_KEY)
        display = column.get(_DISPLAY_NAME_KEY)
        if isinstance(internal, str) and isinstance(display, str):
            column_map[display] = internal
            if isinstance(column.get("type"), str):
                column_types[display] = column["type"]
    if CONDITION_KWARG in document:
        spec = document[CONDITION_KWARG]
        if reads is not None:
            reads.display_to_internal, reads.column_types = column_map, column_types
            spec = read_queries.resolve_text_date_conditions(reads, spec)
        compiled = compile_condition(spec)
        kwargs[CONDITION_KWARG] = compiled.build(column_map or None, column_types or None)
    columns = document.get("columns")
    if isinstance(columns, list):
        kwargs["columns"] = [column_map.get(c, c) if isinstance(c, str) else c for c in columns]
    if not metadata:
        return None, None
    return {internal: display for display, internal in column_map.items()}, column_types


def _relabel_columns(
    service: Any,
    dataset_id: int,
    dataview_id: int,
    project_id: int | None,
    payload: Any,
    mapping: dict[str, str] | None = None,
) -> Any:
    """Rewrite internal column ids to display names in a data/preview payload.

    Handles both shapes the API returns: a preview's ``{"columns": [...]}``
    header list, and a data page's ``{"data": [{col: value}, ...]}`` row dicts.
    System columns (see :data:`_SYSTEM_COLUMNS`) are dropped so output matches
    the columns the user works with. ``mapping`` may be supplied by a caller
    that already fetched it (avoids a second metadata request); otherwise it is
    fetched here, only when there is something to relabel.
    """
    if not isinstance(payload, dict):
        return payload
    columns = payload.get(_COLUMNS_KEY)
    # Preview uses a positional ``rows`` array, while data pages use a
    # ``data`` array of row objects. Keep both wire shapes distinct so preview
    # identity values can be trimmed without changing data-page handling.
    rows_key = "rows" if isinstance(payload.get("rows"), list) else _ROWS_KEY
    rows = payload.get(rows_key)
    has_header = isinstance(columns, list) and all(isinstance(c, str) for c in columns)
    has_rows = isinstance(rows, list) and any(isinstance(r, dict) for r in rows)
    if not (has_header or has_rows):
        return payload
    if mapping is None:
        mapping = _display_name_map(service, dataset_id, dataview_id, project_id)
    payload = dict(payload)
    if has_header and isinstance(columns, list):
        visible_columns = [c for c in columns if c not in _SYSTEM_COLUMNS]
        payload[_COLUMNS_KEY] = [mapping.get(c, c) for c in visible_columns]
        # Preview responses are positional rows.  The backend may append the
        # internal row identity value (``hash``) without appending a matching
        # header, notably after pipeline edits.  Only remove exactly one
        # trailing value; multiple extras indicate an unknown backend shape
        # and must remain visible for diagnosis rather than being discarded.
        if isinstance(rows, list):
            payload[rows_key] = [
                (
                    row[: len(visible_columns)]
                    if isinstance(row, list) and len(row) == len(visible_columns) + 1
                    else row
                )
                for row in rows
            ]
    if has_rows and isinstance(rows, list):
        payload[rows_key] = DataRows(
            (
                {mapping.get(k, k): v for k, v in row.items() if k not in _SYSTEM_COLUMNS}
                if isinstance(row, dict)
                else row
            )
            for row in rows
        )
    return payload


def _resolved_aggregate_item(agg: dict[str, Any], column_map: dict[str, str]) -> dict[str, Any]:
    """Resolve one ``{column, function, as_name}`` input entry's column to its
    internal name and default its ``as_name``, ready to forward to the SDK.

    Function/column validity is the SDK's job (:meth:`DataviewsAPI.aggregate`
    raises ``MammothValidationError``, mapped to an ``invalid_arguments``
    envelope) — this only resolves the display name and computes the default
    label so the result can be relabeled below.
    """
    function = str(agg.get("function") or "").upper()
    column = agg.get("column")
    resolved: dict[str, Any] = {
        "function": function,
        "as_name": agg.get("as_name") or (f"{function}_{column}" if column else function),
    }
    if column:
        resolved["column"] = column_map.get(column, column)
    return resolved
