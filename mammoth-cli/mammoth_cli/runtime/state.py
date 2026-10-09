"""Automatic write read-back: attach the write's new state to its result.

``with_verify`` (see :mod:`mammoth_cli.runtime.verify`) tells the caller
whether a write succeeded. It does not show what the write actually produced:
an export can report ``verified: true`` while the dataset it wrote has one of
four expected columns, and nothing in the result would say so. :func:`with_state`
closes that gap: every manifest command whose ``mutation_class`` is not
``read`` declares, in its command record, either a ``readback`` (a read
command plus how to source its arguments from this write's input/result, plus
a ``kind``) or a ``no_readback`` reason. After the write settles, the executor
runs the declared read and attaches a compact ``state`` block built from it --
never from the request, and never omitted: a read that fails still yields a
``state`` (``kind: unreadable``) rather than silence.

See ``CONTRACT-write-state.md`` (D-077) for the manifest shape this reads.
"""

from __future__ import annotations

import json
import time
from typing import Any

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.output.normalize import Revealed
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.positionals import resolve_positionals

#: Total JSON size a ``state`` block may reach before trimming kicks in.
STATE_SIZE_CAP_BYTES = 1500

#: Sample rows a ``kind: data`` state keeps, and the char length each cell is
#: truncated to -- row count and columns are never dropped to make room.
_SAMPLE_ROW_CAP = 5
_CELL_CHAR_CAP = 80

#: Input fields of a view edit that name the column(s) it wrote; the new
#: values of exactly those columns are echoed back (``renames`` maps old -> new).
_CHANGED_COLUMN_FIELDS = ("new_column", "existing_column", "column", "columns", "new_columns")
_CHANGED_VALUES_CAP = 8

_VIEW_GET_COMMAND = "view.get"
_VIEW_DATA_COMMAND = "view.data.get"
_VIEW_LIST_COMMAND = "view.list"

#: ``verify.state`` of a write that was accepted but has not finished.
_UNFINISHED_VERIFY_STATE = "processing"

_VIEW_TASK_LIST_COMMAND = "view.task.list"

#: A write answered ``status: staged`` (auto-run off) put its step in a draft.
_STAGED_STATUS = "staged"
_STAGED_DETAIL = (
    "Staged in the draft, not run: the live view is unchanged until 'view draft submit'."
)

#: The backend's answer to a data read of a step that has not produced data yet.
_STEP_NOT_RUN_YET = "no data for pipeline step"
_DATA_READ_ATTEMPTS = 6
_DATA_READ_RETRY_S = 2.0


def with_state(invocation: Invocation, data: Any) -> Any:
    """Return ``data`` with a ``state`` read-back block added, per the manifest.

    A command with no ``readback``/``no_readback`` declared yet (mid-rollout)
    is returned unchanged, as is a command that declares ``no_readback`` --
    there is nothing to read back, by the family owner's own account.
    """
    if not isinstance(data, dict):
        return data
    record = command_by_id(invocation.command_id) or {}
    readback = record.get("readback")
    if not isinstance(readback, dict):
        return data
    unfinished = _unfinished_state(data)
    if (
        unfinished is None
        and data.get("status") == _STAGED_STATUS
        and readback.get("kind") == "data"
    ):
        built = _staged_state(invocation, data, readback)
    else:
        built = unfinished or _build_state(invocation, data, readback)
    state = _enforce_cap(built)
    result = {**_unverified_if_unreadable(data, state), "state": state}
    return Revealed(result) if isinstance(data, Revealed) else result


def _unverified_if_unreadable(data: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """A write whose read-back failed is not verified, whatever its own response said."""
    verify = data.get("verify")
    if state.get("kind") != "unreadable" or not isinstance(verify, dict):
        return data
    if not verify.get("verified"):
        return data
    reason = (
        f"the read-back after this write failed ({state.get('reason')}); "
        "read the view before building on it"
    )
    return {**data, "verify": {**verify, "verified": False, "reason": reason}}


def _unfinished_state(data: dict[str, Any]) -> dict[str, Any] | None:
    """A write ``verify`` found still processing has no new state to read yet."""
    verify = data.get("verify")
    if not isinstance(verify, dict) or verify.get("state") != _UNFINISHED_VERIFY_STATE:
        return None
    return {
        "kind": "delivery",
        "read_by": "verify",
        "status": _UNFINISHED_VERIFY_STATE,
        "detail": verify.get("reason"),
    }


def _build_state(
    invocation: Invocation, data: dict[str, Any], readback: dict[str, Any]
) -> dict[str, Any]:
    read_command_id = str(readback["command"])
    kind = str(readback["kind"])
    ids_spec: dict[str, Any] = readback.get("ids") or {}
    resolved_ids: dict[str, Any] = {}
    try:
        resolved_ids = {
            name: _resolve_source(str(source), data, invocation)
            for name, source in ids_spec.items()
        }
        missing = [name for name, value in resolved_ids.items() if value is None]
        if missing:
            raise ValueError(f"could not resolve id(s) {missing} from the write's result/input")
        if kind == "data":
            return _data_state(resolved_ids, invocation)
        read_data = _call_read(read_command_id, resolved_ids, invocation)
        read_by = _read_by_label(read_command_id, resolved_ids)
        if kind == "object":
            return _object_state(read_by, read_data)
        if kind == "delivery":
            return _delivery_state(read_by, read_data)
        raise ValueError(f"unknown readback kind {kind!r}")
    except Exception as exc:  # noqa: BLE001 -- a read failure must surface, never crash the write
        read_by = _read_by_label(read_command_id, resolved_ids)
        reason = exc.message if isinstance(exc, CliError) else str(exc)
        return {"kind": "unreadable", "read_by": read_by, "reason": reason or type(exc).__name__}


def _read_by_label(command_id: str, resolved_ids: dict[str, Any]) -> str:
    representative = next(iter(resolved_ids.values()), None)
    return f"{command_id} {representative}" if representative is not None else command_id


# ---------------------------------------------------------------------------
# id resolution
# ---------------------------------------------------------------------------


def _resolve_source(source: str, data: dict[str, Any], invocation: Invocation) -> Any:
    """Resolve one ``ids`` value; ``a|b`` takes the first alternative that resolves.

    A write whose response comes in more than one shape (an export returns
    either ``{trigger_id, future_id}`` or ``{"job": {...}}``) names each place
    its id can be.
    """
    for alternative in source.split("|"):
        value = _resolve_one_source(alternative, data, invocation)
        if value is not None:
            return value
    return None


def _resolve_one_source(source: str, data: dict[str, Any], invocation: Invocation) -> Any:
    """Resolve one ``result.<path>`` | ``input.<field>`` | ``positional.<n>`` source."""
    if source.startswith("result."):
        return _get_path(data, source[len("result.") :])
    if source.startswith("input."):
        document = invocation.bound_input() or {}
        return _get_path(document, source[len("input.") :])
    if source.startswith("positional."):
        index_text = source[len("positional.") :]
        try:
            index = int(index_text)
        except ValueError:
            raise ValueError(f"invalid positional index in id source {source!r}") from None
        return invocation.extra_args[index] if index < len(invocation.extra_args) else None
    raise ValueError(f"unrecognized id source {source!r}")


def _get_path(root: Any, path: str) -> Any:
    current = root
    for segment in path.split("."):
        if isinstance(current, dict):
            current = current.get(segment)
        elif isinstance(current, list) and segment.isdigit():
            index = int(segment)
            current = current[index] if index < len(current) else None
        else:
            return None
    return current


# ---------------------------------------------------------------------------
# dispatching a read command's handler directly (never through the executor:
# this is an internal follow-up read, not a fresh command invocation)
# ---------------------------------------------------------------------------


def _read_invocation(command_id: str, resolved_ids: dict[str, Any], base: Invocation) -> Invocation:
    """Build the :class:`Invocation` a read command's handler expects.

    Ids that name a declared positional of ``command_id`` are supplied in
    order (matching how handlers read ``extra_args``); any id left over is
    offered as a pre-admitted ``--input`` document instead.
    """
    specs = resolve_positionals(command_id)
    positionals: dict[str, Any] = {}
    extra_args: list[str] = []
    for spec in specs:
        name = spec.name
        if name not in resolved_ids:
            break
        value = resolved_ids[name]
        # An id read from the write's own argv is text; the read's SDK method wants an int.
        if spec.type is int and isinstance(value, str) and value.isdigit():
            value = int(value)
        positionals[name] = value
        extra_args.append(str(value))
    document = {name: value for name, value in resolved_ids.items() if name not in positionals}
    invocation = Invocation(
        command_id=command_id,
        output="json",
        profile=base.profile,
        project=base.project,
        timeout=base.timeout,
        job_timeout=base.job_timeout,
        pipeline_timeout=base.pipeline_timeout,
        return_running=base.return_running,
        no_input=True,
        positionals=positionals,
        extra_args=extra_args,
        readback=True,
    )
    object.__setattr__(invocation, "_prepared_input", document or None)
    return invocation


def _call_read(command_id: str, resolved_ids: dict[str, Any], base: Invocation) -> Any:
    from mammoth_cli.commands.registry import HANDLERS

    handler = HANDLERS.get(command_id)
    if handler is None:
        raise LookupError(f"no handler registered for read command {command_id!r}")
    read_invocation = _read_invocation(command_id, resolved_ids, base)
    read_data, _meta = handler(read_invocation)
    return read_data


# ---------------------------------------------------------------------------
# kind: object
# ---------------------------------------------------------------------------


def _object_state(read_by: str, read_data: Any) -> dict[str, Any]:
    return {"kind": "object", "read_by": read_by, "object": _extract_object(read_data)}


def _extract_object(read_data: Any) -> Any:
    if not isinstance(read_data, dict):
        return read_data
    # A single-record read (``view.get``, ``dataset.get``, ...) carries its own
    # ``id`` at the top level; a listing read (``view.list``, ...) wraps its
    # items under a plural key instead. Checking for ``id`` first keeps a
    # record's own nested list fields (e.g. a dataview's ``metadata`` columns)
    # from being mistaken for the collection.
    if "id" not in read_data:
        listing = _first_list(read_data)
        if listing is not None:
            return [_scalar_fields(item) for item in listing]
    return _scalar_fields(read_data)


def _first_list(record: dict[str, Any]) -> list[Any] | None:
    """The first list-of-dicts value in a ``*.list`` read's result, if any."""
    for value in record.values():
        if isinstance(value, list) and (not value or isinstance(value[0], dict)):
            return value
    return None


def _scalar_fields(item: Any) -> Any:
    """Keep only an object's top-level scalar fields (every id is one)."""
    if not isinstance(item, dict):
        return item
    return {
        key: value
        for key, value in item.items()
        if value is None or isinstance(value, (str, int, float, bool))
    }


# ---------------------------------------------------------------------------
# kind: delivery
# ---------------------------------------------------------------------------


def _delivery_state(read_by: str, read_data: Any) -> dict[str, Any]:
    status: Any = None
    detail: Any = None
    if isinstance(read_data, dict):
        status = read_data.get("status")
        if status is None:
            job = read_data.get("job")
            status = job.get("status") if isinstance(job, dict) else None
        detail = read_data.get("message") or read_data.get("detail") or read_data.get("error")
    return {
        "kind": "delivery",
        "read_by": read_by,
        "status": status if isinstance(status, str) else None,
        "detail": str(detail) if detail is not None else None,
    }


# ---------------------------------------------------------------------------
# kind: data -- the write's output view: real columns, row count, 5 rows.
#
# No single read command returns columns+type, row_count and sample rows
# together, so this always makes two fixed internal reads once it has a
# view id: ``view.get`` for the typed columns and row count, ``view.data.get``
# for the sample. When the write's own ids only resolve a dataset id (a
# dataset/upload write, whose output is that dataset's first view), the
# view id is discovered with one ``view.list`` read first.
# ---------------------------------------------------------------------------


def _write_parent(base: Invocation, view_id: int | None) -> int | None:
    """The parent the write resolved, when the view read back is the view it wrote."""
    written = {_as_int(base.positional("view_id")), _as_int(base.positional("dataview_id"))}
    return base.known_dataset_id if view_id is not None and view_id in written else None


def _data_state(resolved_ids: dict[str, Any], base: Invocation) -> dict[str, Any]:
    view_id = _as_int(resolved_ids.get("view_id") or resolved_ids.get("dataview_id"))
    dataset_id = _as_int(resolved_ids.get("dataset_id")) or _write_parent(base, view_id)
    if view_id is None:
        if dataset_id is None:
            raise ValueError("readback kind 'data' needs a resolved view_id or dataset_id")
        view_id = _discover_view_id(dataset_id, base)
    view_ids: dict[str, Any] = {"view_id": view_id}
    if dataset_id is not None:
        view_ids["dataset_id"] = dataset_id
    info = _call_read(_VIEW_GET_COMMAND, view_ids, base)
    page = _read_data_once_run(view_ids, base)
    rows = page.get("data") if isinstance(page, dict) else None
    sample = [_trim_row(row) for row in (rows or [])[:_SAMPLE_ROW_CAP]]
    state: dict[str, Any] = {
        "kind": "data",
        "read_by": f"{_VIEW_DATA_COMMAND} {view_id}",
        "columns": _columns(info),
        "row_count": info.get("row_count") if isinstance(info, dict) else None,
        "sample": sample,
    }
    known = [column["name"] for column in state["columns"]]
    changed = changed_column_values(changed_columns(base.bound_input()), rows or [], known)
    if changed:
        state["changed_columns"] = changed
    return state


def _read_data_once_run(view_ids: dict[str, Any], base: Invocation) -> Any:
    """The view's data, waiting (bounded) for a step that has not run yet.

    Read right after a write, the new step may have no data yet; the read
    fails with "no data for pipeline step N ... yet" though the step runs a
    moment later (FB-18, FB-22). Any other failure is raised at once.
    """
    for attempt in range(_DATA_READ_ATTEMPTS):
        try:
            return _call_read(_VIEW_DATA_COMMAND, view_ids, base)
        except CliError as exc:
            if _STEP_NOT_RUN_YET not in exc.message or attempt == _DATA_READ_ATTEMPTS - 1:
                raise
            time.sleep(_DATA_READ_RETRY_S)
    raise AssertionError("unreachable")


def _staged_state(
    invocation: Invocation, data: dict[str, Any], readback: dict[str, Any]
) -> dict[str, Any]:
    """A draft write's read-back: the view's steps, and that the staged ones have not run.

    A staged step never ran, so its data cannot be read (FB-20: the agent got
    ``unreadable`` and polled four read commands to learn what it had staged).
    """
    ids_spec: dict[str, Any] = readback.get("ids") or {}
    resolved = {name: _resolve_source(str(src), data, invocation) for name, src in ids_spec.items()}
    view_id = _as_int(resolved.get("view_id") or resolved.get("dataview_id"))
    read_by = f"{_VIEW_TASK_LIST_COMMAND} {view_id}"
    try:
        if view_id is None:
            raise ValueError("a staged write's read-back needs the view id")
        info = _call_read(_VIEW_GET_COMMAND, {"view_id": view_id}, invocation)
        tasks = _call_read(_VIEW_TASK_LIST_COMMAND, {"dataview_id": view_id}, invocation)
    except Exception as exc:  # noqa: BLE001 -- a read failure must surface, never crash the write
        reason = exc.message if isinstance(exc, CliError) else str(exc)
        return {"kind": "unreadable", "read_by": read_by, "reason": reason or type(exc).__name__}
    return {
        "kind": "staged",
        "read_by": read_by,
        "detail": _STAGED_DETAIL,
        "live_row_count": info.get("row_count") if isinstance(info, dict) else None,
        "steps": [_step_summary(task) for task in _tasks_of(tasks)],
    }


def _tasks_of(read_data: Any) -> list[dict[str, Any]]:
    tasks = read_data.get("tasks") if isinstance(read_data, dict) else read_data
    return [task for task in tasks or [] if isinstance(task, dict)]


def _step_summary(task: dict[str, Any]) -> dict[str, Any]:
    params = task.get("params")
    if not isinstance(params, dict):
        params = {}
    return {"id": task.get("id"), "task": params.get("TASK_KEY"), "status": task.get("status")}


def changed_columns(document: Any) -> list[str]:
    """Names of the columns a view edit's input says it wrote."""
    if not isinstance(document, dict):
        return []
    names: list[str] = []
    for field in _CHANGED_COLUMN_FIELDS:
        value = document.get(field)
        names += (
            [value] if isinstance(value, str) else list(value) if isinstance(value, list) else []
        )
    renames = document.get("renames")
    if isinstance(renames, dict):
        names += list(renames.values())
    return list(dict.fromkeys(name for name in names if isinstance(name, str) and name))


def changed_column_values(names: list[str], rows: list[Any], known: list[str]) -> dict[str, Any]:
    """The first values of each named column as the view now holds them.

    A name the view no longer has (a deleted column, a typo) says so instead
    of vanishing, so the caller never mistakes silence for success.
    """
    present = set(known) | {key for row in rows if isinstance(row, dict) for key in row}
    return {
        name: (
            [
                _trim_cell(row.get(name))
                for row in rows[:_CHANGED_VALUES_CAP]
                if isinstance(row, dict)
            ]
            if name in present
            else "not a column of the view after this change"
        )
        for name in names
    }


def _discover_view_id(dataset_id: int, base: Invocation) -> int:
    listing = _call_read(_VIEW_LIST_COMMAND, {"dataset_id": dataset_id}, base)
    views = listing.get("dataviews") if isinstance(listing, dict) else None
    if not isinstance(views, list) or not views or not isinstance(views[0], dict):
        raise ValueError(f"dataset {dataset_id} has no view to read its new state from")
    view_id = views[0].get("id")
    if not isinstance(view_id, int):
        raise ValueError(f"dataset {dataset_id}'s first view has no usable id")
    return view_id


def _columns(info: Any) -> list[dict[str, str]]:
    if not isinstance(info, dict):
        return []
    metadata = info.get("metadata")
    if not isinstance(metadata, list):
        return []
    columns: list[dict[str, str]] = []
    for column in metadata:
        if not isinstance(column, dict):
            continue
        name = column.get("display_name") or column.get("internal_name")
        if name is None:
            continue
        columns.append({"name": str(name), "type": str(column.get("type") or "")})
    return columns


def _trim_row(row: Any) -> Any:
    if not isinstance(row, dict):
        return row
    return {key: _trim_cell(value) for key, value in row.items()}


def _trim_cell(value: Any) -> Any:
    if isinstance(value, str) and len(value) > _CELL_CHAR_CAP:
        return value[:_CELL_CHAR_CAP] + "..."
    return value


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value)
    return None


# ---------------------------------------------------------------------------
# size cap
# ---------------------------------------------------------------------------


def _enforce_cap(state: dict[str, Any]) -> dict[str, Any]:
    """Trim ``state`` under :data:`STATE_SIZE_CAP_BYTES`; never drop columns/row_count."""
    if _size(state) <= STATE_SIZE_CAP_BYTES:
        return state
    kind = state.get("kind")
    if kind == "data":
        sample = list(state.get("sample") or [])
        while sample and _size({**state, "sample": sample}) > STATE_SIZE_CAP_BYTES:
            sample.pop()
        return _trim_changed({**state, "sample": sample})
    if kind == "object":
        capped = {**state, "object": _capped_object(state)}
        original = state.get("object")
        if isinstance(original, list) and len(capped["object"]) < len(original):
            capped["object_total"] = len(original)
        return capped
    if kind == "delivery":
        detail = state.get("detail")
        if isinstance(detail, str):
            overflow = _size(state) - STATE_SIZE_CAP_BYTES
            keep = max(0, len(detail) - overflow - 3)
            return {**state, "detail": detail[:keep] + "..."}
    return state


def _trim_changed(state: dict[str, Any]) -> dict[str, Any]:
    """Shorten the changed-column value lists after the sample rows are gone."""
    changed = state.get("changed_columns")
    if not isinstance(changed, dict):
        return state
    keep = _CHANGED_VALUES_CAP
    while keep > 3 and _size(state) > STATE_SIZE_CAP_BYTES:
        keep -= 1
        changed = {k: v[:keep] if isinstance(v, list) else v for k, v in changed.items()}
        state = {**state, "changed_columns": changed}
    return state


def _capped_object(state: dict[str, Any]) -> Any:
    obj = state.get("object")
    if isinstance(obj, list):
        items = list(obj)
        while items and _size({**state, "object": items}) > STATE_SIZE_CAP_BYTES:
            items.pop()
        return items
    if isinstance(obj, dict):
        fields = dict(obj)
        protected = {key for key in fields if key == "id" or key.endswith("_id")}
        droppable = sorted(
            (key for key in fields if key not in protected),
            key=lambda key: len(str(fields[key])),
            reverse=True,
        )
        for key in droppable:
            if _size({**state, "object": fields}) <= STATE_SIZE_CAP_BYTES:
                break
            fields.pop(key, None)
        return fields
    return obj


def _size(value: Any) -> int:
    return len(json.dumps(value, default=str))
