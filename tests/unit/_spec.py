"""Access to the pinned prod OpenAPI spec, the independent oracle for contract tests."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

SPEC_PATH = (
    Path(__file__).resolve().parents[2] / "mammoth-cli" / "spec" / "openapi" / "openapi.json"
)


@cache
def spec() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(SPEC_PATH.read_text())
    return loaded


def schema(name: str) -> dict[str, Any]:
    found: dict[str, Any] = spec()["components"]["schemas"][name]
    return found


def operations() -> dict[str, dict[str, Any]]:
    """Every operation keyed by operationId: ``{"method", "path", "op"}``."""
    out: dict[str, dict[str, Any]] = {}
    for path, item in spec()["paths"].items():
        for method, op in item.items():
            if method in ("get", "post", "put", "patch", "delete") and "operationId" in op:
                out[op["operationId"]] = {"method": method.upper(), "path": path, "op": op}
    return out
