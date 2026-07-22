#!/usr/bin/env python3
"""Generate typed dashboard models and endpoint wrappers from pinned OpenAPI."""

from __future__ import annotations

import ast
import json
import keyword
from pathlib import Path
from typing import Any

import black
from _command_map import OVERRIDES

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "mammoth-cli/spec/openapi/openapi.json"
OUTPUT = ROOT / "mammoth/api/dashboard_generated.py"
MODELS_OUTPUT = ROOT / "mammoth/models/dashboard_generated.py"
METHODS = {"get", "put", "post", "delete", "patch"}
TAGS = {"Dashboard", "Dashboard v3", "Dashboard v3 Q&A", "Dashboard v3 Surfaces"}

_SCALAR_ANNOTATIONS = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "object": "dict[str, Any]",
}


def _ref_name(schema: dict[str, Any]) -> str | None:
    ref = schema.get("$ref")
    return str(ref).rsplit("/", 1)[-1] if ref else None


def schema_annotation(schema: dict[str, Any]) -> str:
    """Translate an OpenAPI schema into a Python annotation."""
    ref = _ref_name(schema)
    if ref:
        return ref
    if schema.get("type") == "null":
        return "None"
    variants = schema.get("oneOf") or schema.get("anyOf")
    if isinstance(variants, list):
        annotations = [schema_annotation(item) for item in variants if isinstance(item, dict)]
        return " | ".join(dict.fromkeys(annotations)) or "Any"
    if "enum" in schema:
        values = ", ".join(repr(value) for value in schema["enum"])
        return f"Literal[{values}]"
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


def _dashboard_operations(document: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    operations = []
    for path, item in document["paths"].items():
        for method, operation in item.items():
            if method in METHODS and set(operation.get("tags", [])) & TAGS:
                operations.append((path, method, operation))
    return operations


def _media_schema(container: dict[str, Any]) -> dict[str, Any] | None:
    content = container.get("content", {})
    media = content.get("application/json") or next(iter(content.values()), None)
    schema = media.get("schema") if isinstance(media, dict) else None
    return schema if isinstance(schema, dict) and schema else None


def _success_schemas(operation: dict[str, Any]) -> list[dict[str, Any]]:
    schemas = []
    for status, response in operation.get("responses", {}).items():
        if str(status).startswith("2") and isinstance(response, dict):
            schema = _media_schema(response)
            variants = schema.get("oneOf") or schema.get("anyOf") if schema else None
            candidates = variants if isinstance(variants, list) else ([schema] if schema else [])
            for candidate in candidates:
                if isinstance(candidate, dict) and candidate not in schemas:
                    schemas.append(candidate)
    return schemas


def _reachable_components(document: dict[str, Any]) -> set[str]:
    components = document.get("components", {}).get("schemas", {})
    reachable: set[str] = set()

    def visit(schema: Any) -> None:
        if isinstance(schema, dict):
            ref = _ref_name(schema)
            if ref and ref not in reachable and ref in components:
                reachable.add(ref)
                visit(components[ref])
            for value in schema.values():
                visit(value)
        elif isinstance(schema, list):
            for value in schema:
                visit(value)

    for _path, _method, operation in _dashboard_operations(document):
        body = _media_schema(operation.get("requestBody", {}))
        if body:
            visit(body)
        for schema in _success_schemas(operation):
            visit(schema)
    return reachable


def build_models() -> str:
    """Build Pydantic models for every dashboard request/response schema used."""
    document = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    components = document["components"]["schemas"]
    lines = [
        "# ruff: noqa: N801, N815",
        '"""Generated dashboard request and response models. Do not edit by hand."""',
        "from __future__ import annotations",
        "",
        "from typing import Any, Literal",
        "",
        "from pydantic import BaseModel, ConfigDict, RootModel",
        "",
    ]
    names = sorted(_reachable_components(document))
    for name in names:
        if not name.isidentifier() or keyword.iskeyword(name):
            raise ValueError(f"OpenAPI component is not a Python identifier: {name}")
        schema = components[name]
        properties = schema.get("properties")
        if schema.get("type") == "object" or isinstance(properties, dict):
            lines.extend(
                [f"class {name}(BaseModel):", '    model_config = ConfigDict(extra="forbid")']
            )
            required = set(schema.get("required", []))
            if not properties:
                lines.append("    pass")
            for field, field_schema in (properties or {}).items():
                annotation = schema_annotation(field_schema)
                default = "" if field in required else " = None"
                if default and "None" not in annotation.split(" | "):
                    annotation += " | None"
                lines.append(f"    {field}: {annotation}{default}")
            lines.append("")
        else:
            lines.extend([f"class {name}(RootModel[{schema_annotation(schema)}]):", "    pass", ""])
    lines.extend(
        [
            "_MODEL_NAMESPACE = {",
            "    name: value for name, value in globals().items() if isinstance(value, type)",
            "}",
            f"for _model_name in {names!r}:",
            "    globals()[_model_name].model_rebuild(_types_namespace=_MODEL_NAMESPACE)",
            "",
            f"__all__ = {names!r}",
        ]
    )
    return black.format_str("\n".join(lines) + "\n", mode=black.Mode(line_length=100))


def build() -> str:
    """Build typed wrappers for dashboard operations absent from the handwritten API."""
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
        "# ruff: noqa: F401, I001",
        '"""Generated public dashboard API wrappers. Do not edit by hand."""',
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "from pydantic import BaseModel, ValidationError",
        "",
        "from mammoth.models.dashboard_generated import (",
        *[f"    {name}," for name in sorted(_reachable_components(document))],
        ")",
        "",
        "def _json_body(body: BaseModel | dict[str, Any]) -> dict[str, Any]:",
        "    if isinstance(body, BaseModel):",
        '        return body.model_dump(mode="json", by_alias=True, exclude_none=True)',
        "    return body",
        "",
        "def _typed_response(response: Any, models: tuple[type[BaseModel], ...]) -> Any:",
        "    ranked = sorted(models, key=lambda model: len(model.model_fields), reverse=True)",
        "    last_error: ValidationError | None = None",
        "    for model in ranked:",
        "        try:",
        "            return model.model_validate(response)",
        "        except ValidationError as error:",
        "            last_error = error",
        "    if last_error is None:",
        '        raise ValueError("typed response requires at least one model")',
        "    raise last_error",
        "",
    ]
    exports: list[str] = []
    for path, method, operation in _dashboard_operations(document):
        command = OVERRIDES.get(operation["operationId"])
        if not command or not command.startswith("dashboard."):
            continue
        name = command.removeprefix("dashboard.").replace(".", "_").replace("-", "_")
        if name in handwritten:
            continue
        parameters = [
            p
            for p in document["paths"][path].get("parameters", []) + operation.get("parameters", [])
            if "$ref" not in p
        ]
        args = ["self: Any"]
        for parameter in parameters:
            annotation = schema_annotation(parameter.get("schema", {}))
            default = "" if parameter.get("required") else " = None"
            if default and "None" not in annotation.split(" | "):
                annotation += " | None"
            args.append(f"{parameter['name']}: {annotation}{default}")
        body_schema = _media_schema(operation.get("requestBody", {}))
        if body_schema:
            annotation = schema_annotation(body_schema)
            required = bool(operation["requestBody"].get("required"))
            args.append(f"body: {annotation}" + ("" if required else " | None = None"))
        responses = _success_schemas(operation)
        response_types = [schema_annotation(schema) for schema in responses]
        result_annotation = " | ".join(dict.fromkeys(response_types)) or "dict[str, Any]"
        summary = operation.get("summary") or operation["operationId"]
        lines.extend(
            [
                f"def {name}({', '.join(args)}) -> {result_annotation}:",
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
        body_arg = ", json=_json_body(body)" if body_schema else ""
        lines.append(
            "    response = self._client._request_json("
            f"{method.upper()!r}, path, params=params{body_arg})"
        )
        named_responses = [item for item in response_types if item != "dict[str, Any]"]
        if named_responses:
            model_tuple = ", ".join(named_responses)
            if len(named_responses) == 1:
                model_tuple += ","
            lines.append(f"    return _typed_response(response, ({model_tuple}))")
        else:
            lines.append("    return response")
        lines.append("")
        exports.append(name)
    lines.append(f"GENERATED_METHODS = {exports!r}")
    return black.format_str("\n".join(lines) + "\n", mode=black.Mode(line_length=100))


if __name__ == "__main__":
    MODELS_OUTPUT.write_text(build_models(), encoding="utf-8")
    OUTPUT.write_text(build(), encoding="utf-8")
    print(f"wrote {MODELS_OUTPUT} and {OUTPUT}")
