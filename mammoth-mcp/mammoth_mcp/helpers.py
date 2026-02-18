"""Helper utilities for Mammoth MCP tools."""

from __future__ import annotations

from typing import Any

from mammoth import (
    CompoundCondition,
    Condition,
    Operator,
)


def build_condition(d: dict[str, Any]) -> Condition | CompoundCondition:
    """Convert a JSON-friendly dict into SDK Condition objects.

    Supports two forms:
        Simple:   {"column": "Sales", "operator": "GTE", "value": 1000}
        Compound: {"logic": "AND", "conditions": [<cond>, <cond>]}

    Operator names match the Operator enum (GTE, IN_LIST, IS_EMPTY, etc.).
    """
    if "logic" in d:
        inner = [build_condition(c) for c in d["conditions"]]
        if d["logic"].upper() == "AND":
            result = inner[0]
            for c in inner[1:]:
                result = result & c
            return result
        else:
            result = inner[0]
            for c in inner[1:]:
                result = result | c
            return result

    op_str = d["operator"].upper()
    op = Operator(op_str)
    return Condition(
        column=d["column"],
        operator=op,
        value=d.get("value"),
    )


def parse_math_expression(expression: str) -> str:
    """Pass-through — the SDK's math() method handles string parsing internally."""
    return expression


def format_view_info(view: Any) -> dict[str, Any]:
    """Format a View object into a JSON-serializable summary."""
    return {
        "id": view.id,
        "name": view.name,
        "dataset_id": view.dataset_id,
        "columns": [
            {"name": name, "internal_name": view.columns[name], "type": view.column_types.get(name, "TEXT")}
            for name in view.display_names
        ],
        "column_count": len(view.display_names),
    }


def resolve_enum(enum_cls: type, value: str) -> Any:
    """Resolve a string to an enum member, case-insensitive."""
    value_upper = value.upper()
    for member in enum_cls:
        if member.value == value_upper or member.name == value_upper:
            return member
    valid = [m.value for m in enum_cls]
    raise ValueError(f"Invalid value '{value}' for {enum_cls.__name__}. Valid: {valid}")


def error_response(error: Exception) -> dict[str, Any]:
    """Create a structured error response from an exception."""
    return {
        "success": False,
        "error": str(error),
        "error_type": type(error).__name__,
    }


def success_response(data: Any = None, message: str | None = None) -> dict[str, Any]:
    """Create a structured success response."""
    result: dict[str, Any] = {"success": True}
    if message:
        result["message"] = message
    if data is not None:
        result["data"] = data
    return result
