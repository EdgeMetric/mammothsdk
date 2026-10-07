"""Generate ``mammoth_cli/commands/help_summaries.json``.

A group's ``--help`` lists each command with its handler's docstring summary.
Reading a docstring imports the handler's module, which made ``mammoth view
--help`` import the whole view family. The listing reads this index instead; a
unit test fails when the index differs from the live docstrings.

Run from the ``mammoth-cli`` directory: ``python scripts/gen_help_summaries.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mammoth_cli.app import _command_tree, live_command_summary  # noqa: E402

INDEX = Path(__file__).resolve().parent.parent / "mammoth_cli" / "commands" / "help_summaries.json"


def live_index() -> dict[str, str]:
    path_to_command, _ = _command_tree()
    summaries = {
        command_id: live_command_summary(command_id) for command_id in path_to_command.values()
    }
    return {command_id: text for command_id, text in sorted(summaries.items()) if text}


def render(index: dict[str, str]) -> str:
    return json.dumps(index, indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    INDEX.write_text(render(live_index()), encoding="utf-8")
