"""Keep public install guidance pinned to the verified installer contract."""

from pathlib import Path


_ROOT = Path(__file__).resolve().parents[3]


def test_cli_docs_use_pinned_installer() -> None:
    expected = (
        "curl -fsSL https://raw.githubusercontent.com/EdgeMetric/mammothsdk/main/"
        "mammoth-cli/installers/mammoth-install.sh | bash -s -- --version 1.1.12 --noninteractive"
    )
    for path in (_ROOT / "README.md", _ROOT / "mammoth-cli" / "README.md", _ROOT / "mammoth-cli" / "docs" / "installation.md"):
        text = path.read_text(encoding="utf-8")
        assert expected in text
        assert "uv tool install mammoth-cli" not in text
        assert "pip install mammoth-cli" not in text


def test_cli_readme_exposes_honest_core_snapshot_without_raw_evidence_link() -> None:
    text = (_ROOT / "mammoth-cli" / "README.md").read_text(encoding="utf-8")
    assert "Core top-15 snapshot" in text
    assert "live-evidence-20260917" not in text
    assert "REL-174" in text and "REL-326" in text and "REL-224" in text
