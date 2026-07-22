"""Handlers for the ``view`` draft, transform, and view-CRUD commands.

Three kinds of command live here:

* ViewsResource CRUD (``view create``/``get``/``delete``) dispatch through the
  generic :meth:`~mammoth_cli.services.protocol.MammothService.call` seam to
  the reviewed manifest ``sdk_symbol``, exactly like
  :mod:`mammoth_cli.commands.folder`.
* Draft commands (``view draft *``) and transform commands
  (``view transform *``) dispatch through
  :meth:`~mammoth_cli.services.protocol.MammothService.call_view`, which
  resolves the dataview into a rich ``View`` and calls the named public
  method. A ``condition`` field, when the underlying method accepts one, is
  forwarded unchanged as a plain spec; the service layer compiles it.

Command modules never import the SDK's condition builder or any enum type;
enum-typed fields are forwarded as the plain string given on ``--input``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service

HandlerResult = tuple[Any, dict[str, Any]]


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command."""
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code="sdk_symbol_unresolved",
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


def _int_positional(invocation: Invocation, name: str) -> int | None:
    """Parse the first positional argument as an int, or return None if absent."""
    if not invocation.extra_args:
        return None
    raw = invocation.extra_args[0]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code="invalid_argument",
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Return the first positional argument parsed as an int, or raise usage."""
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code="missing_argument",
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _view_id(invocation: Invocation) -> int:
    """Return the target view id from the first positional argument."""
    return _require_int_positional(invocation, "view id")


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code="missing_field",
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy each present field from ``document`` into ``kwargs``, unchanged."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a view command (no project scope)."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": None,
    }


def _dispatch_view(
    invocation: Invocation, view_id: int, method: str, **kwargs: Any
) -> HandlerResult:
    """Open the service, dispatch a View method call, and build the envelope."""
    with open_service(invocation) as (service, auth):
        data = service.call_view(view_id, method, **kwargs)
    return data, _meta(invocation, auth.workspace_id)


# --- ViewsResource CRUD (generic ``service.call`` seam) --------------------


def view_create(invocation: Invocation) -> HandlerResult:
    """Create a view from a dataset. Dataset id is positional; name/clone_from optional."""
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataset_id": dataset_id}
    _forward_optional(document, kwargs, ("name", "clone_from"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def view_get(invocation: Invocation) -> HandlerResult:
    """Get one view by id."""
    view_id = _view_id(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), view_id=view_id)
    return data, _meta(invocation, auth.workspace_id)


def view_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one view by id. Prompt or ``--yes`` required."""
    view_id = _view_id(invocation)
    enforce_confirmation(invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete view {view_id}")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), view_id=view_id)
    return data, _meta(invocation, auth.workspace_id)


# --- Draft commands (``service.call_view`` seam) ---------------------------


def view_draft_enter(invocation: Invocation) -> HandlerResult:
    """Enter draft mode on a view's pipeline."""
    view_id = _view_id(invocation)
    return _dispatch_view(invocation, view_id, "enter_draft_mode")


def view_draft_status(invocation: Invocation) -> HandlerResult:
    """Report whether a view's pipeline is currently in draft mode.

    Draft state is read from the server (``PipelineAPI.get_draft_status``) so it
    is correct across processes, rather than from a process-local flag that a
    freshly resolved view would always report as ``False``.
    """
    view_id = _view_id(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataview_id=view_id)
    return data, _meta(invocation, auth.workspace_id)


def view_draft_submit(invocation: Invocation) -> HandlerResult:
    """Submit a view's draft pipeline changes."""
    view_id = _view_id(invocation)
    return _dispatch_view(invocation, view_id, "submit_draft")


def view_draft_discard(invocation: Invocation) -> HandlerResult:
    """Discard a view's draft pipeline changes. Prompt or ``--yes`` required."""
    view_id = _view_id(invocation)
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"discard the draft for view {view_id}"
    )
    return _dispatch_view(invocation, view_id, "discard_draft")


def view_draft_auto_run(invocation: Invocation) -> HandlerResult:
    """Set whether a view's draft pipeline auto-runs. ``enabled`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    enabled = _require_field(document, "enabled")
    return _dispatch_view(invocation, view_id, "set_auto_run", enabled=enabled)


# --- Transform commands (``service.call_view`` seam) -----------------------


def view_transform_add_column(invocation: Invocation) -> HandlerResult:
    """Add a new column. ``name`` is required; ``column_type`` is optional."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    name = _require_field(document, "name")
    assert document is not None
    kwargs: dict[str, Any] = {"name": name}
    _forward_optional(document, kwargs, ("column_type",))
    return _dispatch_view(invocation, view_id, "add_column", **kwargs)


def view_transform_add_sql(invocation: Invocation) -> HandlerResult:
    """Add a column via a raw SQL expression. ``query`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    query = _require_field(document, "query")
    return _dispatch_view(invocation, view_id, "add_sql", query=query)


def view_transform_ai(invocation: Invocation) -> HandlerResult:
    """Generate a column with an AI prompt. ``prompt``/``context_columns`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    prompt = _require_field(document, "prompt")
    context_columns = _require_field(document, "context_columns")
    assert document is not None
    kwargs: dict[str, Any] = {"prompt": prompt, "context_columns": context_columns}
    _forward_optional(
        document, kwargs, ("new_column", "assistant_data", "context_columns_derivation")
    )
    return _dispatch_view(invocation, view_id, "gen_ai", **kwargs)


def view_transform_bulk_replace(invocation: Invocation) -> HandlerResult:
    """Bulk-replace values. ``columns``/``mapping`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    columns = _require_field(document, "columns")
    mapping = _require_field(document, "mapping")
    assert document is not None
    kwargs: dict[str, Any] = {"columns": columns, "mapping": mapping}
    _forward_optional(document, kwargs, ("match_case", "match_words", "condition"))
    return _dispatch_view(invocation, view_id, "bulk_replace", **kwargs)


def view_transform_combine_columns(invocation: Invocation) -> HandlerResult:
    """Combine columns into one. ``sources`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    sources = _require_field(document, "sources")
    assert document is not None
    kwargs: dict[str, Any] = {"sources": sources}
    _forward_optional(
        document,
        kwargs,
        ("new_column", "column_type", "existing_column", "separator", "condition"),
    )
    return _dispatch_view(invocation, view_id, "combine_columns", **kwargs)


def view_transform_convert_type(invocation: Invocation) -> HandlerResult:
    """Convert column types. ``conversions`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    conversions = _require_field(document, "conversions")
    return _dispatch_view(invocation, view_id, "convert_type", conversions=conversions)


def view_transform_copy_columns(invocation: Invocation) -> HandlerResult:
    """Copy columns. ``copies`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    copies = _require_field(document, "copies")
    return _dispatch_view(invocation, view_id, "copy_columns", copies=copies)


def view_transform_crosstab(invocation: Invocation) -> HandlerResult:
    """Build a crosstab into a new dataset. ``rows``/``pivot_column``/``select``/
    ``dataset_name`` are required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    rows = _require_field(document, "rows")
    pivot_column = _require_field(document, "pivot_column")
    select = _require_field(document, "select")
    dataset_name = _require_field(document, "dataset_name")
    assert document is not None
    kwargs: dict[str, Any] = {
        "rows": rows,
        "pivot_column": pivot_column,
        "select": select,
        "dataset_name": dataset_name,
    }
    _forward_optional(document, kwargs, ("save_as_mode", "target_ds_id", "condition", "timeout"))
    return _dispatch_view(invocation, view_id, "crosstab", **kwargs)


def view_transform_date_diff(invocation: Invocation) -> HandlerResult:
    """Compute the difference between two dates. ``component``/``start``/``end`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    component = _require_field(document, "component")
    start = _require_field(document, "start")
    end = _require_field(document, "end")
    assert document is not None
    kwargs: dict[str, Any] = {"component": component, "start": start, "end": end}
    _forward_optional(document, kwargs, ("new_column", "existing_column"))
    return _dispatch_view(invocation, view_id, "date_diff", **kwargs)


def view_transform_delete_columns(invocation: Invocation) -> HandlerResult:
    """Delete columns. ``columns`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    columns = _require_field(document, "columns")
    return _dispatch_view(invocation, view_id, "delete_columns", columns=columns)


def view_transform_discard_duplicates(invocation: Invocation) -> HandlerResult:
    """Discard duplicate rows. ``ignore_columns`` is optional."""
    view_id = _view_id(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("ignore_columns",))
    return _dispatch_view(invocation, view_id, "discard_duplicates", **kwargs)


def view_transform_extract_date(invocation: Invocation) -> HandlerResult:
    """Extract a date component into a column. ``column``/``component`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    column = _require_field(document, "column")
    component = _require_field(document, "component")
    assert document is not None
    kwargs: dict[str, Any] = {"column": column, "component": component}
    _forward_optional(document, kwargs, ("new_column", "existing_column"))
    return _dispatch_view(invocation, view_id, "extract_date", **kwargs)


def view_transform_fill_missing(invocation: Invocation) -> HandlerResult:
    """Fill missing values. ``column``/``direction`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    column = _require_field(document, "column")
    direction = _require_field(document, "direction")
    assert document is not None
    kwargs: dict[str, Any] = {"column": column, "direction": direction}
    _forward_optional(document, kwargs, ("partition_by", "order_by"))
    return _dispatch_view(invocation, view_id, "fill_missing", **kwargs)


def view_transform_filter(invocation: Invocation) -> HandlerResult:
    """Filter rows. ``condition`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    condition = _require_field(document, "condition")
    assert document is not None
    kwargs: dict[str, Any] = {"condition": condition}
    _forward_optional(document, kwargs, ("filter_type", "prompt"))
    return _dispatch_view(invocation, view_id, "filter_rows", **kwargs)


def view_transform_generate_sql(invocation: Invocation) -> HandlerResult:
    """Generate a SQL query from a natural-language intent. ``intent`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    intent = _require_field(document, "intent")
    return _dispatch_view(invocation, view_id, "generate_sql", intent=intent)


def view_transform_increment_date(invocation: Invocation) -> HandlerResult:
    """Increment a date column. ``column``/``delta`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    column = _require_field(document, "column")
    delta = _require_field(document, "delta")
    assert document is not None
    kwargs: dict[str, Any] = {"column": column, "delta": delta}
    _forward_optional(document, kwargs, ("new_column", "existing_column", "condition"))
    return _dispatch_view(invocation, view_id, "increment_date", **kwargs)


def view_transform_join(invocation: Invocation) -> HandlerResult:
    """Join another view. ``foreign_view``/``join_type``/``on``/``select`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    foreign_view = _require_field(document, "foreign_view")
    join_type = _require_field(document, "join_type")
    on = _require_field(document, "on")
    select = _require_field(document, "select")
    assert document is not None
    kwargs: dict[str, Any] = {
        "foreign_view": foreign_view,
        "join_type": join_type,
        "on": on,
        "select": select,
    }
    _forward_optional(document, kwargs, ("column_prefix",))
    return _dispatch_view(invocation, view_id, "join", **kwargs)


def view_transform_json_extract(invocation: Invocation) -> HandlerResult:
    """Extract fields from a JSON column. ``column`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    column = _require_field(document, "column")
    assert document is not None
    kwargs: dict[str, Any] = {"column": column}
    _forward_optional(
        document, kwargs, ("json_type", "keys", "extractions", "keep_source", "op_type")
    )
    return _dispatch_view(invocation, view_id, "json_extract", **kwargs)


def view_transform_limit_rows(invocation: Invocation) -> HandlerResult:
    """Limit the row count. ``n`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    n = _require_field(document, "n")
    assert document is not None
    kwargs: dict[str, Any] = {"n": n}
    _forward_optional(document, kwargs, ("bottom", "order_by"))
    return _dispatch_view(invocation, view_id, "limit_rows", **kwargs)


def view_transform_lookup(invocation: Invocation) -> HandlerResult:
    """Look up values from another view. ``source``/``lookup_view_id``/``key``/
    ``value`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    source = _require_field(document, "source")
    lookup_view_id = _require_field(document, "lookup_view_id")
    key = _require_field(document, "key")
    value = _require_field(document, "value")
    assert document is not None
    kwargs: dict[str, Any] = {
        "source": source,
        "lookup_view_id": lookup_view_id,
        "key": key,
        "value": value,
    }
    _forward_optional(document, kwargs, ("new_column", "existing_column"))
    return _dispatch_view(invocation, view_id, "lookup", **kwargs)


def view_transform_math(invocation: Invocation) -> HandlerResult:
    """Evaluate a math expression into a column. ``expression`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    expression = _require_field(document, "expression")
    assert document is not None
    kwargs: dict[str, Any] = {"expression": expression}
    _forward_optional(
        document, kwargs, ("new_column", "column_type", "existing_column", "condition")
    )
    return _dispatch_view(invocation, view_id, "math", **kwargs)


def view_transform_pivot(invocation: Invocation) -> HandlerResult:
    """Pivot with aggregations. ``group_by``/``aggregations`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    group_by = _require_field(document, "group_by")
    aggregations = _require_field(document, "aggregations")
    assert document is not None
    kwargs: dict[str, Any] = {"group_by": group_by, "aggregations": aggregations}
    _forward_optional(document, kwargs, ("condition",))
    return _dispatch_view(invocation, view_id, "pivot", **kwargs)


def view_transform_replace(invocation: Invocation) -> HandlerResult:
    """Find and replace values. ``columns``/``find``/``replace`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    columns = _require_field(document, "columns")
    find = _require_field(document, "find")
    replace = _require_field(document, "replace")
    assert document is not None
    kwargs: dict[str, Any] = {"columns": columns, "find": find, "replace": replace}
    _forward_optional(document, kwargs, ("match_case", "match_words", "condition"))
    return _dispatch_view(invocation, view_id, "replace_values", **kwargs)


def view_transform_set_values(invocation: Invocation) -> HandlerResult:
    """Set values conditionally. ``values`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    values = _require_field(document, "values")
    assert document is not None
    kwargs: dict[str, Any] = {"values": values}
    _forward_optional(
        document, kwargs, ("new_column", "column_type", "existing_column", "condition")
    )
    return _dispatch_view(invocation, view_id, "set_values", **kwargs)


def view_transform_small_large(invocation: Invocation) -> HandlerResult:
    """Compute a small/large-N function. ``function``/``columns`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    function = _require_field(document, "function")
    columns = _require_field(document, "columns")
    assert document is not None
    kwargs: dict[str, Any] = {"function": function, "columns": columns}
    _forward_optional(document, kwargs, ("index", "constants", "new_column", "existing_column"))
    return _dispatch_view(invocation, view_id, "small_large", **kwargs)


def view_transform_split(invocation: Invocation) -> HandlerResult:
    """Split a column. ``column``/``delimiter``/``new_columns`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    column = _require_field(document, "column")
    delimiter = _require_field(document, "delimiter")
    new_columns = _require_field(document, "new_columns")
    return _dispatch_view(
        invocation,
        view_id,
        "split_column",
        column=column,
        delimiter=delimiter,
        new_columns=new_columns,
    )


def view_transform_substring(invocation: Invocation) -> HandlerResult:
    """Extract a substring. ``column`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    column = _require_field(document, "column")
    assert document is not None
    kwargs: dict[str, Any] = {"column": column}
    _forward_optional(
        document,
        kwargs,
        (
            "direction",
            "num_char",
            "char_position",
            "regex_pattern",
            "regex_invert",
            "new_column",
            "existing_column",
            "condition",
        ),
    )
    return _dispatch_view(invocation, view_id, "substring", **kwargs)


def view_transform_text(invocation: Invocation) -> HandlerResult:
    """Apply text transforms. ``columns`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    columns = _require_field(document, "columns")
    assert document is not None
    kwargs: dict[str, Any] = {"columns": columns}
    _forward_optional(document, kwargs, ("case", "trim", "condition"))
    return _dispatch_view(invocation, view_id, "text_transform", **kwargs)


def view_transform_unnest(invocation: Invocation) -> HandlerResult:
    """Unnest columns into label/value rows. ``columns`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    columns = _require_field(document, "columns")
    assert document is not None
    kwargs: dict[str, Any] = {"columns": columns}
    _forward_optional(document, kwargs, ("label_column", "value_column"))
    return _dispatch_view(invocation, view_id, "unnest", **kwargs)


def view_transform_window(invocation: Invocation) -> HandlerResult:
    """Compute a window function. ``function`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    function = _require_field(document, "function")
    assert document is not None
    kwargs: dict[str, Any] = {"function": function}
    _forward_optional(
        document,
        kwargs,
        (
            "column",
            "new_column",
            "column_type",
            "existing_column",
            "partition_by",
            "order_by",
            "range_type",
        ),
    )
    return _dispatch_view(invocation, view_id, "window", **kwargs)
