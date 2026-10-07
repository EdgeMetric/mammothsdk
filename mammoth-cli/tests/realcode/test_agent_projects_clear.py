"""``mammoth agent projects clear`` exists, so a user can empty an agent's project list."""

from __future__ import annotations

from mammoth_cli.commands.agent import agent_projects_clear
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.testing import make_runner


def test_agent_projects_clear_is_a_command() -> None:
    assert HANDLERS["agent.projects.clear"] is agent_projects_clear

    group = make_runner().invoke(["agent", "projects", "--help"])
    assert group.exit_code == 0, group.output
    assert "clear" in group.output, group.output

    result = make_runner().invoke(["agent", "projects", "clear", "--help"])
    assert result.exit_code == 0, result.output
    assert "AGENT_KEY" in result.output, result.output
