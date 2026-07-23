"""End-to-end tests that runtime validation (R5, R6, R8) is wired into the app.

These drive the real Typer app in-process (:func:`mammoth_cli.testing.make_runner`)
with no mocked service: every case here is invalid before a handler would ever
open a service or touch the network, so no credentials are required — the
point of each test is that ``app._execute`` rejects the bad input first.
"""

from __future__ import annotations

import json
from pathlib import Path

from mammoth_cli.errors.envelope import EXIT_USAGE
from mammoth_cli.testing import make_runner

_JSON_NO_INPUT = ["--output", "json", "--no-input"]


# --- R5: a surplus positional is refused, not silently dropped ------------


def test_surplus_positional_is_rejected_through_the_app(isolated_cli_config: Path) -> None:
    """'project delete 1 2' must not silently act only on '1'."""
    result = make_runner().invoke(["project", "delete", "1", "2", "--yes", *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "unexpected_argument" in result.output


def test_single_positional_for_project_delete_reaches_past_arg_validation(
    isolated_cli_config: Path,
) -> None:
    """A single id is accepted by argument validation (fails later, on auth)."""
    result = make_runner().invoke(["project", "delete", "1", "--yes", *_JSON_NO_INPUT])
    # No credentials configured: this must fail on auth/profile resolution, not
    # on argument validation.
    assert "unexpected_argument" not in result.output


# --- R6: an --input field that fails its annotated type is rejected -------


def test_input_field_type_mismatch_is_rejected_through_the_app(
    isolated_cli_config: Path, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"limit": "abc"}), encoding="utf-8")
    result = make_runner().invoke(["project", "list", "--input", str(doc), *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_input_field_type" in result.output


def test_non_positive_structured_ids_are_rejected_before_auth(
    isolated_cli_config: Path, tmp_path: Path
) -> None:
    doc = tmp_path / "ids.json"
    doc.write_text(json.dumps({"project_ids": [-1, 0]}), encoding="utf-8")
    result = make_runner().invoke(["project", "bulk-delete", "--input", str(doc), *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_input_field_type" in result.output
    assert "project_ids[0]" in result.output


def test_handler_owned_field_is_rejected_before_auth(
    isolated_cli_config: Path, tmp_path: Path
) -> None:
    doc = tmp_path / "job.json"
    doc.write_text(json.dumps({"timeout": 1}), encoding="utf-8")
    result = make_runner().invoke(["job", "get", "123", "--input", str(doc), *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "unknown_input_field" in result.output


# --- R8: global options and positional ids are validated -------------------


def test_zero_project_option_is_rejected_through_the_app(isolated_cli_config: Path) -> None:
    result = make_runner().invoke(["project", "list", "--project", "0", *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_option_value" in result.output


def test_unrecognized_color_is_rejected_through_the_app(isolated_cli_config: Path) -> None:
    result = make_runner().invoke(["project", "list", "--color", "pink", *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_option_value" in result.output


def test_negative_timeout_is_rejected_through_the_app(isolated_cli_config: Path) -> None:
    result = make_runner().invoke(["project", "list", "--timeout", "-1", *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_option_value" in result.output


def test_zero_view_id_positional_is_rejected_through_the_app(isolated_cli_config: Path) -> None:
    result = make_runner().invoke(["view", "get", "0", *_JSON_NO_INPUT])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_option_value" in result.output
