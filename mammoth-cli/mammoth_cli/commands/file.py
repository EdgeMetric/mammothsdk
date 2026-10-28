"""Handlers for the ``file`` command family.

Files are workspace-level resources: none of the reviewed manifest signatures
in this family take a ``project_id`` argument, so no handler here requires an
active project. The (optional) active project is still reported in the
envelope metadata for context, mirroring the read handlers in
:mod:`mammoth_cli.commands.project`. Handlers dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.view.upload import upload_preview
from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    CODE_UPLOAD_REFUSED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import parents
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
from mammoth_cli.runtime.dryrun import plan_call
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project
from mammoth_cli.services import update_method
from mammoth_cli.services.command_contract import bind_command_inputs
from mammoth_cli.services.delete_check import ensure_deleted
from mammoth_cli.services.paging import listing_with_paging
from mammoth_cli.services.poll import poll_delays


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


def _string_positional(invocation: Invocation) -> str | None:
    """Return the first positional argument, or None if absent."""
    return invocation.extra_args[0] if invocation.extra_args else None


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
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    if document is None or field not in document:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def file_list(invocation: Invocation) -> HandlerResult:
    """List files, optionally filtered and paginated."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(
        document,
        kwargs,
        (
            "fields",
            "file_ids",
            "names",
            "statuses",
            "created_at",
            "updated_at",
            "limit",
            "offset",
            "sort",
        ),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    data = listing_with_paging(
        data,
        key="files",
        command="mammoth file list",
        project=invocation.project,
        requested=kwargs,
    )
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def file_get(invocation: Invocation) -> HandlerResult:
    """Get one file by id."""
    file_id = _require_int_positional(invocation, "file id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"file_id": file_id}
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def file_update(invocation: Invocation) -> HandlerResult:
    """Apply a patch request to one file. File id is positional."""
    file_id = _require_int_positional(invocation, "file id")
    document = invocation.load_input()
    patch_request = _require_field(document, "patch_request")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), file_id=file_id, patch_request=patch_request)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def file_set_password(invocation: Invocation) -> HandlerResult:
    """Set a file's password. High-impact: requires ``--yes --confirm FILE_ID``."""
    file_id = _require_int_positional(invocation, "file id")
    document = invocation.load_input()
    password = _require_field(document, "password")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"set the password on file {file_id}",
        target=str(file_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), file_id=file_id, password=password)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def file_extract_sheets(invocation: Invocation) -> HandlerResult:
    """Extract named sheets from a file. File id is positional."""
    file_id = _require_int_positional(invocation, "file id")
    document = invocation.load_input()
    sheets = _require_field(document, "sheets")
    kwargs: dict[str, Any] = {"file_id": file_id, "sheets": sheets}
    assert document is not None
    _forward_optional(document, kwargs, ("delete_file_after_extract", "combine_after_extract"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def file_multi_sheet_preview(invocation: Invocation) -> HandlerResult:
    """Preview how one sheet of a multi-sheet file reads. File id is positional."""
    file_id = _require_int_positional(invocation, "file id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "file_id": file_id,
        "sheet_name": _require_field(document, "sheet_name"),
    }
    _forward_optional(document, kwargs, ("block_id", "user_instruction", "structure_map"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def file_multi_sheet_extract(invocation: Invocation) -> HandlerResult:
    """Create datasets from accepted sheet reads of a multi-sheet file. File id is positional."""
    file_id = _require_int_positional(invocation, "file id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"file_id": file_id, "tables": _require_field(document, "tables")}
    _forward_optional(document, kwargs, ("delete_file_after_extract",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def file_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one file by id. Prompt or ``--yes`` required."""
    file_id = _require_int_positional(invocation, "file id")
    enforce_confirmation(invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete file {file_id}")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), file_id=file_id)
        # The route answers with no body; read the file back so the result says it is gone.
        ensure_deleted(
            service,
            noun="file",
            resource_id=file_id,
            read_symbol="mammoth.api.files.FilesAPI.get",
            read_kwargs={"file_id": file_id},
            responses=(data,),
        )
    result = {**data} if isinstance(data, dict) else {}
    return {**result, "file_id": file_id, "deleted": [file_id]}, _meta(
        invocation, auth.workspace_id, resolved_project(invocation)
    )


def file_bulk_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete several files by id. Prompt or ``--yes`` required."""
    document = invocation.load_input()
    file_ids = _require_field(document, "file_ids")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete {len(file_ids)} files",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), file_ids=file_ids)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def file_upload(invocation: Invocation) -> HandlerResult:
    """Upload local files: one path as the argument, several via the ``files`` input field."""
    document = invocation.load_input() or {}
    # ``mode`` and ``sheets`` belong to this handler, not to the SDK call: take them out
    # before the inputs are bound.
    mode = document.get("mode")
    sheets = document.get("sheets")
    document = {k: v for k, v in document.items() if k not in ("mode", "sheets")}
    if mode is not None and document.get("append_to_ds_id") is None:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="'mode' only applies when 'append_to_ds_id' is set.",
            exit_status=EXIT_USAGE,
            hint=(
                "It sets the update method of the dataset the file goes into: pass "
                '--input \'{"append_to_ds_id": 123, "mode": "replace"}\'.'
            ),
            details={"field": "mode"},
        )
    wanted_mode = update_method.parse_mode(mode) if mode is not None else None
    # ``files`` is intentionally dual-sourced: explicit paths are expanded to
    # the SDK's list form and take precedence over the same input field.
    kwargs = bind_command_inputs(
        invocation.command_id,
        document,
        **({"files": list(invocation.extra_args)} if invocation.extra_args else {}),
    )
    _require_local_files(kwargs.get("files"))
    if not kwargs.get("files"):
        appending = kwargs.get("append_to_ds_id") is not None
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=(
                "This command requires 'files' when append_to_ds_id is set."
                if appending
                else "A file path is required."
            ),
            exit_status=EXIT_USAGE,
            hint=(
                "Pass one path as the argument (mammoth file upload ./data.csv), or several "
                'with --input \'{"files": ["a.csv", "b.csv"]}\'.'
            ),
        )
    with open_service(invocation) as (service, auth):
        # When the caller opts out of waiting (``wait_for_completion: false``)
        # the bare job id is returned unchanged.
        if not document.get("wait_for_completion", True):
            data = service.call(_symbol(invocation), **kwargs)
            return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
        # The SDK waits for the upload job; ``upload_result`` also returns the
        # files the server refused, which the bare id list of ``upload`` drops.
        target = kwargs.get("append_to_ds_id")
        project_id = resolved_project(invocation)
        mode_change: dict[str, Any] | None = None
        previous_mode: str | None = None
        if wanted_mode is not None and target is not None:
            set_args = {"dataset_id": target, "mode": wanted_mode, "project_id": project_id}
            if invocation.dry_run:
                # Report the mode change beside the upload the gate stops at, without making it.
                plan_call(service, update_method.SET_SYMBOL, set_args)
                mode_in_effect: dict[str, Any] | None = {
                    "mode": "add" if wanted_mode == "combine" else wanted_mode,
                    "effect": update_method.EFFECTS[wanted_mode],
                }
            else:
                # The backend reads the dataset's mode when the file lands, so set it first.
                changed = service.call(update_method.SET_SYMBOL, **set_args)
                mode_change = update_method.describe(changed, target)
                previous_mode = mode_change.get("previous_mode")
                mode_in_effect = mode_change
        else:
            # No mode asked for: the dataset's stored mode decides whether the upload adds a
            # batch or replaces the rows, and the undo depends on which.
            mode_in_effect = _stored_mode(service, target, project_id) if target else None
        rows_before = _dataset_rows(service, target) if target is not None else None
        batches_before = _batch_rows(service, target, project_id) if target is not None else None
        try:
            outcome = service.call(_UPLOAD_RESULT_SYMBOL, **kwargs)
            data = (
                [target]
                if target is not None and outcome["dataset_ids"]
                else outcome["dataset_ids"]
            )
            if target is not None and data:
                # The upload job ends when the staging dataset is made; the rows reach the
                # target after that, while it reads 'processing' (found by recipe run, live).
                target_ready = _wait_until_ready(service, target)
            refused = _refused_files(outcome.get("errors"))
            if outcome.get("errors") and not data:
                raise _upload_refused_error(outcome["errors"], refused)
        except Exception as failure:
            if mode_change is not None and target is not None:
                _restore_mode(service, failure, target, previous_mode, project_id)
            raise
        # A finished upload job does not mean a usable dataset: a CSV with an
        # ambiguous date column lands in ``need_action`` with no view. Report
        # the status the platform holds for each dataset, not an assumed one.
        result = _upload_result(
            data,
            lambda dataset_id: _dataset_status(service, dataset_id),
            files=outcome.get("files"),
        )
        warnings: list[str] = []
        if mode_change is not None:
            warnings.append(
                f"Dataset {target} now has the update method '{mode_change['mode']}', and it "
                "keeps it: every later upload into it follows it too."
            )
        if target is not None and data:
            result["update_method"] = _update_method_entry(mode_in_effect)
            if mode_in_effect is None:
                warnings.append(
                    f"The update method of dataset {target} could not be read, so it is not "
                    "known whether this upload added a batch or replaced the rows; "
                    "'history undo' will not delete anything for it."
                )
        if target is not None and data:
            # The upload made a staging dataset the backend already deleted; the result is
            # the dataset the rows were appended to. The batch it added is what to undo.
            rows_after = _dataset_rows(service, target)
            result["appended_to"] = target
            # Deprecated: kept for one more release; read ``batch_ids`` or ``appended_to``.
            result["staging_dataset_ids"] = list(outcome["dataset_ids"])
            ours, unmatched = _batches_of_upload(
                batches_before or [],
                _batch_rows(service, target, project_id),
                _sent_names(kwargs.get("files")),
                outcome["dataset_ids"],
            )
            result["batch_ids"] = ours
            if unmatched:
                result["unmatched_batch_ids"] = unmatched
                warnings.append(
                    f"Batches {unmatched} appeared in dataset {target} during the upload but "
                    "none could be tied to the uploaded file by name, so they are not listed "
                    "in batch_ids and 'history undo' will not delete them."
                )
            if rows_before is not None and rows_after is not None:
                result.update(
                    rows_before=rows_before,
                    rows_after=rows_after,
                    rows_added=rows_after - rows_before,
                )
        if target is not None and data and not target_ready:
            # The rows may still be on their way: rows_added is what had landed by now.
            result["append_pending"] = True
            warnings.append(
                f"Dataset {target} was still processing after {_APPEND_WAIT_S:.0f} s, so the "
                f"appended rows may not be in it yet. Check with 'mammoth dataset get {target}' "
                "before using it."
            )
        if refused:
            warnings.append(_upload_refused_message(outcome["errors"], refused))
            result["refused_files"] = refused
        if outcome.get("files_error"):
            warnings.append(
                "The project's file list could not be read after the upload, so a file that "
                f"waits on a choice (sheets, a password) is not shown: {outcome['files_error']}. "
                "Check with 'mammoth file list'."
            )
        if warnings:
            result["warnings"] = warnings
        _mark_partial_upload(result, bool(refused))
        if sheets is not None:
            _extract_chosen_sheets(service, result, sheets)
        previewed = 0
        for entry in result["datasets"]:
            if entry.get("status") != "ready" or target is not None:
                # An append lands in a dataset whose views already exist; no preview.
                continue
            if previewed >= _UPLOAD_PREVIEW_LIMIT:
                entry["preview_skipped"] = (
                    f"Only the first {_UPLOAD_PREVIEW_LIMIT} datasets are previewed; "
                    f"run 'view list {entry['id']}' to see this one."
                )
                continue
            previewed += 1
            preview = upload_preview(service, int(entry["id"]), project_id)
            if "preview_error" in preview:
                entry["preview_error"] = preview["preview_error"]
            else:
                entry["view"] = preview
                parents.remember(
                    invocation.profile or profiles.get_selected(),
                    auth.workspace_id,
                    {preview["view_id"]: int(entry["id"])},
                )
    return result, _meta(invocation, auth.workspace_id, resolved_project(invocation))


_BATCH_LIST_SYMBOL = "mammoth.api.batches.BatchesAPI.list"
_EXTRACT_SHEETS_SYMBOL = "mammoth.api.files.FilesAPI.extract_sheets"
_BATCH_PAGE = 100


def _batch_rows(service: Any, dataset_id: int, project_id: int | None) -> list[dict[str, Any]]:
    """Every batch row of a dataset, in listing order, paging through the listing.

    Args:
        service: The SDK service.
        dataset_id: The dataset whose batches to read.
        project_id: The active project, or None for the client default.

    Returns:
        The batch rows (each with an int ``id``); empty when the listing cannot be read.
    """
    found: list[dict[str, Any]] = []
    offset = 0
    while True:
        kwargs: dict[str, Any] = {"dataset_id": dataset_id, "limit": _BATCH_PAGE, "offset": offset}
        if project_id is not None:
            kwargs["project_id"] = project_id
        try:
            response = service.call(_BATCH_LIST_SYMBOL, **kwargs)
        except CliError:
            return found
        rows = response.get("batches") if isinstance(response, dict) else response
        rows = rows if isinstance(rows, list) else []
        seen = {row["id"] for row in found}
        found.extend(
            r
            for r in rows
            if isinstance(r, dict) and isinstance(r.get("id"), int) and r["id"] not in seen
        )
        if len(rows) < _BATCH_PAGE:
            return found
        offset += _BATCH_PAGE


def _sent_names(files: Any) -> list[str]:
    """The base names of the files an upload sends (paths, or file objects with a name)."""
    names: list[str] = []
    for item in files if isinstance(files, list) else [files]:
        raw = item if isinstance(item, (str, Path)) else getattr(item, "name", None)
        if isinstance(raw, (str, Path)) and str(raw):
            names.append(Path(str(raw)).name)
    return names


def _batch_labels(row: dict[str, Any]) -> set[str]:
    """The lower-case names a batch row carries for its source: file name, name, dataset name."""
    source = row.get("source")
    source = source if isinstance(source, dict) else {}
    labels = (source.get("file_name"), source.get("name"), source.get("ds_name"), row.get("name"))
    return {Path(label).name.lower() for label in labels if isinstance(label, str) and label}


def _batches_of_upload(
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    sent_names: list[str],
    staging_ids: list[int],
) -> tuple[list[int], list[int]]:
    """Tell the batches this upload added from the ones that merely appeared meanwhile.

    The backend appends a staging dataset into the target and records it as the batch's
    source, so a new batch is this upload's only when its source names a file this upload
    sent (or the staging dataset made from it). Any other new batch (a folder automation,
    another user) is reported apart and never put up for undo.

    Args:
        before: The batch rows before the upload.
        after: The batch rows after it.
        sent_names: Base names of the files sent.
        staging_ids: The staging dataset ids the upload job made.

    Returns:
        ``(batch ids of this upload, new batch ids that could not be tied to it)``.
    """
    known = {row["id"] for row in before}
    new = [row for row in after if row["id"] not in known]
    wanted = {name.lower() for name in sent_names} | {Path(n).stem.lower() for n in sent_names}
    ours: list[int] = []
    unmatched: list[int] = []
    for row in new:
        source = row.get("source")
        linked = isinstance(source, dict) and source.get("datasource_id") in staging_ids
        if (
            linked
            or _batch_labels(row) & wanted
            or {Path(n).stem for n in _batch_labels(row)} & wanted
        ):
            ours.append(row["id"])
        else:
            unmatched.append(row["id"])
    return ours, unmatched


def _stored_mode(service: Any, dataset_id: int, project_id: int | None) -> dict[str, Any] | None:
    """The dataset's stored update method as ``update_method.describe`` shapes it, or None.

    Args:
        service: The SDK service.
        dataset_id: The dataset an upload appends to.
        project_id: The active project, or None.

    Returns:
        The described mode; None when the read fails, so the caller does not guess.
    """
    try:
        stored = service.call(
            update_method.GET_SYMBOL, dataset_id=dataset_id, project_id=project_id
        )
    except CliError:
        return None
    return update_method.describe(stored, dataset_id)


def _update_method_entry(mode: dict[str, Any] | None) -> dict[str, Any]:
    """The result's ``update_method``: the mode in effect for the upload, or unknown."""
    if mode is None:
        return {"mode": None, "effect": "Unknown: the dataset's update method could not be read."}
    entry: dict[str, Any] = {"mode": mode["mode"], "effect": mode["effect"]}
    if mode.get("previous_mode") is not None:
        entry["previous_mode"] = mode["previous_mode"]
    return entry


def _restore_mode(
    service: Any,
    failure: Exception,
    dataset_id: int,
    previous_mode: str | None,
    project_id: int | None,
) -> None:
    """Put the dataset's update method back after the upload that needed it failed.

    Args:
        service: The SDK service.
        failure: The error being raised; gains a note in its details when the mode stays.
        dataset_id: The dataset whose mode was changed.
        previous_mode: Its mode before the change (``add`` or ``replace``), or None.
        project_id: The active project, or None.
    """
    note = (
        f"Dataset {dataset_id} kept the new mode this upload gave it, because the old one "
        "could not be restored"
    )
    try:
        if previous_mode is None:
            raise CliError(code="unknown", message="the previous mode is not known")
        service.call(
            update_method.SET_SYMBOL,
            dataset_id=dataset_id,
            mode=update_method.parse_mode(previous_mode),
            project_id=project_id,
        )
    except CliError as restore_failure:
        if isinstance(failure, CliError):
            failure.details["update_method_kept"] = f"{note} ({restore_failure.message})."


def _extract_chosen_sheets(service: Any, result: dict[str, Any], sheets: Any) -> None:
    """Extract the caller's sheets from the one workbook waiting for a choice.

    Args:
        service: The SDK service.
        result: The upload result; gains ``extract_sheets`` (the extraction job) and a
            message, or a warning when no single workbook is waiting.
        sheets: The ``sheets`` input: a list of sheet names.

    Raises:
        CliError: ``invalid_argument`` when ``sheets`` is not a list of names.
    """
    if not isinstance(sheets, list) or not sheets or not all(isinstance(s, str) for s in sheets):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="'sheets' must be a non-empty list of sheet names.",
            exit_status=EXIT_USAGE,
            details={"field": "sheets"},
        )
    waiting = [f for f in result.get("files", []) if f.get("action_needed") == _SHEETS_ACTION]
    if len(waiting) != 1:
        result.setdefault("warnings", []).append(
            "'sheets' was ignored: it applies only when exactly one uploaded file waits for a "
            f"sheet choice, and {len(waiting)} did."
        )
        return
    file_id = waiting[0]["file_id"]
    result["extract_sheets"] = service.call(_EXTRACT_SHEETS_SYMBOL, file_id=file_id, sheets=sheets)
    result["message"] = (
        f"Extracting {', '.join(sheets)} from file {file_id}; the datasets appear when the job "
        "ends. Check with 'mammoth file list'."
    )
    result["next_command"] = "mammoth file list"


_UPLOAD_FAILED_STATUSES = frozenset({"error", "failed", "failure"})


def _mark_partial_upload(result: dict[str, Any], has_refused: bool) -> None:
    """Make a mixed upload ``partial``: some files became datasets and some did not.

    A dataset the backend marked ``error`` (an empty file, say) carries its own reason in
    ``status_info``; that reason goes into ``warnings`` so each file's outcome is readable.
    """
    datasets = result["datasets"]
    failed = [d for d in datasets if str(d.get("status")).lower() in _UPLOAD_FAILED_STATUSES]
    if not failed and not has_refused:
        return
    if len(failed) == len(datasets) and not has_refused:
        return  # nothing worked: keep the plain failure
    warnings = list(result.get("warnings", []))
    for entry in failed:
        info = entry.get("status_info")
        said = " ".join(str(v) for v in info.values()) if isinstance(info, dict) else ""
        label = entry.get("name") or f"dataset {entry['id']}"
        warnings.append(f"{label} failed to load: {said or 'the backend gave no reason'}.")
    if not any(d.get("status") == "ready" for d in datasets):
        return
    result["partial"] = True
    result["status"] = "partial"
    result["warnings"] = warnings


#: Uploaded datasets one ``file upload`` previews (several requests each).
_UPLOAD_PREVIEW_LIMIT = 5


def _require_local_files(files: Any) -> None:
    """Fail as a usage error, naming the path, when a local file is missing.

    The SDK raises a bare ``ValueError`` for an unreadable path, which the
    generic mapping renders as an opaque ``api_error``; a relative path from
    the wrong working directory is the usual cause and must say so.
    """
    candidates = files if isinstance(files, list) else [files] if files else []
    for candidate in candidates:
        if not isinstance(candidate, str):
            continue
        path = Path(candidate).expanduser()
        if path.is_dir():
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"{candidate} is a directory, not a file.",
                exit_status=EXIT_USAGE,
                hint=f"Use 'mammoth file upload-folder {candidate}' to upload every file in it.",
                details={"path": candidate},
            )
        if not path.is_file():
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"Local file not found: {candidate}",
                exit_status=EXIT_USAGE,
                hint=(
                    f"Resolved against the working directory {Path.cwd()}; pass an absolute "
                    "path or run the command from the directory that holds the file."
                ),
                details={"path": candidate, "cwd": str(Path.cwd())},
            )


_UPLOAD_RESULT_SYMBOL = "mammoth.api.files.FilesAPI.upload_result"

#: Workbook files that cannot become datasets; ``dashboard pbix-intent`` reads them.
_WORKBOOK_SUFFIXES = (".pbix", ".twb", ".twbx")
_WORKBOOK_HINT = (
    "Power BI and Tableau workbooks are not datasets: attach the workbook in the chat "
    "and use `dashboard pbix-intent` to read it."
)


def _refused_files(errors: Any) -> list[str]:
    """File names the upload job refused, flattened from its ``errors`` map."""
    if not isinstance(errors, dict):
        return []
    names: list[str] = []
    for value in errors.values():
        for item in value if isinstance(value, list) else [value]:
            if isinstance(item, str) and item not in names:
                names.append(item)
    return names


def _upload_refused_message(errors: dict[str, Any], refused: list[str]) -> str:
    reasons = ", ".join(sorted(errors))
    return f"The server refused {', '.join(refused) or 'the upload'} ({reasons})."


def _upload_refused_error(errors: dict[str, Any], refused: list[str]) -> CliError:
    """The error for an upload whose files were all refused (no dataset made)."""
    workbook = any(name.lower().endswith(_WORKBOOK_SUFFIXES) for name in refused)
    return CliError(
        code=CODE_UPLOAD_REFUSED,
        message=_upload_refused_message(errors, refused) + " No dataset was created.",
        exit_status=EXIT_USAGE,
        hint=_WORKBOOK_HINT if workbook else "Upload a supported file type (CSV, Excel, JSON).",
        details={"errors": errors, "refused_files": refused},
    )


_DATASET_GET_SYMBOL = "mammoth.api.datasets.DatasetsAPI.get"
#: How long an append waits for its target dataset to finish taking the rows, and the
#: longest gap between reads.
_APPEND_WAIT_S = 120.0
_APPEND_RETRY_S = 5.0


def _dataset_rows(service: Any, dataset_id: int) -> int | None:
    """The dataset's stored row count, or None when it cannot be read."""
    try:
        response = service.call(_DATASET_GET_SYMBOL, dataset_id=dataset_id)
    except CliError:
        return None
    dataset = response.get("dataset", response) if isinstance(response, dict) else {}
    stats = dataset.get("stats") if isinstance(dataset, dict) else None
    rows = stats.get("row_count") if isinstance(stats, dict) else None
    return rows if isinstance(rows, int) else None


def _wait_until_ready(service: Any, dataset_id: int) -> bool:
    """Wait (up to ``_APPEND_WAIT_S``) until the dataset reads ``ready`` or failed.

    Args:
        service: The SDK service.
        dataset_id: The dataset an append writes into.

    Returns:
        True when the dataset settled (ready or failed), False when the wait ran out.
    """
    for delay in poll_delays(_APPEND_WAIT_S, _APPEND_RETRY_S):
        status = _dataset_status(service, dataset_id)[0]
        if status == "ready" or status in _UPLOAD_FAILED_STATUSES:
            return True
        time.sleep(delay)
    return False


def _dataset_status(service: Any, dataset_id: int) -> tuple[str, dict[str, Any] | None, str | None]:
    """Read ``(status, status_info, name)`` for one dataset; ``unknown`` if the read fails."""
    try:
        response = service.call(_DATASET_GET_SYMBOL, dataset_id=dataset_id)
    except CliError:
        return "unknown", None, None
    dataset = response.get("dataset", response) if isinstance(response, dict) else {}
    status = dataset.get("status") if isinstance(dataset, dict) else None
    status_info = dataset.get("status_info") if isinstance(dataset, dict) else None
    name = dataset.get("name") if isinstance(dataset, dict) else None
    return (
        status if isinstance(status, str) else "unknown",
        status_info if isinstance(status_info, dict) else None,
        name if isinstance(name, str) and name else None,
    )


#: An upload whose job finished without making any dataset.
NO_DATASET_STATUS = "no_dataset"
SHEET_CHOICE_STATUS = "needs_sheet_choice"
PASSWORD_STATUS = "needs_password"  # noqa: S105
_SHEETS_ACTION = "sheet_selection_required"
_PASSWORD_ACTION = "password_required"  # noqa: S105
_NO_DATASET_MESSAGE = (
    "The file was uploaded but no dataset was made from it. A PDF waits in the file list "
    "as action_needed until its tables are extracted; do that in the Mammoth app. Do not "
    "upload the file again."
)

#: Words in a ``need_action`` ``status_info`` that point at a header or title-row problem
#: rather than an ambiguous date: ``interpretation preview`` shows how the rows would read.
_HEADER_CAUSE_WORDS = ("header", "title", "skip")


def _need_action_command(dataset_id: int, status_info: dict[str, Any] | None) -> str:
    """The command that fits why a dataset waits in ``need_action``.

    Args:
        dataset_id: The dataset.
        status_info: Its ``status_info`` from the platform.

    Returns:
        ``dataset interpretation preview`` when the message names a header or title-row
        problem, else ``dataset file-settings get`` (ambiguous dates, delimiters).
    """
    said = " ".join(str(v) for v in (status_info or {}).values()).lower()
    if any(word in said for word in _HEADER_CAUSE_WORDS):
        return f"mammoth dataset interpretation preview {dataset_id}"
    return f"mammoth dataset file-settings get {dataset_id}"


def _waiting_files(files: Any) -> list[dict[str, Any]]:
    """Shape the SDK's ``files`` (uploads that made no dataset) into what to do for each.

    Args:
        files: ``upload_result``'s ``files`` list, or None.

    Returns:
        One entry per file. A file waiting for a sheet choice or a password gets a
        runnable ``next_command`` with its real id and sheet names, and a message.
    """
    entries: list[dict[str, Any]] = []
    for item in files if isinstance(files, list) else []:
        if not isinstance(item, dict) or item.get("file_id") is None:
            continue
        file_id = item["file_id"]
        entry: dict[str, Any] = {k: v for k, v in item.items() if k != "sheets_info"}
        label = item.get("name") or file_id
        action = item.get("action_needed")
        if action == _SHEETS_ACTION:
            names = [
                s.get("sheet_name") if isinstance(s, dict) else s
                for s in item.get("sheets_info") or []
            ]
            names = [n for n in names if isinstance(n, str)]
            entry["sheets_info"] = names
            first = json.dumps(names[:1])
            entry["next_command"] = (
                f"mammoth file extract-sheets {file_id} --input '{{\"sheets\": {first}}}'"
            )
            entry["message"] = (
                f"File {label} has several sheets; the user must choose which ones become "
                "datasets."
            )
        elif action == _PASSWORD_ACTION:
            entry["next_command"] = (
                f"mammoth file set-password {file_id} --input ./password.json "
                f"--yes --confirm {file_id}"
            )
            entry["message"] = (
                f"File {label} is password protected; the user must give the password. It goes "
                'in ./password.json as {"password": "..."}, not on the command line.'
            )
        entries.append(entry)
    return entries


def _upload_result(
    value: Any,
    read_status: Callable[[int], tuple[str, dict[str, Any] | None, str | None]],
    files: Any = None,
) -> dict[str, Any]:
    """Shape the SDK upload return (int | list[int] | None) into a labeled result.

    ``status`` is ``ready`` only when every created dataset reads back as
    ``ready``; otherwise it is the first non-ready status so a caller that
    checks one field sees the dataset that still needs work. ``datasets``
    carries the per-dataset status, and a ``need_action`` or ``needs_view``
    dataset also gets the recovery route so the caller does not have to know
    the recipe. A file that made no dataset is listed in ``files``; with no
    dataset at all, a workbook awaiting a sheet choice or a password sets the status.
    """
    if isinstance(value, list):
        ids = [int(v) for v in value]
    elif isinstance(value, int):
        ids = [value]
    else:
        ids = []
    datasets: list[dict[str, Any]] = []
    for dataset_id in ids:
        status, status_info, name = read_status(dataset_id)
        # The platform reports an all-text CSV as ``ready`` with the message
        # "This file has more than one plausible way to be read.": the rows are
        # ingested, but no view is created. Confirming file settings does not
        # change that (verified on release, 2026-09-24); `view create` does.
        if status == "ready" and status_info and str(status_info.get("ready") or "").strip():
            status = "needs_view"
        entry: dict[str, Any] = {"id": dataset_id, "status": status}
        if name:
            entry["name"] = name
        if status_info:
            entry["status_info"] = status_info
        if status == "need_action":
            entry["next_command"] = _need_action_command(dataset_id, status_info)
        elif status == "needs_view":
            entry["next_command"] = f"mammoth view create {dataset_id}"
        datasets.append(entry)
    overall = next((d["status"] for d in datasets if d["status"] != "ready"), "ready")
    result: dict[str, Any] = {"status": overall, "dataset_ids": ids, "datasets": datasets}
    if len(ids) == 1:
        result["dataset_id"] = ids[0]
    waiting = _waiting_files(files)
    if waiting:
        result["files"] = waiting
    if not ids:
        # A workbook waits for a sheet choice (or a password); a PDF ends the job in
        # ``action_needed`` with no dataset (#255). Nothing here is ready.
        by_action = {f.get("action_needed"): f for f in waiting}
        chosen = by_action.get(_SHEETS_ACTION) or by_action.get(_PASSWORD_ACTION)
        if chosen is not None:
            result["status"] = (
                SHEET_CHOICE_STATUS
                if chosen.get("action_needed") == _SHEETS_ACTION
                else PASSWORD_STATUS
            )
            result["message"] = chosen["message"]
            result["next_command"] = chosen["next_command"]
        else:
            result["status"] = NO_DATASET_STATUS
            result["message"] = _NO_DATASET_MESSAGE
            result["next_command"] = "mammoth file list"
    return result


def file_upload_folder(invocation: Invocation) -> HandlerResult:
    """Upload every file in a local folder. Folder path is positional or ``folder_path``."""
    document = invocation.load_input() or {}
    folder_path = _string_positional(invocation) or document.get("folder_path")
    if not folder_path:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A folder path is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the folder path as a positional argument or a 'folder_path' input field.",
        )
    kwargs: dict[str, Any] = {"folder_path": folder_path}
    _forward_optional(document, kwargs, ("folder_resource_id", "wait_for_completion", "timeout"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))
