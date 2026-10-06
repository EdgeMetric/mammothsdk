"""Handlers for the ``batch`` command family (dataset-scoped).

Every batch operation targets a specific dataset: the dataset id is always the
first CLI positional argument, and — for the single-batch commands — the
batch id is the second positional argument. The project id comes from
``--project`` or the active project (mirroring ``folder.py``). Handlers
dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
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
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services.append_blank_columns import (
    BLANK_COLUMNS_FIELD,
    acknowledged_blank_columns,
)

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


def _int_positional_at(invocation: Invocation, index: int, name: str) -> int | None:
    """Parse the positional argument at ``index`` as an int, or return None."""
    if len(invocation.extra_args) <= index:
        return None
    raw = invocation.extra_args[index]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional_at(invocation: Invocation, index: int, name: str) -> int:
    """Return the required positional argument at ``index`` as an int, or raise."""
    value = _int_positional_at(invocation, index, name)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
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


def _meta(invocation: Invocation, workspace_id: int, project_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a batch command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Forward each field present in ``document`` into ``kwargs`` unchanged."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def batch_list(invocation: Invocation) -> HandlerResult:
    """List batches for a dataset in the active project."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataset_id": dataset_id, "project_id": project_id}
    _forward_optional(document, kwargs, ("limit", "offset"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def batch_get(invocation: Invocation) -> HandlerResult:
    """Get one batch by id for a dataset in the active project."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    batch_id = _require_int_positional_at(invocation, 1, "batch id")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), dataset_id=dataset_id, batch_id=batch_id, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


_DATASET_GET_SYMBOL = "mammoth.api.datasets.DatasetsAPI.get"


def _dataset_columns(service: Any, dataset_id: int, side: str) -> list[dict[str, Any]]:
    """The dataset's own schema rows (``c_name``, ``c_id``, ``c_type``), or raise.

    An unreadable schema is never treated as "no columns": the mapping check
    could not run, so the batch is not created.
    """
    response = service.call(_DATASET_GET_SYMBOL, dataset_id=dataset_id)
    dataset = response.get("dataset") if isinstance(response, dict) else None
    schema = dataset.get("data_schema") if isinstance(dataset, dict) else None
    if not isinstance(schema, list) or not all(
        isinstance(col, dict) and isinstance(col.get("c_name"), str) for col in schema
    ):
        raise CliError(
            code="append_schema_unreadable",
            message=f"Could not read the {side} dataset {dataset_id}'s schema before the batch.",
            hint=f"Read dataset {dataset_id} before creating the batch.",
            details={"side": side, "dataset_id": dataset_id},
        )
    return schema


def _mapping_items(mapping: Any) -> list[Any]:
    """Expand a ``{src: dst}`` mapping into ``ColumnNameMapping`` items, untyped."""
    if isinstance(mapping, dict):
        return [{"source_c_name": src, "destination_c_name": dst} for src, dst in mapping.items()]
    return list(mapping) if isinstance(mapping, list) else []


def _resolve_item(
    item: dict[str, Any], source: list[dict[str, Any]], dest: list[dict[str, Any]]
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """The (source, destination) schema rows an item names by name or id, else None."""
    by_id = "source_c_id" in item
    field, src_key, dest_key = (
        ("c_id", "source_c_id", "destination_c_id")
        if by_id
        else ("c_name", "source_c_name", "destination_c_name")
    )
    src_col = next((col for col in source if col.get(field) == item.get(src_key)), None)
    dest_col = next((col for col in dest if col.get(field) == item.get(dest_key)), None)
    return src_col, dest_col


def _reject_incomplete_batch_mapping(
    ids: tuple[int, int],
    source_names: set[str],
    mapped_sources: set[str],
    unknown: list[str],
) -> None:
    """Refuse a mapping that leaves source columns out or names a missing destination."""
    unmapped = sorted(source_names - mapped_sources)
    if not unmapped and not unknown:
        return
    dataset_id, source_id = ids
    problems = []
    if unknown:
        problems.append(f"destination column(s) not in dataset {dataset_id}: {', '.join(unknown)}")
    if unmapped:
        problems.append(f"source column(s) left unmapped and not appended: {', '.join(unmapped)}")
    raise CliError(
        code="append_mapping_incomplete",
        message=(
            f"mapping for appending dataset {source_id} into dataset {dataset_id} would corrupt "
            f"the append: {'; '.join(problems)}. Unmapped source columns are not appended."
        ),
        exit_status=EXIT_USAGE,
        hint=(
            f"Map every source column of dataset {source_id} to an existing column of dataset "
            f"{dataset_id}."
        ),
        details={"unknown_destinations": unknown, "unmapped_source_columns": unmapped},
    )


def _reject_type_change(item: dict[str, Any], dest_col: dict[str, Any], dataset_id: int) -> None:
    """Refuse an explicit expected type that differs from the destination's real one."""
    expected, actual = item.get("expected_destination_c_type"), dest_col.get("c_type")
    if expected is None or not actual or str(expected).upper() == str(actual).upper():
        return
    raise CliError(
        code="append_type_mismatch",
        message=(
            f"expected_destination_c_type {expected} for destination column "
            f"{dest_col['c_name']!r} of dataset {dataset_id} would change its type from "
            f"{actual}; the append would convert the whole destination column."
        ),
        exit_status=EXIT_USAGE,
        hint=(
            "Omit expected_destination_c_type (the CLI sends the destination's current "
            f"type, {actual})."
        ),
        details={"column": dest_col["c_name"], "expected": expected, "actual": actual},
    )


def _filled_destination_names(
    items: list[dict[str, Any]], dest: list[dict[str, Any]], source: list[dict[str, Any]]
) -> set[str]:
    """Destination column names some mapping item fills (``add_column`` items included)."""
    dest_names = {col["c_name"] for col in dest}
    filled: set[str] = set()
    for item in items:
        _, dest_col = _resolve_item(item, source, dest)
        if dest_col is not None:
            filled.add(dest_col["c_name"])
        elif item.get("action") == "add_column" and item.get("destination_c_name") in dest_names:
            filled.add(item["destination_c_name"])
    return filled


def _checked_batch_mapping(
    service: Any, dataset_id: int, source_id: int, mapping: Any, blank_columns: Any = None
) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate a batch mapping against both schemas; return typed items and warnings.

    Refuses unmapped source columns and unknown destinations (the backend appends
    only the mapped columns) and stamps every item with the destination's actual
    current type, so no destination column is silently re-typed. A mapped pair
    whose source and destination types differ is returned as a warning. A
    destination column no item fills is refused unless ``blank_columns`` names
    exactly those columns; the confirmed blanks are returned as a warning.
    """
    source = _dataset_columns(service, source_id, "source")
    dest = _dataset_columns(service, dataset_id, "target")
    items = [dict(item) for item in _mapping_items(mapping) if isinstance(item, dict)]
    typed: list[dict[str, Any]] = []
    mapped_sources: set[str] = set()
    unknown: list[str] = []
    warnings: list[str] = []
    for item in items:
        src_col, dest_col = _resolve_item(item, source, dest)
        if src_col is not None:
            mapped_sources.add(src_col["c_name"])
        if dest_col is None:
            if item.get("action") != "add_column":
                unknown.append(str(item.get("destination_c_name", item.get("destination_c_id"))))
            typed.append(item)
            continue
        _reject_type_change(item, dest_col, dataset_id)
        item.setdefault("expected_destination_c_type", dest_col.get("c_type"))
        typed.append(item)
        if src_col and src_col.get("c_type") and src_col["c_type"] != dest_col.get("c_type"):
            warnings.append(
                f"mapped column {src_col['c_name']!r} is {str(src_col['c_type']).lower()} but "
                f"destination column {dest_col['c_name']!r} is {str(dest_col['c_type']).lower()}"
            )
    _reject_incomplete_batch_mapping(
        (dataset_id, source_id), {col["c_name"] for col in source}, mapped_sources, unknown
    )
    blank = sorted({col["c_name"] for col in dest} - _filled_destination_names(typed, dest, source))
    return typed, acknowledged_blank_columns(dataset_id, blank, blank_columns) + warnings


def batch_create(invocation: Invocation) -> HandlerResult:
    """Create a batch for a dataset. ``source_id`` and ``mapping`` are required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    document = invocation.load_input()
    source_id = invocation.positional("source_id")
    if source_id is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="This command requires a source id argument.",
            exit_status=EXIT_USAGE,
        )
    source_id = int(source_id)
    mapping = _require_field(document, "mapping")
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "source_id": source_id,
        "mapping": mapping,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(
        document,
        kwargs,
        ("new_ds_params", "is_validation_required", "change_map", "delete_source_ds"),
    )
    # Deleting the source dataset is destructive, so gate it behind a
    # prompt/``--yes`` even though creating a batch is otherwise benign.
    if kwargs.get("delete_source_ds"):
        enforce_confirmation(
            invocation,
            policy=POLICY_PROMPT_OR_YES,
            action=f"create a batch on dataset {dataset_id} and DELETE the source dataset",
        )
    with open_service(invocation) as (service, auth):
        kwargs["mapping"], warnings = _checked_batch_mapping(
            service, dataset_id, source_id, mapping, document.get(BLANK_COLUMNS_FIELD)
        )
        data = service.call(_symbol(invocation), **kwargs)
    if warnings and isinstance(data, dict):
        data["mapping_check"] = {"warnings": warnings}
    return data, _meta(invocation, auth.workspace_id, project_id)


def batch_create_spec(invocation: Invocation) -> HandlerResult:
    """Create a batch using the release ``BatchesPostRequest`` envelope."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    document = invocation.load_input()
    if document is None:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="This command requires a JSON batch spec object.",
            exit_status=EXIT_USAGE,
        )
    if not isinstance(document, dict):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The batch spec must be a JSON object.",
            exit_status=EXIT_USAGE,
        )
    # ``dataset_id`` is positional context admitted by Invocation; it is not
    # part of the release BatchesPostRequest body.
    document = {key: value for key, value in document.items() if key != "dataset_id"}
    if document.get("delete_source_ds"):
        source_id = document.get("source_id")
        if source_id is None:
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message="delete_source_ds requires source_id for target confirmation.",
                exit_status=EXIT_USAGE,
            )
        from mammoth_cli.runtime.confirm import POLICY_CONFIRM_TARGET

        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            target=str(source_id),
            action=f"create a batch and delete source dataset {source_id}",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(
            "mammoth.api.batches.BatchesAPI.create_spec",
            dataset_id=dataset_id,
            spec=document,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def batch_update(invocation: Invocation) -> HandlerResult:
    """Apply patch operations to a dataset's batches. ``patch`` is required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    document = invocation.load_input()
    patch = _require_field(document, "patch")
    # A ``remove`` op deletes batches, so gate any patch containing one behind a
    # prompt/``--yes``; pure ``replace``/``add`` patches stay unconfirmed.
    if isinstance(patch, list) and any(
        isinstance(op, dict) and op.get("op") == "remove" for op in patch
    ):
        enforce_confirmation(
            invocation,
            policy=POLICY_PROMPT_OR_YES,
            action=f"remove batches of dataset {dataset_id}",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), dataset_id=dataset_id, patch=patch, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def batch_delete(invocation: Invocation) -> HandlerResult:
    """Delete one batch by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    batch_id = _require_int_positional_at(invocation, 1, "batch id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete batch {batch_id} of dataset {dataset_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), dataset_id=dataset_id, batch_id=batch_id, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def batch_bulk_delete(invocation: Invocation) -> HandlerResult:
    """Bulk-delete the named batches of a dataset. Prompt or ``--yes`` required.

    ``ids`` is required: the backend rejects a delete with no batch ids, it
    never deletes "all batches".
    """
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    document = invocation.load_input() or {}
    ids = _require_field(document, "ids")
    if not ids:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The 'ids' input field must name at least one batch id.",
            exit_status=EXIT_USAGE,
            hint=f"List batch ids with `mammoth batch list {dataset_id}`.",
        )
    count = len(ids) if isinstance(ids, list) else len(str(ids).split(","))
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete {count} batch(es) of dataset {dataset_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), dataset_id=dataset_id, project_id=project_id, ids=ids
        )
    return data, _meta(invocation, auth.workspace_id, project_id)
