"""Positional, input and envelope helpers every dashboard command uses."""

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
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.command_contract import bind_command_inputs
from mammoth_cli.services.positionals import resolve_positionals

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
