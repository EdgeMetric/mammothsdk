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
import math
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

# Admission limits are deliberately finite and explicit.  They bound the
# amount of input read before parsing and the nesting accepted by the parser;
# they are not a claim that every backend or output path has the same limits.
MAX_INPUT_BYTES = 1_048_576
MAX_INPUT_DEPTH = 100

CODE_INPUT_TOO_LARGE = "input_too_large"
CODE_INPUT_TOO_DEEP = "input_too_deep"
CODE_INVALID_INPUT_ENCODING = "invalid_input_encoding"
CODE_DUPLICATE_INPUT_KEY = "duplicate_input_key"
CODE_NONFINITE_INPUT_NUMBER = "nonfinite_input_number"


class _DuplicateKeyError(ValueError):
    """Internal marker raised by the strict JSON object-pairs hook."""


class _NonFiniteNumberError(ValueError):
    """Internal marker raised by the strict JSON constant hook."""


class _StrictYamlLoader(yaml.SafeLoader):
    """Safe YAML loader that does not silently apply last-key-wins parsing."""


def _construct_yaml_mapping(
    loader: _StrictYamlLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    # PyYAML's stubs leave ``construct_object`` untyped.
    construct: Any = loader.construct_object
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = construct(key_node, deep=deep)
        if key in mapping:
            raise _DuplicateKeyError
        mapping[key] = construct(value_node, deep=deep)
    return mapping


_StrictYamlLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_yaml_mapping
)


def _limit_error(code: str, message: str, hint: str) -> CliError:
    return CliError(code=code, message=message, exit_status=EXIT_USAGE, hint=hint)


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
    if input_file.lstrip().startswith("{"):
        return _JSON_FORMAT
    suffix = Path(input_file).suffix.lower()
    resolved = _EXTENSION_FORMATS.get(suffix)
    if resolved is None:
        raise _format_required_error(f"'{input_file}'")
    return resolved


def _read_bytes(input_file: str) -> bytes:
    """Read one bounded source payload without decoding it implicitly."""
    limit = MAX_INPUT_BYTES + 1
    if input_file == STDIN_SENTINEL:
        stream = getattr(sys.stdin, "buffer", sys.stdin)
        raw = stream.read(limit)
        if isinstance(raw, str):
            try:
                raw = raw.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise CliError(
                    code=CODE_INVALID_INPUT_ENCODING,
                    message="The input document is not valid UTF-8.",
                    exit_status=EXIT_USAGE,
                    hint="Provide a UTF-8 encoded JSON or YAML document.",
                ) from exc
        return raw
    if input_file.lstrip().startswith("{"):
        return input_file.encode("utf-8")
    path = Path(input_file)
    try:
        with path.open("rb") as handle:
            return handle.read(limit)
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


def _strip_at_prefix(input_file: str) -> str:
    """Accept the ``@path`` file convention of curl and gh.

    A value that starts with ``@`` and names an existing file is read from
    that file; anything else (inline JSON, ``-``, a plain path) is returned
    unchanged so an error still quotes what the caller typed.
    """
    if len(input_file) > 1 and input_file.startswith("@") and Path(input_file[1:]).is_file():
        return input_file[1:]
    return input_file


def _read_text(input_file: str) -> str:
    """Read and strictly decode one input payload.

    This function remains a small named seam for callers/tests that instrument
    source reads.  It performs exactly one underlying read for each invocation.
    """
    raw = _read_bytes(input_file)
    if len(raw) > MAX_INPUT_BYTES:
        raise _limit_error(
            CODE_INPUT_TOO_LARGE,
            "The input document exceeds the maximum size of 1 MiB.",
            "Pass a smaller document or use a supported file/import operation.",
        )
    if input_file == STDIN_SENTINEL:
        source = "standard input"
    else:
        source = "the input document"
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CliError(
            code=CODE_INVALID_INPUT_ENCODING,
            message=f"The input from {source} is not valid UTF-8.",
            exit_status=EXIT_USAGE,
            hint="Provide a UTF-8 encoded JSON or YAML document.",
        ) from exc


def _check_json_depth(text: str) -> None:
    """Reject over-deep JSON before handing it to the recursive decoder."""
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > MAX_INPUT_DEPTH:
                raise _limit_error(
                    CODE_INPUT_TOO_DEEP,
                    "The input document exceeds the maximum nesting depth.",
                    f"Reduce nesting to at most {MAX_INPUT_DEPTH} levels.",
                )
        elif character in "]}":
            depth = max(depth - 1, 0)


def _check_yaml_depth(text: str) -> None:
    """Reject indentation that could create an unbounded YAML tree."""
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indentation = len(line) - len(line.lstrip(" "))
        if indentation > MAX_INPUT_DEPTH:
            raise _limit_error(
                CODE_INPUT_TOO_DEEP,
                "The input document exceeds the maximum nesting depth.",
                f"Reduce nesting to at most {MAX_INPUT_DEPTH} levels.",
            )


def _check_loaded_depth(value: Any) -> None:
    """Bound parsed YAML mappings/sequences without recursive traversal."""
    pending: list[tuple[Any, int]] = [(value, 1)]
    visited: set[int] = set()
    while pending:
        current, depth = pending.pop()
        if not isinstance(current, (dict, list)):
            continue
        marker = id(current)
        if marker in visited:
            continue
        visited.add(marker)
        if depth > MAX_INPUT_DEPTH:
            raise _limit_error(
                CODE_INPUT_TOO_DEEP,
                "The input document exceeds the maximum nesting depth.",
                f"Reduce nesting to at most {MAX_INPUT_DEPTH} levels.",
            )
        children = current.values() if isinstance(current, dict) else current
        pending.extend((child, depth + 1) for child in children)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise _NonFiniteNumberError


def _parse_finite_float(value: str) -> float:
    """Parse JSON numbers while rejecting exponent overflow to infinity."""
    parsed = float(value)
    if not math.isfinite(parsed):
        raise _NonFiniteNumberError
    return parsed


def _contains_nonfinite(value: Any) -> bool:
    """Find YAML float NaN/Infinity without recursive Python calls."""
    pending = [value]
    visited: set[int] = set()
    while pending:
        current = pending.pop()
        if isinstance(current, (dict, list)):
            marker = id(current)
            if marker in visited:
                continue
            visited.add(marker)
        if isinstance(current, float) and not math.isfinite(current):
            return True
        if isinstance(current, dict):
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)
    return False


def _parse(text: str, fmt: str) -> Any:
    try:
        if fmt == _JSON_FORMAT:
            _check_json_depth(text)
            return json.loads(
                text,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_nonfinite,
                parse_float=_parse_finite_float,
            )
        _check_yaml_depth(text)
        document = yaml.load(text, Loader=_StrictYamlLoader)  # noqa: S506
        _check_loaded_depth(document)
        if _contains_nonfinite(document):
            raise _NonFiniteNumberError
        return document
    except _DuplicateKeyError as exc:
        raise CliError(
            code=CODE_DUPLICATE_INPUT_KEY,
            message="The input document contains a duplicate object key.",
            exit_status=EXIT_USAGE,
            hint="Use each object key exactly once.",
        ) from exc
    except _NonFiniteNumberError as exc:
        raise CliError(
            code=CODE_NONFINITE_INPUT_NUMBER,
            message="The input document contains a non-finite number.",
            exit_status=EXIT_USAGE,
            hint="Use a finite JSON number instead of NaN or Infinity.",
        ) from exc
    except (json.JSONDecodeError, yaml.YAMLError, RecursionError) as exc:
        raise CliError(
            code=CODE_INVALID_INPUT_DOCUMENT,
            message="The input document is not valid.",
            exit_status=EXIT_USAGE,
            hint=f"Provide a well-formed {fmt} object.",
        ) from exc


def load_input_document(input_file: str | None, input_format: str | None) -> dict[str, Any] | None:
    """Load and validate a structured request document.

    Args:
        input_file: The ``--input`` value: inline JSON, a filesystem path,
            ``"-"`` for standard input, or None when no document was requested.
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
    input_file = _strip_at_prefix(input_file)
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
