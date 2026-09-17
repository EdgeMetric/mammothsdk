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

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project
from mammoth_cli.services.command_contract import bind_command_inputs
from mammoth_cli.services.conditions import CONDITION_KWARG

HandlerResult = tuple[Any, dict[str, Any]]


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command."""
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
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
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Return the first positional argument parsed as an int, or raise usage."""
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _view_id(invocation: Invocation) -> int:
    """Return the target view id from the first positional argument."""
    return _require_int_positional(invocation, "view id")


def _resolve_exact_dataset_id(
    invocation: Invocation, view_id: int, document: dict[str, Any], *, required: bool = False
) -> int | None:
    """Resolve and reconcile optional exact parent identity for one view.

    Every supplied resource reference, positional, and input value must agree.
    Supplying the parent is important: ``ViewsResource.delete`` only invokes
    its legacy parent discovery when ``dataset_id`` is omitted, and that
    discovery can select a different dataset for the same view id.
    """
    resource = invocation.resource_ref
    if resource is not None and resource.view_id not in (None, view_id):
        raise CliError(
            code="invalid_resource_context",
            message="The resource reference view_id does not match the target view.",
            exit_status=EXIT_USAGE,
            hint="Use a resource reference for the same view id as the command target.",
        )
    if resource is not None and resource.project_id is not None:
        # Match the effective project the service will use: explicit --project
        # first, otherwise the selected profile's project.  Do not require a
        # project here; projectless view routes keep their existing semantics.
        effective_project = resolved_project(invocation)
        if effective_project is not None and resource.project_id != effective_project:
            raise CliError(
                code="invalid_resource_context",
                message=(
                    "The resource reference project does not match the effective project scope."
                ),
                exit_status=EXIT_USAGE,
            )
    raw_values = [
        value
        for value in (
            resource.dataset_id if resource is not None else None,
            invocation.positional("dataset_id"),
            document.get("dataset_id"),
        )
        if value is not None
    ]
    if not raw_values:
        if required:
            raise CliError(
                code="resource_identity_required",
                message="This operation requires the exact parent dataset id.",
                exit_status=EXIT_USAGE,
                hint="Pass DATASET_ID or include dataset_id in --input.",
            )
        return None
    try:
        values = {int(value) for value in raw_values}
    except (TypeError, ValueError) as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The dataset id must be an integer.",
            exit_status=EXIT_USAGE,
        ) from exc
    if len(values) != 1:
        raise CliError(
            code="ambiguous_resource_identity",
            message="Conflicting dataset ids identify different parent resources.",
            exit_status=EXIT_USAGE,
            hint="Pass one exact dataset id matching the target view.",
        )
    value = values.pop()
    if value <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The dataset id must be a positive integer.",
            exit_status=EXIT_USAGE,
        )
    return value


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code=CODE_MISSING_FIELD,
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
    # ``dataset_id`` is invocation-local resource context.  It is not a View
    # transform argument, but passing it through lets the service fetch the
    # exact parent endpoint and prevents the SDK's legacy bare-view resolver
    # from probing an unrelated dataset.
    document = invocation.load_input() or {}
    dataset_id = _resolve_exact_dataset_id(
        invocation,
        view_id,
        document,
        # Keep the legacy discovery path for existing transform callers, but
        # reject conflicting explicit identities rather than selecting one.
        required=False,
    )
    with open_service(invocation) as (service, auth):
        if dataset_id is None:
            data = service.call_view(view_id, method, **kwargs)
        else:
            data = service.call_view(view_id, method, dataset_id=int(dataset_id), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def _without_resource_context(document: dict[str, Any]) -> dict[str, Any]:
    """Remove target-resource context before binding transform SDK arguments."""
    # ``Invocation.load_input`` now applies the shared contract to the whole
    # S3 family, which materializes positional locators in the returned
    # mapping.  These identifiers select the View receiver and are not method
    # kwargs; strip both parent and receiver identities before the transform
    # adapter forwards the document.
    return {
        key: value for key, value in document.items() if key not in {"dataset_id", "view_id"}
    }


def _bind_transform_inputs(
    invocation: Invocation, document: dict[str, Any]
) -> dict[str, Any]:
    """Bind every admitted transform field through its reviewed contract.

    Transform handlers still own domain-specific required-field checks and the
    exact View method they call.  They do not, however, maintain a second
    hand-written allow-list of optional fields: the shared contract is the
    destination ledger used by admission, discovery, and this SDK call.  The
    optional ``dataset_id`` is resource identity context for resolving the
    target view and must never be passed to a View transform method.
    """
    bound = bind_command_inputs(
        invocation.command_id, _without_resource_context(document)
    )
    direction = str(getattr(bound.get("direction"), "value", bound.get("direction"))).upper()
    if direction in {"LEFT", "RIGHT"} and bound.get("num_char") is not None:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="LEFT/RIGHT requires char_position, not num_char.",
            exit_status=EXIT_USAGE,
        )
    if direction in {"START", "END"} and bound.get("char_position") is not None:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="START/END requires num_char, not char_position.",
            exit_status=EXIT_USAGE,
        )
    return bound


# --- ViewsResource CRUD (generic ``service.call`` seam) --------------------


def view_create(invocation: Invocation) -> HandlerResult:
    """Create a view from a dataset. Dataset id is positional; name/clone_from optional."""
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input() or {}
    kwargs = bind_command_inputs(invocation.command_id, document, dataset_id=dataset_id)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def view_get(invocation: Invocation) -> HandlerResult:
    """Get one view by id, optionally scoped to an exact dataset parent."""
    view_id = _view_id(invocation)
    document = invocation.load_input() or {}
    dataset_id = _resolve_exact_dataset_id(invocation, view_id, document)
    if dataset_id is not None:
        # The release operation is dataset-scoped.  Bypass the rich-object
        # resolver when the caller supplied the exact parent so no discovery
        # probe can escape the requested project/dataset.
        kwargs: dict[str, Any] = {"dataset_id": dataset_id, "dataview_id": view_id}
        if "fields" in document:
            kwargs["fields"] = document["fields"]
        with open_service(invocation) as (service, auth):
            data = service.call("mammoth.api.dataviews.DataviewsAPI.get", **kwargs)
        return data, _meta(invocation, auth.workspace_id)
    context: dict[str, Any] = {"view_id": view_id}
    if dataset_id is not None:
        context["dataset_id"] = dataset_id
    # The generated contract predates the optional parent context; preserve
    # its declared fields, then add the validated SDK parent explicitly.
    binding_document = {key: value for key, value in document.items() if key != "dataset_id"}
    kwargs = bind_command_inputs(invocation.command_id, binding_document, view_id=view_id)
    if dataset_id is not None:
        kwargs["dataset_id"] = dataset_id
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def view_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one view by id. Prompt or ``--yes`` required.

    ``dataset_id`` may be supplied as the trailing positional, in structured
    input, or by a typed resource reference.  When present it is forwarded to
    the SDK so deletion uses exactly that parent endpoint and never performs a
    workspace-wide parent probe.
    """
    view_id = _view_id(invocation)
    enforce_confirmation(invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete view {view_id}")
    document = invocation.load_input() or {}
    dataset_id = _resolve_exact_dataset_id(invocation, view_id, document)
    context: dict[str, Any] = {"view_id": view_id}
    if dataset_id is not None:
        context["dataset_id"] = dataset_id
    kwargs = bind_command_inputs(invocation.command_id, document, **context)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
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
    _require_field(document, "name")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "add_column", **kwargs)


def view_transform_add_sql(invocation: Invocation) -> HandlerResult:
    """Add a column via a raw SQL expression. ``query`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "query")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "add_sql", **kwargs)


def view_transform_ai(invocation: Invocation) -> HandlerResult:
    """Generate a column with an AI prompt. ``prompt``/``context_columns`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "prompt")
    _require_field(document, "context_columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "gen_ai", **kwargs)


def view_transform_bulk_replace(invocation: Invocation) -> HandlerResult:
    """Bulk-replace values. ``columns``/``mapping`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "columns")
    _require_field(document, "mapping")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "bulk_replace", **kwargs)


def view_transform_combine_columns(invocation: Invocation) -> HandlerResult:
    """Combine columns into one. ``sources`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "sources")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "combine_columns", **kwargs)


def view_transform_convert_type(invocation: Invocation) -> HandlerResult:
    """Convert column types. ``conversions`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "conversions")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "convert_type", **kwargs)


def view_transform_copy_columns(invocation: Invocation) -> HandlerResult:
    """Copy columns. ``copies`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "copies")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "copy_columns", **kwargs)


def view_transform_crosstab(invocation: Invocation) -> HandlerResult:
    """Build a crosstab into a new dataset. ``rows``/``pivot_column``/``select``/
    ``dataset_name`` are required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "rows")
    _require_field(document, "pivot_column")
    _require_field(document, "select")
    _require_field(document, "dataset_name")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "crosstab", **kwargs)


def view_transform_date_diff(invocation: Invocation) -> HandlerResult:
    """Compute the difference between two dates. ``component``/``start``/``end`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "component")
    _require_field(document, "start")
    _require_field(document, "end")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "date_diff", **kwargs)


def view_transform_delete_columns(invocation: Invocation) -> HandlerResult:
    """Delete columns. ``columns`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "delete_columns", **kwargs)


def view_transform_discard_duplicates(invocation: Invocation) -> HandlerResult:
    """Discard duplicate rows. ``ignore_columns`` is optional."""
    view_id = _view_id(invocation)
    document = invocation.load_input() or {}
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "discard_duplicates", **kwargs)


def view_transform_extract_date(invocation: Invocation) -> HandlerResult:
    """Extract a date component into a column. ``column``/``component`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    _require_field(document, "component")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "extract_date", **kwargs)


def view_transform_fill_missing(invocation: Invocation) -> HandlerResult:
    """Fill missing values. ``column``/``direction`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    _require_field(document, "direction")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "fill_missing", **kwargs)


def view_transform_filter(invocation: Invocation) -> HandlerResult:
    """Filter rows. ``condition`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, CONDITION_KWARG)
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "filter_rows", **kwargs)


def view_transform_generate_sql(invocation: Invocation) -> HandlerResult:
    """Generate a SQL query from a natural-language intent. ``intent`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "intent")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "generate_sql", **kwargs)


def view_transform_increment_date(invocation: Invocation) -> HandlerResult:
    """Increment a date column. ``column``/``delta`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    _require_field(document, "delta")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "increment_date", **kwargs)


def view_transform_join(invocation: Invocation) -> HandlerResult:
    """Join another view. ``foreign_view``/``join_type``/``on``/``select`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "foreign_view")
    _require_field(document, "join_type")
    _require_field(document, "on")
    _require_field(document, "select")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "join", **kwargs)


def view_transform_json_extract(invocation: Invocation) -> HandlerResult:
    """Extract fields from a JSON column. ``column`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "json_extract", **kwargs)


def view_transform_limit_rows(invocation: Invocation) -> HandlerResult:
    """Limit the row count. ``n`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "n")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "limit_rows", **kwargs)


def view_transform_lookup(invocation: Invocation) -> HandlerResult:
    """Look up values from another view. ``source``/``lookup_view_id``/``key``/
    ``value`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "source")
    _require_field(document, "lookup_view_id")
    _require_field(document, "key")
    _require_field(document, "value")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "lookup", **kwargs)


def view_transform_math(invocation: Invocation) -> HandlerResult:
    """Evaluate a math expression into a column. ``expression`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "expression")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "math", **kwargs)


def view_transform_pivot(invocation: Invocation) -> HandlerResult:
    """Pivot with aggregations. ``group_by``/``aggregations`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "group_by")
    _require_field(document, "aggregations")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "pivot", **kwargs)


def view_transform_replace(invocation: Invocation) -> HandlerResult:
    """Find and replace values. ``columns``/``find``/``replace`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "columns")
    _require_field(document, "find")
    _require_field(document, "replace")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "replace_values", **kwargs)


def view_transform_set_values(invocation: Invocation) -> HandlerResult:
    """Set values conditionally. ``values`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "values")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "set_values", **kwargs)


def view_transform_small_large(invocation: Invocation) -> HandlerResult:
    """Compute a small/large-N function. ``function``/``columns`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "function")
    _require_field(document, "columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "small_large", **kwargs)


def view_transform_split(invocation: Invocation) -> HandlerResult:
    """Split a column. ``column``/``delimiter``/``new_columns`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    _require_field(document, "delimiter")
    _require_field(document, "new_columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "split_column", **kwargs)


def view_transform_substring(invocation: Invocation) -> HandlerResult:
    """Extract a substring. ``column`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "substring", **kwargs)


def view_transform_text(invocation: Invocation) -> HandlerResult:
    """Apply text transforms. ``columns`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "text_transform", **kwargs)


def view_transform_unnest(invocation: Invocation) -> HandlerResult:
    """Unnest columns into label/value rows. ``columns`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "unnest", **kwargs)


def view_transform_window(invocation: Invocation) -> HandlerResult:
    """Compute a window function. ``function`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "function")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "window", **kwargs)
