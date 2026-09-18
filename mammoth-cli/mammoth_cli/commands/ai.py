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
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services.command_contract import bind_command_inputs

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
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


def _bound_document(invocation: Invocation) -> dict[str, Any]:
    """Return admitted input after the shared S7 contract binding boundary."""
    return bind_command_inputs(invocation.command_id, invocation.load_input() or {})


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
            code=CODE_INVALID_ARGUMENT,
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
            code=CODE_MISSING_ARGUMENT,
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
            code=CODE_MISSING_FIELD,
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy every admitted input field into ``kwargs`` unchanged.

    Args:
        document: The parsed ``--input`` request document.
        kwargs: The keyword argument mapping being built for ``service.call``.
        fields: The optional field names to forward when present.
    """
    for field, value in document.items():
        if field in kwargs and field not in fields:
            continue
        kwargs[field] = value


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
    document = _bound_document(invocation)
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
    document = _bound_document(invocation)
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
    document = _bound_document(invocation)
    intent = (invocation.extra_args[0] if invocation.extra_args else None) or document.get("intent")
    if not intent:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="An intent is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the intent as a positional argument or an 'intent' input field.",
        )
    kwargs: dict[str, Any] = {"intent": intent}
    _forward_optional(document, kwargs, ("sequence_number",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def ai_retention_condition(invocation: Invocation) -> HandlerResult:
    """Generate or test a retention-policy WHERE clause for a dataset."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    if dataset_id < 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The dataset id must be >= 0.",
            exit_status=EXIT_USAGE,
        )
    document = _bound_document(invocation)
    mode = _require_field(document, "mode")
    if mode not in ("generate", "test"):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="'mode' must be either 'generate' or 'test'.",
            exit_status=EXIT_USAGE,
        )
    required = "intent" if mode == "generate" else "condition_sql"
    other = "condition_sql" if mode == "generate" else "intent"
    value = _require_field(document, required)
    if not isinstance(value, str) or not value.strip():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"'{required}' must be a non-empty string when mode is '{mode}'.",
            exit_status=EXIT_USAGE,
        )
    if other in document and document[other] is not None:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=(
                f"'{other}' is only valid when mode is "
                f"'{'test' if mode == 'generate' else 'generate'}'."
            ),
            exit_status=EXIT_USAGE,
        )
    kwargs = {"dataset_id": dataset_id, "mode": mode, "project_id": project_id, required: value}
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def ai_suggestion_list(invocation: Invocation) -> HandlerResult:
    """List AI-powered suggestions for the active project.

    The release route is ``POST .../suggestions`` with a ``UnifiedPromptSpec``
    body: ``suggestion_type`` (``extract_text``, ``add_condition``,
    ``generate_task``, ``apply_ai_template``, ``dashboards`` or
    ``derivative_fuzzy_bucket``) plus the type-specific ``params`` object.
    ``dataset_id``/``dataview_id`` scope the request via query parameters.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The raw suggestions response and envelope metadata.
    """
    project_id = require_project(invocation)
    document = invocation.load_input()
    suggestion_type = _require_field(document, "suggestion_type")
    params = _require_field(document, "params")
    kwargs: dict[str, Any] = {"suggestion_type": suggestion_type, "params": params}
    _forward_optional(document or {}, kwargs, ("dataset_id", "dataview_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)
