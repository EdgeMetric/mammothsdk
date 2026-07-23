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

# OpenAPI validation keyword -> pydantic ``Field`` argument. ``minItems``/
# ``maxItems`` and ``minLength``/``maxLength`` both map onto pydantic's unified
# ``min_length``/``max_length`` (which constrain both strings and sequences).
# The order fixes the emitted keyword order so regeneration stays deterministic.
_CONSTRAINT_ARGUMENTS: list[tuple[str, str]] = [
    ("exclusiveMinimum", "gt"),
    ("exclusiveMaximum", "lt"),
    ("minimum", "ge"),
    ("maximum", "le"),
    ("multipleOf", "multiple_of"),
    ("minLength", "min_length"),
    ("maxLength", "max_length"),
    ("minItems", "min_length"),
    ("maxItems", "max_length"),
    ("pattern", "pattern"),
]

# Canonical anchored regex for a JSON-Schema ``format: uuid`` string. Applied as
# a pydantic ``pattern`` so the field stays a plain ``str`` -- it validates the
# shape while still serialising as a string in JSON (no ``UUID`` object).
_UUID_PATTERN = (
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# JSON-Schema ``format`` -> anchored regex emitted as a pydantic ``pattern``.
# Only formats that keep the field a plain ``str`` (guaranteed string JSON
# serialisation) *and* are genuinely constraining are mapped here. Formats that
# would need a non-``str`` type, or whose canonical regex is ambiguous, are left
# unconstrained on purpose rather than fabricating a partial rule.
_FORMAT_PATTERNS: dict[str, str] = {
    "uuid": _UUID_PATTERN,
}


def _ref_name(schema: dict[str, Any]) -> str | None:
    ref = schema.get("$ref")
    return str(ref).rsplit("/", 1)[-1] if ref else None


def _field_constraints(schema: dict[str, Any], *, apply_format: bool = True) -> list[str]:
    """Return ``Field(...)`` keyword fragments for every constraint on ``schema``.

    When ``apply_format`` is set (the strict request side), a recognised string
    ``format`` (e.g. ``uuid``) is translated into an anchored ``pattern``. The
    explicit spec ``pattern`` always wins: if the field already carries one, the
    format-derived pattern is skipped so there is never a conflicting double
    ``pattern=``. The lenient response side passes ``apply_format=False`` so
    forward-compatible/malformed server data still parses.
    """
    fragments: list[str] = []
    for keyword_name, argument in _CONSTRAINT_ARGUMENTS:
        if keyword_name in schema:
            fragments.append(f"{argument}={schema[keyword_name]!r}")
    if apply_format and "pattern" not in schema:
        fmt = schema.get("format")
        pattern = _FORMAT_PATTERNS.get(fmt) if isinstance(fmt, str) else None
        schema_type = schema.get("type")
        is_string = schema_type == "string" or (
            isinstance(schema_type, list) and "string" in schema_type
        )
        if pattern is not None and is_string:
            fragments.append(f"pattern={pattern!r}")
    return fragments


def schema_annotation(
    schema: dict[str, Any],
    *,
    response_context: bool = False,
    response_variants: frozenset[str] = frozenset(),
) -> str:
    """Translate an OpenAPI schema into a Python annotation.

    When ``response_context`` is set, ``$ref`` targets listed in
    ``response_variants`` resolve to their forward-compatible ``<Name>Response``
    variant instead of the strict request model.
    """
    ref = _ref_name(schema)
    if ref:
        if response_context and ref in response_variants:
            return f"{ref}Response"
        return ref
    if schema.get("type") == "null":
        return "None"
    variants = schema.get("oneOf") or schema.get("anyOf")
    if isinstance(variants, list):
        annotations = [
            schema_annotation(
                item, response_context=response_context, response_variants=response_variants
            )
            for item in variants
            if isinstance(item, dict)
        ]
        return " | ".join(dict.fromkeys(annotations)) or "Any"
    if "enum" in schema:
        values = ", ".join(repr(value) for value in schema["enum"])
        return f"Literal[{values}]"
    schema_type = schema.get("type")
    if schema_type == "array":
        items = schema.get("items")
        item_annotation = (
            schema_annotation(
                items, response_context=response_context, response_variants=response_variants
            )
            if isinstance(items, dict)
            else "Any"
        )
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


def _closure(document: dict[str, Any], seeds: list[dict[str, Any]]) -> set[str]:
    """Return every component schema reachable from ``seeds`` by ``$ref``."""
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

    for seed in seeds:
        visit(seed)
    return reachable


def _request_seeds(document: dict[str, Any]) -> list[dict[str, Any]]:
    seeds = []
    for _path, _method, operation in _dashboard_operations(document):
        body = _media_schema(operation.get("requestBody", {}))
        if body:
            seeds.append(body)
    return seeds


def _response_seeds(document: dict[str, Any]) -> list[dict[str, Any]]:
    seeds = []
    for _path, _method, operation in _dashboard_operations(document):
        seeds.extend(_success_schemas(operation))
    return seeds


def _reachable_components(document: dict[str, Any]) -> set[str]:
    return _closure(document, _request_seeds(document) + _response_seeds(document))


def _response_only_components(document: dict[str, Any]) -> set[str]:
    """Components reachable only from responses (never from a request body).

    Only these may safely tolerate additive server fields: request-reachable
    components stay strict so unknown ``--input`` body fields are still rejected.
    """
    return _closure(document, _response_seeds(document)) - _closure(
        document, _request_seeds(document)
    )


def _dual_use_components(document: dict[str, Any]) -> set[str]:
    """Object components reachable as BOTH a request and a response.

    A single class cannot serve both roles: the request side must stay strict
    (reject unknown body fields) while the response side must tolerate additive
    server fields. Each such component is emitted twice -- a strict ``<Name>``
    and a forward-compatible ``<Name>Response`` -- and references are rewired by
    role. Components whose OpenAPI definition forbids additional properties need
    no lenient variant and are excluded.
    """
    components = document.get("components", {}).get("schemas", {})
    shared = _closure(document, _request_seeds(document)) & _closure(
        document, _response_seeds(document)
    )
    dual: set[str] = set()
    for name in shared:
        schema = components.get(name, {})
        is_object = schema.get("type") == "object" or isinstance(schema.get("properties"), dict)
        if is_object and schema.get("additionalProperties") is not False:
            dual.add(name)
    return dual


def build_models() -> str:
    """Build Pydantic models for every dashboard request/response schema used."""
    document = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    components = document["components"]["schemas"]
    names = sorted(_reachable_components(document))
    response_only = _response_only_components(document)
    request_reachable = _closure(document, _request_seeds(document))
    dual_use = _dual_use_components(document)
    response_variants = frozenset(dual_use)

    def render_class(
        class_name: str, schema: dict[str, Any], extra: str, response_context: bool
    ) -> list[str]:
        block = [
            f"class {class_name}(BaseModel):",
            f'    model_config = ConfigDict(extra="{extra}")',
        ]
        required = set(schema.get("required", []))
        properties = schema.get("properties")
        if not properties:
            block.append("    pass")
        for field, field_schema in (properties or {}).items():
            annotation = schema_annotation(
                field_schema,
                response_context=response_context,
                response_variants=response_variants,
            )
            default = "" if field in required else " = None"
            if default and "None" not in annotation.split(" | "):
                annotation += " | None"
            constraints = _field_constraints(field_schema, apply_format=not response_context)
            if constraints:
                annotation = f"Annotated[{annotation}, Field({', '.join(constraints)})]"
            block.append(f"    {field}: {annotation}{default}")
        block.append("")
        return block

    body: list[str] = []
    emitted: list[str] = []
    for name in names:
        if not name.isidentifier() or keyword.iskeyword(name):
            raise ValueError(f"OpenAPI component is not a Python identifier: {name}")
        schema = components[name]
        properties = schema.get("properties")
        # A response-only schema whose OpenAPI definition permits additional
        # properties (``additionalProperties`` absent or not ``false``) must
        # tolerate additive server fields; forbidding them rejects valid,
        # forward-compatible responses. Request-reachable schemas stay strict.
        lenient = name in response_only and schema.get("additionalProperties") is not False
        extra = "allow" if lenient else "forbid"
        if schema.get("type") == "object" or isinstance(properties, dict):
            # A response-only container renders references to dual-use
            # components as their lenient ``<Name>Response`` variant; a
            # request-reachable container keeps the strict variant. A dual-use
            # component itself is request-reachable, so its primary class stays
            # strict and a separate ``<Name>Response`` variant is emitted below.
            primary_response_context = name not in request_reachable
            body.extend(
                render_class(name, schema, extra, response_context=primary_response_context)
            )
            emitted.append(name)
            if name in dual_use:
                variant = f"{name}Response"
                if variant in components or variant in names:
                    raise ValueError(f"response variant name collides with a component: {variant}")
                body.extend(render_class(variant, schema, "allow", response_context=True))
                emitted.append(variant)
        else:
            body.extend([f"class {name}(RootModel[{schema_annotation(schema)}]):", "    pass", ""])
            emitted.append(name)

    needs_field = any("Annotated[" in line for line in body)
    typing_imports = (
        "from typing import Annotated, Any, Literal"
        if needs_field
        else "from typing import Any, Literal"
    )
    pydantic_imports = (
        "from pydantic import BaseModel, ConfigDict, Field, RootModel"
        if needs_field
        else "from pydantic import BaseModel, ConfigDict, RootModel"
    )
    lines = [
        "# ruff: noqa: N801, N815",
        '"""Generated dashboard request and response models. Do not edit by hand."""',
        "from __future__ import annotations",
        "",
        typing_imports,
        "",
        pydantic_imports,
        "",
    ]
    lines.extend(body)
    lines.extend(
        [
            "_MODEL_NAMESPACE = {",
            "    name: value for name, value in globals().items() if isinstance(value, type)",
            "}",
            f"for _model_name in {emitted!r}:",
            "    globals()[_model_name].model_rebuild(_types_namespace=_MODEL_NAMESPACE)",
            "",
            f"__all__ = {emitted!r}",
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
        "def _typed_response(",
        "    response: Any,",
        "    models: tuple[type[BaseModel], ...],",
        "    *,",
        "    allow_untyped: bool = False,",
        ") -> Any:",
        '    """Coerce ``response`` into the best-matching model.',
        "",
        "    Response models tolerate additive server fields, so more than one may",
        "    validate a payload. The best match is the model that populates the most",
        "    declared fields (ties broken toward the model with more fields). When the",
        "    operation also documents an untyped branch (``allow_untyped``) and no model",
        "    is a positive match, the raw response is returned instead of raising -- so a",
        "    valid arbitrary-object response is never rejected.",
        '    """',
        "    ranked = sorted(models, key=lambda model: len(model.model_fields), reverse=True)",
        "    best: Any = None",
        "    best_score = -1",
        "    last_error: ValidationError | None = None",
        "    for model in ranked:",
        "        try:",
        "            validated = model.model_validate(response)",
        "        except ValidationError as error:",
        "            last_error = error",
        "            continue",
        "        if isinstance(response, dict):",
        "            score = sum(",
        "                1",
        "                for name, field in model.model_fields.items()",
        "                if (field.alias or name) in response or name in response",
        "            )",
        "        else:",
        "            score = 0",
        "        if score > best_score:",
        "            best, best_score = validated, score",
        "    if best is not None and (best_score > 0 or not allow_untyped):",
        "        return best",
        "    if allow_untyped:",
        "        return response",
        "    if last_error is not None:",
        "        raise last_error",
        '    raise ValueError("typed response requires at least one model")',
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
        opaque = {"dict[str, Any]", "Any"}
        named_responses = [item for item in response_types if item not in opaque]
        has_untyped = any(item in opaque for item in response_types)
        if named_responses:
            model_tuple = ", ".join(named_responses)
            if len(named_responses) == 1:
                model_tuple += ","
            lines.append(
                f"    return _typed_response(response, ({model_tuple}), "
                f"allow_untyped={has_untyped})"
            )
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
