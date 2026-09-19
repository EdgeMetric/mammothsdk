"""Unit tests for structured request-document loading."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.runtime import input_loader
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


def test_invalid_utf8_is_a_structured_usage_error(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_bytes(b'{"name":"ok"}\xff')
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(path), None)
    assert excinfo.value.code == input_loader.CODE_INVALID_INPUT_ENCODING
    assert excinfo.value.exit_status == EXIT_USAGE


def test_duplicate_json_keys_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"name":"first","name":"second"}', encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(path), None)
    assert excinfo.value.code == input_loader.CODE_DUPLICATE_INPUT_KEY


def test_nonfinite_json_numbers_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "nonfinite.json"
    path.write_text('{"value":NaN}', encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(path), None)
    assert excinfo.value.code == input_loader.CODE_NONFINITE_INPUT_NUMBER


def test_overflowing_json_exponent_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "overflow.json"
    path.write_text('{"value":1e999}', encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(path), None)
    assert excinfo.value.code == input_loader.CODE_NONFINITE_INPUT_NUMBER


def test_duplicate_yaml_keys_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.yaml"
    path.write_text("name: first\nname: second\n", encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(path), None)
    assert excinfo.value.code == input_loader.CODE_DUPLICATE_INPUT_KEY


def test_size_limit_is_checked_before_parse(tmp_path: Path) -> None:
    path = tmp_path / "large.json"
    path.write_bytes(b"{" + b'"x":"' + b"a" * input_loader.MAX_INPUT_BYTES + b'"}')
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(path), None)
    assert excinfo.value.code == input_loader.CODE_INPUT_TOO_LARGE


def test_depth_limit_is_checked_before_parse(tmp_path: Path) -> None:
    path = tmp_path / "deep.json"
    path.write_text(
        "{" * (input_loader.MAX_INPUT_DEPTH + 1) + "0" + "}" * (input_loader.MAX_INPUT_DEPTH + 1),
        encoding="utf-8",
    )
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(path), None)
    assert excinfo.value.code == input_loader.CODE_INPUT_TOO_DEEP


def test_omitted_empty_and_null_documents_have_distinct_outcomes(tmp_path: Path) -> None:
    assert load_input_document(None, None) is None
    empty = tmp_path / "empty.json"
    empty.write_text("{}", encoding="utf-8")
    assert load_input_document(str(empty), None) == {}
    null = tmp_path / "null.json"
    null.write_text("null", encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        load_input_document(str(null), None)
    assert excinfo.value.code == "invalid_input_document"


def test_stdin_source_is_read_once(monkeypatch: pytest.MonkeyPatch) -> None:
    class CountingInput(io.StringIO):
        reads = 0

        def read(self, size: int = -1) -> str:
            self.reads += 1
            return super().read(size)

    stream = CountingInput('{"k":"v"}')
    monkeypatch.setattr("sys.stdin", stream)
    assert load_input_document("-", "json") == {"k": "v"}
    assert stream.reads == 1


def test_at_prefixed_path_reads_the_file(tmp_path: Path) -> None:
    path = tmp_path / "doc.json"
    path.write_text('{"name": "x"}', encoding="utf-8")
    assert load_input_document(f"@{path}", None) == {"name": "x"}


def test_at_prefixed_missing_file_error_quotes_the_typed_value(tmp_path: Path) -> None:
    typed = f"@{tmp_path / 'absent.json'}"
    with pytest.raises(CliError) as excinfo:
        load_input_document(typed, None)
    assert excinfo.value.code == "input_not_found"
    assert typed in excinfo.value.message
