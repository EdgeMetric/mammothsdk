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
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mammoth.api.appends import APPEND_WAIT_S
from mammoth.appends import FAILURE_SCHEMA_MISMATCH

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.view.upload import upload_preview
from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_JOB_FAILED,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SCHEMA_MISMATCH,
    CODE_SDK_SYMBOL_UNRESOLVED,
    CODE_UPLOAD_REFUSED,
    EXIT_API,
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
    if mode is not None and document.get("wait_for_completion", True) is False:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="'mode' cannot be used with 'wait_for_completion: false'.",
            exit_status=EXIT_USAGE,
            hint=(
                "The update method is set before the upload and put back if it fails, which "
                "needs the wait. Drop 'wait_for_completion: false', or set the mode first "
                "with 'mammoth dataset update-method set'."
            ),
            details={"field": "mode"},
        )
    if document.get("override_target_schema") and (
        document.get("append_to_ds_id") is None
        or document.get("wait_for_completion", True) is False
    ):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=(
                "'override_target_schema' needs 'append_to_ds_id' and the wait for the "
                "upload (no 'wait_for_completion: false')."
            ),
            exit_status=EXIT_USAGE,
            hint=(
                "The server applies it only to a dataset whose update method is 'replace', "
                "which deletes the rows the dataset holds; the CLI checks that before it sends "
                'the file: --input \'{"append_to_ds_id": 123, "mode": "replace", '
                '"override_target_schema": true}\'.'
            ),
            details={"field": "override_target_schema"},
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
        appended: dict[str, Any] = {}
        if target is not None:
            if wanted_mode is not None and invocation.dry_run:
                # Report the mode change beside the upload the gate stops at, without making it.
                plan_call(
                    service,
                    update_method.SET_SYMBOL,
                    {"dataset_id": target, "mode": wanted_mode, "project_id": project_id},
                )
            outcome = _append(service, kwargs, target, wanted_mode)
            appended = {key: outcome.pop(key) for key in _APPEND_REPORT_FIELDS if key in outcome}
            if appended.get("append_failed"):
                raise _append_failed_error(target, outcome.get("status"), appended)
            data = [target] if outcome["dataset_ids"] else []
        else:
            outcome = service.call(_UPLOAD_RESULT_SYMBOL, **kwargs)
            data = outcome["dataset_ids"]
        refused = _refused_files(outcome.get("errors"))
        if outcome.get("errors") and not data:
            raise _upload_refused_error(outcome["errors"], refused)
        # A finished upload job does not mean a usable dataset: a CSV with an
        # ambiguous date column lands in ``need_action`` with no view. Report
        # the status the platform holds for each dataset, not an assumed one.
        result = _upload_result(
            data,
            lambda dataset_id: _dataset_status(service, dataset_id),
            files=outcome.get("files"),
        )
        warnings: list[str] = []
        if target is not None and data:
            # The upload made a staging dataset the backend already deleted; the result is
            # the dataset the rows were appended to. The batch it added is what to undo.
            result.update(appended)
            # Deprecated: kept for one more release; read ``batch_ids`` or ``appended_to``.
            result["staging_dataset_ids"] = list(outcome["dataset_ids"])
            warnings.extend(_append_warnings(target, appended))
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


_EXTRACT_SHEETS_SYMBOL = "mammoth.api.files.FilesAPI.extract_sheets"
_APPEND_SYMBOL = "mammoth.api.appends.AppendsAPI.append"
#: What ``AppendsAPI.append`` reports about the dataset, beside the upload job's own fields.
_APPEND_REPORT_FIELDS = (
    "appended_to",
    "update_method",
    "rows_before",
    "rows_after",
    "rows_added",
    "batch_ids",
    "unmatched_batch_ids",
    "append_pending",
    "append_failed",
    "failure",
    "reason",
    "kept_dataset_ids",
    "next_step",
    "read_error",
    "batches_error",
)


def _append(
    service: Any, kwargs: dict[str, Any], target: int, wanted_mode: str | None
) -> dict[str, Any]:
    """Upload into a dataset with the SDK's append: mode, rows, batches and the wait are its.

    Args:
        service: The SDK service.
        kwargs: The bound upload inputs (``files``, ``append_to_ds_id``, ...).
        target: The dataset the files are added to.
        wanted_mode: The stored mode asked for, or None to keep the dataset's own.

    Returns:
        ``AppendsAPI.append``'s answer: the upload job's fields and the append report.

    Raises:
        CliError: The SDK's failure; a refusal of the files by the server is raised as the
            upload-refused error, and a mode that stayed is named in ``update_method_kept``.
    """
    arguments = {
        key: value for key, value in kwargs.items() if key not in ("append_to_ds_id", "files")
    }
    arguments.pop("wait_for_completion", None)
    try:
        outcome: dict[str, Any] = service.call(
            _APPEND_SYMBOL,
            files=kwargs["files"],
            dataset_id=target,
            mode=wanted_mode,
            **arguments,
        )
        return outcome
    except CliError as failure:
        errors = failure.details.get("errors")
        if not (isinstance(errors, dict) and errors):
            raise
        refusal = _upload_refused_error(errors, _refused_files(errors))
        if failure.details.get("update_method_kept"):
            refusal.details["update_method_kept"] = failure.details["update_method_kept"]
        raise refusal from failure


def _append_failed_error(target: int, status: Any, appended: dict[str, Any]) -> CliError:
    """The error for an append whose dataset ended in a failed status.

    Args:
        target: The dataset the files were added to.
        status: The status the dataset ended in.
        appended: The append report (``rows_before``, ``rows_after``, ...).

    Returns:
        A ``job_failed`` error that carries the report, so the caller sees what was read.
    """
    if appended.get("failure") == FAILURE_SCHEMA_MISMATCH:
        return CliError(
            code=CODE_SCHEMA_MISMATCH,
            message=str(appended["reason"]),
            exit_status=EXIT_API,
            hint=str(appended["next_step"]),
            details={
                "appended_to": target,
                "rows_added": 0,
                "kept_dataset_ids": appended["kept_dataset_ids"],
                "append": appended,
            },
        )
    return CliError(
        code=CODE_JOB_FAILED,
        message=(
            f"The upload reached dataset {target}, but the dataset ended with the status "
            f"'{status}': the file did not load."
        ),
        exit_status=EXIT_API,
        hint=f"Read why with 'mammoth dataset get {target}'; nothing was recorded to undo.",
        details={"status": status, "append": appended},
    )


def _append_warnings(target: int, appended: dict[str, Any]) -> list[str]:
    """The warnings an append's report calls for: the mode that stays, what is unknown.

    Args:
        target: The dataset the files were added to.
        appended: The append report (``update_method``, ``unmatched_batch_ids``, ...).

    Returns:
        Plain sentences for the result's ``warnings``.
    """
    warnings: list[str] = []
    entry = appended.get("update_method") or {}
    if entry.get("previous_mode") is not None:
        warnings.append(
            f"Dataset {target} now has the update method '{entry['mode']}', and it "
            "keeps it: every later upload into it follows it too."
        )
    if entry.get("mode") is None:
        warnings.append(
            f"The update method of dataset {target} could not be read "
            f"({entry.get('error', 'no reason given')}), so it is not "
            "known whether this upload added a batch or replaced the rows; "
            "'history undo' will not delete anything for it."
        )
    if appended.get("unmatched_batch_ids"):
        warnings.append(
            f"Batches {appended['unmatched_batch_ids']} appeared in dataset {target} during the "
            "upload but none could be tied to the uploaded file by name, so they are not listed "
            "in batch_ids and 'history undo' will not delete them."
        )
    if appended.get("batches_error"):
        warnings.append(
            f"The batches of dataset {target} could not be read after the upload "
            f"({appended['batches_error']}), so batch_ids is missing."
        )
    if appended.get("append_pending"):
        warnings.append(
            f"Dataset {target} was still processing after {APPEND_WAIT_S:.0f} s, so the "
            f"appended rows may not be in it yet. Check with 'mammoth dataset get {target}' "
            "before using it."
        )
    return warnings


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
