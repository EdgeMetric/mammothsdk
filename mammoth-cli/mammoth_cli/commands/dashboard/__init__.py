"""Handlers for the ``dashboard`` command family (workspace-scoped, no project).

Dashboards are identified either by an integer ``dashboard_id`` (most commands)
or by a share ``url`` slug (the ``*-by-url`` commands). The few backing SDK
methods that take a ``project_id`` (a new board's project) get an explicit
``--project``; no other handler resolves or forwards one.
Every handler dispatches through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mammoth_cli.commands.dashboard._common import (
    _bound_document,
    _forward_optional,
    _generated_positionals,
    _meta,
    _require_field,
    _require_int_positional,
    _require_int_positional_at,
    _require_str_positional,
    _resolve_job,
    _symbol,
)
from mammoth_cli.commands.dashboard.generated import (
    _deliverable_warnings,
    _dump_model,
    _with_board_values,
)
from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.view._common import _FIND_DATASET_SYMBOL
from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_UNSUPPORTED_BY_SERVER,
    EXIT_API,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime import parents
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service
from mammoth_cli.services.command_contract import bind_command_inputs
from mammoth_cli.services.dashboard_figures import (
    figure_problems,
)
from mammoth_cli.services.dashboard_filters import (
    check_filter,
    declared,
    with_filter,
    without_filter,
)
from mammoth_cli.services.dashboard_review import (
    CANVAS_GET,
)
from mammoth_cli.services.dashboard_review import _profiles as _review_profiles
from mammoth_cli.services.delete_check import ensure_deleted
from mammoth_cli.services.secret_files import read_secret_file


def dashboard_list(invocation: Invocation) -> HandlerResult:
    """List dashboards in the active workspace."""
    kwargs = {"project_id": invocation.project} if invocation.project is not None else {}
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_tags_list(invocation: Invocation) -> HandlerResult:
    """List the workspace dashboard-tag vocabulary."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def dashboard_tags_rename(invocation: Invocation) -> HandlerResult:
    """Rename a dashboard tag. A rename is undone by renaming back, so it asks nothing."""
    tag_id = _require_int_positional(invocation, "tag id")
    if tag_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="tag id must be positive.",
            exit_status=EXIT_USAGE,
        )
    document = _bound_document(invocation)
    name = _require_field(document, "name")
    if not isinstance(name, str) or not name.strip():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="name must be a non-blank string.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), tag_id=tag_id, name=name)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_tags_set(invocation: Invocation) -> HandlerResult:
    """Replace all dashboard tags after exact-target confirmation."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    if dashboard_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="dashboard id must be positive.",
            exit_status=EXIT_USAGE,
        )
    document = _bound_document(invocation)
    tags = _require_field(document, "tags")
    if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="tags must be a list of strings.",
            exit_status=EXIT_USAGE,
        )
    if len(tags) != len(set(tags)):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="tags must not contain duplicates.",
            exit_status=EXIT_USAGE,
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"replace dashboard tags for {dashboard_id}",
        target=str(dashboard_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id, tags=tags)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_tags_delete(invocation: Invocation) -> HandlerResult:
    """Delete a workspace dashboard tag after exact-target confirmation."""
    tag_id = _require_int_positional(invocation, "tag id")
    if tag_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="tag id must be positive.",
            exit_status=EXIT_USAGE,
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"delete dashboard tag {tag_id}",
        target=str(tag_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), tag_id=tag_id)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_tags_merge(invocation: Invocation) -> HandlerResult:
    """Merge a source workspace dashboard tag into a target tag."""
    tag_id = _require_int_positional(invocation, "tag id")
    if tag_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="tag id must be positive.",
            exit_status=EXIT_USAGE,
        )
    document = _bound_document(invocation)
    target_id = _require_field(document, "target_id")
    if isinstance(target_id, bool) or not isinstance(target_id, int) or target_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="target_id must be a positive integer.",
            exit_status=EXIT_USAGE,
        )
    if target_id == tag_id:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="tag id and target_id must differ.",
            exit_status=EXIT_USAGE,
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"merge dashboard tag {tag_id} into {target_id}",
        target=str(tag_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), tag_id=tag_id, target_id=target_id)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_get(invocation: Invocation) -> HandlerResult:
    """Get one dashboard by id, with each KPI card's and tile's number and period.

    The route is workspace-level: a board reads by id whichever project is
    active, and the result names the board's own ``project_id`` (``None`` when
    the backend withholds it, as it does for a viewer outside the project).

    A question about an existing board is answered from what it shows, so the
    read carries the numbers, not only the definitions (UQA-RT10-02).
    """
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id)
        if not invocation.readback:
            data = _with_board_values(service, auth, {"dashboard_id": dashboard_id}, data)
            data = _with_board_project(data)
            data = _with_source_datasets(service, invocation, auth.workspace_id, data)
    return data, _meta(invocation, auth.workspace_id)


#: Sources whose owning dataset one ``dashboard get`` looks up (one request each).
_MAX_SOURCE_LOOKUPS = 20


def _source_dataset(service: Any, invocation: Invocation, workspace_id: Any, view_id: int) -> Any:
    """The dataset that owns ``view_id``: remembered, else looked up; never raises."""
    profile_name = invocation.profile or profiles.get_selected()
    remembered = parents.lookup(profile_name, workspace_id, view_id)
    if remembered is not None:
        return {"view_id": view_id, "dataset_id": remembered}
    try:
        dataset_id = int(service.call(_FIND_DATASET_SYMBOL, dataview_id=view_id))
    except Exception as exc:  # noqa: BLE001 -- one unreadable source must not hide the others
        return {"view_id": view_id, "dataset_id": None, "error": f"{type(exc).__name__}: {exc}"}
    parents.remember(profile_name, workspace_id, {view_id: dataset_id})
    return {"view_id": view_id, "dataset_id": dataset_id}


def _with_source_datasets(
    service: Any, invocation: Invocation, workspace_id: Any, data: Any
) -> Any:
    """Label each source: a board's ``sources`` are VIEW ids, never dataset ids.

    An agent read 3882 from ``sources`` as a dataset id and got a 403
    (RT21-01). ``source_views`` gives each source's ``view_id`` and the
    ``dataset_id`` that owns it.
    """
    sources = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(sources, list) or not sources:
        return data
    view_ids = [view_id for view_id in sources if isinstance(view_id, int)]
    views = [
        _source_dataset(service, invocation, workspace_id, view_id)
        for view_id in view_ids[:_MAX_SOURCE_LOOKUPS]
    ]
    note = "sources are view ids; use a source's dataset_id for dataset commands."
    if len(view_ids) > _MAX_SOURCE_LOOKUPS:
        note += (
            f" Only the first {_MAX_SOURCE_LOOKUPS} of {len(view_ids)} sources were labelled;"
            " read the others with 'view get VIEW_ID'."
        )
    return {**data, "source_views": views, "sources_note": note}


def _with_board_project(data: Any) -> Any:
    """Name the project the board lives in; ``None`` when the backend does not say."""
    data = _dump_model(data)
    return {**data, "project_id": data.get("project_id")} if isinstance(data, dict) else data


def dashboard_get_by_url(invocation: Invocation) -> HandlerResult:
    """Get one dashboard by its share url slug."""
    url = _require_str_positional(invocation, "url")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), url=url)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_analytics(invocation: Invocation) -> HandlerResult:
    """Get analytics for one dashboard by id."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id)
    return data, _meta(invocation, auth.workspace_id)


def _widget_data_kwargs(invocation: Invocation) -> dict[str, Any]:
    """Bind the ``WidgetDataSpec`` fields the draft/published data routes take.

    ``widget_id`` (the widget UUID) is required; ``global_filters`` and
    ``drilldown_filters`` are optional ``{column: value}`` objects.
    """
    document = _bound_document(invocation)
    widget_id = _require_field(document, "widget_id")
    if not isinstance(widget_id, str) or not widget_id.strip():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The 'widget_id' input field must be a non-empty widget UUID string.",
            exit_status=EXIT_USAGE,
            hint="Read widget ids from 'mammoth dashboard canvas get DASHBOARD_ID'.",
        )
    kwargs: dict[str, Any] = {"widget_id": widget_id}
    for name in ("global_filters", "drilldown_filters"):
        if name not in document:
            continue
        value = document[name]
        if not isinstance(value, dict):
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"The '{name}' input field must be an object of column -> value.",
                exit_status=EXIT_USAGE,
            )
        kwargs[name] = value
    return kwargs


def dashboard_data_draft(invocation: Invocation) -> HandlerResult:
    """Read one widget's rows from a dashboard's draft state. Fields come from ``--input``."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    kwargs = _widget_data_kwargs(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id, **kwargs)
        data = _resolve_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_data_published(invocation: Invocation) -> HandlerResult:
    """Read one widget's rows from a dashboard's published state. Fields from ``--input``."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    kwargs = _widget_data_kwargs(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id, **kwargs)
        data = _resolve_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_job_by_url(invocation: Invocation) -> HandlerResult:
    """Get a job's status for a dashboard by URL and job-id positionals."""
    url = _require_str_positional(invocation, "url")
    job_id = _require_int_positional_at(invocation, "job id", 1)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), url=url, job_id=job_id)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_published_data_by_url(invocation: Invocation) -> HandlerResult:
    """Run a published-data request for a dashboard by url. ``body`` from ``--input``."""
    url = _require_str_positional(invocation, "url")
    document = _bound_document(invocation)
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), url=url, body=body)
        data = _resolve_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_widget_data(invocation: Invocation) -> HandlerResult:
    """Run a widget-data request for a dashboard by id. ``body`` from ``--input``."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = _bound_document(invocation)
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id, body=body)
        data = _resolve_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_widget_data_by_url(invocation: Invocation) -> HandlerResult:
    """Run a widget-data request for a dashboard by url. ``body`` from ``--input``."""
    url = _require_str_positional(invocation, "url")
    document = _bound_document(invocation)
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), url=url, body=body)
        data = _resolve_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_source_list(invocation: Invocation) -> HandlerResult:
    """List dashboard sources available in the active workspace."""
    kwargs = bind_command_inputs(invocation.command_id, invocation.load_input() or {})
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_update(invocation: Invocation) -> HandlerResult:
    """Apply a JSON Patch to one dashboard. Dashboard id is positional."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = _bound_document(invocation)
    patch = _require_field(document, "patch")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id, patch=patch)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_action(invocation: Invocation) -> HandlerResult:
    """Apply a lifecycle action to a dashboard. Always requires ``--yes``."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = _bound_document(invocation)
    action = _require_field(document, "action")
    kwargs: dict[str, Any] = {"dashboard_id": dashboard_id, "action": action}
    assert document is not None
    _forward_optional(document, kwargs, ("params_enabled", "params_view_id"))
    with open_service(invocation) as (service, auth):
        published = _was_published(service, dashboard_id)
        enforce_confirmation(
            invocation,
            policy=POLICY_YES_ALWAYS,
            action=f"apply an action to dashboard {dashboard_id}"
            + _board_findings(invocation, service, auth, dashboard_id),
        )
        first_publish = action == "publish-data" and not published
        if first_publish:
            kwargs["action"] = "publish-presentation"
        data = service.call(_symbol(invocation), **kwargs)
    if first_publish:
        data = {
            "action": "publish-presentation",
            "note": (
                "The board was never published, so publish-data was refused by the "
                "server; the presentation was published instead."
            ),
            "response": data,
        }
    return data, _meta(invocation, auth.workspace_id)


def dashboard_share(invocation: Invocation) -> HandlerResult:
    """Share a dashboard. Always requires ``--yes``."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = _bound_document(invocation)
    type_of_auth = _require_field(document, "type_of_auth")
    kwargs: dict[str, Any] = {"dashboard_id": dashboard_id, "type_of_auth": type_of_auth}
    assert document is not None
    _forward_optional(document, kwargs, ("users",))
    password_file = document.get("password_file")
    if password_file is not None:
        if type_of_auth != "password":
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"password_file needs type_of_auth password, not {type_of_auth}.",
                exit_status=EXIT_USAGE,
                hint='Use {"type_of_auth": "password", "password_file": "./pw.txt"}.',
            )
        kwargs["password"] = read_secret_file(password_file)
    with open_service(invocation) as (service, auth):
        was_published = _was_published(service, dashboard_id)
        if not was_published:
            refuse_viewer_share_before_publish(dashboard_id, type_of_auth, kwargs.get("users"))
        unpublished = (
            " (not published yet: sharing alone does not publish it; run dashboard action "
            'with {"action":"publish-presentation"} to publish)'
            if not was_published
            else ""
        )
        enforce_confirmation(
            invocation,
            policy=POLICY_YES_ALWAYS,
            action=f"share dashboard {dashboard_id}{unpublished}"
            + _board_findings(invocation, service, auth, dashboard_id),
        )
        previous = _share_readback(service, dashboard_id)["share"] if password_file else None
        data = service.call(_symbol(invocation), **kwargs)
        if data is None or password_file:
            # The route answers 200 with no body, so the result was ``data: null`` and
            # the caller could not see whether the share took. Read it back.
            data = _share_readback(service, dashboard_id)
        if password_file:
            _require_stored_password(service, invocation, dashboard_id, data["share"], previous)
    return data, _meta(invocation, auth.workspace_id)


def _require_stored_password(
    service: Any,
    invocation: Invocation,
    dashboard_id: int,
    share: Any,
    previous: Any,
) -> None:
    """Fail loud when a password share left a board that has no password, and put it back.

    A Mammoth without PRD-656 stores only the kind of sharing and ignores the password, so
    the share reports success on a board that is now type ``password`` with no password.

    Args:
        service: The open SDK service.
        invocation: The running ``dashboard share`` command.
        dashboard_id: The shared dashboard.
        share: The share as read back after the call.
        previous: The share as read before the call, for the restore.

    Raises:
        CliError: ``unsupported_by_server`` when the stored share is not a password share
            with ``options.has_password`` true; the message says whether the previous
            share was restored.
    """
    options = share.get("options") if isinstance(share, dict) else None
    stored = isinstance(options, dict) and options.get("has_password") is True
    if isinstance(share, dict) and share.get("type_of_auth") == "password" and stored:
        return
    restored = _restore_share(service, invocation, dashboard_id, previous)
    outcome = (
        "The previous sharing was put back."
        if restored
        else (
            f"The board is now type password with no password; switch it back with: mammoth "
            f'dashboard share {dashboard_id} --input \'{{"type_of_auth": "mammoth"}}\' --yes'
        )
    )
    raise CliError(
        code=CODE_UNSUPPORTED_BY_SERVER,
        message=(
            "This Mammoth does not store a share password yet (PRD-656), so the password "
            f"was not set. {outcome}"
        ),
        exit_status=EXIT_API,
        hint="Ask for a Mammoth release with PRD-656, or share by email with type_of_auth mammoth.",
        details={"dashboard_id": dashboard_id, "share_restored": restored},
    )


def _restore_share(service: Any, invocation: Invocation, dashboard_id: int, previous: Any) -> bool:
    """Put a board's earlier share back, best effort.

    Args:
        service: The open SDK service.
        invocation: The running ``dashboard share`` command.
        dashboard_id: The dashboard.
        previous: The share read before the change (``None`` when it had none).

    Returns:
        True when the share was written back and read back as the earlier kind.
    """
    previous = previous if isinstance(previous, dict) else {}
    kind = previous.get("type_of_auth") or "mammoth"
    kwargs: dict[str, Any] = {"dashboard_id": dashboard_id, "type_of_auth": kind}
    options = previous.get("options")
    users = options.get("users") if isinstance(options, dict) else None
    if kind == "mammoth":
        kwargs["users"] = users if isinstance(users, list) else []
    try:
        service.call(_symbol(invocation), **kwargs)
        now = _share_readback(service, dashboard_id)["share"]
    except Exception:
        return False
    return isinstance(now, dict) and now.get("type_of_auth") == kind


def refuse_viewer_share_before_publish(
    dashboard_id: int, type_of_auth: str, users: list[dict[str, Any]] | None
) -> None:
    """Refuse, as the server does, a ``mammoth`` share that gives viewer access before a publish.

    The server (``_apply_mammoth_recipients``) refuses the whole request when any user is
    shared as a viewer (the default role) and the board has no published version.
    """
    if type_of_auth != "mammoth":
        return
    for user in users or []:
        shared = user.get("shared", True)
        shared = shared.lower() in ("true", "1", "yes", "on") if isinstance(shared, str) else shared
        if shared and user.get("role") != "dashboard_editor":
            raise CliError(
                code="dashboard_not_published",
                message=f"Dashboard {dashboard_id} is not published; viewers cannot be invited.",
                exit_status=EXIT_USAGE,
                hint=(
                    "Publish it first: mammoth dashboard action "
                    f'{dashboard_id} --input \'{{"action": "publish-presentation"}}\' --yes, '
                    "then share. Or share only users with role dashboard_editor."
                ),
                details={"dashboard_id": dashboard_id},
            )


def _share_readback(service: Any, dashboard_id: int) -> dict[str, Any]:
    """The board's share state as ``dashboard get`` reports it after a share."""
    board = _dump_model(service.call(_DASHBOARD_GET, dashboard_id=dashboard_id))
    board = board if isinstance(board, dict) else {}
    return {"dashboard_id": dashboard_id, "share": board.get("share")}


def _was_published(service: Any, dashboard_id: int) -> bool:
    """Whether the board was ever published; ``dashboard get`` carries ``was_published``."""
    board = _dump_model(service.call(_DASHBOARD_GET, dashboard_id=dashboard_id))
    return bool(board.get("was_published")) if isinstance(board, dict) else False


def _board_findings(invocation: Invocation, service: Any, auth: Any, dashboard_id: int) -> str:
    """The deliverable check's findings as confirmation text; empty when clean or unreadable."""
    try:
        warnings = _deliverable_warnings(invocation, service, auth, dashboard_id)
    except Exception:  # noqa: BLE001 -- advice must never block the confirmation
        return ""
    if not warnings:
        return ""
    return " -- deliverable check: " + "; ".join(
        f"{warning['issue']}: {warning['detail']}" for warning in warnings
    )


def _figure_page_kwargs(page: Any) -> dict[str, Any]:
    """Map the endpoint's ``page`` ({"id"} or {"new_title"}) onto the SDK's page arguments."""
    if not isinstance(page, dict) or set(page) not in ({"id"}, {"new_title"}):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message='The \'page\' input field must be {"id": ...} or {"new_title": ...}.',
            exit_status=EXIT_USAGE,
        )
    if "id" in page:
        return {"page_id": page["id"]}
    return {"page_new_title": page["new_title"]}


_FIGURE_INTENT = "mammoth.api.dashboards.DashboardsAPI.figure_intent"
_FIGURE_SHAPES_HINT = (
    "Pass either an intent, and the server picks the chart: "
    "--input '{\"intent\": \"Revenue by region\"}' (the same as 'dashboard figure-intent'), "
    'or an exact figure: --input \'{"dataview_id": VIEW_ID, "figure": {"kind": "hbar", '
    '"dim": "Region", "measure": "Revenue", "agg": "sum"}}\'.'
)


def _figure_add_mode(document: dict[str, Any]) -> str:
    """``intent`` or ``figure``: which of the two input shapes the caller sent."""
    has_intent = document.get("intent") is not None
    has_figure = document.get("figure") is not None
    if has_intent != has_figure:
        return "intent" if has_intent else "figure"
    raise CliError(
        code=CODE_INVALID_ARGUMENT if has_intent else CODE_MISSING_FIELD,
        message=(
            "Pass 'intent' or 'figure', not both."
            if has_intent
            else "This command requires an 'intent' or a 'figure' input field."
        ),
        exit_status=EXIT_USAGE,
        hint=_FIGURE_SHAPES_HINT,
    )


def dashboard_figure_add(invocation: Invocation) -> HandlerResult:
    """Add one figure to a dashboard, from an intent or an exact figure spec.

    ``intent`` (optional ``kind``) goes through the figure-intent route, where the
    server picks and draws the chart. Otherwise ``dataview_id`` and ``figure`` are
    required; ``banded`` and ``page`` (``{"id": ...}`` or ``{"new_title": ...}``) are
    optional, and the result carries ``bake_job_id``.
    """
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = _bound_document(invocation)
    if _figure_add_mode(document) == "intent":
        params = {"intent": document["intent"]}
        if document.get("kind") is not None:
            params["kind"] = document["kind"]
        with open_service(invocation) as (service, auth):
            data = service.call(_FIGURE_INTENT, dashboard_id=dashboard_id, body={"params": params})
        result = _dump_model(data)
        result = {**result, "route": "figure-intent"} if isinstance(result, dict) else result
        return result, _meta(invocation, auth.workspace_id)
    kwargs: dict[str, Any] = {
        "dashboard_id": dashboard_id,
        "dataview_id": _require_field(document, "dataview_id"),
        "figure": _require_field(document, "figure"),
    }
    _forward_optional(document, kwargs, ("banded",))
    if document.get("page") is not None:
        kwargs.update(_figure_page_kwargs(document["page"]))
    with open_service(invocation) as (service, auth):
        _refuse_bad_figure(service, dashboard_id, kwargs)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def _refuse_bad_figure(service: Any, dashboard_id: int, kwargs: dict[str, Any]) -> None:
    """Fail before the call when the figure names a missing column or sums text.

    Reads the board's column profile (one canvas read); an unreadable canvas or
    a board with no profile yet skips the check, as the server still validates.
    """
    figure = kwargs.get("figure")
    if not isinstance(figure, dict):
        return
    try:
        canvas_doc = _dump_model(service.call(CANVAS_GET, dashboard_id=dashboard_id))
    except Exception:  # noqa: BLE001 -- the check is advice; the server still validates
        return
    profiles = _review_profiles(canvas_doc) if isinstance(canvas_doc, dict) else []
    canvas = canvas_doc.get("canvas") if isinstance(canvas_doc, dict) else None
    derived = [
        str(d.get("id"))
        for d in (canvas.get("derived") or [] if isinstance(canvas, dict) else [])
        if isinstance(d, dict)
    ]
    problems = figure_problems(figure, profiles, derived=derived, view_id=kwargs.get("dataview_id"))
    if not problems:
        return
    first = problems[0]
    raise CliError(
        code=CODE_INVALID_ARGUMENT,
        message=f"The figure cannot be drawn: {first['detail']}",
        exit_status=EXIT_USAGE,
        hint=(
            "Fix the figure and run the command again."
            if "fix" not in first
            else "Convert the column, then add the figure."
        ),
        recovery_commands=[p["fix"] for p in problems if "fix" in p]
        or [f"mammoth dashboard canvas get {dashboard_id}"],
        details={"problems": problems},
    )


def dashboard_cancel_generation(invocation: Invocation) -> HandlerResult:
    """Cancel an in-progress dashboard generation."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_restore(invocation: Invocation) -> HandlerResult:
    """Restore a trashed dashboard."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id)
        data = _resolve_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_trash(invocation: Invocation) -> HandlerResult:
    """Move one dashboard to the trash (reversible)."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id)
        data = _resolve_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one dashboard by id. Prompt or ``--yes`` required."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete dashboard {dashboard_id}"
    )
    with open_service(invocation) as (service, auth):
        # Read it first: the get route answers 403 for a deleted id, as it does for a real
        # denial, so the read-back below may call a 403 "gone" only if this read had access.
        try:
            service.call(_DASHBOARD_GET, dashboard_id=dashboard_id)
            had_access = True
        except CliError:
            had_access = False
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id)
        ensure_deleted(
            service,
            noun="dashboard",
            resource_id=dashboard_id,
            read_symbol=_DASHBOARD_GET,
            read_kwargs={"dashboard_id": dashboard_id},
            responses=(data,),
            forbidden_means_gone=had_access,
        )
    result = {**data} if isinstance(data, dict) else {}
    return {**result, "dashboard_id": dashboard_id, "deleted": [dashboard_id]}, _meta(
        invocation, auth.workspace_id
    )


def dashboard_archive(invocation: Invocation) -> HandlerResult:
    """Set the archived state of one dashboard with exact target confirmation."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    # Inspect the admitted JSON document before the shared SDK binder applies
    # its convenience coercions; the OpenAPI boolean is intentionally strict.
    raw = invocation.prepare_input() or {}
    if "archived" not in raw or type(raw["archived"]) is not bool:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The 'archived' input field must be a boolean.",
            exit_status=EXIT_USAGE,
        )
    document = _bound_document(invocation)
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"set archived state for dashboard {dashboard_id}",
        target=str(dashboard_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), dashboard_id=dashboard_id, archived=document["archived"]
        )
    if not isinstance(data, dict):
        # The route declares no response body; give the committed state a
        # stable object shape instead of a bare scalar.
        data = {"dashboard_id": dashboard_id, "archived": document["archived"], "response": data}
    return data, _meta(invocation, auth.workspace_id)


def dashboard_duplicate(invocation: Invocation) -> HandlerResult:
    """Copy a v3 dashboard; with ``target_dataview_id`` also wait for its data swap.

    The result keeps ``id`` and ``swap_job_id`` and adds ``swap_state`` and
    ``swap_result`` when a swap job was queued.
    """
    document = _bound_document(invocation)
    positionals = _generated_positionals(invocation)
    kwargs = bind_command_inputs(invocation.command_id, document, **positionals)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
        if hasattr(data, "model_dump"):
            data = data.model_dump(mode="json")
        if isinstance(data, dict) and data.get("swap_job_id") is not None:
            settled = service.wait_if_job({"job_id": data["swap_job_id"]})
            data = {**data, "swap_state": "success", "swap_result": settled}
    return data, _meta(invocation, auth.workspace_id)


def dashboard_attachment_read(invocation: Invocation) -> HandlerResult:
    """Run a workbook read on an attachment (intent or assess) and return the job's result."""
    positionals = _generated_positionals(invocation)
    with open_service(invocation) as (service, auth):
        queued = service.call(_symbol(invocation), **positionals)
        if hasattr(queued, "model_dump"):
            queued = queued.model_dump(mode="json")
        data = service.wait_if_job(queued)
    return data, _meta(invocation, auth.workspace_id)


_DASHBOARD_GET = "mammoth.api.dashboards.DashboardsAPI.get"
_CANVAS_SAVE = "mammoth.api.dashboards.DashboardsAPI.canvas_save"
_FILTER_KEYS = ("field", "control", "label", "default")


def _edit_filters(
    invocation: Invocation, edit: Callable[[dict[str, Any]], dict[str, Any]]
) -> HandlerResult:
    """Read the draft canvas, apply ``edit`` to the read, save it, and return the filters."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    with open_service(invocation) as (service, auth):
        current = _dump_model(service.call(CANVAS_GET, dashboard_id=dashboard_id))
        canvas = edit(current)
        saved = _dump_model(
            service.call(
                _CANVAS_SAVE,
                dashboard_id=dashboard_id,
                body={"params": {"canvas": canvas, "base_sequence": current["meta"]["sequence"]}},
            )
        )
    result = {
        "dashboard_id": dashboard_id,
        "filters": declared(canvas),
        "sequence": saved.get("sequence"),
        "bake_job_id": saved.get("bake_job_id"),
    }
    return result, _meta(invocation, auth.workspace_id)


def dashboard_filter_add(invocation: Invocation) -> HandlerResult:
    """Add (or replace) the filter control on one column of a board."""
    document = _bound_document(invocation)
    _require_field(document, "field")
    entry = {key: document[key] for key in _FILTER_KEYS if document.get(key) is not None}

    def edit(current: dict[str, Any]) -> dict[str, Any]:
        check_filter(current, entry)
        return with_filter(current["canvas"], entry)

    return _edit_filters(invocation, edit)


def dashboard_filter_remove(invocation: Invocation) -> HandlerResult:
    """Remove the filter control on one column of a board."""
    field = str(_require_field(_bound_document(invocation), "field"))
    return _edit_filters(invocation, lambda current: without_filter(current["canvas"], field))


def dashboard_filter_list(invocation: Invocation) -> HandlerResult:
    """List the filter controls a board declares."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    with open_service(invocation) as (service, auth):
        current = _dump_model(service.call(CANVAS_GET, dashboard_id=dashboard_id))
    result = {"dashboard_id": dashboard_id, "filters": declared(current["canvas"])}
    return result, _meta(invocation, auth.workspace_id)
