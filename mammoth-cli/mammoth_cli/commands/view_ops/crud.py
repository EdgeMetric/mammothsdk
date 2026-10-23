"""View CRUD handlers: ``view create``, ``view variants create``, ``view get`` and ``view delete``.

They dispatch through the generic :meth:`~mammoth_cli.services.protocol.MammothService.call`
seam to the reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.view._common import (
    _DATAVIEW_GET_SYMBOL,
    _FIND_DATASET_SYMBOL,
    apply_column_renames,
)
from mammoth_cli.commands.view.columns import _display_name_map
from mammoth_cli.commands.view.listing import BRIEF_VIEW_FIELDS, brief_view_record
from mammoth_cli.commands.view_ops import (
    _meta,
    _profile_name,
    _require_field,
    _require_int_positional,
    _resolve_exact_dataset_id,
    _symbol,
    _view_id,
    reject_pipeline_reference_errors,
)
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENTS,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime import parents
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service
from mammoth_cli.services.command_contract import bind_command_inputs
from mammoth_cli.services.delete_check import ensure_deleted
from mammoth_cli.services.view_variants import (
    VariantPlan,
    created_entry,
    name_template_of,
    partial_failure,
    plan_variants,
    require_known_column,
    variants_result,
)

HandlerResult = tuple[Any, dict[str, Any]]


def view_create(invocation: Invocation) -> HandlerResult:
    """Create a view from a dataset. Dataset id is positional; name/clone_from optional."""
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input() or {}
    kwargs = bind_command_inputs(invocation.command_id, document, dataset_id=dataset_id)
    with open_service(invocation) as (service, auth):
        clone_from = kwargs.get("clone_from")
        if clone_from is not None:
            _require_clone_from_same_dataset(service, int(clone_from), dataset_id)
        data = service.call(_symbol(invocation), **kwargs)
    return _created_view(_view_payload(data)), _meta(invocation, auth.workspace_id)


def _created_view(record: Any) -> Any:
    """What ``view create`` reports: the new ids and a short summary (the columns are in ``state``).

    The full dataview record (pipeline metadata, dependency graph) is some 30 KB with
    the id buried in it; ``view get VIEW_ID`` returns it.
    """
    if not isinstance(record, dict):
        return record
    summary = {
        "view_id": record.get("id"),
        "dataset_id": record.get("dataset_id") or record.get("ds_id"),
        "id": record.get("id"),
        "name": record.get("name"),
        "row_count": record.get("row_count"),
        "column_count": record.get("column_count"),
    }
    return {key: value for key, value in summary.items() if value is not None}


def _require_clone_from_same_dataset(service: Any, clone_from: int, dataset_id: int) -> None:
    """Refuse ``clone_from`` when it is a view of a different dataset.

    The backend accepts a cross-dataset clone and produces a broken view (no
    columns; every later data read fails), so this is checked here before the
    request is sent rather than surfaced by the server.
    """
    source_dataset_id = int(service.call(_FIND_DATASET_SYMBOL, dataview_id=clone_from))
    if source_dataset_id != dataset_id:
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message="clone_from must be a view of the same dataset.",
            exit_status=EXIT_USAGE,
            hint=(
                f"View {clone_from} belongs to dataset {source_dataset_id}, not "
                f"{dataset_id}. Create a plain view (omit clone_from) instead."
            ),
            details={
                "clone_from": clone_from,
                "source_dataset_id": source_dataset_id,
                "dataset_id": dataset_id,
            },
        )


_VIEW_CREATE_SYMBOL = "mammoth.client.ViewsResource.create"


def view_variants_create(invocation: Invocation) -> HandlerResult:
    """Create one view per value of a column: each a clone of ``from_view`` filtered to it.

    Composes ``view create`` (``clone_from``) and ``view transform filter``. All
    checks that need no write run first; the first failing write stops the run
    and the error names every view already created.
    """
    dataset_id = _require_int_positional(invocation, "dataset id")
    raw = invocation.load_input()
    for field in ("from_view", "column", "values"):
        _require_field(raw, field)
    document = bind_command_inputs(invocation.command_id, raw)
    from_view = int(document["from_view"])
    column = str(document["column"])
    with open_service(invocation) as (service, auth):
        _require_clone_from_same_dataset(service, from_view, dataset_id)
        source = service.call(_DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=from_view)
        names = set(_display_name_map(service, dataset_id, from_view, None).values())
        require_known_column(from_view, column, names)
        plans = plan_variants(
            str(source.get("name", "")) if isinstance(source, dict) else "",
            column,
            document["values"],
            name_template_of(document),
        )
        created = _create_variants(service, dataset_id, from_view, plans)
    result = variants_result(dataset_id, from_view, column, created)
    return result, _meta(invocation, auth.workspace_id)


def _create_variants(
    service: Any, dataset_id: int, from_view: int, plans: list[VariantPlan]
) -> list[dict[str, Any]]:
    """Create and filter each variant in order; the first failure stops with a full report."""
    created: list[dict[str, Any]] = []
    for position, plan in enumerate(plans):
        new_id: int | None = None
        try:
            view = _view_payload(
                service.call(
                    _VIEW_CREATE_SYMBOL, dataset_id=dataset_id, name=plan.name, clone_from=from_view
                )
            )
            new_id = int(view["id"])
            data = service.call_view(
                new_id, "filter_rows", dataset_id=dataset_id, condition=plan.condition
            )
            reject_pipeline_reference_errors(service, new_id, dataset_id, data)
        except CliError as exc:
            raise partial_failure(
                plan, exc, created, plans[position + 1 :], new_id, dataset_id
            ) from exc
        created.append(created_entry(plan, view))
    return created


_DASHBOARDS_LIST_SYMBOL = "mammoth.api.dashboards.DashboardsAPI.list"


def _read_with_boards(service: Any, symbol: str, kwargs: dict[str, Any]) -> tuple[Any, Any]:
    """Run the view read and the dashboards list together; return ``(view, boards)``.

    The two are independent, so their round trips overlap instead of adding up.
    The view read's failure is raised as before; a failed dashboards read is
    dropped (``None``), because a decoration must not fail the read it decorates.
    """
    view, boards = service.call_many([(symbol, kwargs), (_DASHBOARDS_LIST_SYMBOL, {})])
    if isinstance(view, CliError):
        raise view
    return view, None if isinstance(boards, CliError) else boards


def _with_dashboards(view_id: int, record: Any, boards: Any) -> Any:
    """Add the dashboards built on this view, so a user on the view's page who
    says "this board" is understood (eval T1-D-22); unchanged when none."""
    if not isinstance(record, dict):
        return record
    built_on = [
        {"id": board.get("id"), "title": board.get("title")}
        for board in (boards if isinstance(boards, list) else [])
        if isinstance(board, dict) and view_id in (board.get("sources") or [])
    ]
    return {**record, "dashboards": built_on} if built_on else record


def view_get(invocation: Invocation) -> HandlerResult:
    """Get one view by id, optionally scoped to an exact dataset parent."""
    view_id = _view_id(invocation)
    document = invocation.load_input() or {}
    dataset_id = _resolve_exact_dataset_id(invocation, view_id, document)
    if dataset_id is not None:
        # The release operation is dataset-scoped.  Bypass the rich-object
        # resolver when the caller supplied the exact parent so no discovery
        # probe can escape the requested project/dataset.
        kwargs: dict[str, Any] = {
            "dataset_id": dataset_id,
            "dataview_id": view_id,
            # Server-side projection; the brief set (plus the display
            # properties that carry column renames) unless the caller asks.
            "fields": (
                document.get("fields")
                or ",".join(
                    [key for key in BRIEF_VIEW_FIELDS if key != "dataset_id"]
                    + ["display_properties"]
                )
            ),
        }
        with open_service(invocation) as (service, auth):
            data, boards = _read_with_boards(
                service, "mammoth.api.dataviews.DataviewsAPI.get", kwargs
            )
            parents.remember(_profile_name(invocation), auth.workspace_id, {view_id: dataset_id})
            data = apply_column_renames(data) if document.get("fields") else brief_view_record(data)
            data = _with_dashboards(view_id, data, boards)
        return data, _meta(invocation, auth.workspace_id)
    context: dict[str, Any] = {"view_id": view_id}
    if dataset_id is not None:
        context["dataset_id"] = dataset_id
    # The generated contract predates the optional parent context; preserve
    # its declared fields, then add the validated SDK parent explicitly.
    # ``fields`` projects the exact-parent route only; the discovery route
    # returns the full record, trimmed below unless ``fields`` was asked for.
    binding_document = {
        key: value for key, value in document.items() if key not in ("dataset_id", "fields")
    }
    kwargs = bind_command_inputs(invocation.command_id, binding_document, view_id=view_id)
    if dataset_id is not None:
        kwargs["dataset_id"] = dataset_id
    with open_service(invocation) as (service, auth):
        data, boards = _read_with_boards(service, _symbol(invocation), kwargs)
        payload = _view_payload(data)
        parents.remember_records(_profile_name(invocation), auth.workspace_id, payload)
        if not document.get("fields"):
            # The discovery path returns the standard record; trim it to the same
            # brief shape the exact path asks the server for.
            payload = brief_view_record(payload)
        else:
            payload = apply_column_renames(payload)
        payload = _with_dashboards(view_id, payload, boards)
    return payload, _meta(invocation, auth.workspace_id)


def _view_payload(value: Any) -> Any:
    """Return the dataview record for a resolved rich ``View`` object.

    The discovery path returns the SDK's ``View`` (methods, client handle),
    which the output normaliser rightly refuses to serialise. Its ``raw``
    attribute is the same dataview record the exact-parent path returns, so
    both paths emit one shape; the discovered parent is added because the
    caller did not know it and needs it for every mutating follow-up.
    """
    raw = getattr(value, "raw", None)
    if not isinstance(raw, dict):
        return value
    record = dict(raw)
    # The record's own ``ds_id`` is the parent; the resolver's probed dataset is
    # only a fallback, since the backend serves a view under a dataset that does
    # not own it.
    own_parent = record.get("ds_id")
    probed = getattr(value, "dataset_id", None)
    dataset_id = own_parent if isinstance(own_parent, int) else probed
    if isinstance(dataset_id, int) and "dataset_id" not in record:
        record["dataset_id"] = dataset_id
    return record


def view_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one view by id. Prompt or ``--yes`` required.

    ``dataset_id`` is required: the trailing positional, the structured input
    field, or a typed resource reference must name the exact parent. It is
    forwarded to the SDK so deletion uses exactly that parent endpoint and
    never performs a project-wide parent probe before a destructive call.
    """
    view_id = _view_id(invocation)
    enforce_confirmation(invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete view {view_id}")
    document = invocation.load_input() or {}
    dataset_id = _resolve_exact_dataset_id(invocation, view_id, document, required=True)
    context: dict[str, Any] = {"view_id": view_id, "dataset_id": dataset_id}
    kwargs = bind_command_inputs(invocation.command_id, document, **context)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
        ensure_deleted(
            service,
            noun="view",
            resource_id=view_id,
            read_symbol=_DATAVIEW_GET_SYMBOL,
            read_kwargs={
                "dataset_id": dataset_id,
                "dataview_id": view_id,
                "project_id": invocation.project,
            },
            responses=(data,),
            recovery_commands=[f"mammoth view task list {view_id}"],
        )
    return data, _meta(invocation, auth.workspace_id)
