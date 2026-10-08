"""``mammoth agent --help`` gives each subgroup a description of its own."""

from __future__ import annotations

from mammoth_cli.testing import make_runner

_GROUPS = (
    "access",
    "action",
    "charter",
    "feedback",
    "goldens",
    "memory",
    "projects",
    "run",
    "scratch",
    "session",
    "team",
    "turn",
)


def test_agent_subgroups_do_not_share_one_description() -> None:
    result = make_runner().invoke(["agent", "--help"])
    assert result.exit_code == 0, result.output
    rows = [line.strip(" │").split(None, 1) for line in result.output.splitlines()]
    described = {row[0]: row[1].strip(" │") for row in rows if len(row) == 2 and row[0] in _GROUPS}
    assert set(described) == set(_GROUPS), result.output
    assert len(set(described.values())) == len(_GROUPS), result.output
