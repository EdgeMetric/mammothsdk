"""Recursive JSON-shape descriptions, examples, and validation for SDK types."""

from __future__ import annotations

import enum
import types
import typing
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints

from mammoth import condition as _condition_module
from pydantic import BaseModel, ValidationError

from mammoth_cli.services.argspec import _sdk_type_namespace, render_type_name

_UNIONS = (typing.Union, types.UnionType)
_CONDITION_TYPES = (
    _condition_module.Condition,
    _condition_module.CompoundCondition,
    _condition_module.NotCondition,
)


class TypeValidationError(ValueError):
    """A JSON value does not conform to its SDK annotation."""

    def __init__(self, path: str, expected: str, value: Any) -> None:
        self.path = path
        self.expected = expected
        self.value = value
        super().__init__(f"{path} must be {expected}, got {value!r}")


def is_opaque_mapping(annotation: Any) -> bool:
    """Whether an annotation is an unstructured JSON mapping needing OpenAPI detail."""
    origin = get_origin(annotation)
    if origin in _UNIONS:
        members = [item for item in get_args(annotation) if item is not type(None)]
        return len(members) == 1 and is_opaque_mapping(members[0])
    if origin not in (dict, typing.Dict):  # noqa: UP006
        return False
    args = get_args(annotation)
    return not args or (len(args) == 2 and args[1] is Any)


def _condition_schema() -> dict[str, Any]:
    leaf = {
        "type": "object",
        "properties": {
            "column": {"type": "string", "example": "Status"},
            "operator": {"type": "string", "example": "EQ"},
            "value": {"example": "Active"},
            "case_sensitive": {"type": "boolean"},
            "value_is_column": {"type": "boolean"},
            "component": {"type": "string"},
            "truncate": {"type": "string"},
            "value_is_date_fn": {"type": "boolean"},
        },
        "required": ["column", "operator"],
        "additionalProperties": False,
    }
    compound = {
        "oneOf": [
            leaf,
            {
                "type": "object",
                "properties": {
                    "and": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"$ref": "#/$defs/condition"},
                    }
                },
                "required": ["and"],
                "additionalProperties": False,
            },
            {
                "type": "object",
                "properties": {
                    "or": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"$ref": "#/$defs/condition"},
                    }
                },
                "required": ["or"],
                "additionalProperties": False,
            },
            {
                "type": "object",
                "properties": {"not": {"$ref": "#/$defs/condition"}},
                "required": ["not"],
                "additionalProperties": False,
            },
        ]
    }
    return {
        **compound,
        "$defs": {"condition": compound},
        "example": {"column": "Status", "operator": "EQ", "value": "Active"},
    }


def json_schema(annotation: Any) -> dict[str, Any]:
    """Describe an annotation as recursive, JSON-Schema-like data."""
    if annotation is None or annotation is Any:
        return {}
    if annotation in _CONDITION_TYPES:
        return _condition_schema()
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in _UNIONS:
        return {"anyOf": [json_schema(member) for member in args]}
    if origin in (list, typing.List):  # noqa: UP006
        return {"type": "array", "items": json_schema(args[0]) if args else {}}
    if origin in (dict, typing.Dict):  # noqa: UP006
        return {
            "type": "object",
            "additionalProperties": json_schema(args[1]) if len(args) > 1 else {},
        }
    if origin is typing.Literal:
        return {"enum": list(args)}
    if annotation is type(None):
        return {"type": "null"}
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        values = [member.value for member in annotation]
        return {"type": "string", "enum": values, "example": values[0]}
    if is_dataclass(annotation):
        hints = get_type_hints(annotation, localns=_sdk_type_namespace())
        properties: dict[str, Any] = {}
        required: list[str] = []
        for field in fields(annotation):
            properties[field.name] = json_schema(hints.get(field.name, Any))
            if field.default is MISSING and field.default_factory is MISSING:
                required.append(field.name)
        result: dict[str, Any] = {
            "type": "object",
            "title": getattr(annotation, "__name__", str(annotation)),
            "properties": properties,
            "additionalProperties": False,
        }
        if required:
            result["required"] = required
        result["example"] = sample_value(annotation)
        return result
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        result = annotation.model_json_schema()
        result["example"] = sample_value(annotation)
        return result
    scalar = {str: "string", bool: "boolean", int: "integer", float: "number"}.get(annotation)
    if scalar:
        return {"type": scalar, "example": sample_value(annotation)}
    if annotation is Path or (isinstance(annotation, type) and issubclass(annotation, Path)):
        return {"type": "string", "format": "path", "example": "example.csv"}
    return {"title": render_type_name(annotation)}


def sample_value(annotation: Any) -> Any:
    """Return a non-empty, semantically useful JSON example for an annotation."""
    if annotation is None or annotation is Any:
        return "example"
    if annotation in _CONDITION_TYPES:
        return {"column": "Status", "operator": "EQ", "value": "Active"}
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in _UNIONS:
        members = [member for member in args if member is not type(None)]
        return sample_value(members[0]) if members else None
    if origin in (list, typing.List):  # noqa: UP006
        return [sample_value(args[0] if args else Any)]
    if origin in (dict, typing.Dict):  # noqa: UP006
        return {"example": sample_value(args[1] if len(args) > 1 else Any)}
    if origin is typing.Literal:
        return args[0] if args else None
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return next(iter(annotation)).value
    if is_dataclass(annotation):
        hints = get_type_hints(annotation, localns=_sdk_type_namespace())
        return {
            field.name: sample_value(hints.get(field.name, Any))
            for field in fields(annotation)
            if field.default is MISSING and field.default_factory is MISSING
        }
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        from mammoth_cli.services.openapi_types import sample_from_schema

        return sample_from_schema(annotation.model_json_schema())
    if annotation is bool:
        return True
    if annotation is int:
        return 1
    if annotation is float:
        return 1.0
    if annotation is str:
        return "example"
    if annotation is Path or (isinstance(annotation, type) and issubclass(annotation, Path)):
        return "example.csv"
    return "example"


def validate_value(value: Any, annotation: Any, path: str) -> Any:
    """Recursively validate and scalar-coerce a JSON value."""
    if annotation is None or annotation is Any:
        return value
    if annotation in _CONDITION_TYPES:
        from mammoth_cli.services.conditions import compile_condition

        try:
            compile_condition(value)
        except Exception as error:  # noqa: BLE001 - normalized to type-system error
            raise TypeValidationError(path, "a valid condition object", value) from error
        return value
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in _UNIONS:
        errors: list[TypeValidationError] = []
        for member in args:
            try:
                return validate_value(value, member, path)
            except TypeValidationError as error:
                errors.append(error)
        raise TypeValidationError(path, render_type_name(annotation), value) from (
            errors[-1] if errors else None
        )
    if origin in (list, typing.List):  # noqa: UP006
        if not isinstance(value, list):
            raise TypeValidationError(path, "array", value)
        inner = args[0] if args else Any
        return [validate_value(item, inner, f"{path}[{index}]") for index, item in enumerate(value)]
    if origin in (dict, typing.Dict):  # noqa: UP006
        if not isinstance(value, dict):
            raise TypeValidationError(path, "object", value)
        key_type, value_type = args if len(args) == 2 else (Any, Any)
        return {
            validate_value(key, key_type, f"{path}.<key>"): validate_value(
                item, value_type, f"{path}.{key}"
            )
            for key, item in value.items()
        }
    if origin is typing.Literal:
        if value not in args:
            raise TypeValidationError(path, f"one of {list(args)!r}", value)
        return value
    if annotation is type(None):
        if value is not None:
            raise TypeValidationError(path, "null", value)
        return None
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        if isinstance(value, annotation):
            return value
        try:
            return annotation(value).value
        except (ValueError, TypeError):
            raise TypeValidationError(
                path, f"one of {[m.value for m in annotation]!r}", value
            ) from None
    if is_dataclass(annotation):
        if not isinstance(value, dict):
            raise TypeValidationError(path, "object", value)
        declared = {field.name: field for field in fields(annotation)}
        unknown = sorted(set(value) - set(declared))
        if unknown:
            raise TypeValidationError(f"{path}.{unknown[0]}", "a declared field", value[unknown[0]])
        hints = get_type_hints(annotation, localns=_sdk_type_namespace())
        result: dict[str, Any] = {}
        for name, field in declared.items():
            if name not in value:
                if field.default is MISSING and field.default_factory is MISSING:
                    raise TypeValidationError(f"{path}.{name}", "a required field", None)
                continue
            result[name] = validate_value(value[name], hints.get(name, Any), f"{path}.{name}")
        return result
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        if not isinstance(value, dict):
            raise TypeValidationError(path, "object", value)
        try:
            annotation.model_validate(value)
        except ValidationError as error:
            location = ".".join(str(part) for part in error.errors()[0]["loc"])
            raise TypeValidationError(
                f"{path}.{location}" if location else path, annotation.__name__, value
            ) from error
        return value
    if annotation is bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in {"true", "1", "yes", "y", "on"}:
            return True
        if isinstance(value, str) and value.strip().lower() in {"false", "0", "no", "n", "off"}:
            return False
        raise TypeValidationError(path, "boolean", value)
    if annotation is int:
        if isinstance(value, bool):
            raise TypeValidationError(path, "integer", value)
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            try:
                return int(value.strip())
            except ValueError:
                pass
        raise TypeValidationError(path, "integer", value)
    if annotation is float:
        if isinstance(value, bool):
            raise TypeValidationError(path, "number", value)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.strip())
            except ValueError:
                pass
        raise TypeValidationError(path, "number", value)
    if annotation is str:
        if not isinstance(value, str):
            raise TypeValidationError(path, "string", value)
        return value
    if annotation is Path or (isinstance(annotation, type) and issubclass(annotation, Path)):
        if not isinstance(value, (str, Path)):
            raise TypeValidationError(path, "path string", value)
        return str(value)
    if annotation is typing.BinaryIO:
        if not isinstance(value, str):
            raise TypeValidationError(path, "path string", value)
        return value
    if isinstance(annotation, type):
        if not isinstance(value, annotation):
            raise TypeValidationError(path, annotation.__name__, value)
    return value
