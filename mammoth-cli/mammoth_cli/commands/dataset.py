"""Handlers for the ``dataset`` command family (project-scoped).

Every dataset operation runs inside a resolved project: the project id comes
from ``--project`` or the active project, and dataset ids come from a
positional argument or the strict ``--input`` document. Handlers dispatch
through the generic :meth:`~mammoth_cli.services.protocol.MammothService.call`
seam to the public SDK method named by the command's reviewed manifest
``sdk_symbol``.
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
from mammoth_cli.runtime.session import open_service, require_project

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
    """Parse the first positional argument as an int, or raise ``missing_argument``."""
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
    """Build the common envelope metadata for a dataset command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy any of ``fields`` present in ``document`` into ``kwargs``."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def dataset_list(invocation: Invocation) -> HandlerResult:
    """List datasets in the active project."""
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"project_id": project_id}
    _forward_optional(document, kwargs, ("limit", "sort"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_get(invocation: Invocation) -> HandlerResult:
    """Get one dataset by id in the active project."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_data(invocation: Invocation) -> HandlerResult:
    """Fetch a dataset's data, waiting for the backing job to complete."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataset_id": dataset_id, "project_id": project_id}
    _forward_optional(document, kwargs, ("timeout", "poll_interval"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_file_settings(invocation: Invocation) -> HandlerResult:
    """Get file settings (delimiter, header, dates, ...) for a dataset."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_file_settings_update(invocation: Invocation) -> HandlerResult:
    """Update a dataset's file settings. Required fields come from ``--input``."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input()
    delimiter = _require_field(document, "delimiter")
    has_header = _require_field(document, "has_header")
    initial_skip_count = _require_field(document, "initial_skip_count")
    quotechar = _require_field(document, "quotechar")
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "delimiter": delimiter,
        "has_header": has_header,
        "initial_skip_count": initial_skip_count,
        "quotechar": quotechar,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(
        document,
        kwargs,
        (
            "date_format",
            "preview_mode",
            "skip_auto_process_check",
            "date_formats",
            "set_project_level_date_format",
        ),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_file_settings_undo(invocation: Invocation) -> HandlerResult:
    """Undo the last file settings change for a dataset. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"undo file settings for dataset {dataset_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_create(invocation: Invocation) -> HandlerResult:
    """Create a dataset from a spec and creation type (required ``--input`` fields)."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    dataset_spec = _require_field(document, "dataset_spec")
    ds_creation_type = _require_field(document, "ds_creation_type")
    kwargs: dict[str, Any] = {
        "dataset_spec": dataset_spec,
        "ds_creation_type": ds_creation_type,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("folder_resource_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_create_from_pdf(invocation: Invocation) -> HandlerResult:
    """Create dataset(s) from tables extracted out of a PDF file."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    file_object_id = invocation.positional("file_object_id")
    if file_object_id is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="This command requires a file object id argument.",
            exit_status=EXIT_USAGE,
        )
    file_object_id = int(file_object_id)
    file_name = _require_field(document, "file_name")
    kwargs: dict[str, Any] = {
        "file_object_id": file_object_id,
        "file_name": file_name,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(
        document,
        kwargs,
        (
            "file_id",
            "table_list",
            "delete_file_after_extract",
            "is_preview_needed",
            "user_instruction",
        ),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_rename(invocation: Invocation) -> HandlerResult:
    """Rename a dataset. Dataset id is positional; new name comes from ``--input``."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input()
    name = _require_field(document, "name")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), dataset_id=dataset_id, name=name, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_trash(invocation: Invocation) -> HandlerResult:
    """Move one dataset to the project trash (reversible)."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_restore(invocation: Invocation) -> HandlerResult:
    """Restore a trashed dataset."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one dataset by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete dataset {dataset_id}"
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_bulk_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete all datasets in the active project. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete all datasets in project {project_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_bulk_update(invocation: Invocation) -> HandlerResult:
    """Apply a bulk patch across the active project's datasets. High-impact."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    patch_data = _require_field(document, "patch_data")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"bulk-update datasets in project {project_id}",
        target=str(project_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), patch_data=patch_data, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_update(invocation: Invocation) -> HandlerResult:
    """Apply JSON Patch operations to datasets in the active project. High-impact."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    patch_data = _require_field(document, "patch_data")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"update datasets in project {project_id}",
        target=str(project_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), patch_data=patch_data, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)
