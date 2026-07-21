"""Handlers for the ``ai`` command family (AI-assisted generation, project-scoped).

Every command in this family operates against the active project. For
``ai.condition.generate`` and ``ai.expression.generate`` the dataset id comes
from a positional argument, the natural-language ``intent`` (and, for
expressions, ``mode``) come from the strict ``--input`` document, and the
project id is forwarded explicitly because the backing SDK method accepts it.
``ai.sql.generate`` and ``ai.suggestion.list`` call SDK methods with no
``project_id`` parameter at all: the project is instead bound on the SDK
client when the service is opened, so these handlers still call
:func:`~mammoth_cli.runtime.session.require_project` to raise a friendly error
when no project is active, but do not forward ``project_id`` as a keyword
argument. Handlers dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project

HandlerResult = tuple[Any, dict[str, Any]]


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The dotted SDK symbol recorded in the manifest for this command.

    Raises:
        CliError: ``sdk_symbol_unresolved`` when the manifest has no symbol.
    """
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code="sdk_symbol_unresolved",
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


def _int_positional(invocation: Invocation, name: str) -> int | None:
    """Parse the first positional argument as an int, or return None if absent.

    Args:
        invocation: The current command's resolved global options.
        name: A human-readable name for the argument, used in error messages.

    Returns:
        The parsed integer, or None when no positional argument was given.

    Raises:
        CliError: ``invalid_argument`` when the positional is not an integer.
    """
    if not invocation.extra_args:
        return None
    raw = invocation.extra_args[0]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code="invalid_argument",
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Parse the first positional argument as an int, or raise usage.

    Args:
        invocation: The current command's resolved global options.
        name: A human-readable name for the argument, used in error messages.

    Returns:
        The parsed positive integer.

    Raises:
        CliError: ``missing_argument`` when no positional was given;
            ``invalid_argument`` when it is not an integer.
    """
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code="missing_argument",
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage.

    Args:
        document: The parsed ``--input`` request document, or None.
        field: The required field name.

    Returns:
        The field's value.

    Raises:
        CliError: ``missing_field`` when ``document`` is None or lacks ``field``.
    """
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
    """Copy any present ``fields`` from ``document`` into ``kwargs``.

    Args:
        document: The parsed ``--input`` request document.
        kwargs: The keyword argument mapping being built for ``service.call``.
        fields: The optional field names to forward when present.
    """
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for an ``ai`` command.

    Args:
        invocation: The current command's resolved global options.
        workspace_id: The resolved auth's workspace id.
        project_id: The resolved active project id.

    Returns:
        The envelope metadata mapping.
    """
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def ai_condition_generate(invocation: Invocation) -> HandlerResult:
    """Generate a filter condition from a natural language intent.

    The dataset id is a positional argument; ``intent`` is a required
    ``--input`` field; ``dataview_id`` and ``sequence_number`` are forwarded
    when present.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The raw generated-condition response and envelope metadata.
    """
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input()
    intent = _require_field(document, "intent")
    kwargs: dict[str, Any] = {
        "intent": intent,
        "dataset_id": dataset_id,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("dataview_id", "sequence_number"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def ai_expression_generate(invocation: Invocation) -> HandlerResult:
    """Generate a math/metric expression from a natural language intent.

    The dataset id is a positional argument; ``intent`` and ``mode`` are
    required ``--input`` fields; ``dataview_id`` and ``sequence_number`` are
    forwarded when present.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The raw generated-expression response and envelope metadata.
    """
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input()
    intent = _require_field(document, "intent")
    mode = _require_field(document, "mode")
    kwargs: dict[str, Any] = {
        "intent": intent,
        "mode": mode,
        "dataset_id": dataset_id,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("dataview_id", "sequence_number"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def ai_sql_generate(invocation: Invocation) -> HandlerResult:
    """Generate SQL from a natural language intent.

    ``intent`` comes from the first positional argument or an ``intent``
    ``--input`` field; ``sequence_number`` is forwarded when present. The
    backing SDK method has no ``project_id`` parameter — it resolves the
    project bound on the client — so an active project is required but not
    forwarded as a keyword argument.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The raw generated-SQL response and envelope metadata.
    """
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    intent = (invocation.extra_args[0] if invocation.extra_args else None) or document.get(
        "intent"
    )
    if not intent:
        raise CliError(
            code="missing_argument",
            message="An intent is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the intent as a positional argument or an 'intent' input field.",
        )
    kwargs: dict[str, Any] = {"intent": intent}
    _forward_optional(document, kwargs, ("sequence_number",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def ai_suggestion_list(invocation: Invocation) -> HandlerResult:
    """List AI-powered transformation suggestions for the active project.

    The backing SDK method takes no arguments — it resolves the project bound
    on the client — so an active project is required but not forwarded as a
    keyword argument.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The raw suggestions response and envelope metadata.
    """
    project_id = require_project(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, project_id)
