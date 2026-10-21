"""Checkpoint and data-check handlers."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.view._common import (
    HandlerResult,
    _forward_optional,
    _meta,
    _require_field,
    _require_int_positional_at,
    _resolve_dataset_id,
    _symbol,
)
from mammoth_cli.runtime.confirm import (
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import (
    open_service,
    require_project,
)


def view_checkpoint_create(invocation: Invocation) -> HandlerResult:
    """Create a checkpoint on a dataview. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
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
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    checkpoint_id = _require_int_positional_at(invocation, 1, "checkpoint id")
    document = invocation.load_input() or {}
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete checkpoint {checkpoint_id} of view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
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
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    checkpoint_id = _require_int_positional_at(invocation, 1, "checkpoint id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "checkpoint_id": checkpoint_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_checkpoint_list(invocation: Invocation) -> HandlerResult:
    """List checkpoints on a dataview, with optional filters from ``--input``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields", "sort", "sequence", "status"))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_checkpoint_update(invocation: Invocation) -> HandlerResult:
    """Update one checkpoint by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    checkpoint_id = _require_int_positional_at(invocation, 1, "checkpoint id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
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
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
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
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    data_check_id = _require_int_positional_at(invocation, 1, "data check id")
    document = invocation.load_input() or {}
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete data check {data_check_id} of view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
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
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    data_check_id = _require_int_positional_at(invocation, 1, "data check id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "data_check_id": data_check_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_data_check_list(invocation: Invocation) -> HandlerResult:
    """List data checks on a dataview, with optional filters from ``--input``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields", "sort", "sequence", "status"))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_data_check_update(invocation: Invocation) -> HandlerResult:
    """Update one data check by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    data_check_id = _require_int_positional_at(invocation, 1, "data check id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
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
