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
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project

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


def file_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one file by id. Prompt or ``--yes`` required."""
    file_id = _require_int_positional(invocation, "file id")
    enforce_confirmation(invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete file {file_id}")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), file_id=file_id)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


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
    """Upload one or more local files. Paths come from positionals or ``files``."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    if invocation.extra_args:
        kwargs["files"] = list(invocation.extra_args)
    elif "files" in document:
        kwargs["files"] = document["files"]
    _forward_optional(
        document,
        kwargs,
        (
            "folder_resource_id",
            "append_to_ds_id",
            "override_target_schema",
            "wait_for_completion",
            "timeout",
        ),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


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
