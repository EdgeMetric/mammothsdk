"""``skill show -o plain`` (or ``-o text``) prints the markdown itself.

The JSON envelope carries the file as one escaped string, which a person (or an
agent reading a terminal) cannot read. Plain and text output print the file as
it is. The skill's front-matter ``version`` is the running CLI's version.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from mammoth_cli import __version__
from mammoth_cli.skills import steering
from mammoth_cli.testing import make_runner

_SKILL = Path(steering.__file__).parents[1] / "bundled_skill" / "mammoth-cli"


def _front_matter_version(text: str) -> str:
    front = text.split("---", 2)[1]
    found = re.search(r"^version:\s*(\S+)\s*$", front, re.MULTILINE)
    assert found, front
    return found.group(1)


@pytest.mark.parametrize("mode", ["plain", "text"])
def test_skill_show_prints_the_markdown_as_is(mode: str) -> None:
    result = make_runner().invoke(["skill", "show", "-o", mode])
    assert result.exit_code == 0, result.output
    assert result.stdout == steering.show()["text"]
    assert result.stdout.startswith("---\nname: mammoth-cli\n")
    assert "\\n" not in result.stdout.splitlines()[0]


def test_skill_show_plain_prints_a_reference_file_as_is() -> None:
    result = make_runner().invoke(
        ["skill", "show", "--input", '{"file": "references/machine-output.md"}', "-o", "plain"]
    )
    assert result.exit_code == 0, result.output
    expected = (_SKILL / "references" / "machine-output.md").read_text(encoding="utf-8")
    assert result.stdout == expected


def test_skill_show_json_still_carries_the_text_in_the_envelope() -> None:
    result = make_runner().invoke(["skill", "show", "-o", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)["data"]
    assert data["file"] == "SKILL.md"
    assert data["text"].startswith("---\nname: mammoth-cli\n")


def test_text_is_an_alias_of_plain_for_any_command() -> None:
    plain = make_runner().invoke(["version", "-o", "plain"])
    text = make_runner().invoke(["version", "-o", "text"])
    assert plain.exit_code == text.exit_code == 0, text.output
    assert text.stdout == plain.stdout


def test_the_bundled_skill_version_is_the_cli_version() -> None:
    text = (_SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert _front_matter_version(text) == __version__


def test_skill_show_reports_the_running_cli_version() -> None:
    assert _front_matter_version(str(steering.show()["text"])) == __version__
