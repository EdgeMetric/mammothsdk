"""Request-body schemas for SDK methods whose annotation is only ``dict``."""

from __future__ import annotations

import copy
import json
from functools import cache
from pathlib import Path
from typing import Any, cast

from mammoth_cli.manifest.loader import command_by_id

_OPENAPI_PATH = Path(__file__).resolve().parents[2] / "spec" / "openapi" / "openapi.json"


@cache
def _document() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(_OPENAPI_PATH.read_text(encoding="utf-8")))


@cache
def _operations() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path_item in _document().get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict) and operation.get("operationId"):
                result[str(operation["operationId"])] = operation
    return result


def _rewrite_refs(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                item.replace("#/components/schemas/", "#/$defs/")
                if key == "$ref" and isinstance(item, str)
                else _rewrite_refs(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_rewrite_refs(item) for item in value]
    return value


def _referenced_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            names.add(ref.rsplit("/", 1)[-1])
        for item in value.values():
            names.update(_referenced_names(item))
    elif isinstance(value, list):
        for item in value:
            names.update(_referenced_names(item))
    return names


@cache
def openapi_body_schema_for(operation_ids: tuple[str, ...]) -> dict[str, Any] | None:
    """Return a standalone request-body schema for explicit operation ids."""
    for operation_id in operation_ids:
        operation = _operations().get(str(operation_id), {})
        content = operation.get("requestBody", {}).get("content", {})
        media = content.get("application/json") or content.get("application/*+json")
        if not isinstance(media, dict) or not isinstance(media.get("schema"), dict):
            continue
        raw_schema = copy.deepcopy(media["schema"])
        all_definitions = _document().get("components", {}).get("schemas", {})
        pending = list(_referenced_names(raw_schema))
        selected: dict[str, Any] = {}
        while pending:
            name = pending.pop()
            if name in selected or name not in all_definitions:
                continue
            definition = copy.deepcopy(all_definitions[name])
            selected[name] = definition
            pending.extend(_referenced_names(definition) - set(selected))
        schema = _rewrite_refs(raw_schema)
        definitions = _rewrite_refs(selected)
        if definitions:
            schema["$defs"] = definitions
        return cast(dict[str, Any], schema)
    return None


def openapi_body_schema(command_id: str) -> dict[str, Any] | None:
    """Return a standalone request-body JSON Schema for a manifest command."""
    record = command_by_id(command_id)
    if record is None:
        return None
    return openapi_body_schema_for(tuple(str(item) for item in record.get("operation_ids", [])))


def sample_from_schema(schema: dict[str, Any]) -> Any:
    """Synthesize a non-empty JSON value from a bundled OpenAPI schema."""
    definitions = schema.get("$defs", {})

    def sample(
        node: dict[str, Any], seen: frozenset[str] = frozenset(), field_name: str | None = None
    ) -> Any:
        if "const" in node:
            return node["const"]
        if "default" in node:
            return node["default"]
        if "enum" in node and node["enum"]:
            return node["enum"][0]
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            name = ref.rsplit("/", 1)[-1]
            if name in seen:
                return {}
            return sample(definitions.get(name, {}), seen | {name}, field_name)
        for composition in ("oneOf", "anyOf", "allOf"):
            if node.get(composition):
                if composition == "allOf":
                    merged: dict[str, Any] = {}
                    for member in node[composition]:
                        value = sample(member, seen, field_name)
                        if isinstance(value, dict):
                            merged.update(value)
                    return merged
                return sample(node[composition][0], seen, field_name)
        kind = node.get("type")
        if isinstance(kind, list):
            kind = next((item for item in kind if item != "null"), "null")
        if kind == "object" or "properties" in node:
            properties = node.get("properties", {})
            required = list(node.get("required", []))
            if not required and properties:
                required.append(next(iter(properties)))
            return {
                name: sample(properties[name], seen, name)
                for name in required
                if name in properties
            }
        if kind == "array":
            return [sample(node.get("items", {}), seen)]
        if kind == "integer":
            return 1
        if kind == "number":
            # A non-integral number remains valid when schemas distinguish
            # ``number`` from ``integer`` with ``oneOf``.
            return 1.5
        if kind == "boolean":
            return True
        if kind == "null":
            return None
        string_samples = {
            "date": "2026-01-01",
            "date-time": "2026-01-01T00:00:00Z",
            "email": "agent@example.com",
            "uuid": "00000000-0000-4000-8000-000000000001",
            "uri": "https://example.com",
        }
        if kind == "string" and node.get("format") in string_samples:
            return string_samples[node["format"]]
        conventional_strings = {"op": "replace", "path": "role"}
        if kind == "string" and field_name in conventional_strings:
            return conventional_strings[field_name]
        return "example"

    return sample(schema)
