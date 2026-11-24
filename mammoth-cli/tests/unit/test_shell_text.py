"""Commands the CLI prints to paste: quoted for the shell of the platform."""

from __future__ import annotations

import json
import shlex

import pytest

from mammoth_cli.runtime import shell_text

_DOCUMENT = {"query": "select 'a' where id > 5 & x"}


def test_posix_quotes_with_single_quotes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shell_text, "WINDOWS", False)
    assert shell_text.shell_join(["a b", "x>=1"]) == "'a b' 'x>=1'"


@pytest.mark.parametrize("character", list(" <>|&^(),;=@{}'`$!"))
def test_windows_double_quotes_what_its_shells_read_as_syntax(
    character: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shell_text, "WINDOWS", True)
    assert shell_text.shell_join(["plain", f"a{character}b"]) == f'plain "a{character}b"'


def test_windows_refuses_a_double_quote_it_cannot_quote(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shell_text, "WINDOWS", True)
    with pytest.raises(ValueError, match="cmd.exe"):
        shell_text.shell_join(['{"a": 1}'])


def test_posix_puts_the_document_in_the_command(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shell_text, "WINDOWS", False)
    fields = shell_text.command_with_input(["mammoth", "x"], _DOCUMENT)
    assert list(fields) == ["next"]
    assert json.loads(shlex.split(fields["next"])[-1]) == _DOCUMENT


def test_windows_keeps_the_document_out_of_the_command(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shell_text, "WINDOWS", True)
    assert shell_text.command_with_input(["mammoth", "x"], _DOCUMENT) == {
        "next": "mammoth x --input FILE.json",
        "next_input": _DOCUMENT,
    }
