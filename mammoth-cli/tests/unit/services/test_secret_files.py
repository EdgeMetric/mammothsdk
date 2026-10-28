"""Reading a secret from a file."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.secret_files import read_secret_file


@pytest.mark.parametrize("written", ["hunter2-long\n", "hunter2-long\r\n", "hunter2-long"])
def test_read_secret_file_strips_only_the_trailing_newline(tmp_path: Path, written: str) -> None:
    path = tmp_path / "pw.txt"
    path.write_bytes(written.encode())
    path.chmod(0o600)
    assert read_secret_file(path) == "hunter2-long"


def test_read_secret_file_keeps_inner_and_leading_spaces(tmp_path: Path) -> None:
    path = tmp_path / "pw.txt"
    path.write_text("  two words  \n", encoding="utf-8")
    path.chmod(0o600)
    assert read_secret_file(str(path)) == "  two words  "


def test_read_secret_file_refuses_an_empty_file_without_echoing_anything(tmp_path: Path) -> None:
    path = tmp_path / "pw.txt"
    path.write_text("\n", encoding="utf-8")
    path.chmod(0o600)
    with pytest.raises(CliError, match="is empty"):
        read_secret_file(path)


def test_read_secret_file_names_a_missing_file_by_path_only(tmp_path: Path) -> None:
    with pytest.raises(CliError) as caught:
        read_secret_file(tmp_path / "absent.txt")
    assert "absent.txt" in caught.value.message
    assert caught.value.details["field"] == "password_file"


def test_read_secret_file_refuses_a_file_other_users_can_read(tmp_path: Path) -> None:
    path = tmp_path / "pw.txt"
    path.write_text("hunter2-long\n", encoding="utf-8")
    path.chmod(0o644)
    with pytest.raises(CliError) as caught:
        read_secret_file(path)
    assert caught.value.code == "insecure_input_file"
    assert "hunter2-long" not in caught.value.message
