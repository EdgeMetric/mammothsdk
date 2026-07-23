"""Mammoth CLI — a typed command-line interface for the Mammoth Analytics platform.

All Mammoth transport goes through the public ``mammoth-io`` SDK. The CLI does
not implement a second HTTP client and does not call private SDK members.
"""

from __future__ import annotations

__version__ = "1.0.2"

# The versioned machine output envelope contract.
SCHEMA_VERSION = 1

__all__ = ["__version__", "SCHEMA_VERSION"]
