"""Shared pytest configuration and markers."""

from __future__ import annotations


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests (no API calls)")
    config.addinivalue_line("markers", "integration: Integration tests (live API)")
    config.addinivalue_line("markers", "slow: Slow tests")
