"""Regression checks for the opt-in live API test configuration."""

from __future__ import annotations

import re
from pathlib import Path

LIVE_TEST = Path(__file__).resolve().parents[1] / "test_live_api.py"
_LITERAL_CREDENTIAL_ASSIGNMENT = re.compile(
    r"^\s*(?:API_KEY|API_SECRET)\s*=\s*['\"][^'\"]+['\"]", re.MULTILINE
)


def test_live_api_test_has_no_literal_credential_defaults() -> None:
    source = LIVE_TEST.read_text(encoding="utf-8")

    assert _LITERAL_CREDENTIAL_ASSIGNMENT.search(source) is None
    assert 'os.environ["MAMMOTH_API_KEY"]' in source
    assert 'os.environ["MAMMOTH_API_SECRET"]' in source
