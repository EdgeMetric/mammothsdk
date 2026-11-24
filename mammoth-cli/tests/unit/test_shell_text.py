"""Commands the CLI prints to paste: quoted for the shell of the platform."""

from __future__ import annotations

import pytest

from mammoth_cli.runtime import shell_text

_ARGUMENTS = [r"C:\Program Files\py.exe", "--input", '{"a": 1}', "mammoth-io>=1,<2", "plain"]


def test_posix_quotes_with_single_quotes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shell_text, "WINDOWS", False)
    assert shell_text.shell_join(["a b", "x>=1"]) == "'a b' 'x>=1'"


def test_windows_quotes_paths_json_and_version_ranges_with_double_quotes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(shell_text, "WINDOWS", True)
    assert shell_text.shell_join(_ARGUMENTS) == (
        r'"C:\Program Files\py.exe" --input "{\"a\": 1}" "mammoth-io>=1,<2" plain'
    )
