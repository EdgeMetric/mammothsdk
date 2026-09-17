"""Keep bundled and public cleanup guidance aligned with R09 retention rules."""

from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_BUNDLED = _ROOT / "mammoth_cli" / "bundled_skill" / "mammoth-cli"


def test_bundled_skill_defines_four_retention_roles_and_explicit_authorization() -> None:
    text = (_BUNDLED / "references" / "retention.md").read_text(encoding="utf-8")
    for role in ("Temporary", "Intermediate", "Retained deliverable", "Protected"):
        assert role in text
    assert "exact IDs" in text
    assert "delete all resources created by a task" not in text
    assert "Never use a blanket" in text
    assert "durable cleanup journal" in text


def test_bundled_workflows_preserve_requested_deliverables() -> None:
    skill = (_BUNDLED / "SKILL.md").read_text(encoding="utf-8")
    cleanup = (_BUNDLED / "references" / "recipes" / "cleanup.md").read_text(encoding="utf-8")
    resources = (_BUNDLED / "references" / "recipes" / "resources.md").read_text(encoding="utf-8")
    exports = (_BUNDLED / "references" / "recipes" / "exports.md").read_text(encoding="utf-8")
    dashboard = (_BUNDLED / "references" / "recipes" / "dashboards.md").read_text(encoding="utf-8")

    assert "never means delete-all-owned-resources" in skill
    assert "requested dataset, dashboard, view, or export artifact" in cleanup
    assert "retained deliverables" in resources
    assert "source dataset/view is requested as a deliverable" in exports
    assert "dashboard is requested as a" in dashboard


def test_public_safety_docs_reject_blanket_cleanup() -> None:
    text = (_ROOT / "docs" / "safety.md").read_text(encoding="utf-8")
    assert "Owned” does not mean “delete all." in text
    assert "IDs, resource types, parent scope, and dependency order" in text
    assert "not a durable cleanup journal" in text
