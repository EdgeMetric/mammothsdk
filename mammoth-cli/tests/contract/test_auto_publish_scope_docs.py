"""The dashboards recipe says auto-publish covers data refreshes only.

Auto-publish republishes data refreshes; layout and chat edits wait for
``publish-presentation`` (deliberate in the backend, ruling Gaurav 2026-10-16).
Nothing in the CLI's docs said so, so an agent editing a live auto-publish
board reported the change as live when it was still in the draft.
"""

from pathlib import Path

_RECIPE = (
    Path(__file__).resolve().parents[2]
    / "mammoth_cli"
    / "bundled_skill"
    / "mammoth-cli"
    / "references"
    / "recipes"
    / "dashboards.md"
)


def test_the_recipe_says_auto_publish_covers_data_only() -> None:
    text = _RECIPE.read_text(encoding="utf-8")
    section = text.split("## Publishing and the url routes", 1)[1]
    assert "data refreshes only" in section
    assert "is_publish_presentation_pending" in section
    assert "publish-presentation" in section
