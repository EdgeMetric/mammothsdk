"""Handlers for the ``dashboard`` command family (workspace-scoped, no project).

Dashboards are identified either by an integer ``dashboard_id`` (most commands)
or by a share ``url`` slug (the ``*-by-url`` commands). None of the backing SDK
signatures accept a ``project_id``, so handlers never resolve or forward one.
Every handler dispatches through the generic
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
    POLICY_NONE,
    POLICY_PROMPT_OR_YES,
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service
from mammoth_cli.services.argspec import arg_spec

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
    return service.wait_if_job(data)


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


def dashboard_get(invocation: Invocation) -> HandlerResult:
    """Get one dashboard by id."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id)
    return data, _meta(invocation, auth.workspace_id)


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


def dashboard_data_draft(invocation: Invocation) -> HandlerResult:
    """Run a SQL query against a dashboard's draft data. ``sql`` comes from ``--input``."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = invocation.load_input()
    sql = _require_field(document, "sql")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id, sql=sql)
        data = _resolve_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_data_published(invocation: Invocation) -> HandlerResult:
    """Run a SQL query against a dashboard's published data. ``sql`` from ``--input``."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = invocation.load_input()
    sql = _require_field(document, "sql")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id, sql=sql)
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
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), url=url, body=body)
        data = _resolve_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_widget_data(invocation: Invocation) -> HandlerResult:
    """Run a widget-data request for a dashboard by id. ``body`` from ``--input``."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id, body=body)
        data = _resolve_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_widget_data_by_url(invocation: Invocation) -> HandlerResult:
    """Run a widget-data request for a dashboard by url. ``body`` from ``--input``."""
    url = _require_str_positional(invocation, "url")
    document = invocation.load_input()
    body = _require_field(document, "body")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), url=url, body=body)
        data = _resolve_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_source_list(invocation: Invocation) -> HandlerResult:
    """List dashboard sources available in the active workspace."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def dashboard_create(invocation: Invocation) -> HandlerResult:
    """Create a dashboard. Intent comes from a positional or the ``intent`` field."""
    document = invocation.load_input() or {}
    intent = _string_positional(invocation) or document.get("intent")
    if not intent:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A dashboard intent is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the intent as a positional argument or an 'intent' input field.",
        )
    source = _require_field(document, "source")
    kwargs: dict[str, Any] = {"intent": intent, "source": source}
    _forward_optional(document, kwargs, ("enable_filters", "enable_pages"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_update(invocation: Invocation) -> HandlerResult:
    """Apply a JSON Patch to one dashboard. Dashboard id is positional."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = invocation.load_input()
    patch = _require_field(document, "patch")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dashboard_id=dashboard_id, patch=patch)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_action(invocation: Invocation) -> HandlerResult:
    """Apply a lifecycle action to a dashboard. Always requires ``--yes``."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = invocation.load_input()
    action = _require_field(document, "action")
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"apply an action to dashboard {dashboard_id}",
    )
    kwargs: dict[str, Any] = {"dashboard_id": dashboard_id, "action": action}
    assert document is not None
    _forward_optional(document, kwargs, ("params_enabled", "params_view_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_share(invocation: Invocation) -> HandlerResult:
    """Share a dashboard. Always requires ``--yes``."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = invocation.load_input()
    type_of_auth = _require_field(document, "type_of_auth")
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"share dashboard {dashboard_id}",
    )
    kwargs: dict[str, Any] = {"dashboard_id": dashboard_id, "type_of_auth": type_of_auth}
    assert document is not None
    _forward_optional(document, kwargs, ("users",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


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

    document = invocation.load_input() or {}
    kwargs = dict(document)
    kwargs.update(invocation.positionals)

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
    target = next((str(value) for value in invocation.positionals.values()), None)
    enforce_confirmation(
        invocation,
        policy=policy,
        action=invocation.command_id.replace(".", " "),
        target=target if policy == POLICY_CONFIRM_TARGET else None,
    )

    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
        data = _resolve_job(service, invocation, data)
    return data, _meta(invocation, auth.workspace_id)
