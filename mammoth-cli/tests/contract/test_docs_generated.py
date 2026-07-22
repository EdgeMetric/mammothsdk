"""Contract test: the generated docs corpus is committed and up to date."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_GEN_PATH = Path(__file__).resolve().parents[2] / "scripts" / "gen_docs.py"


def _load_generator() -> object:
    spec = importlib.util.spec_from_file_location("mammoth_cli_gen_docs", _GEN_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_generated_docs_match_committed() -> None:
    generator = _load_generator()
    for path, content in generator.build().items():  # type: ignore[attr-defined]
        assert path.exists(), f"missing generated doc: {path} (run scripts/gen_docs.py)"
        assert path.read_text(encoding="utf-8") == content, (
            f"stale generated doc: {path} — run scripts/gen_docs.py"
        )


def test_generator_check_flag_is_clean() -> None:
    generator = _load_generator()
    assert generator.main(["--check"]) == 0  # type: ignore[attr-defined]
