"""Recursive normalization of SDK return values into plain JSON-safe data.

Normalizes dicts, lists, tuples, sets, Pydantic models, dataclasses, enums,
paths, dates, and objects exposing a ``to_dict``/``model_dump``. Sessions,
clients, and secret-bearing objects are never serialized. Object keys are sorted
so snapshots are deterministic.
"""

from __future__ import annotations

import dataclasses
import datetime
import enum
from pathlib import Path
from typing import Any

_SECRET_KEY_HINTS = (
    "api_secret",
    "apisecret",
    "secret",
    "password",
    "passwd",
    "private_key",
    "token",
    "access_key",
    "secret_key",
    "client_secret",
)
REDACTED = "***REDACTED***"


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(hint in lowered for hint in _SECRET_KEY_HINTS)


def normalize(value: Any, *, redact_secrets: bool = True) -> Any:
    """Return a deterministic, JSON-safe representation of ``value``."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    # Pydantic v2 models.
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        return normalize(dump(mode="python"), redact_secrets=redact_secrets)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return normalize(dataclasses.asdict(value), redact_secrets=redact_secrets)

    if isinstance(value, dict):
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

    # Views and other rich objects: expose safe public data if available.
    for attr in ("data", "raw", "__dict__"):
        candidate = getattr(value, attr, None)
        if isinstance(candidate, dict):
            return normalize(
                {k: v for k, v in candidate.items() if not str(k).startswith("_")},
                redact_secrets=redact_secrets,
            )
    return str(value)
