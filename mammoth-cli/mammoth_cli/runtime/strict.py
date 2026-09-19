"""Strict argument and input validation shared by every command.

The generic Typer leaf accepts unknown options and surplus positionals so that
handlers can read their own positionals from ``ctx.args``. That permissiveness
must not reach the user: a misspelled option, a surplus positional token, or an
unknown or mistyped request-document key has to fail loudly instead of being
silently ignored or mis-executed.

This module centralizes three checks, all driven by the command's reviewed
backing SDK signature (see :mod:`mammoth_cli.services.argspec`) and its
derived positional shape (see :mod:`mammoth_cli.services.positionals`):

* :func:`validate_extra_args` rejects any trailing token that looks like an
  option — the generic leaf never declares command-specific options, so any
  ``-``/``--`` token in ``ctx.args`` is by definition unrecognized — and
  rejects any positional token beyond the command's accepted positional count,
  so a surplus argument (for example a stray second id) is refused instead of
  being silently dropped on the floor.
* :func:`validate_input_fields` rejects any ``--input`` document key the
  backing method cannot accept, then coerces each recognized key's value to
  its annotated scalar type (``bool``/``int``/``float``) in place, so a
  mistyped field fails cleanly instead of reaching the SDK as a raw string or
  being blanket-``bool()``-ed into the wrong truth value.

Commands with no resolvable signature remain extensible by default.  The one
intentional exception is the local ``config.get`` command: it is a reviewed
closed, zero-input contract (its key is a positional), so an ``--input``
document must be rejected explicitly.  This keeps that M2 contract honest
without taking away the compatibility escape hatch used by genuinely bespoke
or not-yet-backed commands.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.services.argspec import FieldSpec
from mammoth_cli.services.command_contract import (
    resolve_command_contract,
    thaw_contract_metadata,
)
from mammoth_cli.services.input_fields import is_closed_zero_input
from mammoth_cli.services.positionals import resolve_positionals
from mammoth_cli.services.type_system import TypeValidationError, is_opaque_mapping, validate_value

_OPTION_PREFIX = "-"

CODE_UNKNOWN_OPTION = "unknown_option"
CODE_UNEXPECTED_ARGUMENT = "unexpected_argument"
CODE_UNKNOWN_INPUT_FIELD = "unknown_input_field"
CODE_INVALID_INPUT_FIELD_TYPE = "invalid_input_field_type"

# Case-insensitive string tokens accepted for a boolean ``--input`` field.
# Deliberately explicit: a boolean field must never be coerced with a blanket
# ``bool(str)``, which treats any non-empty string (including ``"false"``) as
# true.
_TRUE_STRINGS = frozenset({"true", "1", "yes", "y", "on"})
_FALSE_STRINGS = frozenset({"false", "0", "no", "n", "off"})


def _unknown_option_hint(command_id: str, token: str) -> tuple[str, dict[str, Any]]:
    """Name the accepted form when an unknown ``--option`` matches a real field.

    Generic leaves take no per-field options, so ``--name`` on ``project
    create`` is a guess at the positional ``name`` and ``--dataset-id`` on a
    view command is a guess at the ``dataset_id`` input field. Saying which
    lets a caller fix the call without a schema round-trip.
    """
    guessed = token.lstrip(_OPTION_PREFIX).split("=", 1)[0].replace("-", "_")
    command = command_id.replace(".", " ")
    if guessed:
        for position, spec in enumerate(resolve_positionals(command_id)):
            if spec.name == guessed:
                return (
                    f"'{guessed}' is positional argument {position + 1} of '{command}', "
                    f"not an option: mammoth {command} {guessed.upper()}.",
                    {"positional": guessed},
                )
        contract = resolve_command_contract(command_id)
        if contract is not None and any(
            field.name == guessed for field in contract.accepted_fields
        ):
            return (
                f"'{guessed}' is an --input field of '{command}', not an option: "
                f"pass --input '{{\"{guessed}\": VALUE}}' after the positional arguments.",
                {"input_field": guessed},
            )
    return "Check the command schema with 'mammoth schema get'.", {}


def validate_extra_args(command_id: str, extra_args: Iterable[str]) -> None:
    """Reject unrecognized options and surplus positional tokens.

    Args:
        command_id: The manifest command id being invoked.
        extra_args: The trailing tokens Typer collected for the command.

    Raises:
        CliError: ``unknown_option`` with :data:`EXIT_USAGE` when a token begins
            with ``-`` (and is not the bare ``-`` stdin sentinel), since the
            generic leaf declares no command-specific options for it to match.
            ``unexpected_argument`` with :data:`EXIT_USAGE` when there are more
            positional tokens than the command's derived positional count (see
            :func:`mammoth_cli.services.positionals.resolve_positionals`), so a
            surplus id is refused instead of silently ignored.
    """
    tokens = list(extra_args)
    for token in tokens:
        if token.startswith(_OPTION_PREFIX) and token != _OPTION_PREFIX:
            hint, hint_details = _unknown_option_hint(command_id, token)
            raise CliError(
                code=CODE_UNKNOWN_OPTION,
                message=f"Unknown option '{token}' for '{command_id.replace('.', ' ')}'.",
                exit_status=EXIT_USAGE,
                hint=hint,
                details={"option": token, **hint_details},
            )

    max_positionals = len(resolve_positionals(command_id))
    if len(tokens) > max_positionals:
        surplus = tokens[max_positionals:]
        raise CliError(
            code=CODE_UNEXPECTED_ARGUMENT,
            message=(
                f"'{command_id.replace('.', ' ')}' accepts at most {max_positionals} "
                f"positional argument(s); got {len(tokens)} (surplus: "
                f"{', '.join(surplus)})."
            ),
            exit_status=EXIT_USAGE,
            hint="Check the command schema with 'mammoth schema get'.",
            details={"surplus": surplus, "max_positionals": max_positionals},
        )


def _invalid_field_type_error(command_id: str, field: str, value: Any, expected: str) -> CliError:
    return CliError(
        code=CODE_INVALID_INPUT_FIELD_TYPE,
        message=(
            f"Input field '{field}' for '{command_id.replace('.', ' ')}' must be a " f"{expected}."
        ),
        exit_status=EXIT_USAGE,
        hint=f"Pass '{field}' as a {expected} value.",
        details={"field": field, "expected_type": expected},
    )


def _coerce_bool(value: Any, *, command_id: str, field: str) -> bool:
    """Coerce a ``--input`` value to bool, never via a blanket ``bool(str)``."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUE_STRINGS:
            return True
        if lowered in _FALSE_STRINGS:
            return False
    raise _invalid_field_type_error(command_id, field, value, "boolean")


def _coerce_int(value: Any, *, command_id: str, field: str) -> int:
    if isinstance(value, bool):
        raise _invalid_field_type_error(command_id, field, value, "integer")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            raise _invalid_field_type_error(command_id, field, value, "integer") from None
    raise _invalid_field_type_error(command_id, field, value, "integer")


def _coerce_float(value: Any, *, command_id: str, field: str) -> float:
    if isinstance(value, bool):
        raise _invalid_field_type_error(command_id, field, value, "number")
    if isinstance(value, (int, float)):
        result = float(value)
        if math.isfinite(result):
            return result
        raise _invalid_field_type_error(command_id, field, value, "number")
    if isinstance(value, str):
        try:
            result = float(value.strip())
            if math.isfinite(result):
                return result
        except ValueError:
            pass
    raise _invalid_field_type_error(command_id, field, value, "number")


def _relax_numeric_oneof(schema: Any) -> Any:
    """Turn ``oneOf: [number, integer, ...]`` into ``anyOf`` throughout ``schema``.

    The backend's generated schemas declare numeric fields (``threshold`` on a
    data check, for one) as ``oneOf`` over ``number`` and ``integer``. An
    integral value satisfies both branches, so strict ``oneOf`` rejects
    exactly the values the backend accepts (``5`` fails, ``0.5`` passes).
    The intent is clearly "any of these"; validate it that way.
    """
    if isinstance(schema, list):
        return [_relax_numeric_oneof(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    relaxed: dict[str, Any] = {}
    for key, value in schema.items():
        if key == "oneOf" and isinstance(value, list):
            types = {b.get("type") for b in value if isinstance(b, dict)}
            if {"number", "integer"} <= types:
                relaxed["anyOf"] = _relax_numeric_oneof(value)
                continue
        relaxed[key] = _relax_numeric_oneof(value)
    return relaxed


def _coerce_document_fields(
    command_id: str,
    document: dict[str, Any],
    fields_by_name: dict[str, FieldSpec],
    input_schema: Mapping[str, Any] | None,
) -> None:
    """Recursively validate/coerce recognized fields in place."""
    for key in document:
        field = fields_by_name.get(key)
        if field is None:
            continue
        if (
            key == "body"
            and is_opaque_mapping(field.annotation)
            and input_schema is not None
            and (body_schema := input_schema.get("properties", {}).get("body")) is not None
        ):
            from jsonschema import ValidationError, validate  # type: ignore[import-untyped]

            try:
                validate(document[key], _relax_numeric_oneof(thaw_contract_metadata(body_schema)))
            except ValidationError as error:
                path = ".".join(str(part) for part in error.absolute_path)
                field_path = f"body.{path}" if path else "body"
                raise _invalid_field_type_error(
                    command_id,
                    field_path,
                    error.instance,
                    "a value matching the declared schema",
                ) from None
            continue
        try:
            document[key] = validate_value(document[key], field.annotation, key)
        except TypeValidationError as error:
            raise _invalid_field_type_error(
                command_id, error.path, error.value, error.expected
            ) from None


def validate_input_fields(command_id: str, document: dict[str, Any] | None) -> None:
    """Reject unknown ``--input`` keys, then coerce known keys to their type.

    Args:
        command_id: The manifest command id being invoked.
        document: The parsed ``--input`` mapping, or None when none was given.
            Mutated in place: each recognized scalar-typed field's value is
            replaced with its coerced form, so callers that read ``document``
            after this returns (every handler does, via
            :meth:`mammoth_cli.runtime.invocation.Invocation.load_input`) see
            the coerced value.

    Raises:
        CliError: ``unknown_input_field`` with :data:`EXIT_USAGE` when a key is
            not a parameter of the command's backing method.
            ``invalid_input_field_type`` with :data:`EXIT_USAGE` when a
            recognized field's value cannot be coerced to its annotated
            ``bool``/``int``/``float`` type. No-op when the command has no
            resolvable signature (except for an explicitly reviewed closed
            zero-input command) or the method accepts arbitrary keyword
            arguments.
    """
    if document is None:
        return
    # ArchiveDashboard's OpenAPI body is a strict boolean set-state field;
    # unlike ordinary CLI convenience scalars, string coercion would change
    # the wire contract (and make ``"false"`` truthy).
    if command_id == "dashboard.archive" and "archived" in document:
        if type(document["archived"]) is not bool:
            raise _invalid_field_type_error(command_id, "archived", document["archived"], "boolean")
    contract = resolve_command_contract(command_id)
    if contract is None:
        return
    if contract.accepts_extra:
        return
    # Admission is owned by the resolved contract.  Do not reconstruct the
    # accepted set from the raw SDK symbol here: positional/context exclusions
    # and explicitly reviewed adapter inputs are contract decisions.
    fields_by_name = {field.name: field for field in contract.accepted_fields}
    unknown = sorted(key for key in document if key not in fields_by_name)
    if unknown:
        raise CliError(
            code=CODE_UNKNOWN_INPUT_FIELD,
            message=(
                f"Unknown input field(s) for '{command_id.replace('.', ' ')}': "
                f"{', '.join(unknown)}."
            ),
            exit_status=EXIT_USAGE,
            hint=f"Accepted fields: {', '.join(sorted(fields_by_name)) or '(none)' }.",
            details={"unknown": unknown, "accepted": sorted(fields_by_name)},
        )
    if is_closed_zero_input(command_id) and document == {}:
        raise CliError(
            code=CODE_UNKNOWN_INPUT_FIELD,
            message=(
                f"This command does not declare structured input fields for "
                f"'{command_id.replace('.', ' ')}'."
            ),
            exit_status=EXIT_USAGE,
            hint="Remove --input or check the command schema.",
            details={"unknown": unknown, "accepted": sorted(fields_by_name)},
        )
    _coerce_document_fields(
        command_id,
        document,
        fields_by_name,
        contract.input_schema,
    )
