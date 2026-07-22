"""Handlers for the sub-client-backed ``view`` command family.

This module covers dataview operations, checkpoints, data checks, derivatives,
versions, pipeline/task operations, exports, and AI helpers that are backed by
real SDK sub-clients (``DataviewsAPI``, ``CheckpointsAPI``, ``DataChecksAPI``,
``DerivativesAPI``, ``PipelineAPI``, ``PipelineVersionsAPI``, ``ExportsAPI``,
``AIAPI``). It intentionally excludes ``view transform *`` (pipeline
transformation builders), the interactive ``view draft *`` workflow commands,
and ``view create/get/delete`` — those are implemented elsewhere.

Most commands here are project-scoped (their SDK signature carries a
``project_id`` parameter) and take a ``dataset_id`` and/or ``dataview_id`` as
leading positionals, in the order those ids appear in the signature. A few
pipeline/task/AI commands have no ``project_id`` parameter at all — those pass
``None`` as the project id in the envelope metadata, mirroring
:mod:`mammoth_cli.commands.project`'s read handlers. Handlers dispatch through
the generic :meth:`~mammoth_cli.services.protocol.MammothService.call` seam to
the public SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import (
    POLICY_PROMPT_OR_YES,
    POLICY_YES_ALWAYS,
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
            code="sdk_symbol_unresolved",
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
            code="invalid_argument",
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional_at(invocation: Invocation, index: int, name: str) -> int:
    """Return the required positional argument at ``index`` as an int, or raise."""
    value = _int_positional_at(invocation, index, name)
    if value is None:
        raise CliError(
            code="missing_argument",
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code="missing_field",
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy any of ``fields`` present in ``document`` into ``kwargs`` unchanged."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for a view command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


# ---------------------------------------------------------------------------
# view.list / view.bulk-delete (dataset-scoped, no dataview_id)
# ---------------------------------------------------------------------------


def view_list(invocation: Invocation) -> HandlerResult:
    """List dataviews for a dataset in the active project."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataset_id": dataset_id, "project_id": project_id}
    _forward_optional(document, kwargs, ("limit", "sort"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_bulk_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete several dataviews by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    document = invocation.load_input()
    dataview_ids = _require_field(document, "dataview_ids")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete dataviews of dataset {dataset_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_ids=dataview_ids,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataset_id + dataview_id (project-scoped)
# ---------------------------------------------------------------------------


def view_active_user_list(invocation: Invocation) -> HandlerResult:
    """List the active users on a dataview."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_active_user_mark(invocation: Invocation) -> HandlerResult:
    """Mark the caller as an active user on a dataview."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_parameter_context(invocation: Invocation) -> HandlerResult:
    """Get a dataview's parameter context."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_preview(invocation: Invocation) -> HandlerResult:
    """Preview a dataview's rows and columns."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "dataview_id": dataview_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("rows", "cols"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_restore(invocation: Invocation) -> HandlerResult:
    """Restore a trashed dataview."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_trash(invocation: Invocation) -> HandlerResult:
    """Move one dataview to the project trash (reversible)."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_update(invocation: Invocation) -> HandlerResult:
    """Apply JSON Patch operations to a dataview. ``patch_data`` is required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    document = invocation.load_input()
    patch_data = _require_field(document, "patch_data")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            patch_data=patch_data,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_data_get(invocation: Invocation) -> HandlerResult:
    """Fetch a dataview's data, waiting for the backing job to complete."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "dataview_id": dataview_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("timeout", "poll_interval"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_data_query(invocation: Invocation) -> HandlerResult:
    """Query a dataview's data with optional filtering, sorting, and paging."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "dataview_id": dataview_id,
        "project_id": project_id,
    }
    _forward_optional(
        document, kwargs, ("sequence", "offset", "limit", "columns", "condition", "sort")
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_conditional_format_create(invocation: Invocation) -> HandlerResult:
    """Create a conditional-format rule on a dataview. ``rule`` is required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    document = invocation.load_input()
    rule = _require_field(document, "rule")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            rule=rule,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_conditional_format_delete_all(invocation: Invocation) -> HandlerResult:
    """Delete all conditional-format rules on a dataview. Prompt or ``--yes``."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete all conditional-format rules on view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_conditional_format_list(invocation: Invocation) -> HandlerResult:
    """List conditional-format rules on a dataview."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_conditional_format_update(invocation: Invocation) -> HandlerResult:
    """Update a conditional-format rule on a dataview. ``rule`` is required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    document = invocation.load_input()
    rule = _require_field(document, "rule")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            rule=rule,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataset_id + dataview_id + checkpoint_id (project-scoped)
# ---------------------------------------------------------------------------


def view_checkpoint_create(invocation: Invocation) -> HandlerResult:
    """Create a checkpoint on a dataview. ``body`` is required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_checkpoint_delete(invocation: Invocation) -> HandlerResult:
    """Delete one checkpoint by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    checkpoint_id = _require_int_positional_at(invocation, 2, "checkpoint id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete checkpoint {checkpoint_id} of view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            checkpoint_id=checkpoint_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_checkpoint_get(invocation: Invocation) -> HandlerResult:
    """Get one checkpoint by id."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    checkpoint_id = _require_int_positional_at(invocation, 2, "checkpoint id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "dataview_id": dataview_id,
        "checkpoint_id": checkpoint_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_checkpoint_list(invocation: Invocation) -> HandlerResult:
    """List checkpoints on a dataview, with optional filters from ``--input``."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "dataview_id": dataview_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields", "sort", "sequence", "status"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_checkpoint_update(invocation: Invocation) -> HandlerResult:
    """Update one checkpoint by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    checkpoint_id = _require_int_positional_at(invocation, 2, "checkpoint id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            checkpoint_id=checkpoint_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataset_id + dataview_id + data_check_id (project-scoped)
# ---------------------------------------------------------------------------


def view_data_check_create(invocation: Invocation) -> HandlerResult:
    """Create a data check on a dataview. ``body`` is required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_data_check_delete(invocation: Invocation) -> HandlerResult:
    """Delete one data check by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    data_check_id = _require_int_positional_at(invocation, 2, "data check id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete data check {data_check_id} of view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            data_check_id=data_check_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_data_check_get(invocation: Invocation) -> HandlerResult:
    """Get one data check by id."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    data_check_id = _require_int_positional_at(invocation, 2, "data check id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "dataview_id": dataview_id,
        "data_check_id": data_check_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_data_check_list(invocation: Invocation) -> HandlerResult:
    """List data checks on a dataview, with optional filters from ``--input``."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "dataview_id": dataview_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields", "sort", "sequence", "status"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_data_check_update(invocation: Invocation) -> HandlerResult:
    """Update one data check by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    data_check_id = _require_int_positional_at(invocation, 2, "data check id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            data_check_id=data_check_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataset_id + dataview_id + derivative_id (project-scoped)
# ---------------------------------------------------------------------------


def view_derivative_create(invocation: Invocation) -> HandlerResult:
    """Create a derivative on a dataview. ``body`` is required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_derivative_data(invocation: Invocation) -> HandlerResult:
    """Fetch data for one derivative by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    derivative_id = _require_int_positional_at(invocation, 2, "derivative id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            derivative_id=derivative_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_derivative_delete(invocation: Invocation) -> HandlerResult:
    """Delete one derivative by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    derivative_id = _require_int_positional_at(invocation, 2, "derivative id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete derivative {derivative_id} of view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            derivative_id=derivative_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_derivative_list(invocation: Invocation) -> HandlerResult:
    """List derivatives on a dataview."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_derivative_update(invocation: Invocation) -> HandlerResult:
    """Update one derivative by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    derivative_id = _require_int_positional_at(invocation, 2, "derivative id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            derivative_id=derivative_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataset_id + dataview_id + version_id (project-scoped)
# ---------------------------------------------------------------------------


def view_version_apply(invocation: Invocation) -> HandlerResult:
    """Apply one pipeline version by id."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    version_id = _require_int_positional_at(invocation, 2, "version id")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            version_id=version_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_version_delete(invocation: Invocation) -> HandlerResult:
    """Delete one pipeline version by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    version_id = _require_int_positional_at(invocation, 2, "version id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete version {version_id} of view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            version_id=version_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_version_get(invocation: Invocation) -> HandlerResult:
    """Get one pipeline version by id."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    version_id = _require_int_positional_at(invocation, 2, "version id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "dataview_id": dataview_id,
        "version_id": version_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_version_list(invocation: Invocation) -> HandlerResult:
    """List pipeline versions on a dataview, with optional filters from ``--input``."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "dataview_id": dataview_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields", "sort", "limit", "offset", "name"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_version_update(invocation: Invocation) -> HandlerResult:
    """Update one pipeline version by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    dataview_id = _require_int_positional_at(invocation, 1, "dataview id")
    version_id = _require_int_positional_at(invocation, 2, "version id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            version_id=version_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataview_id (+ optional dataset_id), NOT project-scoped: ai, draft.command,
# pipeline.*, task.*
# ---------------------------------------------------------------------------


def view_ai_generate_data(invocation: Invocation) -> HandlerResult:
    """Generate synthetic data for a dataview with an AI prompt. ``prompt`` required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    prompt = _require_field(document, "prompt")
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "prompt": prompt}
    assert document is not None
    _forward_optional(document, kwargs, ("no_of_rows", "columns", "dataset_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_ai_generation_info(invocation: Invocation) -> HandlerResult:
    """Get the status/info of an AI data-generation run for a dataview."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_ai_profile(invocation: Invocation) -> HandlerResult:
    """Generate an AI profile for a dataview."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_draft_command(invocation: Invocation) -> HandlerResult:
    """Run a raw draft pipeline command against a dataview. ``command`` required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    command = _require_field(document, "command")
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "command": command}
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_pipeline_edit(invocation: Invocation) -> HandlerResult:
    """Apply JSON Patch operations to a dataview's pipeline. ``patches`` required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    patches = _require_field(document, "patches")
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "patches": patches}
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_pipeline_get(invocation: Invocation) -> HandlerResult:
    """Get a dataview's full pipeline."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_pipeline_items(invocation: Invocation) -> HandlerResult:
    """List a dataview's pipeline items, with optional filters from ``--input``."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(
        document, kwargs, ("dataset_id", "fields", "limit", "offset", "sort", "sequence", "status")
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_pipeline_rerun(invocation: Invocation) -> HandlerResult:
    """Rerun a dataview's pipeline, optionally from a given sequence."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("from_sequence", "dataset_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_pipeline_wait(invocation: Invocation) -> HandlerResult:
    """Wait for a dataview's pipeline to finish running."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("dataset_id", "timeout", "poll_interval"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_task_add(invocation: Invocation) -> HandlerResult:
    """Add a pipeline task to a dataview. ``task_spec`` is required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    task_spec = _require_field(document, "task_spec")
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "task_spec": task_spec}
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_task_delete(invocation: Invocation) -> HandlerResult:
    """Delete one pipeline task by id. Prompt or ``--yes`` required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    task_id = _require_int_positional_at(invocation, 1, "task id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete task {task_id} of view {dataview_id}",
    )
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "task_id": task_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_task_get(invocation: Invocation) -> HandlerResult:
    """Get one pipeline task by id."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    task_id = _require_int_positional_at(invocation, 1, "task id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "task_id": task_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_task_list(invocation: Invocation) -> HandlerResult:
    """List a dataview's pipeline tasks."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_task_preview(invocation: Invocation) -> HandlerResult:
    """Preview the effect of a pipeline task without persisting it. ``task_spec`` required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    task_spec = _require_field(document, "task_spec")
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "task_spec": task_spec}
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_task_update(invocation: Invocation) -> HandlerResult:
    """Update one pipeline task by id. ``task_spec`` is required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    task_id = _require_int_positional_at(invocation, 1, "task id")
    document = invocation.load_input()
    task_spec = _require_field(document, "task_spec")
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "task_id": task_id,
        "task_spec": task_spec,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


# ---------------------------------------------------------------------------
# view.export.* (mixed: most project-scoped; csv and list are not)
# ---------------------------------------------------------------------------


def view_export_create(invocation: Invocation) -> HandlerResult:
    """Create an export for a dataview. ``export_spec`` required. Always ``--yes``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    export_spec = _require_field(document, "export_spec")
    enforce_confirmation(
        invocation, policy=POLICY_YES_ALWAYS, action=f"create an export on view {dataview_id}"
    )
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "export_spec": export_spec,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_csv(invocation: Invocation) -> HandlerResult:
    """Export a dataview to a local CSV file."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("output_path", "timeout", "dataset_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_export_delete(invocation: Invocation) -> HandlerResult:
    """Delete one export by id. Always requires ``--yes``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    export_id = _require_int_positional_at(invocation, 1, "export id")
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"delete export {export_id} of view {dataview_id}",
    )
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "export_id": export_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("skip_validation", "dataset_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_get(invocation: Invocation) -> HandlerResult:
    """Get one export by id."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    export_id = _require_int_positional_at(invocation, 1, "export id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "export_id": export_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields", "dataset_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_list(invocation: Invocation) -> HandlerResult:
    """List exports for a dataview, with optional filters from ``--input``."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(
        document,
        kwargs,
        (
            "fields",
            "limit",
            "offset",
            "sort",
            "sequence",
            "status",
            "reordered",
            "handler_type",
            "end_of_pipeline",
            "runnable",
        ),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_export_publish_db(invocation: Invocation) -> HandlerResult:
    """Publish a dataview to a database endpoint. Always requires ``--yes``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    odbc_type = _require_field(document, "odbc_type")
    target_properties = _require_field(document, "target_properties")
    enforce_confirmation(
        invocation, policy=POLICY_YES_ALWAYS, action=f"publish-db on view {dataview_id}"
    )
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "odbc_type": odbc_type,
        "target_properties": target_properties,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_publish_db_update(invocation: Invocation) -> HandlerResult:
    """Patch a dataview's published database endpoint. Always requires ``--yes``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    patch = _require_field(document, "patch")
    enforce_confirmation(
        invocation, policy=POLICY_YES_ALWAYS, action=f"publish-db-update on view {dataview_id}"
    )
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "patch": patch,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_update(invocation: Invocation) -> HandlerResult:
    """Apply JSON Patch operations to an export. Always requires ``--yes``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    export_id = _require_int_positional_at(invocation, 1, "export id")
    document = invocation.load_input()
    patches = _require_field(document, "patches")
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"update export {export_id} of view {dataview_id}",
    )
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "export_id": export_id,
        "patches": patches,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("skip_validation", "dataset_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)
