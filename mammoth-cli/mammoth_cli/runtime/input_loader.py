"""Load a strict structured request document from a file or standard input.

Agents drive multi-field commands by passing a single JSON or YAML document
with ``--input`` rather than assembling long option lists. This module turns
that flag (and the optional ``--input-format``) into a validated mapping, or a
stable :class:`~mammoth_cli.errors.envelope.CliError` when the source is
missing, the format is undeclared or unknown, the text does not parse, or the
top level is not a mapping. The document is never echoed, so a secret carried
inside it never reaches stdout or an error envelope.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

from mammoth_cli.errors.envelope import (
    CODE_INPUT_FORMAT_REQUIRED,
    CODE_INVALID_INPUT_DOCUMENT,
    CODE_INVALID_INPUT_FORMAT,
    EXIT_USAGE,
    CliError,
)

STDIN_SENTINEL = "-"
_JSON_FORMAT = "json"
_YAML_FORMAT = "yaml"
_VALID_FORMATS = (_JSON_FORMAT, _YAML_FORMAT)
_EXTENSION_FORMATS = {
    ".json": _JSON_FORMAT,
    ".yaml": _YAML_FORMAT,
    ".yml": _YAML_FORMAT,
}


def _invalid_format_error(value: str) -> CliError:
    return CliError(
        code=CODE_INVALID_INPUT_FORMAT,
        message=f"Unsupported input format '{value}'.",
        exit_status=EXIT_USAGE,
        hint=f"Use one of: {', '.join(_VALID_FORMATS)}.",
    )


def _format_required_error(source: str) -> CliError:
    return CliError(
        code=CODE_INPUT_FORMAT_REQUIRED,
        message=f"Cannot infer the input format for {source}.",
        exit_status=EXIT_USAGE,
        hint="Pass --input-format json or --input-format yaml.",
    )


def _resolve_format(input_file: str, input_format: str | None) -> str:
    if input_format is not None:
        normalized = input_format.strip().lower()
        if normalized not in _VALID_FORMATS:
            raise _invalid_format_error(input_format)
        return normalized
    if input_file == STDIN_SENTINEL:
        raise _format_required_error("standard input")
    suffix = Path(input_file).suffix.lower()
    resolved = _EXTENSION_FORMATS.get(suffix)
    if resolved is None:
        raise _format_required_error(f"'{input_file}'")
    return resolved


def _read_text(input_file: str) -> str:
    if input_file == STDIN_SENTINEL:
        return sys.stdin.read()
    path = Path(input_file)
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise CliError(
            code="input_not_found",
            message=f"No input document found at '{input_file}'.",
            exit_status=EXIT_USAGE,
            hint="Check the path, or pass '-' to read from standard input.",
        ) from exc
    except OSError as exc:
        raise CliError(
            code="input_unreadable",
            message=f"Could not read the input document at '{input_file}'.",
            exit_status=EXIT_USAGE,
        ) from exc


def _parse(text: str, fmt: str) -> Any:
    try:
        if fmt == _JSON_FORMAT:
            return json.loads(text)
        return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise CliError(
            code=CODE_INVALID_INPUT_DOCUMENT,
            message="The input document is not valid.",
            exit_status=EXIT_USAGE,
            hint=f"Provide a well-formed {fmt} object.",
        ) from exc


def load_input_document(input_file: str | None, input_format: str | None) -> dict[str, Any] | None:
    """Load and validate a structured request document.

    Args:
        input_file: The ``--input`` value: a filesystem path, ``"-"`` for
            standard input, or None when no document was requested.
        input_format: The ``--input-format`` value (``"json"`` or ``"yaml"``),
            or None to infer from the file extension. Required for stdin.

    Returns:
        The parsed document as a mapping, or None when ``input_file`` is None.

    Raises:
        CliError: With exit status :data:`EXIT_USAGE` when the format cannot be
            resolved, the source is missing or unreadable, the text does not
            parse, or the top-level value is not a mapping.
    """
    if input_file is None:
        return None
    fmt = _resolve_format(input_file, input_format)
    document = _parse(_read_text(input_file), fmt)
    if not isinstance(document, dict):
        raise CliError(
            code=CODE_INVALID_INPUT_DOCUMENT,
            message="The input document must be a mapping of fields.",
            exit_status=EXIT_USAGE,
            hint="Wrap the request fields in a top-level object.",
        )
    return document
