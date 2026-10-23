"""Each command names itself to the server's request log through the User-Agent."""

from __future__ import annotations

import pytest

from mammoth_cli import __version__
from mammoth_cli.runtime import linecapture, trace


def test_user_agent_outside_a_command_is_the_product_token() -> None:
    assert trace.user_agent() == f"mammoth-cli/{__version__}"


def test_user_agent_names_the_command_its_invocation_and_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name, _ in trace.AGENT_ENV:
        monkeypatch.delenv(name, raising=False)
    with trace.begin("view.data.get") as current:
        assert trace.current() is current
        assert trace.user_agent() == (
            f"mammoth-cli/{__version__} "
            f"(cmd=view.data.get; inv={current.invocation_id}; surface=terminal)"
        )
    assert trace.current() is None


def test_each_invocation_has_its_own_id_and_a_run_line_its_own_surface() -> None:
    with trace.begin("run") as outer:
        with linecapture.capturing(), trace.begin("project.list") as line:
            assert line.surface == "run"
            assert line.invocation_id != outer.invocation_id
        assert trace.current() is outer


@pytest.mark.parametrize(
    ("environ", "agent"),
    [
        ({}, None),
        ({"CLAUDECODE": "1"}, "claude-code"),
        ({"CLAUDECODE": "0"}, None),
        ({"CURSOR_AGENT": "1"}, "cursor"),
        ({"GEMINI_CLI": "1"}, "gemini-cli"),
        ({"CODEX_SANDBOX": "seatbelt"}, "codex"),
        ({"MAMMOTH_AGENT": "acme bot (v2)", "CLAUDECODE": "1"}, "acme-bot--v2-"),
    ],
)
def test_detect_agent(environ: dict[str, str], agent: str | None) -> None:
    assert trace.detect_agent(environ) == agent


def test_comment_keeps_header_separators_out() -> None:
    comment = trace.Trace("a b;c", "abc123", "terminal", "x").comment()
    assert comment == "(cmd=a-b-c; inv=abc123; surface=terminal; agent=x)"
