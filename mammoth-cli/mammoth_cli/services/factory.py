"""Construct the production service for one resolved authentication context.

Commands call :func:`build_service` instead of constructing
:class:`~mammoth_cli.services.sdk_service.SdkMammothService` directly. Tests
monkeypatch this single seam to substitute
:class:`~mammoth_cli.services.testing.FakeMammothService` so no network is
touched.
"""

from __future__ import annotations

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.services.protocol import MammothService
from mammoth_cli.services.sdk_service import SdkMammothService


def build_service(auth: ResolvedAuth, *, timeout: float | None = None) -> MammothService:
    """Build the production SDK-backed service for ``auth``.

    Args:
        auth: Resolved credentials, workspace id, and base url.
        timeout: Optional per-request timeout override, in seconds.

    Returns:
        A :class:`MammothService` implementation backed by ``MammothClient``.
    """
    return SdkMammothService(auth, timeout=timeout)
