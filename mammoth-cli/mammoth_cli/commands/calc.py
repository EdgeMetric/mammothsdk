"""The ``calc`` command: local, read-only, exact arithmetic.

T2-WPP-W8: an agent ran ``view data aggregate`` on two views and subtracted
the totals mentally, reporting 45,849 where the true difference was 145,849
(2,063,664 - 1,917,815) -- a transcription/mental-math error a machine never
makes. Every number an agent reports must come from a tool result, never
mental arithmetic; ``calc`` is that tool for a single expression (``view
data compare`` is the tool for a per-key comparison across two views).

The expression is parsed with :mod:`ast` and only a small, explicitly
allowed set of node types is walked -- never Python's ``eval()``. All
arithmetic is :class:`decimal.Decimal`, so results are exact, not a float
approximation.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Callable
from decimal import (
    ROUND_HALF_UP,
    Decimal,
    DivisionByZero,
    InvalidOperation,
    localcontext,
)
from typing import Any

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError
from mammoth_cli.runtime.invocation import Invocation

HandlerResult = tuple[Any, dict[str, Any]]

#: A trailing "N%" is rewritten to "(N/100)" before parsing -- ``%`` is not
#: valid Python expression syntax on its own.
_PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")

#: Significant digits kept in a result (Python's default is 28).
_PRECISION = 60

_BINOPS: dict[type, Callable[[Decimal, Decimal], Decimal]] = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
}


def _unsupported(expression: str) -> CliError:
    return CliError(
        code=CODE_INVALID_ARGUMENT,
        message=f"Unsupported syntax in {expression!r}.",
        exit_status=EXIT_USAGE,
        hint="calc supports + - * / and parentheses, unary +/-, a trailing "
        "'%' (divides by 100), and round(x[, ndigits]).",
    )


def _literal(node: ast.Constant, source: str) -> Decimal:
    """The number as written: going through a float would round away digits past 17."""
    try:
        return Decimal(ast.get_source_segment(source, node) or "")
    except InvalidOperation:
        return Decimal(str(node.value))


def _evaluate(node: ast.AST, expression: str, source: str) -> Decimal:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, expression, source)
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return _literal(node, source)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        left = _evaluate(node.left, expression, source)
        right = _evaluate(node.right, expression, source)
        try:
            return _BINOPS[type(node.op)](left, right)
        except (InvalidOperation, DivisionByZero, ZeroDivisionError) as exc:
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"Division by zero in {expression!r}.",
                exit_status=EXIT_USAGE,
            ) from exc
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate(node.operand, expression, source)
        return value if isinstance(node.op, ast.UAdd) else -value
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "round"
        and not node.keywords
        and 1 <= len(node.args) <= 2
    ):
        value = _evaluate(node.args[0], expression, source)
        ndigits = 0
        if len(node.args) == 2:
            digits_node = node.args[1]
            if not (
                isinstance(digits_node, ast.Constant)
                and isinstance(digits_node.value, int)
                and not isinstance(digits_node.value, bool)
            ):
                raise _unsupported(expression)
            ndigits = digits_node.value
        quantum = Decimal(1).scaleb(-ndigits)
        try:
            return value.quantize(quantum, rounding=ROUND_HALF_UP)
        except InvalidOperation as exc:
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"round() digits out of range in {expression!r}.",
                exit_status=EXIT_USAGE,
            ) from exc
    raise _unsupported(expression)


def calc(invocation: Invocation) -> HandlerResult:
    """Evaluate one arithmetic expression exactly.

    The sole positional argument is the expression: ``+ - * /``,
    parentheses, unary ``+``/``-``, a trailing ``%`` (divides by 100), and
    ``round(x[, ndigits])``. Returns the expression and its exact
    :class:`~decimal.Decimal` result as a string.
    """
    expression = invocation.extra_args[0] if invocation.extra_args else None
    if not expression or not expression.strip():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="calc requires an expression argument, e.g. '2063664 - 1917815'.",
            exit_status=EXIT_USAGE,
        )
    normalized = _PERCENT_RE.sub(r"(\1/100)", expression)
    try:
        tree = ast.parse(normalized, mode="eval")
    except SyntaxError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"Could not parse {expression!r}: {exc.msg}.",
            exit_status=EXIT_USAGE,
            hint="calc supports + - * / and parentheses, unary +/-, a trailing "
            "'%' (divides by 100), and round(x[, ndigits]).",
        ) from exc
    source = normalized
    with localcontext() as context:
        context.prec = _PRECISION
        result = _evaluate(tree, expression, source)
    return {"expression": expression, "result": str(result)}, {}
