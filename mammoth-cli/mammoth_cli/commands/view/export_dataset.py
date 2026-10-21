"""Dataset-export conflict and append-schema checks."""

from __future__ import annotations

import shlex
from typing import Any

from mammoth_cli.commands.view._common import (
    _DATAVIEW_GET_SYMBOL,
    _DISPLAY_NAME_KEY,
    _INTERNAL_NAME_KEY,
    _METADATA_KEY,
    apply_column_renames,
)
from mammoth_cli.commands.view.settle import (
    _PIPELINE_GET_SYMBOL,
)
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENTS,
    EXIT_USAGE,
    CliError,
)


def _source_column_names(service: Any, dataview_id: int, dataset_id: int | None) -> set[str]:
    """The source view's column display names; unreadable is an error, never "none"."""
    columns = service.call_view(dataview_id, "columns", dataset_id=dataset_id)
    if not isinstance(columns, dict):
        raise CliError(
            code="append_schema_unreadable",
            message=f"Could not read view {dataview_id}'s columns before the append.",
            hint="Read the source view before appending from it.",
            details={"side": "source", "dataview_id": dataview_id},
        )
    return set(columns)


def _blank_destination_columns(
    source_names: set[str], target_names: set[str], column_mapping: Any
) -> list[str]:
    """The destination columns an append leaves NULL: in the target, fed by nothing.

    That is a target column that is neither a source column (matched by name) nor a
    ``column_mapping`` destination. The one rule behind both the export-create
    acknowledgement and the rerun report.
    """
    mapping = column_mapping if isinstance(column_mapping, dict) else {}
    return sorted(target_names - source_names - set(mapping.values()))


def _reject_export_into_draft(service: Any, dataview_id: int, dataset_id: int) -> None:
    """Refuse a dataset export on a view whose changes are held in a draft.

    With auto-run off the view keeps new pipeline changes in a draft, so the
    export would only be staged and write nothing; the SDK then waits out its
    whole timeout for a write that cannot happen (eval T1-O-11).
    """
    pipeline = service.call(_PIPELINE_GET_SYMBOL, dataview_id=dataview_id, dataset_id=dataset_id)
    draft_mode = pipeline.get("draft_mode") if isinstance(pipeline, dict) else None
    if draft_mode in (None, "off"):
        return
    raise CliError(
        code="view_in_draft",
        message=(
            f"View {dataview_id} holds its changes in a draft (auto-run is off), so an "
            "export added now would be staged and write nothing."
        ),
        exit_status=EXIT_USAGE,
        hint=(
            f"Turn auto-run on with mammoth view draft auto-run {dataview_id} --input "
            "'{\"enabled\": true}', add the export, then turn auto-run off again if the "
            f"dataset should only update when asked (mammoth view pipeline rerun {dataview_id})."
        ),
        details={"dataview_id": dataview_id, "draft_mode": draft_mode},
    )


#: The name the SDK gives a branch-out dataset when none is given (the app's Branch out form's).
_DEFAULT_NEW_DATASET_NAME = "Result Dataset"


def _new_dataset_facts(name: Any, hidden_left_out: list[str]) -> dict[str, Any]:
    """What a dry run of an export into a NEW dataset says beyond the call: the dataset it
    creates, the source view's hidden columns it leaves out, and that the export stays on
    the view and writes again on every rerun. Read from what the export already looked up."""
    return {
        "creates_dataset": True,
        "new_dataset_name": name or _DEFAULT_NEW_DATASET_NAME,
        "hidden_columns_left_out": hidden_left_out,
        "standing_export": True,
    }


def _pending_dataset_export(error: CliError, view_id: int, project_id: int) -> dict[str, Any]:
    """A dataset export that was accepted but whose dataset id is not known yet.

    The export was submitted and the server is writing it (or has written it); only
    the lookup of its id ran out of time. That is not a failure, so say what is known
    and how to read the dataset when it lands, never an error.
    """
    name = error.details.get("dataset_name")
    pending: dict[str, Any] = {
        "status": "pending",
        "source_view_id": view_id,
        "project_id": project_id,
        "refreshes_on_pipeline_run": True,
        "note": (
            "The export was submitted and is still being written, so its dataset id is not "
            "known yet. Do not export again: that would create a second dataset. Look it up "
            f"in a moment with the next command (its source reads 'export of view {view_id}')."
        ),
    }
    if name is not None:
        pending["dataset_name"] = name
        pending["next"] = f"mammoth dataset find {shlex.quote(str(name))} --project {project_id}"
    if error.details.get("dataset_id") is not None:
        pending["dataset_id"] = error.details["dataset_id"]
    return pending


_EXPORTS_LIST_SYMBOL = "mammoth.api.exports.ExportsAPI.list"
_INTERNAL_DATASET_HANDLER_TYPE = "internal_dataset"


def _existing_internal_dataset_export(
    service: Any, dataview_id: int, dataset_id: int | None, target_ds_id: int
) -> Any | None:
    """This dataview's ``internal_dataset`` export already writing into
    ``target_ds_id``, if one exists (the most recent by id, when more than
    one somehow matches). ``None`` on no match.

    ``TARGET_DS_ID`` is compared as ``int``: the wire value can come back as
    a string, which would otherwise never match (mirrors the same int/str
    fix already applied to the SDK's own write-confirmation poll). A
    soft-deleted export (``status == ExportStatus.DELETED``) is never a
    match: the backend soft-deletes triggers rather than removing the row,
    and the list endpoint does not filter on status, so a deleted export
    would otherwise block every later export into that target forever.
    """
    from mammoth.models.exports import ExportStatus

    listing = service.call(
        _EXPORTS_LIST_SYMBOL,
        dataview_id=dataview_id,
        dataset_id=dataset_id,
        handler_type=_INTERNAL_DATASET_HANDLER_TYPE,
    )
    exports = getattr(listing, "exports", None) or []
    matches = [
        export
        for export in exports
        if export.status is not ExportStatus.DELETED
        and (target := (export.target_properties or {}).get("TARGET_DS_ID")) is not None
        and int(target) == target_ds_id
    ]
    return max(matches, key=lambda export: export.id or 0) if matches else None


def _hidden_column_names(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> list[str]:
    """Display names of the view's hidden columns, which a new-dataset export leaves out."""
    info = apply_column_renames(
        service.call(
            _DATAVIEW_GET_SYMBOL,
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    )
    if not isinstance(info, dict):
        return []
    display = info.get("display_properties")
    hidden = display.get("HIDDEN_COLUMNS") if isinstance(display, dict) else None
    if not isinstance(hidden, list) or not hidden:
        return []
    names = {
        column.get(_INTERNAL_NAME_KEY): column.get(_DISPLAY_NAME_KEY) or column.get("name")
        for column in info.get(_METADATA_KEY) or []
        if isinstance(column, dict)
    }
    return [str(names.get(column) or column) for column in hidden]


def reject_dataset_export_conflicts(
    service: Any,
    dataview_id: int,
    dataset_id: int,
    target_ds_id: int | None,
    save_as_mode: str | None = None,
) -> None:
    """Refuse a dataset export (or crosstab) that cannot write, or would double-write.

    Not into the view's own dataset, not from a view holding its changes in a
    draft, and not into a target this view already exports into. Each dataset
    export creates its own PERSISTENT trigger on the view, which re-runs on
    every pipeline run; REPLACE_IN_DS/APPEND_TO_DS only touch that trigger's OWN
    rows, so a second export into the same target is a second writer, not a
    refresh -- the fix is to rerun the pipeline, not to export again.
    """
    if target_ds_id is not None and target_ds_id == dataset_id:
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message="target_ds_id equals the view's own dataset.",
            exit_status=EXIT_USAGE,
            hint=(
                "A view cannot write into its own dataset. Export to a new "
                "dataset name (omit target_ds_id), or target a different dataset."
            ),
            details={"dataset_id": dataset_id, "target_ds_id": target_ds_id},
        )
    _reject_export_into_draft(service, dataview_id, dataset_id)
    if target_ds_id is None:
        return
    existing_export = _existing_internal_dataset_export(
        service, dataview_id, dataset_id, target_ds_id
    )
    if existing_export is not None:
        raise CliError(
            code="export_already_exists",
            message=(
                f"View {dataview_id} already exports into dataset "
                f"{target_ds_id} (export {existing_export.id}). This export "
                f"re-runs on every pipeline run, and {save_as_mode or 'REPLACE_IN_DS'} "
                "writes only its own rows -- a second export into the same target "
                "duplicates rows instead of refreshing them."
            ),
            exit_status=EXIT_USAGE,
            hint="Refresh the target by rerunning the pipeline, not by exporting again.",
            recovery_commands=[f"mammoth view pipeline rerun {dataview_id}"],
            details={
                "dataview_id": dataview_id,
                "target_ds_id": target_ds_id,
                "export_id": existing_export.id,
                "requested_save_as_mode": save_as_mode,
            },
        )


_DATASET_GET_SYMBOL = "mammoth.api.datasets.DatasetsAPI.get"


def _target_dataset_schema(service: Any, target_ds_id: int) -> dict[str, str]:
    """The target dataset's own schema: column display name -> type ('' if absent).

    ``dataset.get``'s ``data_schema`` is the dataset's base schema, not any
    view's live/rendered columns -- a view's own rename task can show a
    different display name than the dataset's schema still uses (evidence:
    a target view renamed 'Cust ID' -> 'cust_id' while the dataset's
    data_schema still said 'Cust ID'). The backend's own append-schema match
    (``match_existing_target_schema``) compares against this dataset-level
    schema, not a view's, so this check must too. An unreadable or
    malformed response is never treated as "no columns" -- fail loud,
    rather than let an append write past a check that could not actually
    run. The response nests the dataset under ``dataset``, and each schema
    column carries its name as ``c_name`` (``c_id`` is the internal id).
    """
    response = service.call(_DATASET_GET_SYMBOL, dataset_id=target_ds_id)
    dataset = response.get("dataset") if isinstance(response, dict) else None
    data_schema = dataset.get("data_schema") if isinstance(dataset, dict) else None
    if not isinstance(data_schema, list):
        raise CliError(
            code="append_schema_unreadable",
            message=f"Could not read target dataset {target_ds_id}'s schema before the append.",
            hint="Read the target dataset before appending to it.",
            details={"side": "target", "dataset_id": target_ds_id},
        )
    names: dict[str, str] = {}
    for column in data_schema:
        display_name = column.get("c_name") if isinstance(column, dict) else None
        if not isinstance(display_name, str):
            raise CliError(
                code="append_schema_unreadable",
                message=(f"Target dataset {target_ds_id}'s schema had a malformed column entry."),
                hint="Read the target dataset before appending to it.",
                details={"side": "target", "dataset_id": target_ds_id},
            )
        names[display_name] = str(column.get("c_type") or "")
    return names


def _reject_append_type_mismatch(
    source_types: Any,
    target_schema: dict[str, str],
    mapping: dict[str, str],
    ids: tuple[int, int],
) -> None:
    """Refuse an append where a column both sides name has a different type.

    The backend does not coerce: a same-named column of another type lands in
    a separate new column, splitting the data. Columns only on one side, or
    renamed through ``column_mapping``, are not compared; an unknown type
    (empty) on either side is not a mismatch.
    """
    if not isinstance(source_types, dict):
        return
    mismatched = {
        name: (str(source_types[name]).lower(), target_schema[name].lower())
        for name in sorted(source_types.keys() & target_schema.keys() - set(mapping))
        if source_types[name]
        and target_schema[name]
        and str(source_types[name]).lower() != target_schema[name].lower()
    }
    if not mismatched:
        return
    view_id, target_ds_id = ids
    listed = "; ".join(f"{n}: source {src}, target {tgt}" for n, (src, tgt) in mismatched.items())
    raise CliError(
        code="append_type_mismatch",
        message=(
            f"View {view_id} has column(s) whose type differs from target dataset "
            f"{target_ds_id}: {listed}. An append would create separate columns."
        ),
        exit_status=EXIT_USAGE,
        hint=(
            f"Run mammoth view transform convert-type on view {view_id} so each column "
            "matches the target type, then retry the export."
        ),
        details={"mismatched": {n: {"source": s, "target": t} for n, (s, t) in mismatched.items()}},
    )


def _reject_partial_append_mapping(
    source_names: set[str],
    target_names: set[str],
    mapping: dict[str, str],
    ids: tuple[int, int],
) -> None:
    """Refuse a non-empty append ``column_mapping`` that drops or invents columns.

    The backend maps every column by name when the mapping is empty, but uses
    a non-empty one as-is: unmapped source columns are not appended (their
    target cells stay NULL) and a destination the target lacks becomes a new
    column named after the source.
    """
    if not mapping:
        return
    unknown = {src: dest for src, dest in sorted(mapping.items()) if dest not in target_names}
    unmapped = sorted(source_names - set(mapping))
    if not unknown and not unmapped:
        return
    view_id, target_ds_id = ids
    problems = []
    if unknown:
        listed = ", ".join(f"{dest!r} (for {src!r})" for src, dest in unknown.items())
        problems.append(f"destination column(s) not in target dataset {target_ds_id}: {listed}")
    if unmapped:
        problems.append(f"source column(s) left unmapped and not appended: {', '.join(unmapped)}")
    raise CliError(
        code="append_mapping_incomplete",
        message=(
            f"column_mapping for appending view {view_id} into dataset {target_ds_id} would "
            f"corrupt the append: {'; '.join(problems)}. A non-empty column_mapping is used "
            "as-is: unmapped columns are not appended and an unknown destination creates a "
            "new column."
        ),
        exit_status=EXIT_USAGE,
        hint=(
            "Omit column_mapping to map all columns by name, or map every source column to "
            f"an existing column of dataset {target_ds_id}."
        ),
        details={
            "unknown_destinations": unknown,
            "unmapped_source_columns": unmapped,
            "target_columns": sorted(target_names),
        },
    )


def _mapped_type_warnings(
    source_types: Any, target_schema: dict[str, str], mapping: dict[str, str]
) -> list[str]:
    """Warn where a mapped source column's type differs from its target column's."""
    if not isinstance(source_types, dict):
        return []
    return [
        f"mapped column {src!r} is {str(source_types[src]).lower()} but target column "
        f"{dest!r} is {target_schema[dest].lower()}"
        for src, dest in sorted(mapping.items())
        if source_types.get(src)
        and target_schema.get(dest)
        and str(source_types[src]).lower() != target_schema[dest].lower()
    ]


def _reject_append_schema_mismatch(
    service: Any,
    dataview_id: int,
    dataset_id: int | None,
    target_ds_id: int,
    column_mapping: Any,
) -> tuple[list[str], list[str]]:
    """Refuse an ``APPEND_TO_DS``/``REPLACE_IN_DS`` export into an existing target
    whose source has a column the target
    dataset's schema does not, and ``column_mapping`` does not cover.

    A non-empty ``column_mapping`` is stricter: the backend then copies only
    the mapped columns and turns an unknown destination into a new column, so
    every source column must be mapped to a column the target already has
    (``_reject_partial_append_mapping``).

    An append writes into rows the target dataset already has; a source
    column with no home in the target schema and no explicit mapping would
    otherwise reach the backend as a malformed write. Checked here, before
    the call, so the refusal costs nothing and names exactly what to fix.

    Returns the target-only column names (present in the target schema, not
    in the source, not a ``column_mapping`` destination) and the type
    warnings for mapped pairs -- both allowed, but worth a warning.
    """
    source_names = _source_column_names(service, dataview_id, dataset_id)
    target_schema = _target_dataset_schema(service, target_ds_id)
    target_names = set(target_schema)
    mapping = column_mapping if isinstance(column_mapping, dict) else {}
    # View.columns (mammoth/view.py) maps display name -> internal name; these
    # dict keys are display names, matching what the backend's own schema
    # match compares by -- never the internal ids in the dict's values.
    _reject_partial_append_mapping(source_names, target_names, mapping, (dataview_id, target_ds_id))
    source_only = sorted(source_names - target_names - set(mapping))
    target_only = _blank_destination_columns(source_names, target_names, mapping)
    source_types = service.call_view(dataview_id, "column_types", dataset_id=dataset_id)
    _reject_append_type_mismatch(source_types, target_schema, mapping, (dataview_id, target_ds_id))
    if source_only:
        raise CliError(
            code="append_schema_mismatch",
            message=(
                f"View {dataview_id} has column(s) the target dataset {target_ds_id} "
                f"does not: {', '.join(source_only)}."
            ),
            exit_status=EXIT_USAGE,
            hint=(
                "Map these in column_mapping (source column -> an existing target "
                "column), or rename them in the source view to match the target schema."
            ),
            details={"source_only": source_only, "target_only": target_only},
        )
    return target_only, _mapped_type_warnings(source_types, target_schema, mapping)
