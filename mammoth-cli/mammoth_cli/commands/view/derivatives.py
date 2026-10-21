"""Derivative and pipeline-version handlers."""

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
from mammoth_cli.services.local_time import local_time

_METRIC_CARD_BASE: dict[str, Any] = {
    "FORMAT_INFO": {"RESULT": {}},
    "IS_FORMAT_INFO_DIRTY": False,
    "LOCKED": False,
    "type": "metric",
}


def _with_metric_card(body: Any) -> Any:
    """Default a METRIC derivative's ``display_properties`` to its explore-panel card.

    Without it the API stores ``display_properties: null``, which the explore
    panel reads as "no card". An explicit value (including ``{}``) is kept.
    """
    param = body.get("param") if isinstance(body, dict) else None
    metric = param.get("METRIC") if isinstance(param, dict) else None
    if not isinstance(metric, dict) or body.get("display_properties") is not None:
        return body
    return {
        **body,
        "display_properties": {**_METRIC_CARD_BASE, "info": {"title": metric.get("AS")}},
    }


def view_derivative_create(invocation: Invocation) -> HandlerResult:
    """Create a derivative on a dataview. ``body`` is required.

    A METRIC with no ``display_properties`` gets the metric card config so it
    shows in the explore panel; the result's ``card`` says whether a card exists.
    """
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input()
    body = _with_metric_card(_require_field(document, "body"))
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
    card = bool(body.get("display_properties")) if isinstance(body, dict) else False
    return {**data, "card": card}, _meta(invocation, auth.workspace_id, project_id)


def view_derivative_data(invocation: Invocation) -> HandlerResult:
    """Fetch data for one derivative by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    derivative_id = _require_int_positional_at(invocation, 1, "derivative id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
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
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    derivative_id = _require_int_positional_at(invocation, 1, "derivative id")
    document = invocation.load_input() or {}
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete derivative {derivative_id} of view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
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
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
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
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    derivative_id = _require_int_positional_at(invocation, 1, "derivative id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
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
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    version_id = _require_int_positional_at(invocation, 1, "version id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
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
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    version_id = _require_int_positional_at(invocation, 1, "version id")
    document = invocation.load_input() or {}
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete version {version_id} of view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
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
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    version_id = _require_int_positional_at(invocation, 1, "version id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "version_id": version_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_version_list(invocation: Invocation) -> HandlerResult:
    """List pipeline versions on a dataview, with optional filters from ``--input``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields", "sort", "limit", "offset", "name"))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = _with_version_times(service.call(_symbol(invocation), **kwargs))
    return data, _meta(invocation, auth.workspace_id, project_id)


def _with_version_times(data: Any) -> Any:
    """Give each version a ``when`` with an explicit offset.

    ``created_at`` is naive UTC and the server-made ``name`` ("30-Sep-2026 11:17 AM")
    is that same UTC wall time, so neither can be shown to a user as local time.
    """
    versions = data.get("versions") if isinstance(data, dict) else None
    if not isinstance(versions, list):
        return data
    stamped = [
        {**v, "when": local_time(v.get("created_at"))} if isinstance(v, dict) else v
        for v in versions
    ]
    return {
        **data,
        "versions": stamped,
        "time_note": "created_at and the version name are UTC; `when` carries its offset.",
    }


def view_version_update(invocation: Invocation) -> HandlerResult:
    """Update one pipeline version by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    version_id = _require_int_positional_at(invocation, 1, "version id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
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
