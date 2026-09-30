"""Keep the send_an_alert attachment shape documented, not truncated mid-sentence.

RCA G4/T2-08: `references/commands/automation.md`'s status line for
`automation.create` was cut off mid-word right where it would reveal the
working `send_an_alert` attachment shape, and `references/recipes/scheduling.md`
omitted `attachments` from the `send_an_alert` bullet entirely. An agent
reading either file in full must be able to see the shape and that it is
sent as a CSV.
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLED = _ROOT / "mammoth_cli" / "bundled_skill" / "mammoth-cli"


def test_automation_create_status_line_is_not_truncated_mid_word() -> None:
    text = (_BUNDLED / "references" / "commands" / "automation.md").read_text(encoding="utf-8")
    section = text.split("### `automation.create`", 1)[1].split("### `", 1)[0]
    assert "…" not in section
    assert "attachments.dataview_ids" in section
    assert "csv" in section.casefold()


def test_scheduling_recipe_names_the_send_an_alert_attachment_shape() -> None:
    text = (_BUNDLED / "references" / "recipes" / "scheduling.md").read_text(encoding="utf-8")
    assert "attachments.dataview_ids" in text
    assert "csv" in text.casefold()
