"""Math expression string parser for the Mammoth SDK.

Converts human-readable math expressions like ``"Price * Quantity"`` into
the backend format used by MATH pipeline tasks.

Example::

    from mammoth._expression_parser import parse_expression

    column_map = {"Price": "column_1", "Quantity": "column_2"}
    result = parse_expression("Price * Quantity", column_map)
    # [{"TYPE": "COLUMN", "VALUE": "column_1"},
    #  {"TYPE": "OPERATOR", "VALUE": "*"},
    #  {"TYPE": "COLUMN", "VALUE": "column_2"}]

Supports:
    - Column references (resolved via display-to-internal name mapping)
    - Numeric literals (integers and floats)
    - Operators: +, -, *, /, %
    - Parentheses (produce nested lists per backend convention)
    - Multi-word column names (matched longest-first)
    - Function calls: ABS(), INT(), SMALL(), LARGE()
"""

from __future__ import annotations

import re
from typing import Any

# Supported math functions
_FUNCTIONS = frozenset({"ABS", "INT", "SMALL", "LARGE"})


def parse_expression(
    expression: str,
    column_map: dict[str, str],
) -> list[Any]:
    """Parse a math expression string into backend format.

    Args:
        expression: Human-readable expression (e.g. ``"Price * Quantity"``).
        column_map: Mapping from display names to internal column names.

    Returns:
        List of expression parts in backend format. Parenthesized
        sub-expressions become nested lists.

    Raises:
        ValueError: If the expression contains unrecognized tokens.
    """
    tokens = _tokenize(expression, column_map)
    return _build_tree(tokens)


def _tokenize(expression: str, column_map: dict[str, str]) -> list[dict[str, Any] | str]:
    """Tokenize an expression string into typed tokens.

    Returns a flat list of dicts (COLUMN/NUMBER/OPERATOR/FUNCTION_START) and
    paren strings "(" and ")".
    """
    # Sort column names by length (longest first) for greedy matching
    sorted_names = sorted(column_map.keys(), key=len, reverse=True)

    tokens: list[dict[str, Any] | str] = []
    pos = 0
    text = expression.strip()

    while pos < len(text):
        # Skip whitespace
        while pos < len(text) and text[pos] == " ":
            pos += 1
        if pos >= len(text):
            break

        matched = False

        # Try function names before column names (e.g. ABS(...))
        func_match = re.match(r"([A-Z]+)\s*\(", text[pos:])
        if func_match and func_match.group(1) in _FUNCTIONS:
            func_name = func_match.group(1)
            tokens.append({"TYPE": "FUNCTION_START", "VALUE": func_name})
            tokens.append("(")
            pos += func_match.end()
            continue

        # Try column names (longest match)
        for name in sorted_names:
            if text[pos : pos + len(name)] == name:
                # Check boundary: next char should not be alphanumeric/underscore
                end = pos + len(name)
                if end < len(text) and (text[end].isalnum() or text[end] == "_"):
                    continue
                tokens.append({"TYPE": "COLUMN", "VALUE": column_map[name]})
                pos = end
                matched = True
                break

        if matched:
            continue

        char = text[pos]

        # Commas (argument separator in functions)
        if char == ",":
            tokens.append(",")
            pos += 1
            continue

        # Parentheses
        if char in ("(", ")"):
            tokens.append(char)
            pos += 1
            continue

        # Operators
        if char in "+-*/%":
            tokens.append({"TYPE": "OPERATOR", "VALUE": char})
            pos += 1
            continue

        # Numbers
        num_match = re.match(r"\d+(?:\.\d+)?", text[pos:])
        if num_match:
            num_str = num_match.group()
            num_val: int | float = float(num_str) if "." in num_str else int(num_str)
            tokens.append({"TYPE": "NUMBER", "VALUE": num_val})
            pos += len(num_str)
            continue

        raise ValueError(f"Unrecognized token at position {pos} in expression: {expression!r}")

    return tokens


def _build_tree(tokens: list[Any]) -> list[Any]:
    """Convert flat token list with parens into nested lists.

    Also handles FUNCTION_START tokens by collecting arguments and
    producing {"TYPE": "FUNCTION", "VALUE": {"FUNCTION": name, "ARGUMENT": [...]}}
    """
    result: list[Any] = []
    i = 0

    while i < len(tokens):
        token = tokens[i]

        if isinstance(token, dict) and token.get("TYPE") == "FUNCTION_START":
            func_name = token["VALUE"]
            # Next token should be "("
            if i + 1 >= len(tokens) or tokens[i + 1] != "(":
                raise ValueError(f"Expected '(' after function {func_name}")
            # Find matching close paren
            depth = 1
            start = i + 2
            j = start
            while j < len(tokens) and depth > 0:
                if tokens[j] == "(":
                    depth += 1
                elif tokens[j] == ")":
                    depth -= 1
                j += 1
            if depth != 0:
                raise ValueError(f"Unmatched parenthesis in function {func_name}")
            # Split inner tokens by commas to get arguments
            inner_tokens = tokens[start : j - 1]
            args = _split_by_comma(inner_tokens)
            parsed_args = [_build_tree(arg) for arg in args]
            # Flatten single-element argument lists
            flat_args = []
            for a in parsed_args:
                if len(a) == 1:
                    flat_args.append(a[0])
                else:
                    flat_args.append(a)
            result.append({
                "TYPE": "FUNCTION",
                "VALUE": {"FUNCTION": func_name, "ARGUMENT": flat_args},
            })
            i = j
        elif token == "(":
            # Find matching close paren
            depth = 1
            start = i + 1
            j = start
            while j < len(tokens) and depth > 0:
                if tokens[j] == "(":
                    depth += 1
                elif tokens[j] == ")":
                    depth -= 1
                j += 1
            if depth != 0:
                raise ValueError("Unmatched parenthesis in expression")
            # Recursively process inner tokens
            inner = _build_tree(tokens[start : j - 1])
            result.append(inner)
            i = j
        elif token == ")":
            raise ValueError("Unexpected closing parenthesis")
        else:
            result.append(token)
            i += 1

    return result


def _split_by_comma(tokens: list[Any]) -> list[list[Any]]:
    """Split a flat token list by top-level commas."""
    args: list[list[Any]] = []
    current: list[Any] = []
    depth = 0
    for token in tokens:
        if token == "(":
            depth += 1
            current.append(token)
        elif token == ")":
            depth -= 1
            current.append(token)
        elif token == "," and depth == 0:
            args.append(current)
            current = []
        else:
            current.append(token)
    if current:
        args.append(current)
    return args
