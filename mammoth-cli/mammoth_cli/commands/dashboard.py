"""Handlers for the ``dashboard`` command family (workspace-scoped, no project).

Dashboards are identified either by an integer ``dashboard_id`` (most commands)
or by a share ``url`` slug (the ``*-by-url`` commands). None of the backing SDK
signatures accept a ``project_id``, so handlers never resolve or forward one.
Every handler dispatches through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import ValidationError

from mammoth_cli.commands.view import _FIND_DATASET_SYMBOL, view_profiles
from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    CODE_UNSUPPORTED_CONTRACT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import embedded, parents
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_NONE,
    POLICY_PROMPT_OR_YES,
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project, resolved_project
from mammoth_cli.services.argspec import arg_spec
from mammoth_cli.services.board_values import board_values, dashboard_link
from mammoth_cli.services.command_contract import bind_command_inputs
from mammoth_cli.services.dashboard_figures import (
    bake_error_problem,
    canvas_figure_problems,
    figure_problems,
)
from mammoth_cli.services.dashboard_filters import (
    check_filter,
    declared,
    with_filter,
    without_filter,
)
from mammoth_cli.services.dashboard_pages import (
    check_added_pages,
    generate_substitutions,
    page_substitutions,
)
from mammoth_cli.services.dashboard_review import (
    CANVAS_GET,
    NEW_COLUMN_NOTE,
    columns_not_on_dashboard,
    has_profiles,
    reporting_month,
    review,
)
from mammoth_cli.services.dashboard_review import _profiles as _review_profiles
from mammoth_cli.services.local_files import refuse_existing_file
from mammoth_cli.services.positionals import resolve_positionals
from mammoth_cli.services.read_memo import forget, remember

HandlerResult = tuple[Any, dict[str, Any]]

# Wait policies for which a job-shaped dashboard response must be resolved to
# its completed result (honoring --job-timeout) rather than returned raw. The
# dashboard SDK methods -- generated and handwritten alike -- never wait
# internally, so the CLI handler is the only place this can happen.
_JOB_WAIT_POLICIES = frozenset({"always_wait", "start_or_wait"})


def _resolve_job(service: Any, invocation: Invocation, data: Any) -> Any:
    """Wait for a job-shaped response when the command's wait policy opts in.

    ``wait_if_job`` is a no-op for payloads that are not a recognized job
    reference, so this is safe to apply to any dashboard response: it blocks
    (honoring ``--job-timeout``) only when the reviewed ``wait_policy`` is
    wait-capable *and* the server actually returned a job handle.
    """
    record = command_by_id(invocation.command_id)
    if record is None or record.get("wait_policy") not in _JOB_WAIT_POLICIES:
        return data
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")
    # A job dispatched by a /dashboards/url/{url}/... route is readable only
    # through the URL-scoped job route; the generic GET /jobs/{id} answers
    # 4PERM002 and used to fail the command although the job succeeded.
    return service.wait_if_job(data, dashboard_url=_url_scope(invocation))


def _url_scope(invocation: Invocation) -> str | None:
    """Return the dashboard URL slug positional when this command addresses one."""
    value = invocation.positionals.get("url")
    if value is None:
        for index, spec in enumerate(resolve_positionals(invocation.command_id)):
            if spec.name == "url" and index < len(invocation.extra_args):
                value = invocation.extra_args[index]
                break
    return str(value) if value else None


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


def _require_str_positional(invocation: Invocation, name: str) -> str:
    """Return the first positional argument, or raise ``missing_argument``."""
    value = _string_positional(invocation)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


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


def _require_int_positional_at(invocation: Invocation, name: str, index: int) -> int:
    """Parse the positional at ``index`` as an integer."""
    if len(invocation.extra_args) <= index:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    raw = invocation.extra_args[index]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


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


def _bound_document(invocation: Invocation) -> dict[str, Any]:
    """Return the admitted family input after shared contract binding.

    Dashboard commands have several explicit adapter transformations (for
    example ``action``/``share`` bodies and dashboard-create's intent
    positional).  The structured document itself must nevertheless cross one
    shared boundary first, so a supplied field cannot be silently dropped by
    a handwritten adapter.
    """
    return bind_command_inputs(invocation.command_id, invocation.load_input() or {})


def _generated_positionals(invocation: Invocation) -> dict[str, Any]:
    """Resolve generated-route positionals for CLI and direct-handler calls.

    The application supplies typed values in ``Invocation.positionals``.  Unit
    and contract callers may construct an invocation with legacy ``extra_args``;
    normalize those through the reviewed positional catalog so both paths have
    identical SDK destinations.
    """
    values = dict(invocation.positionals)
    for index, spec in enumerate(resolve_positionals(invocation.command_id)):
        if spec.name in values or index >= len(invocation.extra_args):
            continue
        raw = invocation.extra_args[index]
        if spec.type is int:
            try:
                values[spec.name] = int(raw)
            except ValueError as exc:
                raise CliError(
                    code=CODE_INVALID_ARGUMENT,
                    message=f"The {spec.name} argument '{raw}' is not an integer.",
                    exit_status=EXIT_USAGE,
                ) from exc
        else:
            values[spec.name] = raw
    return values


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy any of ``fields`` present in ``document`` into ``kwargs``."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a dashboard command (no project scope)."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": None,
    }


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
        data = service.call(_symbol(invocation), **kwargs)
        if data is None:
            # The route answers 200 with no body, so the result was ``data: null`` and
            # the caller could not see whether the share took. Read it back.
            data = _share_readback(service, dashboard_id)
    return data, _meta(invocation, auth.workspace_id)


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
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id)
    return data, _meta(invocation, auth.workspace_id)


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


def generated_dashboard(invocation: Invocation) -> HandlerResult:
    """Dispatch a generated dashboard command through its reviewed manifest.

    Positionals have already been typed by the shared positional resolver and
    structured input is recursively validated by :meth:`Invocation.load_input`.
    The manifest remains authoritative for both the backing SDK method and the
    mutation confirmation policy.
    """
    record = command_by_id(invocation.command_id)
    if record is None:
        raise CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"No command manifest exists for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )

    document = _bound_document(invocation)
    positionals = _generated_positionals(invocation)
    kwargs = bind_command_inputs(invocation.command_id, document, **positionals)

    # The generated contract treats named request bodies as opaque mappings;
    # AddPages has a release-level minItems constraint that must be enforced
    # before confirmation or transport.
    if invocation.command_id == "dashboard.pages.add" and "body" in kwargs:
        from mammoth.models.dashboards import AddPagesSpec

        try:
            kwargs["body"] = AddPagesSpec.model_validate(kwargs["body"]).model_dump(
                mode="json", exclude_none=True
            )
        except ValidationError as exc:
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"Invalid add-pages request: {exc}",
                exit_status=EXIT_USAGE,
            ) from exc

    spec = arg_spec(_symbol(invocation))
    if spec is not None:
        missing = [
            field.name for field in spec.fields if field.required and field.name not in kwargs
        ]
        if missing:
            field = missing[0]
            raise CliError(
                code=CODE_MISSING_FIELD,
                message=f"This command requires the '{field}' input field.",
                exit_status=EXIT_USAGE,
                hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
            )

    policy = str(record.get("confirmation") or POLICY_NONE)
    target = next((str(value) for value in positionals.values()), None)
    enforce_confirmation(
        invocation,
        policy=policy,
        action=invocation.command_id.replace(".", " "),
        target=target if policy == POLICY_CONFIRM_TARGET else None,
    )

    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
        data = _resolve_job(service, invocation, data)
        if invocation.command_id == "dashboard.pages.add" and "body" in kwargs:
            requested = kwargs["body"].get("params", {}).get("pages", [])
            data = check_added_pages(service, positionals["dashboard_id"], requested, data)
        if invocation.command_id in _REVIEWED_COMMANDS:
            data = _with_deliverable_check(invocation, service, auth, positionals, data, kwargs)
        if invocation.command_id in _VALUED_COMMANDS:
            data = _with_board_values(service, auth, positionals, data)
        forget(service)
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


#: Board-building steps whose result carries the evaluated card/tile numbers.
_VALUED_COMMANDS = frozenset({"dashboard.v3.generate", "dashboard.chat.edit"})


def _with_board_values(service: Any, auth: Any, positionals: dict[str, Any], data: Any) -> Any:
    """Add ``dashboard_link`` and each KPI card's and tile's evaluated number.

    The result of a build/edit is definitions; the agent must see the numbers
    it is about to report (a rate that reads 21.9% where the data says 14.9%).
    """
    data = _dump_model(data)
    if not isinstance(data, dict):
        return data
    dashboard_id = positionals.get("dashboard_id") or data.get("id")
    if not isinstance(dashboard_id, int):
        return {**data, "values": {"unavailable": "the result names no dashboard id"}}
    return {
        **data,
        "dashboard_link": dashboard_link(auth.base_url, auth.workspace_id, dashboard_id),
        "values": board_values(service, dashboard_id),
    }


def _dump_model(value: Any) -> Any:
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


#: Authoring steps whose result carries ``deliverable_check``.
_REVIEWED_COMMANDS = frozenset(
    {
        "dashboard.create-blank",
        "dashboard.canvas.save",
        "dashboard.pages.add",
        "dashboard.v3.generate",
        "dashboard.chat.edit",
    }
)


def _with_deliverable_check(
    invocation: Invocation,
    service: Any,
    auth: Any,
    positionals: dict[str, Any],
    data: Any,
    kwargs: dict[str, Any] | None = None,
) -> Any:
    """Add ``deliverable_check`` (money shown? blanks decided?) to an authoring result.

    One canvas read; advice only, so a failed read leaves the result as it was.
    The same read also catches a figure the board cannot draw (an unknown column,
    a sum over text, a bake error) and any chart the server swapped or dropped; those
    set ``bake_ok``/``partial`` so ``verify`` reports the write as not clean.
    """
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")
    if not isinstance(data, dict):
        return data
    dashboard_id = positionals.get("dashboard_id") or data.get("id")
    data = _reflect_not_applied(invocation.command_id, data, dashboard_id)
    if not isinstance(dashboard_id, int):
        return {
            **data,
            "deliverable_check": {
                "checked": False,
                "warnings": [],
                "error": "the result names no dashboard id, so no canvas was read",
            },
        }
    try:
        canvas = service.call(CANVAS_GET, dashboard_id=dashboard_id)
        # The board's numbers (next step of a build or edit) read the same canvas.
        remember(service, CANVAS_GET, {"dashboard_id": dashboard_id}, canvas)
        canvas_doc = _dump_model(canvas)
        warnings = _deliverable_warnings(invocation, service, auth, dashboard_id, canvas_doc)
    except Exception as exc:  # noqa: BLE001 -- advice must never fail the authoring step
        error = f"{type(exc).__name__}: {exc}"
        return {
            **data,
            "deliverable_check": {"checked": False, "warnings": [], "error": error},
        }
    check: dict[str, Any] = {"checked": True, "warnings": warnings}
    if warnings:
        check["note"] = (
            "Fix these before you report the dashboard as done, or say in your "
            "report why not."
            + (" " + NEW_COLUMN_NOTE if any("fix" in warning for warning in warnings) else "")
        )
    return {
        **data,
        "deliverable_check": check,
        **_authoring_problems(invocation, data, canvas_doc, kwargs or {}),
    }


def _reflect_not_applied(
    command_id: str, data: dict[str, Any], dashboard_id: Any
) -> dict[str, Any]:
    """A chat edit that reports ``changed: false`` was not applied, whatever its message says.

    The model's own ``message`` ("I added a Total Events card") describes what it meant
    to do. It is kept as ``model_message`` and the ``message`` says plainly that nothing
    was applied, with the fallback that works.
    """
    if command_id != "dashboard.chat.edit" or data.get("changed") is not False:
        return data
    claim = data.get("message")
    target = dashboard_id if dashboard_id is not None else "DASHBOARD_ID"
    out = {
        **data,
        "message": (
            "NOT APPLIED: the dashboard was not changed"
            + (" (the board did not bake)" if data.get("bake_ok") is False else "")
            + ". The assistant's reply below describes what it intended, not what happened."
        ),
        "next_steps": [
            f"Read the board: mammoth dashboard get {target}",
            f"Add the card directly: mammoth dashboard figure add {target} --input "
            '\'{"dataview_id": VIEW_ID, "figure": {"kind": "kpi", "measure": '
            '"COLUMN", "agg": "sum"}}\'',
        ],
    }
    if isinstance(claim, str):
        out["model_message"] = claim
    return out


def _authoring_problems(
    invocation: Invocation, data: dict[str, Any], canvas_doc: Any, kwargs: dict[str, Any]
) -> dict[str, Any]:
    """Fields that make ``verify`` report a figure that failed or was swapped as not clean."""
    command_id = invocation.command_id
    params = (kwargs.get("body") or {}).get("params") or {}
    broken: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []
    if command_id in {"dashboard.canvas.save", "dashboard.pages.add"}:
        broken = canvas_figure_problems(canvas_doc)
        bake = bake_error_problem(canvas_doc)
        if bake is not None:
            broken.append(bake)
    if command_id == "dashboard.pages.add":
        profiles = [p["name"] for p in _canvas_profiles(canvas_doc)]
        refused = (data.get("chart_check") or {}).get("refused") or []
        partial = page_substitutions(
            params.get("pages") or [], data.get("added_page_ids"), canvas_doc, refused, profiles
        )
        partial += [
            {
                "issue": "page_dropped",
                "requested": {"page": removed.get("title")},
                "used": None,
                "detail": f"page '{removed.get('title')}' got no charts and was removed.",
            }
            for removed in (data.get("chart_check") or {}).get("removed_pages") or []
        ]
    elif command_id == "dashboard.v3.generate":
        partial = generate_substitutions(params.get("intent"), canvas_doc, data.get("message"))
    elif command_id == "dashboard.chat.edit":
        partial = generate_substitutions(None, canvas_doc, data.get("message"))
    extra: dict[str, Any] = {}
    if broken:
        extra["bake_ok"] = False
        extra["figure_check"] = {
            "problems": broken,
            "notes": [str(problem["detail"]) for problem in broken],
        }
    if partial:
        extra["partial"] = True
        extra["substitution_check"] = {
            "problems": partial,
            "notes": [str(problem["detail"]) for problem in partial],
        }
    if broken or partial:
        previous = data.get("warnings")
        extra["warnings"] = [*(previous if isinstance(previous, list) else []), *broken, *partial]
    return extra


def _canvas_profiles(canvas_doc: Any) -> list[dict[str, Any]]:
    return _review_profiles(canvas_doc) if isinstance(canvas_doc, dict) else []


def _deliverable_warnings(
    invocation: Invocation,
    service: Any,
    auth: Any,
    dashboard_id: int,
    canvas_doc: Any = None,
) -> list[dict[str, Any]]:
    """Read the canvas (and its view) once and return the review's warnings."""
    if canvas_doc is None:
        canvas_doc = _dump_model(service.call(CANVAS_GET, dashboard_id=dashboard_id))
    source = (canvas_doc.get("canvas") or {}).get("dataset") or {}
    view_id = source.get("dataview_id")
    profile = invocation.profile or profiles.get_selected()
    dataset_id = (
        parents.lookup(profile, auth.workspace_id, view_id) if isinstance(view_id, int) else None
    )
    current = (
        view_profiles(service, dataset_id, view_id, resolved_project(invocation))
        if isinstance(view_id, int) and dataset_id is not None
        else None
    )
    scope = reporting_month(canvas_doc, dashboard_id)
    if not has_profiles(canvas_doc):
        return scope + review(canvas_doc, dataset_id, current)
    stale = columns_not_on_dashboard(canvas_doc, current)
    return (
        scope
        + stale
        + [
            warning
            for warning in review(canvas_doc, dataset_id)
            # On a stale board the money advice is the rebuild, not a new column.
            if not (stale and warning["issue"] in {"money_not_shown", "unit_price_summed"})
        ]
    )


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


def _wait_workbook_job(service: Any, data: Any) -> Any:
    """Wait for the workbook job the upload started and return its finished result.

    The upload routes answer with a job handle; ``wait_if_job`` honors
    ``--job-timeout`` and is a no-op when the answer is already the result.
    """
    data = _dump_model(data)
    if isinstance(data, dict):
        data = _dump_model(service.wait_if_job(data))
    return data


def _refuse_rejected_workbook(data: Any) -> None:
    """Raise when the server rejected the upload (a junk file, an unreadable workbook)."""
    rejected = data.get("rejected") if isinstance(data, dict) else None
    if not rejected:
        return
    detail = rejected if isinstance(rejected, dict) else {"reason": str(rejected)}
    reason = str(detail.get("code") or detail.get("reason") or "not_a_workbook")
    text = detail.get("message") or detail.get("detail") or detail.get("error")
    raise CliError(
        code=reason,
        message=str(text) if text else f"The file was rejected: {reason}.",
        exit_status=EXIT_USAGE,
        hint="Pass a Tableau workbook (.twb or .twbx) or a Power BI file (.pbix).",
        details={"rejected": detail},
    )


#: Said plainly on an import result: the rows are made up to fit the workbook's fields.
_SYNTHETIC_ROWS_NOTE = (
    "The dataset holds generated sample rows (data_source fitted_sample), made up to fit "
    "the workbook's fields. They are synthetic, not the workbook's own data: load the real "
    "data into this dataset before you trust any number."
)


def dashboard_assess_twb(invocation: Invocation) -> HandlerResult:
    """Assess a local Tableau workbook through the SDK multipart seam."""
    file_path = _require_str_positional(invocation, "file")
    if not Path(file_path).is_file():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"File not found: {file_path}.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        data = _wait_workbook_job(service, service.call(_symbol(invocation), file=file_path))
    _refuse_rejected_workbook(data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_assess_pbix(invocation: Invocation) -> HandlerResult:
    """Assess a local Power BI workbook through the SDK multipart seam."""
    file_path = _require_str_positional(invocation, "file")
    if not Path(file_path).is_file():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"File not found: {file_path}.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        data = _wait_workbook_job(service, service.call(_symbol(invocation), file=file_path))
    _refuse_rejected_workbook(data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_import_workbook(invocation: Invocation) -> HandlerResult:
    """Import a local workbook into a confirmed project scope."""
    file_path = _require_str_positional(invocation, "file")
    if not Path(file_path).is_file():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"File not found: {file_path}.",
            exit_status=EXIT_USAGE,
        )
    document = invocation.load_input() or {}
    resolved_project = require_project(invocation)
    project_id = document.get("project_id", resolved_project)
    if "project_id" in document and (
        isinstance(project_id, bool) or not isinstance(project_id, int) or project_id <= 0
    ):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="Input project_id must be a positive integer.",
            exit_status=EXIT_USAGE,
        )
    if project_id != resolved_project:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="Input project_id does not match resolved project.",
            exit_status=EXIT_USAGE,
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action="dashboard import workbook",
        target=str(project_id),
    )
    with open_service(invocation) as (service, auth):
        data = _wait_workbook_job(
            service, service.call(_symbol(invocation), file=file_path, project_id=project_id)
        )
    _refuse_rejected_workbook(data)
    if isinstance(data, dict) and data.get("data_source") == "fitted_sample":
        data = _flag_synthetic_import(data, file_path)
    return data, _meta(invocation, auth.workspace_id)


def _packaged_row_count(file_path: str) -> int | None:
    """Data rows in the CSV a ``.twbx`` packages (largest one), or None when it has none."""
    import csv
    import io
    import zipfile

    try:
        with zipfile.ZipFile(file_path) as bundle:
            sizes = []
            for info in bundle.infolist():
                if not info.filename.lower().endswith(".csv"):
                    continue
                with bundle.open(info) as raw:
                    # csv, not line counting: a quoted value may hold a line break.
                    text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
                    sizes.append(sum(1 for _ in csv.reader(text)) - 1)
    except (zipfile.BadZipFile, OSError, csv.Error):
        return None
    return max(sizes) if sizes and max(sizes) >= 0 else None


def _flag_synthetic_import(data: dict[str, Any], file_path: str) -> dict[str, Any]:
    """Make a fitted-sample import ``partial``: its numbers are not the workbook's.

    The backend importer substitutes generated rows for the workbook's data. That must
    not read ``settled`` with no warning, so the result is partial (exit 3) and says how
    many rows were expected and received and how to load the real data.
    """
    expected = _packaged_row_count(file_path)
    received = next(
        (data[k] for k in ("row_count", "rows", "rows_imported") if isinstance(data.get(k), int)),
        None,
    )
    warning = (
        "The imported data is synthetic: the backend replaced the workbook's data with "
        f"generated rows. Expected {expected if expected is not None else 'the workbook'}"
        f"{' rows' if expected is not None else chr(39) + 's own rows'}, received "
        f"{received if received is not None else 'a generated sample'}"
        f"{' rows' if received is not None else ''}. Do not trust any number on this dataset."
    )
    dataview_id = data.get("dataview_id")
    steps = [
        "Upload the real data as a CSV: mammoth file upload REAL.csv --project PROJECT_ID "
        "(or add it to this dataset with --input '{\"append_to_ds_id\": DATASET_ID}').",
        "Point the imported dashboard at the real dataset (dashboard figure add or "
        "dashboard chat edit), then delete the synthetic one"
        + (f" (view {dataview_id})." if dataview_id is not None else "."),
    ]
    return {
        **data,
        "synthetic_data": True,
        "data_note": _SYNTHETIC_ROWS_NOTE,
        "partial": True,
        "warnings": [warning],
        "next_steps": steps,
    }


# ── BI export (Power BI / Tableau) ───────────────────────────────────────────

_BI_TARGETS: tuple[Literal["powerbi", "tableau"], ...] = ("powerbi", "tableau")
_BI_EXPORT_EMBEDDED_REFUSAL = (
    "The file cannot be downloaded from here. Send the user to the dashboard's Publish menu"
    " (the arrow next to Publish) -> Export to Power BI / Export to Tableau."
)


def _bi_target(document: dict[str, Any]) -> Literal["powerbi", "tableau"]:
    """Read and validate the required ``target`` input field."""
    target = document.get("target")
    if target not in _BI_TARGETS:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="Input `target` must be 'powerbi' or 'tableau'.",
            exit_status=EXIT_USAGE,
            hint='Pass --input \'{"target": "powerbi"}\' or \'{"target": "tableau"}\'.',
        )
    return cast(Literal["powerbi", "tableau"], target)


def dashboard_bi_preflight(invocation: Invocation) -> HandlerResult:
    """What a Power BI or Tableau export of this dashboard would carry.

    Side-effect free -- nothing is built and nothing is logged, so the export
    dialog can be opened and dismissed freely. Required input ``target``
    (``powerbi`` or ``tableau``) selects which release route answers.
    """
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = invocation.load_input() or {}
    target = _bi_target(document)
    symbol = f"mammoth.api.dashboards.DashboardsAPI.{target}_preflight"
    with open_service(invocation) as (service, auth):
        data = service.call(symbol, dashboard_id=dashboard_id)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_bi_export(invocation: Invocation) -> HandlerResult:
    """Download this dashboard as a Power BI project (.zip) or Tableau workbook (.twbx).

    Required input ``target`` (``powerbi`` or ``tableau``) selects the release
    route. With no ``output_path`` the file is written to the current
    directory under an auto-generated name.

    Embedded (see ``mammoth_cli.runtime.embedded``) it is refused: the route
    needs the Authorization header, so a link handed to the user's browser
    401s. The user downloads it from the dashboard's own export dialog.
    """
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = invocation.load_input() or {}
    target = _bi_target(document)
    if embedded.active():
        raise CliError(
            code=CODE_UNSUPPORTED_CONTRACT,
            message=_BI_EXPORT_EMBEDDED_REFUSAL,
            exit_status=EXIT_USAGE,
            hint="Run `dashboard bi-preflight` to tell the user what will convert first.",
        )
    symbol = f"mammoth.api.dashboards.DashboardsAPI.export_{target}"
    kwargs: dict[str, Any] = {"dashboard_id": dashboard_id}
    _forward_optional(document, kwargs, ("output_path",))
    extension = "zip" if target == "powerbi" else "twbx"
    refuse_existing_file(
        invocation, kwargs.get("output_path") or f"dashboard_{dashboard_id}_{target}.{extension}"
    )
    with open_service(invocation) as (service, auth):
        preflight = _bi_preflight_or_none(service, target, dashboard_id)
        data = service.call(symbol, **kwargs)
    # The SDK returns a Path; render it as a string so the written location is
    # visible in every output mode and serializes cleanly to JSON.
    result: dict[str, Any] = {"output_path": str(data)}
    result.update(_bi_drops(preflight, target))
    return result, _meta(invocation, auth.workspace_id)


def _bi_preflight_or_none(service: Any, target: str, dashboard_id: int) -> Any:
    """The pre-flight for this export; ``None`` when it cannot be read (the export still runs)."""
    try:
        return _dump_model(
            service.call(
                f"mammoth.api.dashboards.DashboardsAPI.{target}_preflight",
                dashboard_id=dashboard_id,
            )
        )
    except Exception:  # noqa: BLE001 -- advice; the export is the command
        return None


def _bi_drops(preflight: Any, target: str) -> dict[str, Any]:
    """Name the figures the export leaves out, as a structured warning.

    The export writes a file whatever it dropped, so the result must say so:
    ``partial`` makes ``verify`` report it as not clean.
    """
    if not isinstance(preflight, dict):
        return {}
    refusals = [r for r in preflight.get("refusals") or [] if isinstance(r, dict)]
    if not refusals:
        return {}
    dropped = [{"title": r.get("title"), "reason": r.get("reason")} for r in refusals]
    total = preflight.get("figures_total")
    exported = preflight.get("figures_exported")
    return {
        "figures_total": total,
        "figures_exported": exported,
        "dropped_figures": dropped,
        "partial": True,
        "warnings": [
            {
                "issue": "figures_dropped",
                "target": target,
                "detail": (
                    f"{len(dropped)} of {total} figures are not in the file "
                    f"({exported} exported): "
                    + "; ".join(f"{d['title']} ({d['reason']})" for d in dropped)
                ),
                "dropped": dropped,
            }
        ],
    }
