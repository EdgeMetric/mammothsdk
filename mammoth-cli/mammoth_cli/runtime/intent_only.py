"""Embedded (in-product) dashboards are built from the user's intent alone.

The in-product agent passes only what the user asked for to the dashboard
builder (``dashboard v3 generate``, ``dashboard chat edit``). The commands that
let a caller author a canvas or a page by hand stay in the standalone CLI and
fail fast when an embedded call reaches them.
"""

from __future__ import annotations

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.runtime import embedded

CODE_INTENT_ONLY_DASHBOARDS = "intent_only_dashboards"

#: Manifest command ids that write a dashboard from hand-made content.
HAND_CRAFT_COMMANDS = frozenset(
    {
        "dashboard.create-blank",
        "dashboard.canvas.save",
        "dashboard.canvas.restore",
        "dashboard.pages.add",
        "dashboard.template.apply",
        "dashboard.template.fit",
        "dashboard.templates.use",
        "dashboard.template.create",
        "dashboard.import-workbook",
        "dashboard.filter.add",
        "dashboard.filter.remove",
    }
)


def refuse_hand_crafted_write(command_id: str) -> None:
    """Raise ``intent_only_dashboards`` for a hand-crafting command when embedded."""
    if embedded.active() and command_id in HAND_CRAFT_COMMANDS:
        raise CliError(
            code=CODE_INTENT_ONLY_DASHBOARDS,
            message=f"`{command_id.replace('.', ' ')}` is not available here.",
            exit_status=EXIT_USAGE,
            hint=(
                "Pass the user's intent, in their own words, to `dashboard v3 generate` "
                "to build a board or to `dashboard chat edit` to change one."
            ),
            recovery_commands=["mammoth dashboard v3 generate", "mammoth dashboard chat edit"],
        )
