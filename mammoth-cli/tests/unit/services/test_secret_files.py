"""Reading a secret from a file, and keeping it out of a dry-run report."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.dryrun import REDACTED_ARGUMENT, redact_arguments
from mammoth_cli.services.secret_files import read_secret_file


@pytest.mark.parametrize("written", ["hunter2-long\n", "hunter2-long\r\n", "hunter2-long"])
def test_read_secret_file_strips_only_the_trailing_newline(tmp_path: Path, written: str) -> None:
    path = tmp_path / "pw.txt"
    path.write_bytes(written.encode())
    assert read_secret_file(path) == "hunter2-long"


def test_read_secret_file_keeps_inner_and_leading_spaces(tmp_path: Path) -> None:
    path = tmp_path / "pw.txt"
    path.write_text("  two words  \n", encoding="utf-8")
    assert read_secret_file(str(path)) == "  two words  "


def test_read_secret_file_refuses_an_empty_file_without_echoing_anything(tmp_path: Path) -> None:
    path = tmp_path / "pw.txt"
    path.write_text("\n", encoding="utf-8")
    with pytest.raises(CliError, match="is empty"):
        read_secret_file(path)


def test_read_secret_file_names_a_missing_file_by_path_only(tmp_path: Path) -> None:
    with pytest.raises(CliError) as caught:
        read_secret_file(tmp_path / "absent.txt")
    assert "absent.txt" in caught.value.message
    assert caught.value.details["field"] == "password_file"


def test_redact_arguments_masks_a_password_at_any_depth_and_keeps_the_rest() -> None:
    arguments = {
        "dashboard_id": 7,
        "type_of_auth": "password",
        "password": "hunter2-long",
        "nested": [{"password_file": "./pw.txt", "keep": "x"}],
    }
    shown = redact_arguments(arguments)
    assert shown == {
        "dashboard_id": 7,
        "type_of_auth": "password",
        "password": REDACTED_ARGUMENT,
        "nested": [{"password_file": REDACTED_ARGUMENT, "keep": "x"}],
    }
    assert arguments["password"] == "hunter2-long"
    assert "hunter2-long" not in repr(shown)
