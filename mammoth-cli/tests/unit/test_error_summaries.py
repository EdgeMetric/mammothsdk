"""Every error code the CLI can raise carries a user-safe summary."""

from __future__ import annotations

import ast
import pathlib

import pytest

import mammoth_cli
from mammoth_cli.errors.envelope import (
    DEFAULT_ERROR_SUMMARY,
    ERROR_SUMMARIES,
    CliError,
    missing_project_error,
)
from mammoth_cli.runtime.strict import validate_input_fields

#: Codes raised through helpers whose ``code`` argument is positional.
_POSITIONAL_CODES = {"no_output", "aborted", "internal_error"}


def _strings(node: ast.AST) -> set[str]:
    return {
        n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)
    }


def _raised_codes() -> set[str]:
    codes = set(_POSITIONAL_CODES)
    root = pathlib.Path(mammoth_cli.__file__).parent
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.keyword) and node.arg == "code":
                codes |= _strings(node.value)
            elif isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and (t.id == "code" or t.id.startswith("CODE_"))
                for t in node.targets
            ):
                codes |= _strings(node.value)
    return codes - {"code"}


def test_every_raised_code_has_a_summary() -> None:
    missing = sorted(_raised_codes() - set(ERROR_SUMMARIES))
    assert not missing, f"error codes without a user-safe summary: {missing}"


def test_no_summary_for_a_code_that_does_not_exist() -> None:
    assert sorted(set(ERROR_SUMMARIES) - _raised_codes()) == []


@pytest.mark.parametrize("code", sorted(ERROR_SUMMARIES))
def test_summary_is_plain_language(code: str) -> None:
    summary = ERROR_SUMMARIES[code]
    assert summary != DEFAULT_ERROR_SUMMARY
    assert len(summary) <= 100
    for banned in ("mammoth ", "--", "_", "{", "`", '"'):
        assert banned not in summary


def test_envelope_carries_summary_next_to_model_facing_fields() -> None:
    error = missing_project_error().to_envelope()["error"]
    assert error["summary"] == ERROR_SUMMARIES["project_required"]
    assert error["message"] == "No project is set for this command."
    assert error["hint"]


def test_unknown_code_falls_back_to_generic_summary() -> None:
    error = CliError(code="not_a_real_code", message="x").to_envelope()["error"]
    assert error["summary"] == DEFAULT_ERROR_SUMMARY


def test_unknown_input_field_message_lists_accepted_fields() -> None:
    with pytest.raises(CliError) as caught:
        validate_input_fields("dataset.list", {"workspace_id": 1})
    error = caught.value
    assert "workspace_id" in error.message
    assert "Accepted fields:" in error.message
    for accepted in error.details["accepted"]:
        assert accepted in error.message
