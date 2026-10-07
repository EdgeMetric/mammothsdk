"""Fuzz-suite wiring: the report is written once the session ends."""

from __future__ import annotations

import pytest

from tests.fuzz import report


def pytest_sessionfinish(session: pytest.Session) -> None:
    path = report.write_report()
    if path is not None:
        print(f"\nmammoth-cli fuzz report: {path}")
