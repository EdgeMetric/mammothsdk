"""Auto-discovering dispatcher for the Mammoth SDK bridge.

Scans ``mammoth.__init__.__all__`` at import time to build registries of
enums and dataclasses.  Dispatches JSON-RPC-style calls to View instances,
ViewsResource, ViewExport, and MammothClient sub-clients — no hardcoded
method list, so new SDK methods are picked up automatically.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any, get_type_hints

import mammoth
from mammoth import MammothClient
from mammoth.client import ViewsResource
from mammoth.condition import CompoundCondition, Condition, NotCondition
from mammoth.view import View, ViewExport

# ── Auto-discovery registries ──────────────────────────────────

ENUM_REGISTRY: dict[str, type[Enum]] = {}
DATACLASS_REGISTRY: dict[str, type[Any]] = {}

for _name in mammoth.__all__:
    _obj = getattr(mammoth, _name, None)
    if _obj is None:
        continue
    if isinstance(_obj, type):
        if issubclass(_obj, Enum):
            ENUM_REGISTRY[_name] = _obj
        elif dataclasses.is_dataclass(_obj):
            DATACLASS_REGISTRY[_name] = _obj


# ── Enum / dataclass helpers ──────────────────────────────────

def resolve_enum(enum_cls: type[Enum], value: Any) -> Enum:
    """Resolve a string to an enum member (by name or value)."""
    if isinstance(value, enum_cls):
        return value
    s = str(value)
    # Try by name first (e.g. "GTE"), then by value (e.g. "year")
    try:
        return enum_cls[s]
    except KeyError:
        pass
    for member in enum_cls:
        if member.value == s:
            return member
    raise ValueError(f"Cannot resolve {s!r} to {enum_cls.__name__}. "
                     f"Valid: {[m.name for m in enum_cls]}")


def _find_enum_for_field(field_type: Any) -> type[Enum] | None:
    """If field_type is an Enum subclass (or Optional[EnumSubclass]), return it."""
    origin = getattr(field_type, "__origin__", None)
    # Handle Optional[X] = Union[X, None]
    if origin is not None:
        args = getattr(field_type, "__args__", ())
        for arg in args:
            if isinstance(arg, type) and issubclass(arg, Enum):
                return arg
        return None
    if isinstance(field_type, type) and issubclass(field_type, Enum):
        return field_type
    return None


def convert_dataclass(cls: type[Any], data: dict[str, Any]) -> Any:
    """Recursively convert a dict into a dataclass instance.

    Resolves enum-typed fields and nested Condition objects automatically.
    """
    if not isinstance(data, dict):
        return data

    try:
        hints = get_type_hints(cls)
    except Exception:
        hints = {}

    kwargs: dict[str, Any] = {}
    for f in dataclasses.fields(cls):
        if f.name not in data:
            continue
        val = data[f.name]
        hint = hints.get(f.name)

        # Condition-typed fields (e.g. SetValue.condition)
        if f.name == "condition" and isinstance(val, dict):
            kwargs[f.name] = build_condition(val)
            continue

        # Enum resolution
        if hint is not None:
            enum_cls = _find_enum_for_field(hint)
            if enum_cls is not None and val is not None:
                kwargs[f.name] = resolve_enum(enum_cls, val)
                continue

        kwargs[f.name] = val

    return cls(**kwargs)


# ── Condition tree builder ────────────────────────────────────

def build_condition(data: dict[str, Any]) -> Condition | CompoundCondition | NotCondition:
    """Recursively build a Condition tree from a JSON dict.

    Formats:
        {"column": "X", "operator": "GTE", "value": 1000}
        {"and": [<condition>, ...]}
        {"or":  [<condition>, ...]}
        {"not": <condition>}
    """
    if "and" in data:
        children = [build_condition(c) for c in data["and"]]
        return CompoundCondition("AND", children)
    if "or" in data:
        children = [build_condition(c) for c in data["or"]]
        return CompoundCondition("OR", children)
    if "not" in data:
        return NotCondition(build_condition(data["not"]))

    # Leaf condition
    column = data["column"]
    operator = data["operator"]
    value = data.get("value")
    extra: dict[str, Any] = {}
    for key in ("case_sensitive", "value_is_column", "component", "truncate"):
        if key in data:
            extra[key] = data[key]
    return Condition(column, operator, value, **extra)


# ── Type-aware argument conversion ────────────────────────────

def _get_element_type(hint: Any) -> type | None:
    """Extract T from list[T] annotations."""
    origin = getattr(hint, "__origin__", None)
    if origin is list or origin is list:
        args = getattr(hint, "__args__", ())
        return args[0] if args else None
    return None


def convert_args(method: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Convert raw JSON args to SDK types using method type hints."""
    try:
        hints = get_type_hints(method)
    except Exception:
        hints = {}

    converted: dict[str, Any] = {}
    for key, val in args.items():
        hint = hints.get(key)

        # Condition parameters
        if key == "condition" and isinstance(val, dict):
            converted[key] = build_condition(val)
            continue

        # Enum parameters (by type hint)
        if hint is not None:
            enum_cls = _find_enum_for_field(hint)
            if enum_cls is not None and val is not None:
                converted[key] = resolve_enum(enum_cls, val)
                continue

        # Enum parameters (by name heuristic — e.g. filter_type, join_type)
        if isinstance(val, str) and key.endswith("_type") and hint is None:
            for reg_cls in ENUM_REGISTRY.values():
                try:
                    converted[key] = resolve_enum(reg_cls, val)
                    break
                except ValueError:
                    continue
            else:
                converted[key] = val
            continue

        # list[Dataclass] parameters
        if isinstance(val, list) and val and isinstance(val[0], dict):
            elem_type = _get_element_type(hint) if hint else None
            if elem_type and dataclasses.is_dataclass(elem_type):
                converted[key] = [convert_dataclass(elem_type, item) for item in val]
                continue
            # Heuristic: check dataclass registry by singular key name
            singular = key.rstrip("s")
            for dc_name, dc_cls in DATACLASS_REGISTRY.items():
                if dc_name.lower() == singular or dc_name.lower() == key:
                    converted[key] = [convert_dataclass(dc_cls, item) for item in val]
                    break
            else:
                converted[key] = val
            continue

        # Single dataclass parameter
        if isinstance(val, dict) and hint is not None:
            raw_hint = hint
            # Unwrap Optional
            origin = getattr(raw_hint, "__origin__", None)
            if origin is not None:
                for arg in getattr(raw_hint, "__args__", ()):
                    if isinstance(arg, type) and dataclasses.is_dataclass(arg):
                        raw_hint = arg
                        break
            if isinstance(raw_hint, type) and dataclasses.is_dataclass(raw_hint):
                converted[key] = convert_dataclass(raw_hint, val)
                continue

        converted[key] = val

    return converted


# ── Serialization ─────────────────────────────────────────────

def serialize(obj: Any) -> Any:
    """Convert SDK return values to JSON-serializable form."""
    if obj is None:
        return None
    if isinstance(obj, View):
        return {
            "id": obj.id,
            "name": obj.name,
            "dataset_id": obj.dataset_id,
            "columns": obj.columns,
            "display_names": obj.display_names,
            "column_types": obj.column_types,
        }
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serialize(item) for item in obj]
    if hasattr(obj, "__fspath__"):
        return str(obj)
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: serialize(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    return str(obj)


# ── Dispatcher ────────────────────────────────────────────────

class Dispatcher:
    """Routes ``method`` strings to SDK calls.

    Namespace resolution:
        view.<method>          → View instance (needs view_id)
        view.export.<method>   → ViewExport on the View
        views.<method>         → ViewsResource (get/list/create/delete)
        client.<method>        → MammothClient method
        client.<sub>.<method>  → Sub-client (e.g. client.projects.list)
    """

    def __init__(self, client: MammothClient) -> None:
        self.client = client
        self._view_cache: dict[int, View] = {}

    def _get_view(self, view_id: int) -> View:
        """Fetch a View, using the cache for subsequent calls."""
        if view_id not in self._view_cache:
            self._view_cache[view_id] = self.client.views.get(view_id)
        return self._view_cache[view_id]

    def list_methods(self) -> dict[str, list[str]]:
        """Return all available methods grouped by namespace."""
        result: dict[str, list[str]] = {}

        # View methods (public, non-dunder, callable)
        view_methods = [
            name for name in dir(View)
            if not name.startswith("_") and callable(getattr(View, name, None))
        ]
        result["view"] = sorted(view_methods)

        # ViewExport methods
        export_methods = [
            name for name in dir(ViewExport)
            if not name.startswith("_") and callable(getattr(ViewExport, name, None))
        ]
        result["view.export"] = sorted(export_methods)

        # ViewsResource methods
        views_methods = [
            name for name in dir(ViewsResource)
            if not name.startswith("_") and callable(getattr(ViewsResource, name, None))
        ]
        result["views"] = sorted(views_methods)

        # Client methods
        client_methods = [
            name for name in dir(MammothClient)
            if not name.startswith("_") and callable(getattr(MammothClient, name, None))
        ]
        result["client"] = sorted(client_methods)

        # Sub-clients
        for attr_name in sorted(dir(self.client)):
            if attr_name.startswith("_"):
                continue
            attr = getattr(self.client, attr_name, None)
            if attr is None or isinstance(attr, (str, int, float, bool)):
                continue
            if hasattr(attr, "__module__") and "mammoth.api" in getattr(attr, "__module__", ""):
                sub_methods = [
                    name for name in dir(attr)
                    if not name.startswith("_") and callable(getattr(attr, name, None))
                ]
                if sub_methods:
                    result[f"client.{attr_name}"] = sorted(sub_methods)

        return result

    def dispatch(
        self,
        method: str,
        view_id: int | None = None,
        args: dict[str, Any] | None = None,
    ) -> Any:
        """Dispatch a method call and return the serialized result."""
        args = args or {}
        parts = method.split(".")

        # ── view.export.<method> ──
        if len(parts) == 3 and parts[0] == "view" and parts[1] == "export":
            if view_id is None:
                raise ValueError("view_id is required for view.export.* methods")
            view = self._get_view(view_id)
            fn = getattr(view.export, parts[2])
            converted = convert_args(fn, args)
            result = fn(**converted)
            return serialize(result)

        # ── view.<method> ──
        if len(parts) == 2 and parts[0] == "view":
            if view_id is None:
                raise ValueError("view_id is required for view.* methods")
            view = self._get_view(view_id)
            fn = getattr(view, parts[1])
            converted = convert_args(fn, args)
            result = fn(**converted)
            return serialize(result)

        # ── views.<method> ──
        if len(parts) == 2 and parts[0] == "views":
            fn = getattr(self.client.views, parts[1])
            converted = convert_args(fn, args)
            result = fn(**converted)
            return serialize(result)

        # ── client.<sub>.<method> ──
        if len(parts) == 3 and parts[0] == "client":
            sub = getattr(self.client, parts[1])
            fn = getattr(sub, parts[2])
            converted = convert_args(fn, args)
            result = fn(**converted)
            return serialize(result)

        # ── client.<method> ──
        if len(parts) == 2 and parts[0] == "client":
            fn = getattr(self.client, parts[1])
            converted = convert_args(fn, args)
            result = fn(**converted)
            return serialize(result)

        raise ValueError(
            f"Unknown method {method!r}. "
            "Use view.<m>, view.export.<m>, views.<m>, client.<m>, or client.<sub>.<m>"
        )
