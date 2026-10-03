"""Build and check the conditional-format rule body ``view conditional-format create`` sends.

The release route takes ``{"cf_type": "RULE", "payload": {"FORMAT", "CONDITION"}}``. One
rule can cover many columns: ``FORMAT.applies_to`` is ``"columns"`` with ``column_ids`` (a
JSON-encoded list of internal names) or ``"row"``, and ``CONDITION`` is an OR/AND group over
any columns. The typed input fields build exactly that, so a threshold on nine columns is one
rule, not nine.
"""

from __future__ import annotations

import json
from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.services.conditions import compile_condition

CODE_INVALID_RULE = "invalid_rule"
APPLIES_TO = ("row", "columns")
_EMPTY_COLUMN_IDS = "[]"
TYPED_FIELDS = ("columns", "operator", "value", "color", "name", "applies_to")
_NO_VALUE_OPERATORS = frozenset({"IS_EMPTY", "IS_NOT_EMPTY"})


def _invalid(message: str, hint: str | None = None) -> CliError:
    return CliError(code=CODE_INVALID_RULE, message=message, exit_status=EXIT_USAGE, hint=hint)


def _check_format(fmt: Any) -> None:
    """Mirror the backend's FORMAT validation so a bad rule fails before any request."""
    if not isinstance(fmt, dict):
        raise _invalid("A RULE payload needs a FORMAT object.")
    applies_to = fmt.get("applies_to")
    if applies_to not in APPLIES_TO:
        raise _invalid(
            f"FORMAT.applies_to must be one of {', '.join(APPLIES_TO)}; got {applies_to!r}.",
            "Use 'row' to colour whole rows, or 'columns' with column_ids.",
        )
    column_ids = fmt.get("column_ids", _EMPTY_COLUMN_IDS)
    empty = column_ids == _EMPTY_COLUMN_IDS
    if applies_to == "row" and not empty:
        raise _invalid("FORMAT.column_ids must be '[]' when applies_to is 'row'.")
    if applies_to == "columns" and empty:
        raise _invalid("FORMAT.column_ids must not be '[]' when applies_to is 'columns'.")


def validate_rule(rule: Any) -> None:
    """Raise ``invalid_rule`` when a raw rule's FORMAT has a bad ``applies_to``/``column_ids``.

    Everything else about the body (cf_type, CONDITION) is left to the backend, which
    owns those shapes; only the FORMAT enum was reaching it unchecked.
    """
    payload = rule.get("payload") if isinstance(rule, dict) else None
    if isinstance(payload, dict) and "FORMAT" in payload:
        _check_format(payload["FORMAT"])


def _resolve_columns(names: Any, column_map: dict[str, str]) -> list[str]:
    if not isinstance(names, list) or not names or not all(isinstance(n, str) for n in names):
        raise _invalid("'columns' must be a non-empty list of column names.")
    missing = [name for name in names if name not in column_map]
    if missing:
        raise _invalid(
            f"Unknown column(s): {', '.join(missing)}.",
            "Use display names of the view's columns: " + ", ".join(sorted(column_map)),
        )
    return list(dict.fromkeys(names))


def _leaf(column: str, document: dict[str, Any]) -> dict[str, Any]:
    leaf: dict[str, Any] = {"column": column, "operator": document["operator"]}
    if "value" in document:
        leaf["value"] = document["value"]
    return leaf


def _require_typed(document: dict[str, Any]) -> None:
    for field in ("columns", "operator", "color"):
        if document.get(field) is None:
            raise _invalid(
                f"The typed form needs '{field}'.",
                'One rule over many columns: --input \'{"columns": ["A", "B"], '
                '"operator": "<", "value": 55, "color": "red"}\'.',
            )


def build_rule(
    document: dict[str, Any], column_map: dict[str, str], column_types: dict[str, str]
) -> dict[str, Any]:
    """One RULE entry from the typed fields: an OR over ``columns``, applied to them or the row."""
    _require_typed(document)
    names = _resolve_columns(document["columns"], column_map)
    conditions = [
        compile_condition(_leaf(name, document)).build(column_map, column_types) for name in names
    ]
    applies_to = document.get("applies_to") or "columns"
    column_ids = json.dumps([column_map[n] for n in names]) if applies_to == "columns" else "[]"
    operator = str(document["operator"])
    label = (
        operator
        if operator.upper() in _NO_VALUE_OPERATORS
        else f"{operator} {document.get('value')}"
    )
    fmt = {
        "name": document.get("name") or f"{', '.join(names)} {label}"[:80],
        "color": document["color"],
        "applies_to": applies_to,
        "column_ids": column_ids,
    }
    rule = {"cf_type": "RULE", "payload": {"FORMAT": fmt, "CONDITION": {"OR": conditions}}}
    validate_rule(rule)
    return rule
