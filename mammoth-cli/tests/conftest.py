"""Shared test fixtures and path setup for the Mammoth CLI test suite."""

from __future__ import annotations

import sys
from pathlib import Path

CLI_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = CLI_ROOT.parent

# Install the local SDK and CLI as import paths so published PyPI state cannot
# mask local SDK changes during tests.
for path in (REPO_ROOT, CLI_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
