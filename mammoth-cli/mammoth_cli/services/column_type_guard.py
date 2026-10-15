"""Refuse a date or math step on a column of the wrong type before any task is added.

Mammoth uploads numbers and ISO dates as NUMERIC and DATE, but a date in another format, or a
number column holding text such as ``N/A``, arrives as TEXT. Running ``extract-date`` or ``math``
on it makes the server add a task that later fails, after the caller has already been told the
step was accepted. The view's own metadata already says each column's type, so the CLI says it
first, names the column and its type, and gives the ``convert-type`` command that fixes a TEXT
column.
"""

from __future__ import annotations

import json
import re
import shlex
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError

CODE_COLUMN_TYPE_MISMATCH = "column_type_mismatch"

DATE = "DATE"
NUMERIC = "NUMERIC"
TEXT = "TEXT"


@dataclass(frozen=True)
class TypeCheck:
    """One column an operation reads, and the types the operation accepts there."""

    column: str
    accepts: frozenset[str]
    operation: str


def math_columns(expression: object, known: Iterable[str]) -> list[str]:
    """The known column names an expression text mentions, as whole words."""
    text = str(expression)
    return [name for name in known if re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", text)]


def check_column_types(view_id: int, types: Mapping[str, str], checks: Iterable[TypeCheck]) -> None:
    """Raise ``column_type_mismatch`` for the first column whose type the step cannot use.

    A column the view does not list, or whose type is unknown, is left to the normal
    column resolution: this guard only speaks when it is sure.
    """
    for check in checks:
        actual = types.get(check.column, "").upper()
        if not actual or actual in check.accepts:
            continue
        wanted = " or ".join(sorted(check.accepts))
        recovery: list[str] = []
        hint = f"Pick a {wanted} column (see 'mammoth view get {view_id}' for column types)."
        if actual == TEXT and len(check.accepts) == 1:
            target = next(iter(check.accepts))
            spec = json.dumps({"conversions": [{"column": check.column, "to": target}]})
            command = f"mammoth view transform convert-type {view_id} --input {shlex.quote(spec)}"
            recovery.append(command)
            hint = (
                f"Convert the column first: {command} . A date in a non-ISO format or a number "
                "column holding text such as N/A is stored as TEXT until converted."
            )
        raise CliError(
            code=CODE_COLUMN_TYPE_MISMATCH,
            message=(
                f"Column '{check.column}' is {actual}, but {check.operation} needs a {wanted} "
                "column."
            ),
            exit_status=EXIT_USAGE,
            hint=hint,
            details={
                "column": check.column,
                "actual_type": actual,
                "required_type": sorted(check.accepts),
                "operation": check.operation,
                "view_id": view_id,
            },
            recovery_commands=recovery,
        )
