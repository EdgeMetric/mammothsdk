"""The exports recipe must connect the product's "Export Auto-Sync" term to
the CLI's own fields (T1-O-11): an agent chased the unrelated doc term
"Export Auto-Sync" for 30+ calls, never realizing it already had
`run_immediately`/`trigger_type` on `view export dataset` in hand.
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_EXPORTS_RECIPE = (
    _ROOT
    / "mammoth_cli"
    / "bundled_skill"
    / "mammoth-cli"
    / "references"
    / "recipes"
    / "exports.md"
)


def test_exports_recipe_bridges_auto_sync_to_run_immediately_and_trigger_type() -> None:
    text = _EXPORTS_RECIPE.read_text(encoding="utf-8")
    assert "Auto-Sync" in text
    assert "run_immediately" in text
    assert "trigger_type" in text
