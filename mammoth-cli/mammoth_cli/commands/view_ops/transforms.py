"""Handlers for ``view transform *``.

Each builds its step and adds it through the shared write path in
:mod:`mammoth_cli.commands.view_ops`.
"""

from __future__ import annotations

import json
import re
import shlex
from collections.abc import Callable
from typing import Any

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.view._common import (
    _DATAVIEW_GET_SYMBOL,
    apply_column_renames,
)
from mammoth_cli.commands.view.columns import _dataview_metadata
from mammoth_cli.commands.view.export_dataset import reject_dataset_export_conflicts
from mammoth_cli.commands.view.join_check import (
    join_after_snapshot,
    join_dry_run_preview,
    join_snapshot,
    with_join_check,
)
from mammoth_cli.commands.view.settle import (
    wait_for_followon_job,
)
from mammoth_cli.commands.view_ops import (
    CODE_TASK_RUNTIME_ERROR,
    _bind_transform_inputs,
    _dispatch_view,
    _require_field,
    _require_one_destination,
    _view_id,
)
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    EXIT_API,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.dryrun import DryRunStop
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import resolved_project
from mammoth_cli.services.column_type_guard import (
    DATE,
    NUMERIC,
    TypeCheck,
    check_column_types,
    math_columns,
)
from mammoth_cli.services.conditions import CONDITION_KWARG, compile_condition
from mammoth_cli.services.sql_check import check_sql_binds
from mammoth_cli.services.write_impact import (
    STANDING_HINT,
    STANDING_NOTE,
    ImpactRead,
    Measure,
    Measured,
    empties_view_error,
    measure_bulk_replace,
    measure_duplicates,
    measure_fill_missing,
    measure_filter,
    measure_replace,
    no_op_error,
)


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
    return _dispatch_view(
        invocation, view_id, "add_sql", prepare=_sql_binding_check(invocation, view_id), **kwargs
    )


def _sql_binding_check(
    invocation: Invocation, view_id: int
) -> Callable[[Any, int, dict[str, Any]], Any]:
    """A ``prepare`` hook: a dry run fails with ``would_fail`` when the SQL names a column
    the step cannot bind (see :mod:`mammoth_cli.services.sql_check`). A real run is unchanged."""

    def check(service: Any, dataset_id: int, kwargs: dict[str, Any]) -> Any:
        if invocation.dry_run:
            view = service.call(
                _DATAVIEW_GET_SYMBOL,
                dataset_id=dataset_id,
                dataview_id=view_id,
                project_id=resolved_project(invocation),
            )
            if isinstance(view, dict):
                check_sql_binds(str(kwargs.get("query", "")), view)
        return None

    return check


def view_transform_ai(invocation: Invocation) -> HandlerResult:
    """Generate a column with an AI prompt. ``prompt``/``context_columns`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "prompt")
    _require_field(document, "context_columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    data, meta = _dispatch_view(invocation, view_id, "gen_ai", **kwargs)
    _reject_failed_ai_run(view_id, data)
    return data, meta


def _reject_failed_ai_run(view_id: int, data: Any) -> None:
    """Fail an AI step that was added but errored when it ran (an empty new column)."""
    error = data.get("pipeline_error") if isinstance(data, dict) else None
    if not isinstance(error, dict) or error.get("execution_state") != "runtime_error":
        return
    task_id = error.get("task_id")
    raise CliError(
        code=CODE_TASK_RUNTIME_ERROR,
        message=(
            f"The AI step (task {task_id}) was added to view {view_id} but failed when it ran "
            f"(error {error.get('error_code')}); its new column is empty."
        ),
        exit_status=EXIT_API,
        hint=(
            "Likely causes: the workspace's AI quota, or a prompt the step cannot run. "
            f"Remove the task with `mammoth view task delete {view_id} {task_id} --yes` "
            "and try again."
        ),
        details={"view_id": view_id, "task_id": task_id, "pipeline_error": error},
        recovery_commands=[f"mammoth view task delete {view_id} {task_id} --yes"],
    )


def view_transform_bulk_replace(invocation: Invocation) -> HandlerResult:
    """Bulk-replace values. ``columns``/``mapping`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "columns")
    _require_field(document, "mapping")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    prepare = _impact_check(invocation, view_id, measure_bulk_replace)
    return _dispatch_view(invocation, view_id, "bulk_replace", prepare=prepare, **kwargs)


def view_transform_combine_columns(invocation: Invocation) -> HandlerResult:
    """Combine columns into one. ``sources`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "sources")
    assert document is not None
    _require_one_destination(document, invocation.command_id)
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "combine_columns", **kwargs)


def view_transform_convert_type(invocation: Invocation) -> HandlerResult:
    """Convert column types. ``conversions`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "conversions")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    project_id = invocation.project

    def drop_same_type(service: Any, dataset_id: int, call: dict[str, Any]) -> Any:
        # Converting a column to the type it already has puts the pipeline in
        # ref_error ("type mismatch") and every read of the view fails until
        # the task is removed (release, 2026-09-25). Uploads type numbers and
        # ISO dates on their own, so this is easy to hit: skip those entries.
        conversions = call.get("conversions")
        if not isinstance(conversions, list):
            return None
        current = {
            column.get("display_name"): str(column.get("type") or "").upper()
            for column in _dataview_metadata(service, dataset_id, view_id, project_id)
            if isinstance(column, dict)
        }
        kept, skipped = [], []
        for entry in conversions:
            name = entry.get("column") if isinstance(entry, dict) else None
            target = str(entry.get("to") or "").upper() if isinstance(entry, dict) else ""
            note = f"{name} (TEXT to {target})"
            if current.get(name) == "TEXT" and target in ("NUMERIC", "DATE") and note not in lossy:
                lossy.append(note)
        for entry in conversions:
            name = entry.get("column") if isinstance(entry, dict) else None
            target = str(entry.get("to") or "").upper() if isinstance(entry, dict) else ""
            if name is not None and target and current.get(name) == target:
                skipped.append({"column": name, "type": target})
            else:
                kept.append(entry)
        if not skipped:
            return None
        if not kept:
            return {
                "status": "no_change",
                "skipped": skipped,
                "note": "Every column already has the requested type; no task was added.",
            }
        call["conversions"] = kept
        skipped_record.extend(skipped)
        return None

    skipped_record: list[dict[str, Any]] = []
    lossy: list[str] = []

    def note_skipped(service: Any, dataset_id: int, state: Any, data: Any) -> Any:
        if skipped_record and isinstance(data, dict):
            data = {**data, "skipped": skipped_record}
        if lossy and isinstance(data, dict):
            data = {
                **data,
                "warnings": [
                    *(data.get("warnings") or []),
                    f"Converted {', '.join(lossy)}: values that do not parse (such as N/A or "
                    "text) become empty. Check the column with 'mammoth view data explore' "
                    "before relying on totals or averages.",
                ],
            }
        return data

    return _dispatch_view(
        invocation,
        view_id,
        "convert_type",
        prepare=drop_same_type,
        after=note_skipped,
        waits_for_run=True,
        **kwargs,
    )


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

    def guard_target(service: Any, dataset_id: int, call_kwargs: dict[str, Any]) -> None:
        target = call_kwargs.get("target_ds_id")
        mode = call_kwargs.get("save_as_mode")
        reject_dataset_export_conflicts(
            service,
            view_id,
            dataset_id,
            int(target) if target is not None else None,
            save_as_mode=mode if isinstance(mode, str) else None,
        )

    def name_persistence(_service: Any, _dataset_id: int, _state: Any, data: Any) -> Any:
        return {
            "dataset_id": data,
            "source_view_id": view_id,
            "refreshes_on_pipeline_run": True,
            "note": (
                f"This crosstab is a standing export on view {view_id}: it rewrites dataset "
                f"{data} on every pipeline run of that view, not just now."
            ),
        }

    return _dispatch_view(
        invocation, view_id, "crosstab", prepare=guard_target, after=name_persistence, **kwargs
    )


def _type_guard(
    invocation: Invocation,
    view_id: int,
    checks_for: Callable[[dict[str, Any], dict[str, str]], list[TypeCheck]],
) -> Callable[[Any, int, dict[str, Any]], Any]:
    """A ``prepare`` hook: refuse the step when a column it reads has the wrong type.

    ``checks_for(document, types)`` lists the columns to check from the input document and the
    view's ``{display name: type}`` map. A read that cannot run never blocks the write.
    """

    def check(service: Any, dataset_id: int, kwargs: dict[str, Any]) -> Any:
        types = _view_column_types(service, dataset_id, view_id, resolved_project(invocation))
        if types:
            check_column_types(view_id, types, checks_for(invocation.load_input() or {}, types))
        return None

    return check


def _view_column_types(
    service: Any, dataset_id: int, view_id: int, project_id: int | None
) -> dict[str, str]:
    """``{display name: type}`` of the view's columns; empty when the view cannot be read."""
    try:
        info = service.call(
            _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
        )
    except CliError:
        return {}
    return ImpactRead(
        service, dataset_id, view_id, project_id, apply_column_renames(info)
    ).column_types()


_DATE_ONLY = frozenset({DATE})


def _date_column_checks(*fields: str, operation: str) -> Callable[..., list[TypeCheck]]:
    def checks(document: dict[str, Any], types: dict[str, str]) -> list[TypeCheck]:
        return [
            TypeCheck(str(document[name]), _DATE_ONLY, operation)
            for name in fields
            if isinstance(document.get(name), str) and document[name] in types
        ]

    return checks


def _math_type_checks(document: dict[str, Any], types: dict[str, str]) -> list[TypeCheck]:
    return [
        TypeCheck(name, frozenset({NUMERIC, DATE}), "math")
        for name in math_columns(document.get("expression", ""), types)
    ]


def view_transform_date_diff(invocation: Invocation) -> HandlerResult:
    """Compute the difference between two dates. ``component``/``start``/``end`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "component")
    _require_field(document, "start")
    _require_field(document, "end")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    guard = _type_guard(
        invocation, view_id, _date_column_checks("start", "end", operation="date-diff")
    )
    return _dispatch_view(invocation, view_id, "date_diff", prepare=guard, **kwargs)


def view_transform_delete_columns(invocation: Invocation) -> HandlerResult:
    """Delete columns. ``columns`` is required. Prompt or ``--yes`` required."""
    view_id = _view_id(invocation)
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete columns on view {view_id}"
    )
    document = invocation.load_input()
    _require_field(document, "columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "delete_columns", **kwargs)


def view_transform_discard_duplicates(invocation: Invocation) -> HandlerResult:
    """Discard duplicate rows. ``ignore_columns`` or ``key_columns`` is optional.

    ``key_columns`` names the columns that make a row a duplicate (a duplicate
    order id, say); every other column is ignored. ``--dry-run`` counts the
    duplicates first: it reports ``predicted_impact``, or fails with ``no_op``
    when there are none (nothing to discard).
    """
    view_id = _view_id(invocation)
    document = dict(invocation.load_input() or {})
    key_columns = document.pop("key_columns", None)
    if key_columns is not None and document.get("ignore_columns"):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="Give key_columns or ignore_columns, not both.",
            exit_status=EXIT_USAGE,
        )
    kwargs = _bind_transform_inputs(invocation, document)
    measure_impact = _impact_check(invocation, view_id, measure_duplicates)

    def prepare(service: Any, dataset_id: int, call_kwargs: dict[str, Any]) -> Any:
        if key_columns is not None:
            call_kwargs["ignore_columns"] = _all_but_keys(
                service, invocation, dataset_id, view_id, key_columns
            )
        return measure_impact(service, dataset_id, call_kwargs)

    return _dispatch_view(
        invocation, view_id, "discard_duplicates", prepare=prepare, reduces_rows=True, **kwargs
    )


def _all_but_keys(
    service: Any, invocation: Invocation, dataset_id: int, view_id: int, key_columns: list[str]
) -> list[str]:
    """The view's other column names, so only ``key_columns`` decide what a duplicate is."""
    keys = list(key_columns)
    info = service.call(
        _DATAVIEW_GET_SYMBOL,
        dataset_id=dataset_id,
        dataview_id=view_id,
        project_id=resolved_project(invocation),
    )
    names = [str(c["display_name"]) for c in apply_column_renames(info).get("metadata") or []]
    unknown = [key for key in keys if key not in names]
    if not keys or unknown:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"key_columns must be existing column names; not found: {unknown or keys}.",
            hint=f"The view's columns are: {', '.join(names)}.",
            exit_status=EXIT_USAGE,
        )
    return [name for name in names if name not in keys]


def _stage_standing(invocation: Invocation, measured: Measured) -> None:
    """Let a step that changes no row today go ahead, and say so in the envelope."""
    if invocation.dry_run:
        report = {**measured.report, "standing": True, "note": STANDING_NOTE}
        object.__setattr__(invocation, "predicted_impact", report)
    else:
        object.__setattr__(invocation, "standing_noop", True)


def _impact_check(
    invocation: Invocation, view_id: int, measure: Measure
) -> Callable[[Any, int, dict[str, Any]], Any]:
    """A ``prepare`` hook: measure what the step would change, by a read.

    A count of zero is a no-op: ``--dry-run`` fails with ``no_op`` and a real run
    adds no task (``status: no_change``, like a same-type convert) unless
    ``--standing`` stages the step as a rule for future rows. Otherwise a
    dry run reports the count as ``predicted_impact``. A keep filter no row matches
    fails a dry run with ``empties_view`` unless ``--allow-empty`` is set. A count that cannot run
    is reported as unchecked in a dry run, never as zero, and never blocks a write.
    """

    def check(service: Any, dataset_id: int, kwargs: dict[str, Any]) -> Any:
        project_id = resolved_project(invocation)
        info = service.call(
            _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
        )
        read = ImpactRead(
            service,
            dataset_id,
            view_id,
            project_id,
            apply_column_renames(info),
            invocation.load_input() or {},
            invocation.dry_run,
        )
        try:
            measured = measure(read, kwargs)
        except CliError as exc:
            if invocation.dry_run:
                object.__setattr__(
                    invocation, "predicted_impact", {"checked": False, "reason": exc.message}
                )
            return None
        if measured.empties_message and invocation.dry_run and not invocation.allow_empty:
            raise empties_view_error(measured.empties_message, view_id=view_id)
        if measured.changes == 0:
            if invocation.standing:
                _stage_standing(invocation, measured)
                return None
            if invocation.dry_run:
                raise no_op_error(measured.no_op_message, view_id=view_id)
            return {
                "status": "no_change",
                "note": f"{measured.no_op_message} No task was added.",
                "hint": STANDING_HINT,
            }
        if invocation.dry_run:
            object.__setattr__(invocation, "predicted_impact", measured.report)
        return None

    return check


def view_transform_extract_date(invocation: Invocation) -> HandlerResult:
    """Extract a date component into a column. ``column``/``component`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    _require_field(document, "component")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    guard = _type_guard(
        invocation, view_id, _date_column_checks("column", operation="extract-date")
    )
    return _dispatch_view(invocation, view_id, "extract_date", prepare=guard, **kwargs)


def view_transform_fill_missing(invocation: Invocation) -> HandlerResult:
    """Fill missing values. ``column``/``direction`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    _require_field(document, "direction")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    prepare = _impact_check(invocation, view_id, measure_fill_missing)
    return _dispatch_view(invocation, view_id, "fill_missing", prepare=prepare, **kwargs)


def view_transform_filter(invocation: Invocation) -> HandlerResult:
    """Filter rows. ``condition`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, CONDITION_KWARG)
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    prepare = _impact_check(invocation, view_id, measure_filter)
    return _dispatch_view(
        invocation, view_id, "filter_rows", prepare=prepare, reduces_rows=True, **kwargs
    )


def _bind_view_table(
    service: Any, dataset_id: int, view_id: int, query: str, invocation: Invocation
) -> str:
    """The query with the view's own name as its table rewritten to ``"view:<id>"``.

    ``generate-sql`` names the table by the view's name; ``add-sql`` binds
    ``"view:<id>"`` (see ``schema get view.transform.add-sql``). A name that cannot be
    read leaves the query as generated.
    """
    try:
        info = service.call(
            _DATAVIEW_GET_SYMBOL,
            dataset_id=dataset_id,
            dataview_id=view_id,
            project_id=resolved_project(invocation),
        )
        name = info.get("name") if isinstance(info, dict) else getattr(info, "name", None)
    except Exception:  # noqa: BLE001 -- the generated query is still returned
        return query
    if not isinstance(name, str) or not name:
        return query
    pattern = re.compile(r'(\b(?:FROM|JOIN)\s+)"' + re.escape(name) + '"', re.IGNORECASE)
    return pattern.sub(lambda m: f'{m.group(1)}"view:{view_id}"', query)


def view_transform_generate_sql(invocation: Invocation) -> HandlerResult:
    """Generate a SQL query from a natural-language intent. ``intent`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "intent")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)

    def describe(service: Any, dataset_id: int, state: Any, data: Any) -> Any:
        # The route writes and validates a query but adds no task (release,
        # 2026-09-25); a bare string read as "done" by an agent that expected
        # the view to change. Say so, and give the command that applies it.
        if not isinstance(data, str):
            return data
        query = _bind_view_table(service, dataset_id, view_id, data, invocation)
        spec = json.dumps({"dataset_id": dataset_id, "query": query})
        project_id = resolved_project(invocation)
        scope = f" --project {project_id}" if project_id is not None else ""
        result = {
            "sql": data,
            "applied": False,
            "note": "The view is unchanged. Run 'apply' to add the query as a SQL task.",
            "apply": f"mammoth view transform add-sql {view_id} --input {shlex.quote(spec)}{scope}",
        }
        if query != data:
            result["apply_sql"] = query
        return result

    return _dispatch_view(invocation, view_id, "generate_sql", after=describe, **kwargs)


def view_transform_increment_date(invocation: Invocation) -> HandlerResult:
    """Increment a date column. ``column``/``delta`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    _require_field(document, "delta")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    guard = _type_guard(
        invocation, view_id, _date_column_checks("column", operation="increment-date")
    )
    return _dispatch_view(invocation, view_id, "increment_date", prepare=guard, **kwargs)


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
    project_id = invocation.project
    preview: dict[str, Any] = {}

    def before(service: Any, dataset_id: int) -> Any:
        if invocation.dry_run:
            preview.update(_join_preview(service, dataset_id, view_id, document, project_id))
        return join_snapshot(service, dataset_id, view_id, project_id)

    def after(service: Any, dataset_id: int, state: Any, data: Any) -> Any:
        # The join runs as a follow-on job; a pipeline read taken before it finishes
        # still shows the old view (no columns added, no rows to check).
        wait_for_followon_job(service, data)
        return with_join_check(
            data,
            state,
            join_after_snapshot(service, dataset_id, view_id, project_id, state),
            document,
            _join_preview(service, dataset_id, view_id, document, project_id),
        )

    try:
        return _dispatch_view(invocation, view_id, "join", before=before, after=after, **kwargs)
    except DryRunStop as stop:
        if preview:
            stop.record["join_preview"] = preview
        raise


def _join_preview(
    service: Any, dataset_id: int, view_id: int, document: dict[str, Any], project_id: int | None
) -> dict[str, Any]:
    """The dry run's key overlap; the other view's dataset is ``foreign_dataset_id``."""
    foreign, foreign_dataset = document.get("foreign_view"), document.get("foreign_dataset_id")
    if isinstance(foreign, dict):
        foreign_dataset = foreign_dataset or foreign.get("dataset_id")
        foreign = foreign.get("view_id", foreign.get("dataview_id", foreign.get("id")))
    if not isinstance(foreign, int) or not isinstance(foreign_dataset, int):
        return {"checked": False, "error": "foreign_view/foreign_dataset_id unknown"}
    return join_dry_run_preview(
        service, (dataset_id, view_id), (foreign_dataset, foreign), document, project_id
    )


def view_transform_json_extract(invocation: Invocation) -> HandlerResult:
    """Extract fields from a JSON column. ``column`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "json_extract", **kwargs)


def view_transform_limit_rows(invocation: Invocation) -> HandlerResult:
    """Limit the row count. ``n`` (or its alias ``limit``) is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "n")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "limit_rows", **kwargs)


def view_transform_repeat_rows(invocation: Invocation) -> HandlerResult:
    """Repeat every row. Exactly one of ``times``, ``values`` or ``series`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input() or {}
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "repeat_rows", **kwargs)


def view_transform_rename_columns(invocation: Invocation) -> HandlerResult:
    """Rename columns (a view display setting, not a task). ``renames`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "renames")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "rename_columns", **kwargs)


def view_column_format_set(invocation: Invocation) -> HandlerResult:
    """Set how columns display (date or number format; a view display setting, not a task)."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "formats")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "set_column_format", **kwargs)


def view_transform_sort(invocation: Invocation) -> HandlerResult:
    """Set the view's row order (a display setting, not a task). ``order_by`` is required.

    ``sort_by`` is accepted as its alias.
    """
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "order_by")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "sort_rows", **kwargs)


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
    _require_one_destination(document, invocation.command_id)
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "lookup", **kwargs)


def view_transform_math(invocation: Invocation) -> HandlerResult:
    """Evaluate a math expression into a column. ``expression`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "expression")
    assert document is not None
    _require_one_destination(document, invocation.command_id)
    return _math_into_column(invocation, view_id, document)


def _math_into_column(
    invocation: Invocation, view_id: int, document: dict[str, Any], **dispatch: Any
) -> HandlerResult:
    """The math write for a ``view transform math`` input ``document``, with its blank note."""
    kwargs = _bind_transform_inputs(invocation, document, "view.transform.math")
    blanks: dict[str, int] = {}

    guard = _type_guard(invocation, view_id, _math_type_checks)

    def count_blank_inputs(service: Any, dataset_id: int, _kwargs: dict[str, Any]) -> None:
        guard(service, dataset_id, _kwargs)
        blanks.update(
            _blank_math_inputs(
                service, dataset_id, view_id, resolved_project(invocation), document["expression"]
            )
        )

    data, meta = _dispatch_view(
        invocation, view_id, "math", prepare=count_blank_inputs, **dispatch, **kwargs
    )
    return _with_blank_input_note(data, blanks), meta


def _keep_data(service: Any, dataset_id: int, state: Any, data: Any) -> Any:
    """An ``after`` that adds nothing: the write is read back by waiting on its own task."""
    return data


def view_transform_update_column(invocation: Invocation) -> HandlerResult:
    """Overwrite a column with a math expression in one call; ``column``, ``expression`` required.

    ``view transform math`` with ``existing_column``, with the result waiting on
    its own task's run (a step staged in draft mode stays staged).
    """
    view_id = _view_id(invocation)
    document = invocation.load_input()
    column = _require_field(document, "column")
    _require_field(document, "expression")
    assert document is not None
    math_document = {
        **{key: value for key, value in document.items() if key != "column"},
        "existing_column": column,
    }
    return _math_into_column(
        invocation, view_id, math_document, after=_keep_data, waits_for_run=True
    )


#: The text up to the first whitespace: a person's first name, a path's first segment.
_FIRST_WORD_PATTERN = r"^\S+"


def view_transform_first_name(invocation: Invocation) -> HandlerResult:
    """Extract the first word of a text column, in one call. ``column`` is required.

    ``view transform substring`` with the first-word regex, with the same own-task
    wait as ``view transform update-column``.
    """
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    assert document is not None
    _require_one_destination(document, invocation.command_id)
    kwargs = _bind_transform_inputs(
        invocation, {**document, "regex_pattern": _FIRST_WORD_PATTERN}, "view.transform.substring"
    )
    return _dispatch_view(
        invocation,
        view_id,
        "substring",
        after=_keep_data,
        waits_for_run=True,
        **kwargs,
    )


def _blank_math_inputs(
    service: Any, dataset_id: int, view_id: int, project_id: int | None, expression: Any
) -> dict[str, int]:
    """Blank cells of each column a math expression names, for the columns that have any.

    Mammoth computes a blank input as 0, so ``qty * unit_price`` gives 0 for an
    unpriced row and a later total counts it with no warning (FB-01).
    """
    info = service.call(
        _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
    )
    read = ImpactRead(service, dataset_id, view_id, project_id, apply_column_renames(info))
    text = str(expression)
    named = [
        name
        for name in read.display_to_internal()
        if re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", text)
    ]
    try:
        counts = {
            name: read.count(compile_condition({"column": name, "operator": "IS_EMPTY"}))
            for name in named
        }
    except CliError:
        return {}  # A count that cannot run never blocks the write; it only drops the note.
    return {name: count for name, count in counts.items() if count}


def _with_blank_input_note(data: Any, blanks: dict[str, int]) -> Any:
    """``data`` with a ``blank_inputs`` note when a math input column has blanks."""
    if not blanks or not isinstance(data, dict):
        return data
    listed = ", ".join(f"{name} is blank in {count} row(s)" for name, count in blanks.items())
    note = (
        f"A blank input counts as 0 in this math step: {listed}, so the result there is "
        "computed as if it were 0. Fill or filter those rows first if a blank must not count as 0."
    )
    return {**data, "blank_inputs": {"columns": blanks, "note": note}}


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
    prepare = _impact_check(invocation, view_id, measure_replace)
    return _dispatch_view(invocation, view_id, "replace_values", prepare=prepare, **kwargs)


def view_transform_set_values(invocation: Invocation) -> HandlerResult:
    """Set values conditionally. ``values`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "values")
    assert document is not None
    _require_one_destination(document, invocation.command_id)
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
    _require_one_destination(document, invocation.command_id)
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "window", **kwargs)
