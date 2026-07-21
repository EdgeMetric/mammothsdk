#!/usr/bin/env python3
"""Deterministic metadata extraction from the pinned OpenAPI snapshot.

Shared by the manifest builder and the parity report. No network access.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")
SPEC_DIR = Path(__file__).resolve().parent.parent / "spec" / "openapi"
SNAPSHOT_PATH = SPEC_DIR / "openapi.json"

_REF = re.compile(r"#/components/schemas/(?P<name>[A-Za-z0-9_.]+)")


def load_snapshot() -> dict[str, Any]:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def _schema_names(node: Any, out: list[str]) -> None:
    """Collect referenced schema names from a schema node (shallow union-aware)."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str):
            match = _REF.search(ref)
            if match:
                name = match.group("name")
                if name not in out:
                    out.append(name)
            return
        for key in ("oneOf", "anyOf", "allOf"):
            for item in node.get(key, []) or []:
                _schema_names(item, out)
        # items/additionalProperties for arrays/maps of refs
        if "items" in node:
            _schema_names(node["items"], out)


def _request_schema(operation: dict[str, Any]) -> str | None:
    content = operation.get("requestBody", {}).get("content", {})
    for media in ("application/json", "multipart/form-data"):
        schema = content.get(media, {}).get("schema")
        if schema:
            names: list[str] = []
            _schema_names(schema, names)
            return names[0] if names else None
    return None


def _response_schemas(operation: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for code, response in sorted(operation.get("responses", {}).items()):
        # Only success responses (2xx) carry the meaningful result contract.
        if not str(code).startswith("2"):
            continue
        content = response.get("content", {})
        schema = content.get("application/json", {}).get("schema")
        if schema:
            _schema_names(schema, names)
    return names


def normalize_path(path: str) -> str:
    return path


def identity(method: str, path: str) -> str:
    return f"{method.upper()} {normalize_path(path)}"


def iter_operations(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Return one metadata dict per HTTP operation, sorted by path then method."""
    global_security = document.get("security", [])
    records: list[dict[str, Any]] = []
    for path in sorted(document.get("paths", {})):
        path_item = document["paths"][path]
        if not isinstance(path_item, dict):
            continue
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue
            security = operation.get("security", global_security)
            scheme_names: list[str] = []
            for requirement in security or []:
                for scheme in requirement:
                    if scheme not in scheme_names:
                        scheme_names.append(scheme)
            records.append(
                {
                    "identity": identity(method, path),
                    "method": method.upper(),
                    "path": path,
                    "operation_id": operation.get("operationId"),
                    "tags": operation.get("tags", []),
                    "summary": operation.get("summary", ""),
                    "security": scheme_names,
                    "request_schema": _request_schema(operation),
                    "response_schemas": _response_schemas(operation),
                    "deprecated": bool(operation.get("deprecated", False)),
                }
            )
    records.sort(key=lambda record: (record["path"], record["method"]))
    return records


if __name__ == "__main__":
    ops = iter_operations(load_snapshot())
    print(f"operations: {len(ops)}")
    print(f"with request schema: {sum(1 for op in ops if op['request_schema'])}")
    print(f"deprecated: {sum(1 for op in ops if op['deprecated'])}")
