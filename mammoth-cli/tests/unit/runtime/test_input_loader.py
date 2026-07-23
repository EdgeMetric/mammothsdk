"""Unit tests for structured request-document loading."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.runtime.input_loader import load_input_document


def test_returns_none_when_no_input_requested() -> None:
    assert load_input_document(None, None) is None


def test_shell_quoted_inline_json_is_a_document() -> None:
    document = '{"mapping":[{"search":["old"],"replace":"new"}]}'
    assert load_input_document(document, None) == {
        "mapping": [{"search": ["old"], "replace": "new"}]
    }


def test_loads_json_file_by_extension(tmp_path: Path) -> None:
    path = tmp_path / "req.json"
    path.write_text(json.dumps({"name": "x", "n": 1}), encoding="utf-8")
    assert load_input_document(str(path), None) == {"name": "x", "n": 1}


def test_loads_yaml_file_by_extension(tmp_path: Path) -> None:
    path = tmp_path / "req.yaml"
    path.write_text("name: x\nn: 1\n", encoding="utf-8")
    assert load_input_document(str(path), None) == {"name": "x", "n": 1}


def test_explicit_format_overrides_extension(tmp_path: Path) -> None:
    path = tmp_path / "req.txt"
    path.write_text(json.dumps({"k": "v"}), encoding="utf-8")
    assert load_input_document(str(path), "json") == {"k": "v"}


def test_stdin_requires_explicit_format(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO('{"k": "v"}'))
    with pytest.raises(CliError) as excinfo:
        load_input_document("-", None)
    assert excinfo.value.code == "input_format_required"
    assert excinfo.value.exit_status == EXIT_USAGE


def test_reads_json_from_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO('{"k": "v"}'))
    assert load_input_document("-", "json") == {"k": "v"}


def test_missing_file_is_usage_error(tmp_path: Path) -> None:
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(tmp_path / "absent.json"), None)
    assert excinfo.value.code == "input_not_found"
    assert excinfo.value.exit_status == EXIT_USAGE


def test_unknown_extension_without_format_is_usage_error(tmp_path: Path) -> None:
    path = tmp_path / "req.dat"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(path), None)
    assert excinfo.value.code == "input_format_required"


def test_invalid_format_value_is_usage_error(tmp_path: Path) -> None:
    path = tmp_path / "req.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(path), "toml")
    assert excinfo.value.code == "invalid_input_format"


def test_malformed_json_is_usage_error(tmp_path: Path) -> None:
    path = tmp_path / "req.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(path), None)
    assert excinfo.value.code == "invalid_input_document"


def test_non_mapping_document_is_usage_error(tmp_path: Path) -> None:
    path = tmp_path / "req.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(path), None)
    assert excinfo.value.code == "invalid_input_document"


def test_yaml_alias_yml_extension(tmp_path: Path) -> None:
    path = tmp_path / "req.yml"
    path.write_text("a: 1\n", encoding="utf-8")
    assert load_input_document(str(path), None) == {"a": 1}
