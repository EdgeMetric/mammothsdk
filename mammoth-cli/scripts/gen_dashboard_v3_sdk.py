#!/usr/bin/env python3
"""Generate typed dashboard endpoint wrappers for newly pinned operations."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import black
from _command_map import OVERRIDES

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "mammoth-cli/spec/openapi/openapi.json"
OUTPUT = ROOT / "mammoth/api/dashboard_generated.py"
METHODS = {"get", "put", "post", "delete", "patch"}

_SCALAR_ANNOTATIONS = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "object": "dict[str, Any]",
}


def schema_annotation(schema: dict[str, object]) -> str:
    """Translate an OpenAPI parameter schema into a Python annotation."""
    variants = schema.get("oneOf") or schema.get("anyOf")
    if isinstance(variants, list):
        annotations = [
            schema_annotation(item)
            for item in variants
            if isinstance(item, dict) and item.get("type") != "null"
        ]
        if any(isinstance(item, dict) and item.get("type") == "null" for item in variants):
            annotations.append("None")
        return " | ".join(dict.fromkeys(annotations)) or "Any"

    schema_type = schema.get("type")
    if schema_type == "array":
        items = schema.get("items")
        item_annotation = schema_annotation(items) if isinstance(items, dict) else "Any"
        return f"list[{item_annotation}]"
    if isinstance(schema_type, list):
        annotations = [
            "None" if item == "null" else _SCALAR_ANNOTATIONS.get(str(item), "Any")
            for item in schema_type
        ]
        return " | ".join(dict.fromkeys(annotations))
    return _SCALAR_ANNOTATIONS.get(str(schema_type), "Any")


def build() -> str:
    document = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    dashboard_source = (ROOT / "mammoth/api/dashboards.py").read_text(encoding="utf-8")
    dashboard_class = next(
        node
        for node in ast.parse(dashboard_source).body
        if isinstance(node, ast.ClassDef) and node.name == "DashboardsAPI"
    )
    handwritten = {
        node.name
        for node in dashboard_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    lines = [
        '"""Generated public dashboard API wrappers. Do not edit by hand."""',
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
    ]
    exports: list[str] = []
    for path, item in document["paths"].items():
        for method, operation in item.items():
            if method not in METHODS or not set(operation.get("tags", [])) & {
                "Dashboard",
                "Dashboard v3",
                "Dashboard v3 Q&A",
                "Dashboard v3 Surfaces",
            }:
                continue
            command = OVERRIDES.get(operation["operationId"])
            if not command or not command.startswith("dashboard."):
                continue
            name = command.removeprefix("dashboard.").replace(".", "_").replace("-", "_")
            if name in handwritten:
                continue
            parameters = [
                p
                for p in item.get("parameters", []) + operation.get("parameters", [])
                if "$ref" not in p
            ]
            args = ["self: Any"]
            for parameter in parameters:
                annotation = schema_annotation(parameter.get("schema", {}))
                default = "" if parameter.get("required") else " = None"
                if default and "None" not in annotation.split(" | "):
                    annotation += " | None"
                args.append(f"{parameter['name']}: {annotation}{default}")
            if "requestBody" in operation:
                required = bool(operation["requestBody"].get("required"))
                args.append("body: dict[str, Any]" + ("" if required else " | None = None"))
            summary = operation.get("summary") or operation["operationId"]
            lines.extend(
                [
                    f"def {name}({', '.join(args)}) -> Any:",
                    f'    """{summary.strip().rstrip(".")}."""',
                    f"    path = {path!r}",
                ]
            )
            for parameter in parameters:
                if parameter["in"] == "path":
                    marker = "{" + parameter["name"] + "}"
                    lines.append(f"    path = path.replace({marker!r}, str({parameter['name']}))")
            query_names = [p["name"] for p in parameters if p["in"] == "query"]
            if query_names:
                pairs = ", ".join(f"{n!r}: {n}" for n in query_names)
                lines.append(
                    "    params = {key: value for key, value in "
                    f"{{{pairs}}}.items() if value is not None}}"
                )
            else:
                lines.append("    params = None")
            body_arg = ", json=body" if "requestBody" in operation else ""
            lines.extend(
                [
                    "    return self._client._request_json("
                    f"{method.upper()!r}, path, params=params{body_arg})",
                    "",
                ]
            )
            exports.append(name)
    lines.append(f"GENERATED_METHODS = {exports!r}")
    return black.format_str("\n".join(lines) + "\n", mode=black.Mode(line_length=100))


if __name__ == "__main__":
    OUTPUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUTPUT}")
