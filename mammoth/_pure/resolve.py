"""Pure column-resolution helpers — no HTTP, no View, no client.

All functions are stateless and take column metadata as plain dicts.

Column metadata convention:
    columns:        dict[str, str]  display_name -> internal_name
    internal_names: list[str]       all internal names (for bypass check)

A caller that already holds internal names can pass them directly; the
resolver accepts them as-is (same semantics as View._resolve_column).
"""

from __future__ import annotations

import random
import string
from collections.abc import Callable
from typing import Any


def resolve_column(
    name: str,
    columns: dict[str, str],
    internal_names: list[str],
) -> str:
    """Resolve a display name to its internal column name.

    Accepts either a display name (looked up in *columns*) or an internal
    name that is already in *internal_names* (pass-through).

    Args:
        name: Display name (e.g. "Sales") or internal name (e.g. "column_1").
        columns: Mapping of display_name -> internal_name.
        internal_names: List of all internal names (used for pass-through).

    Returns:
        Internal column name (e.g. "column_1").

    Raises:
        MammothColumnError: If *name* is neither a display name nor an
            internal name.
    """
    if name in columns:
        return columns[name]
    if name in internal_names:
        return name
    from mammoth.exceptions import MammothColumnError

    raise MammothColumnError(name, list(columns.keys()))


def resolve_columns(
    names: list[str],
    columns: dict[str, str],
    internal_names: list[str],
) -> list[str]:
    """Resolve multiple display names to internal column names.

    Args:
        names: List of display names or internal names.
        columns: Mapping of display_name -> internal_name.
        internal_names: List of all internal names.

    Returns:
        List of resolved internal column names.
    """
    return [resolve_column(n, columns, internal_names) for n in names]


def _default_name_gen() -> str:
    """Generate a random 10-char internal column name (mirrors View._next_internal_name)."""
    chars = string.ascii_lowercase + string.digits
    return f"column_{''.join(random.choices(chars, k=10))}"


def next_internal_name(name_gen: Callable[[], str] | None = None) -> str:
    """Generate a unique internal column name.

    Args:
        name_gen: Optional callable that returns a unique name string.
            Defaults to the same random scheme used by View._next_internal_name.
            Pass a deterministic generator in tests for reproducible output.

    Returns:
        A new internal column name string (e.g. "column_abc1234567").
    """
    return (name_gen or _default_name_gen)()


def build_as_column(
    name: str,
    column_type: str = "TEXT",
    internal_name: str | None = None,
    name_gen: Callable[[], str] | None = None,
) -> dict[str, str]:
    """Build an AS (new column) spec dict.

    Args:
        name: Display name for the new column.
        column_type: Column type string (e.g. "TEXT", "NUMERIC", "DATE").
            Case-normalized to uppercase.
        internal_name: Explicit internal name. If omitted, one is generated
            via *name_gen* (or the default random scheme).
        name_gen: Optional callable for generating internal names.

    Returns:
        Dict with COLUMN, TYPE, and INTERNAL_NAME keys.
    """
    return {
        "COLUMN": name,
        "TYPE": column_type.upper(),
        "INTERNAL_NAME": internal_name or next_internal_name(name_gen),
    }


def build_condition(
    condition: Any,
    columns: dict[str, str],
    column_types: dict[str, str] | None = None,
    internal_names: list[str] | None = None,
) -> dict[str, Any] | None:
    """Build a condition dict from a Condition object or raw dict.

    Args:
        condition: A Condition/CompoundCondition/NotCondition object, a raw
            dict (passed through unchanged), or None.
        columns: Mapping of display_name -> internal_name (used by Condition.build).
        column_types: Mapping of display_name -> type (passed to Condition.build
            for EQ/NE TEXT rewrite; mirrors View._build_condition).

    Returns:
        Condition dict, or None if *condition* is None.
    """
    if condition is None:
        return None
    if isinstance(condition, dict):
        return condition
    # Condition / CompoundCondition / NotCondition all implement .build(columns, column_types).
    # ``internal_names`` is intentionally an opt-in strictness seam: legacy
    # direct Condition.build callers may still use backend names, while View
    # operations validate every typed reference before submitting a task.
    if columns:
        _validate_condition_columns(
            condition,
            columns,
            internal_names if internal_names is not None else list(columns.values()),
        )
    return condition.build(columns, column_types)


def _validate_condition_columns(
    condition: Any, columns: dict[str, str], internal_names: list[str]
) -> None:
    """Validate all typed condition references without mutating a payload.

    Conditions can be nested and may compare one column to another. Walking
    the already-parsed condition object keeps this check scoped to identifiers;
    it never performs the unsafe substring replacement used by old callers.
    """
    from mammoth.condition import CompoundCondition, Condition, NotCondition

    if isinstance(condition, Condition):
        resolve_column(condition.column, columns, internal_names)
        if condition.value_is_column:
            if not isinstance(condition.value, str):
                raise ValueError("column-to-column condition value must be a column name")
            resolve_column(condition.value, columns, internal_names)
    elif isinstance(condition, CompoundCondition):
        for child in condition.conditions:
            _validate_condition_columns(child, columns, internal_names)
    elif isinstance(condition, NotCondition):
        _validate_condition_columns(condition.condition, columns, internal_names)


def resolve_order_by(
    order_by: list[list[str]],
    columns: dict[str, str],
) -> list[list[str]]:
    """Resolve display names in order_by specs to internal names.

    Args:
        order_by: List of [column_name, direction] pairs.
        columns: Mapping of display_name -> internal_name.

    Returns:
        List of [internal_name, direction] pairs.
    """
    resolved: list[list[str]] = []
    for ob in order_by:
        col_name = str(ob[0])
        col = columns.get(col_name, col_name)
        direction = ob[1] if len(ob) > 1 else "ASC"
        resolved.append([col, direction])
    return resolved
