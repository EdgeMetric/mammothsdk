"""A URL dataset is no longer described as a one-time copy.

Since Refresh from URL shipped, a `weburl` dataset keeps its (masked) link and
refreshes on demand (`dataset refresh` or the web app) — a single CSV only, never on
a schedule, and `run_data_retrieval` still cannot refresh it (KB PR #118). The CLI's
`dataset create` restrictions, SKILL.md and two recipes kept saying "one-time
copy with no source details", which tells an agent the link is gone (changelog
analytics build, 2026-10-15).
"""

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SKILL = _ROOT / "mammoth_cli" / "bundled_skill" / "mammoth-cli"
_TEXTS = [
    _SKILL / "SKILL.md",
    _SKILL / "references" / "recipes" / "resources.md",
    _SKILL / "references" / "recipes" / "scheduling.md",
    _ROOT / "spec" / "manifests" / "commands" / "dataset.yaml",
]


@pytest.mark.parametrize("path", _TEXTS, ids=lambda p: p.name)
def test_a_url_dataset_is_not_called_a_one_time_copy(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "URL is a one-time copy" not in text
    assert "weburl dataset is a one-time copy" not in text
    assert "`weburl` dataset is a one-time copy" not in text
    assert "(`weburl`) is a one-time copy" not in text


@pytest.mark.parametrize("path", _TEXTS, ids=lambda p: p.name)
def test_it_still_says_a_url_dataset_is_never_scheduled(path: Path) -> None:
    """The half that stays true: no schedule, so an agent must not promise one."""
    text = path.read_text(encoding="utf-8").casefold()
    assert "on demand" in text
    assert "never on a schedule" in text or "not on a schedule" in text


@pytest.mark.parametrize("path", _TEXTS, ids=lambda p: p.name)
def test_it_does_not_say_the_cli_cannot_refresh_a_url_dataset(path: Path) -> None:
    text = " ".join(path.read_text(encoding="utf-8").split())
    assert "no refresh command" not in text
    assert "not from the CLI" not in text
    assert "via the CLI" not in text
