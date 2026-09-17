"""Recursive normalization of SDK return values into plain JSON-safe data.

Normalizes dicts, lists, tuples, sets, Pydantic models, dataclasses, enums,
paths, dates, and objects exposing a ``to_dict``/``model_dump``. Sessions,
clients, and secret-bearing objects are never serialized. Object keys are sorted
so snapshots are deterministic.
"""

from __future__ import annotations

import dataclasses
import datetime
import decimal
import enum
import ipaddress
import math
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_SECRET_KEY_HINTS = (
    "api_secret",
    "apisecret",
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "secure_key",
    "securekey",
    "private_key",
    "token",
    "access_key",
    "secret_key",
    "client_secret",
)
REDACTED = "***REDACTED***"
_SCHEMA_PROPERTY_CONTAINERS = frozenset({"properties", "patternProperties", "$defs", "definitions"})
_SCHEMA_VALUE_KEYWORDS = frozenset({"default", "example", "examples", "const"})


class _NormalizedJsonSchema(dict[str, Any]):
    """A JSON-safe schema mapping that retains declaration provenance.

    The renderer defensively calls :func:`normalize` after ``Result`` already
    normalized its data.  This narrow marker lets that second pass preserve
    property names from a trusted model schema without treating arbitrary
    result fields named ``schema`` as declarations.
    """


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    # ``token_count`` is ordinary result metadata (for example an LLM usage
    # counter), not a credential.  Do not let the broad token guard erase it.
    if lowered in {"token_count", "next_token", "continuation_token", "design_tokens"}:
        return False
    return any(hint in lowered for hint in _SECRET_KEY_HINTS)


def _is_secret_value(value: Any) -> bool:
    """Return whether ``value`` is an explicitly typed secret wrapper.

    Key-name redaction is useful for ordinary mappings, but SDK/Pydantic models
    can carry a ``SecretStr`` under an innocuous field name.  Never coerce such
    wrappers to text: some implementations expose their real value from an
    accessor or a Python-mode model dump.
    """
    value_type = type(value)
    return value_type.__name__ in {"SecretStr", "SecretBytes"} or (
        "secret" in value_type.__name__.lower()
        and hasattr(value, "get_secret_value")
    )


def _typed_cursor_value(value: Any) -> Any | None:
    """Extract an opaque cursor wrapper without inspecting arbitrary objects."""
    if not type(value).__name__.lower().endswith("cursor"):
        return None
    candidate = getattr(value, "value", None)
    return candidate if isinstance(candidate, (str, int, float, bool, type(None))) else None


def _normalize_json_schema(value: Any, *, sensitive_property: bool = False) -> Any:
    """Normalize a trusted JSON-Schema declaration without losing field names.

    ``properties.api_key`` is a declaration name, while an ``api_key`` in an
    ordinary API result is a credential value.  This helper is used only for
    objects that explicitly expose ``model_json_schema`` and distinguishes
    those two cases.  Defaults/examples for credential-shaped properties are
    still redacted.
    """
    if isinstance(value, Mapping):
        result: _NormalizedJsonSchema = _NormalizedJsonSchema()
        for key in sorted(value, key=str):
            str_key = str(key)
            child = value[key]
            if str_key in _SCHEMA_PROPERTY_CONTAINERS and isinstance(child, Mapping):
                result[str_key] = {
                    str(name): _normalize_json_schema(
                        declaration, sensitive_property=_is_secret_key(str(name))
                    )
                    for name, declaration in sorted(child.items(), key=lambda item: str(item[0]))
                }
            elif sensitive_property and str_key in _SCHEMA_VALUE_KEYWORDS:
                result[str_key] = REDACTED
            else:
                result[str_key] = _normalize_json_schema(
                    child, sensitive_property=sensitive_property
                )
        return result
    if isinstance(value, (list, tuple)):
        return [
            _normalize_json_schema(item, sensitive_property=sensitive_property) for item in value
        ]
    return normalize(value)


def normalize(value: Any, *, redact_secrets: bool = True) -> Any:
    """Return a deterministic, JSON-safe representation of ``value``."""
    if redact_secrets and _is_secret_value(value):
        return REDACTED
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        # ``json.dumps`` otherwise emits JavaScript-incompatible NaN/Infinity,
        # making an otherwise successful machine result unparseable.
        return value if math.isfinite(value) else str(value)
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(
        value, (uuid.UUID, decimal.Decimal, ipaddress.IPv4Address, ipaddress.IPv6Address)
    ):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    cursor_value = _typed_cursor_value(value)
    if cursor_value is not None:
        return normalize(cursor_value, redact_secrets=redact_secrets)

    # Pydantic v2 models.
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        return normalize(dump(mode="python"), redact_secrets=redact_secrets)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return normalize(dataclasses.asdict(value), redact_secrets=redact_secrets)

    if isinstance(value, _NormalizedJsonSchema):
        return _normalize_json_schema(value)

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value, key=str):
            str_key = str(key)
            if redact_secrets and _is_secret_key(str_key):
                result[str_key] = REDACTED
            else:
                result[str_key] = normalize(value[key], redact_secrets=redact_secrets)
        return result
    if isinstance(value, (list, tuple)):
        return [normalize(item, redact_secrets=redact_secrets) for item in value]
    if isinstance(value, (set, frozenset)):
        return [normalize(item, redact_secrets=redact_secrets) for item in sorted(value, key=str)]

    # A generic object exposing to_dict.
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return normalize(to_dict(), redact_secrets=redact_secrets)

    # Schema objects are declarations, not result instances.  Preserve their
    # JSON-safe schema instead of falling back to a version-dependent repr.
    model_json_schema = getattr(value, "model_json_schema", None)
    if callable(model_json_schema):
        return _normalize_json_schema(model_json_schema())

    # Views and other rich objects: expose safe public data if available.
    for attr in ("data", "raw", "__dict__"):
        candidate = getattr(value, attr, None)
        if isinstance(candidate, dict):
            return normalize(
                {k: v for k, v in candidate.items() if not str(k).startswith("_")},
                redact_secrets=redact_secrets,
            )
    return str(value)
