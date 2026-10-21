"""``view data get`` / ``view data query`` handlers and their paging helpers."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.view._common import (
    _COLUMNS_KEY,
    _FIND_DATASET_SYMBOL,
    _QUERY_DATA_SYMBOL,
    _ROWS_KEY,
    HandlerResult,
    _forward_optional,
    _int_field,
    _page_offset,
    _read_meta,
    _read_meta_and_info,
    _require_int_positional_at,
    _resolve_dataset_id,
    _symbol,
)
from mammoth_cli.commands.view.column_checks import (
    _profile_of_info,
    _relabel_and_check,
)
from mammoth_cli.commands.view.columns import (
    _compile_query_filters,
)
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_RESOURCE_NOT_FOUND,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.output.normalize import DataRows
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import (
    open_service,
    require_project,
)
from mammoth_cli.services import read_queries
from mammoth_cli.services.conditions import CONDITION_KWARG
from mammoth_cli.services.paging import paging_block
from mammoth_cli.services.read_queries import ReadContext


def view_data_get(invocation: Invocation) -> HandlerResult:
    """Fetch a dataview's data, waiting for the backing job to complete.

    The dataset is resolved from the view unless given as a trailing positional
    or a ``dataset_id`` --input field. ``offset`` (0-based: rows to skip; default 0,
    ``limit`` default 50) reads a later page through the query route; ``paging`` carries
    ``next_command`` and ``previous_command`` (null when there is no such page).
    The result carries ``column_warnings`` when the
    rows show a text column of numbers or dates, or blanks. ``raw: true`` returns DATE
    values with their time.
    """
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    limit = document.get("limit", _DATA_GET_DEFAULT_LIMIT)
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        try:
            meta, info = _read_meta_and_info(
                service, invocation, auth.workspace_id, dataset_id, view_id, project_id
            )
        except CliError as exc:
            _explain_swapped_ids(service, exc, view_id, dataset_id)
            raise
        mapping, types, _currencies = _profile_of_info(info)
        kwargs: dict[str, Any] = {
            "dataset_id": dataset_id,
            "dataview_id": view_id,
            "project_id": project_id,
        }
        if document.get("offset") is not None:
            # The CLI offset is 0-based (rows to skip); the data route counts from 1.
            kwargs["offset"] = _page_offset(document["offset"]) + 1
            page_limit = _int_field(limit, "limit")
            kwargs["limit"] = page_limit if page_limit > 0 else 400
            _forward_optional(document, kwargs, ("sequence", "raw"))
            data = service.call(_QUERY_DATA_SYMBOL, **kwargs)
        else:
            _forward_optional(document, kwargs, ("timeout", "poll_interval", "sequence", "raw"))
            data = service.call(_symbol(invocation), **kwargs)
        whole_view = document.get("offset") is None
        data = _relabel_and_check(
            service,
            dataset_id,
            view_id,
            project_id,
            data,
            mapping=mapping,
            types=types,
            whole_view=whole_view,
        )
    page_size = _DATA_PAGE_ROWS if whole_view else kwargs["limit"]
    data = _trim_rows(data, limit, page_size)
    data = keep_columns(data, document.get("columns"))
    if document.get("sequence") is None:
        # The view's row count is its latest step's; a read at an earlier step differs.
        data = _with_paging_total(data, meta)
        data = _close_last_page(data, kwargs.get("offset"))
    data = _with_cli_paging(data, invocation, view_id, kwargs.get("offset"), page_size, limit)
    return data, meta


def keep_columns(data: Any, columns: list[str] | None) -> Any:
    """Keep only ``columns`` (display names) in a data page's rows and column header.

    A name the page does not have is refused with the names it does have, so a typo
    never reads as an empty column.
    """
    if columns is None or not isinstance(data, dict):
        return data
    rows = data.get(_ROWS_KEY)
    if not isinstance(rows, list):
        return data
    first = rows[0] if rows else None
    available = list(first) if isinstance(first, dict) else list(data.get(_COLUMNS_KEY) or [])
    missing = [name for name in columns if name not in available]
    if missing:
        raise CliError(
            code="unknown_column",
            message=f"Column(s) not in the view: {', '.join(missing)}.",
            exit_status=EXIT_USAGE,
            hint="Use column display names from this view.",
            details={"columns": missing, "available": available},
        )
    kept = {**data, _ROWS_KEY: DataRows([{c: row[c] for c in columns} for row in rows])}
    if isinstance(data.get(_COLUMNS_KEY), list):
        kept[_COLUMNS_KEY] = list(columns)
    return kept


def _with_cli_paging(
    data: Any,
    invocation: Invocation,
    view_id: int,
    api_offset: Any,
    page_size: int,
    limit: Any,
) -> Any:
    """Replace the route's ``paging`` with the CLI's 0-based block (see ``paging_block``)."""
    if not isinstance(data, dict) or not isinstance(data.get(_ROWS_KEY), list):
        return data
    old = data.get("paging")
    total = old.get("total") if isinstance(old, dict) else None
    returned = data.get("rows_returned", len(data[_ROWS_KEY]))
    try:
        asked = int(limit)
    except (TypeError, ValueError):
        asked = _DATA_GET_DEFAULT_LIMIT
    block = paging_block(
        command=f"mammoth view data get {view_id}",
        project=invocation.project,
        offset=(api_offset - 1) if isinstance(api_offset, int) else 0,
        limit=asked if asked > 0 else page_size,
        returned=returned,
        total=total if isinstance(total, int) and total > 0 else None,
    )
    return {**data, "paging": block}


def _with_paging_total(data: Any, meta: dict[str, Any]) -> Any:
    """Fill ``paging.total`` with the view's row count; the query route reports 0."""
    paging = data.get("paging") if isinstance(data, dict) else None
    row_count = meta["view"].get("row_count")
    if (
        isinstance(paging, dict)
        and isinstance(row_count, int)
        and row_count > paging.get("total", 0)
    ):
        return {**data, "paging": {**paging, "total": row_count}}
    return data


def _close_last_page(data: Any, offset: Any) -> Any:
    """Clear ``truncated`` when the rows read reach the view's last row.

    A page that came back full is only a guess that more rows exist; the view's
    row count (``paging.total``) settles it. ``offset`` is the data route's 1-based
    row, so a page holding rows ``offset`` .. ``offset + rows_returned - 1`` is the last one when
    that reaches the total.
    """
    if not isinstance(data, dict) or not data.get("truncated"):
        return data
    paging = data.get("paging")
    total = paging.get("total") if isinstance(paging, dict) else None
    returned = data.get("rows_returned")
    if not isinstance(total, int) or not isinstance(returned, int) or total <= 0:
        return data
    first_row = offset if isinstance(offset, int) else 1
    if first_row - 1 + returned < total:
        return data
    closed = {**data, "truncated": False}
    closed.pop("more_rows_may_exist", None)
    return closed


def _explain_swapped_ids(service: Any, error: CliError, view_id: int, dataset_id: int) -> None:
    """Raise a clear refusal when a not-found read was given DATASET_ID then VIEW_ID.

    The arguments are ``VIEW_ID [DATASET_ID]``; passing them the other way round
    only produces a bare 404. If the first number is really a view of the second,
    say so. Any other outcome leaves the original error to be re-raised.
    """
    if error.code != CODE_RESOURCE_NOT_FOUND:
        return
    try:
        parent = int(service.call(_FIND_DATASET_SYMBOL, dataview_id=dataset_id))
    except CliError:
        return
    if parent != view_id:
        return
    raise CliError(
        code=CODE_INVALID_ARGUMENT,
        message=(
            f"{view_id} is a dataset id and {dataset_id} is its view; "
            "the order is VIEW_ID DATASET_ID"
        ),
        exit_status=EXIT_USAGE,
        hint=f"Run it again as: mammoth view data get {dataset_id} {view_id}",
        details={"view_id": dataset_id, "dataset_id": view_id},
    ) from error


#: Rows a plain ``view data get`` returns unless ``limit`` says otherwise.
_DATA_GET_DEFAULT_LIMIT = 50

#: Rows the server returns per data read when no ``offset`` is given (its page size).
_DATA_PAGE_ROWS = 400


def _trim_rows(data: Any, limit: Any, page_size: int | None = None) -> Any:
    """Keep the first ``limit`` rows of a data page and say what was cut.

    The route returns one page of the view (``page_size`` rows at most); an
    agent reading back a transform needs a sample and the total. ``limit`` 0
    or a negative value means "all rows of the page". A page that came back
    full may have more rows behind it, so it is reported as truncated too.
    """
    if not isinstance(data, dict) or not isinstance(data.get(_ROWS_KEY), list):
        return data
    try:
        cap = int(limit)
    except TypeError:
        cap = _DATA_GET_DEFAULT_LIMIT
    except ValueError:
        cap = _DATA_GET_DEFAULT_LIMIT
    rows = data[_ROWS_KEY]
    total = len(rows)
    if cap <= 0 or total <= cap:
        page_full = page_size is not None and total >= page_size
        result = {**data, "rows_returned": total, "rows_total_in_page": total}
        result["truncated"] = page_full
        if page_full:
            result["more_rows_may_exist"] = "The page is full; read the next page with offset."
        return result
    return {
        **data,
        _ROWS_KEY: DataRows(rows[:cap]),
        "rows_returned": cap,
        "rows_total_in_page": total,
        "truncated": True,
    }


def view_data_query(invocation: Invocation) -> HandlerResult:
    """Query a dataview's data with optional filtering, sorting, and paging.

    The dataset is resolved from the view unless given as a trailing positional
    or a ``dataset_id`` --input field. ``raw: true`` returns DATE values with their time.
    """
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        meta = _read_meta(service, invocation, auth.workspace_id, dataset_id, view_id, project_id)
        kwargs: dict[str, Any] = {
            "dataset_id": dataset_id,
            "dataview_id": view_id,
            "project_id": project_id,
        }
        _forward_optional(document, kwargs, ("sequence", "offset", "limit", "sort", "raw"))
        reads = ReadContext(
            service,
            dataset_id,
            view_id,
            project_id,
            {},
            {},
            document.get("sequence"),
            document.get("text_date_format"),
        )
        mapping, types = _compile_query_filters(
            service, dataset_id, view_id, project_id, document, kwargs, reads
        )
        data = service.call(_symbol(invocation), **kwargs)
        data = _relabel_and_check(service, dataset_id, view_id, project_id, data, mapping, types)
        columns = read_queries.condition_columns(document.get(CONDITION_KWARG))
        data = read_queries.with_observed_range(reads, data, columns)
        data = read_queries.with_assumptions(reads, data)
    return data, meta
