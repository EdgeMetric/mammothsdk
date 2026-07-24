"""Recursive JSON-shape descriptions, examples, and validation for SDK types."""

from __future__ import annotations

import enum
import types
import typing
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints

from mammoth import condition as _condition_module
from mammoth.view import View as _View
from pydantic import BaseModel, ValidationError

from mammoth_cli.services.argspec import _sdk_type_namespace, render_type_name

_UNIONS = (typing.Union, types.UnionType)
_CONDITION_TYPES = (
    _condition_module.Condition,
    _condition_module.CompoundCondition,
    _condition_module.NotCondition,
)
# SDK domain objects that a JSON ``--input`` document can only reference by their
# positive integer id (a live View instance cannot be expressed as JSON). A
# field annotated with one of these -- alone or as a union member such as
# ``int | View`` -- is a resource reference and must be a positive id.
_RESOURCE_DOMAIN_TYPES = (_View,)


def _is_resource_domain(annotation: Any) -> bool:
    """Whether an annotation is an SDK domain object referenced by id."""
    return isinstance(annotation, type) and issubclass(annotation, _RESOURCE_DOMAIN_TYPES)


def _is_resource_reference(annotation: Any) -> bool:
    """Whether an annotation resolves to a resource reference (id form)."""
    if _is_resource_domain(annotation):
        return True
    if get_origin(annotation) in _UNIONS:
        return any(_is_resource_domain(member) for member in get_args(annotation))
    return False


def _coerce_positive_id(value: Any, path: str) -> int:
    """Coerce ``value`` to a positive resource id, or raise."""
    if isinstance(value, bool):
        raise TypeValidationError(path, "positive resource ID", value)
    if isinstance(value, int):
        number = value
    elif isinstance(value, float) and value.is_integer():
        number = int(value)
    elif isinstance(value, str):
        try:
            number = int(value.strip())
        except ValueError:
            raise TypeValidationError(path, "positive resource ID", value) from None
    else:
        raise TypeValidationError(path, "positive resource ID", value)
    if number <= 0:
        raise TypeValidationError(path, "positive resource ID", value)
    return number


class TypeValidationError(ValueError):
    """A JSON value does not conform to its SDK annotation."""

    def __init__(self, path: str, expected: str, value: Any) -> None:
        self.path = path
        self.expected = expected
        self.value = value
        super().__init__(f"{path} must be {expected}, got {value!r}")


def _is_resource_id_path(path: str) -> bool:
    """Whether ``path`` names one resource ID or an item in an ID collection."""
    leaf = path.rsplit(".", 1)[-1]
    name, bracket, _index = leaf.partition("[")
    return name.endswith("_id") or (bool(bracket) and name.endswith("_ids"))


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


def json_schema(annotation: Any, field_name: str | None = None) -> dict[str, Any]:
    """Describe an annotation as recursive, JSON-Schema-like data."""
    if annotation is None or annotation is Any:
        return {}
    if annotation in _CONDITION_TYPES:
        return _condition_schema()
    if _is_resource_reference(annotation):
        return {
            "type": "integer",
            "minimum": 1,
            "example": 1,
            "description": "Positive id of the referenced resource.",
        }
    if annotation is typing.BinaryIO:
        return {"type": "string", "format": "path", "example": "example.csv"}
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in _UNIONS:
        return {"anyOf": [json_schema(member, field_name) for member in args]}
    if origin in (list, typing.List):  # noqa: UP006
        array_schema: dict[str, Any] = {
            "type": "array",
            "items": (
                json_schema(args[0], field_name.removesuffix("s") if field_name else None)
                if args
                else {}
            ),
        }
        if field_name and field_name.endswith("_ids"):
            array_schema["minItems"] = 1
        return array_schema
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
            properties[field.name] = json_schema(hints.get(field.name, Any), field.name)
            if field.default is MISSING and field.default_factory is MISSING:
                required.append(field.name)
        dataclass_schema: dict[str, Any] = {
            "type": "object",
            "title": getattr(annotation, "__name__", str(annotation)),
            "properties": properties,
            "additionalProperties": False,
        }
        if required:
            dataclass_schema["required"] = required
        dataclass_schema["example"] = sample_value(annotation)
        return dataclass_schema
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        model_schema = annotation.model_json_schema()
        model_schema["example"] = sample_value(annotation)
        return model_schema
    scalar = {str: "string", bool: "boolean", int: "integer", float: "number"}.get(annotation)
    if scalar:
        scalar_schema: dict[str, Any] = {
            "type": scalar,
            "example": sample_value(annotation),
        }
        if annotation is int and field_name and field_name.endswith("_id"):
            scalar_schema["minimum"] = 1
        return scalar_schema
    if annotation is Path or (isinstance(annotation, type) and issubclass(annotation, Path)):
        return {"type": "string", "format": "path", "example": "example.csv"}
    return {"title": render_type_name(annotation)}


def sample_value(annotation: Any) -> Any:
    """Return a non-empty, semantically useful JSON example for an annotation."""
    if annotation is None or annotation is Any:
        return "example"
    if annotation in _CONDITION_TYPES:
        return {"column": "Status", "operator": "EQ", "value": "Active"}
    if _is_resource_reference(annotation):
        return 1
    if annotation is typing.BinaryIO:
        return "example.csv"
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
    # A resource reference (a domain object such as ``View``, alone or in a
    # union like ``int | View``) can only be expressed in JSON as a positive id;
    # accept nothing else, so a negative or non-numeric id is rejected here
    # rather than by the server.
    if _is_resource_reference(annotation):
        return _coerce_positive_id(value, path)
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in _UNIONS:
        # For a numeric value, try non-``str`` members first so a ``str | int``
        # union keeps the number as a number; ``str`` only wins (coercing to
        # text) when no numeric member accepts it, as in a ``str | None`` id
        # field the server returned as a number.
        members = list(args)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            members = sorted(args, key=lambda member: member is str)
        errors: list[TypeValidationError] = []
        for member in members:
            try:
                return validate_value(value, member, path)
            except TypeValidationError as error:
                errors.append(error)
        # Preserve the most specific branch error (normally a nested member
        # path) instead of replacing it with an opaque top-level union error.
        if errors:
            raise errors[0]
        raise TypeValidationError(path, render_type_name(annotation), value)
    if origin in (list, typing.List):  # noqa: UP006
        if not isinstance(value, list):
            raise TypeValidationError(path, "array", value)
        if path.rsplit(".", 1)[-1].endswith("_ids") and not value:
            raise TypeValidationError(path, "non-empty array of positive resource IDs", value)
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
            coerced_int = value
            if _is_resource_id_path(path) and coerced_int <= 0:
                raise TypeValidationError(path, "positive resource ID", value)
            return coerced_int
        if isinstance(value, float) and value.is_integer():
            coerced_int = int(value)
            if _is_resource_id_path(path) and coerced_int <= 0:
                raise TypeValidationError(path, "positive resource ID", value)
            return coerced_int
        if isinstance(value, str):
            try:
                coerced_int = int(value.strip())
                if _is_resource_id_path(path) and coerced_int <= 0:
                    raise TypeValidationError(path, "positive resource ID", value)
                return coerced_int
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
        if isinstance(value, str):
            return value
        # Accept a JSON number where a string is expected and coerce it to its
        # string form. Servers return id-like fields (for example a folder's
        # ``resource_id``) as numbers, but the SDK types the corresponding
        # input (``folder_resource_id``) as a string; without this a user who
        # pastes the number straight from a create response hits a spurious
        # type error. Booleans are never strings here.
        if isinstance(value, bool):
            raise TypeValidationError(path, "string", value)
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        raise TypeValidationError(path, "string", value)
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
