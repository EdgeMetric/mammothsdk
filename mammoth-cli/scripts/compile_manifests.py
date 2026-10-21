#!/usr/bin/env python3
"""Compile the YAML command manifests to JSON under ``spec/manifests/compiled/``.

The CLI reads the compiled JSON at run time, so it never parses YAML. Run this after
editing anything under ``spec/manifests`` (``build_manifests.py`` runs it too) and
commit the result; ``tests/unit/test_compiled_manifests.py`` fails when it is stale.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mammoth_cli.manifest.loader import compile_manifests  # noqa: E402

if __name__ == "__main__":
    for written in compile_manifests():
        print(f"wrote {written}")
