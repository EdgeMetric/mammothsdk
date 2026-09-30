"""Every shipped module parses on the oldest Python the packages support.

Both ``mammoth-io`` and ``mammoth-cli`` declare ``requires-python >= 3.12``, but a
formatter targeting 3.14 rewrites ``except (A, B):`` to PEP 758's unparenthesized
``except A, B:``, which 3.12 and 3.13 reject at import time (mammoth/view.py
shipped that way in 0.7.24-0.7.27).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_PACKAGES = (_ROOT / "mammoth", _ROOT / "mammoth-cli" / "mammoth_cli")
_OLDEST = (3, 12)


@pytest.mark.parametrize(
    "path",
    sorted(p for package in _PACKAGES for p in package.rglob("*.py")),
    ids=lambda p: str(p.relative_to(_ROOT)),
)
def test_module_parses_on_the_oldest_supported_python(path: Path) -> None:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=_OLDEST)
