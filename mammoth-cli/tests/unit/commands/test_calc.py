"""Unit tests for the ``calc`` command handler."""

from __future__ import annotations

import pytest

from mammoth_cli.commands import calc as calc_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation


def _inv(**overrides: object) -> Invocation:
    return Invocation(command_id="calc", **overrides)  # type: ignore[arg-type]


def test_calc_requires_an_expression() -> None:
    with pytest.raises(CliError) as excinfo:
        calc_cmd.calc(_inv(extra_args=[]))
    assert excinfo.value.code == "invalid_argument"


def test_calc_subtracts_exactly() -> None:
    """T2-WPP-W8's exact evidence: the model mentally subtracted 2,063,664 -
    1,917,815 and reported 45,849; the true difference is 145,849.
    """
    data, _meta = calc_cmd.calc(_inv(extra_args=["2063664 - 1917815"]))
    assert data["result"] == "145849"


def test_calc_percentage_matches_w8_gap() -> None:
    """145849 / 2063664 * 100, rounded to 2 places, is 7.07 (the true YouTube-
    vs-Adobe gap; the model reported 2.2%).
    """
    data, _meta = calc_cmd.calc(_inv(extra_args=["round(145849 / 2063664 * 100, 2)"]))
    assert data["result"] == "7.07"


def test_calc_trailing_percent_divides_by_100() -> None:
    data, _meta = calc_cmd.calc(_inv(extra_args=["50% * 200"]))
    assert data["result"] == "100.0"


def test_calc_parentheses_and_precedence() -> None:
    data, _meta = calc_cmd.calc(_inv(extra_args=["(2 + 3) * 4"]))
    assert data["result"] == "20"


def test_calc_unary_minus() -> None:
    data, _meta = calc_cmd.calc(_inv(extra_args=["-5 + 2"]))
    assert data["result"] == "-3"


def test_calc_division_by_zero_fails_loud() -> None:
    with pytest.raises(CliError) as excinfo:
        calc_cmd.calc(_inv(extra_args=["1 / 0"]))
    assert excinfo.value.code == "invalid_argument"


def test_calc_rejects_non_arithmetic_syntax_never_eval() -> None:
    """The parser walks a restricted AST, never Python's eval() -- anything
    outside +-*/() unary round() must be rejected, not executed.
    """
    with pytest.raises(CliError) as excinfo:
        calc_cmd.calc(_inv(extra_args=["__import__('os').system('echo hi')"]))
    assert excinfo.value.code == "invalid_argument"


def test_calc_rejects_malformed_expression() -> None:
    with pytest.raises(CliError) as excinfo:
        calc_cmd.calc(_inv(extra_args=["2 +"]))
    assert excinfo.value.code == "invalid_argument"
