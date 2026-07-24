"""Shared fixtures for bespoke command tests: a fake service seam."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> FakeMammothService:
    """Patch the single service-construction seam with a network-free fake."""
    service = FakeMammothService()

    def _build(
        auth: Any,
        *,
        timeout: float | None = None,
        job_timeout: float | None = None,
        pipeline_timeout: float | None = None,
        project_id: int | None = None,
        progress: bool = False,
    ) -> FakeMammothService:
        return service

    monkeypatch.setattr(service_factory, "build_service", _build)
    return service
